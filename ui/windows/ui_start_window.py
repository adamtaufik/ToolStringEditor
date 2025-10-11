from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor, QPainter, QPainterPath, QImage, QDesktopServices
from PyQt6.QtCore import Qt, QSize, QRectF, QUrl
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from ui.apps.ui_calculations_app import WirelineCalculatorApp
from ui.apps.ui_pce_editor_app import PCEEditor
from ui.apps.ui_survey_app import SGSTXTApp
from ui.apps.ui_simulator_app import WirelineSimulatorApp
from ui.apps.ui_toolstring_editor_app import ToolStringEditor
# from ui.apps.ui_sgs_fgs_app import SGSFGSApp

from ui.components.ui_footer import FooterWidget
from utils.path_finder import get_path, get_icon_path

import os


class AppCard(QPushButton):
    def __init__(self, icon_path: str, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(170, 170)  # square card
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._title = title
        self._subtitle = subtitle
        p = os.fspath(icon_path) if icon_path else ""
        self._img = QImage(p) if (p and os.path.exists(p)) else QImage()

        self._radius = 16
        self._overlay = 0.65
        self.setStyleSheet("AppCard { border: 0; background: transparent; }")

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(22)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(10)
        self._shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(self._shadow)

        # cached, dpi-aware pixmap
        self._scaled_pm = QPixmap()
        self._last_target = QSize()
        self._last_dpr = 0.0
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        if self._img.isNull():
            self._scaled_pm = QPixmap()
            return
        dpr = self.devicePixelRatioF()
        target = QSize(int(self.width() * dpr), int(self.height() * dpr))
        if target == self._last_target and abs(dpr - self._last_dpr) < 1e-3:
            return
        # scale with cover behavior in device pixels
        scaled_img = self._img.scaled(target, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                      Qt.TransformationMode.SmoothTransformation)
        pm = QPixmap.fromImage(scaled_img)
        pm.setDevicePixelRatio(dpr)  # make it Hi-DPI aware
        self._scaled_pm = pm
        self._last_target = target
        self._last_dpr = dpr

    def resizeEvent(self, e):
        self._update_scaled_pixmap()
        super().resizeEvent(e)

    def paintEvent(self, e):
        self._update_scaled_pixmap()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)  # crisp scale

        rect = QRectF(self.rect())
        r = self._radius

        # rounded clip
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        painter.setClipPath(path)

        # draw background image (full-bleed). We simply draw-to-fit; pm has DPR set.
        if not self._scaled_pm.isNull():
            painter.drawPixmap(self.rect(), self._scaled_pm, self._scaled_pm.rect())
        else:
            painter.fillRect(rect, QColor("#2a3038"))

        # subtle darken
        painter.fillRect(rect, QColor(0, 0, 0, 30))

        # glass bar
        bar_h = 76
        bar = QRectF(0, self.height() - bar_h, self.width(), bar_h)
        painter.fillRect(bar, QColor(20, 24, 28, int(self._overlay * 255)))
        painter.fillRect(QRectF(0, self.height() - bar_h, self.width(), 1.0), QColor(255, 255, 255, 22))

        # text
        left = 14
        top = self.height() - bar_h + 12
        painter.setPen(QColor(240, 244, 248))
        painter.setFont(QFont("Segoe UI Semibold", 11))
        painter.drawText(QRectF(left, top, self.width() - 2*left, 24),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._title)

        painter.setPen(QColor(195, 206, 218))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRectF(left, top + 26, self.width() - 2*left, bar_h - 34),
                         Qt.TextFlag.TextWordWrap, self._subtitle)

        # faint outline
        painter.setClipping(False)
        painter.setPen(QColor(255, 255, 255, 26))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), r, r)

    # hover effects
    def enterEvent(self, e):
        self._overlay = 0.75
        self._shadow.setBlurRadius(28)
        self._shadow.setYOffset(14)
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._overlay = 0.65
        self._shadow.setBlurRadius(22)
        self._shadow.setYOffset(10)
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._overlay = 0.82
        self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._overlay = 0.75
        self.update()
        super().mouseReleaseEvent(e)


# ---------- Modern Start Window ----------
class StartWindow(QWidget):
    def __init__(self, app_icon=None):
        super().__init__()
        self.setWindowTitle("Deleum WireHub")
        self.setFixedSize(860, 600)  # a bit wider to breathe

        if app_icon:
            self.setWindowIcon(app_icon)

        # Subtle gradient / image backdrop
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #101418, stop:0.45 #151a21, stop:1 #1a2028);
                color: white;
            }
        """)

        # ---- Top: brand/logo ----
        logo_path = get_path(os.path.join("assets", "icons", "WireHub Logo.png"))
        logo = QLabel()
        if os.path.exists(logo_path):
            logo.setPixmap(QPixmap(logo_path).scaledToHeight(100, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header = QVBoxLayout()
        header.setContentsMargins(0, 15, 0, 15)
        header.addWidget(logo)

        # ---- Center: app cards grid ----
        grid = QGridLayout()
        grid.setContentsMargins(20, 10, 20, 10)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(24)
        grid.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Build cards
        cards_spec = [
            (os.path.join("assets", "icons", "app_toolstring_editor.jpg"),
             "Tool String Editor", "Design & present wireline BHAs", self.open_toolstring_editor_app),

            (os.path.join("assets", "icons", "app_pce_editor.jpg"),
             "PCE Stack-Up Editor", "Design & present PCE Stack-ups", self.open_pce_app),

            (os.path.join("assets", "icons", "app_sgs_txt.jpg"),
             "Survey Interpreter", "Process SGS/FGS data", self.open_sgstxt_app),

            (os.path.join("assets", "icons", "app_calculator.jpg"),
             "Wireline Calculator", "Quick physics & conversions", self.open_calculations_app),

            (os.path.join("assets", "icons", "app_simulator.jpg"),
             "Wireline Simulator", "Model tension/overpull vs depth", self.open_simulator_app),
        ]

        row, col = 0, 0
        max_cols = 3  # like your example: 3 tiles centered
        for icon_rel, title, subtitle_text, callback in cards_spec:
            icon_abs = get_path(icon_rel)
            card = AppCard(icon_abs, title, subtitle_text)
            card.clicked.connect(callback)
            grid.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        # ---- Footer: version ----
        footer_widget = FooterWidget()
        footer_version_info = footer_widget.get_version_info()
        footer = QLabel(footer_version_info)
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer.setStyleSheet("color: #9aa7b5; font-size: 11px; padding: 6px 10px;")

        # ---- Main layout ----
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addLayout(header)
        main.addSpacing(10)
        main.addLayout(grid)
        main.addStretch()
        main.addWidget(footer)


        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 12, 12)
        buttons_layout.setSpacing(8)
        buttons_layout.addStretch()

        # version button
        self.version_btn = QPushButton()
        self.version_btn.setFixedSize(34, 34)
        self.version_btn.setIcon(QIcon(get_icon_path("version")))
        self.version_btn.setIconSize(QSize(18, 18))
        self.version_btn.setToolTip("View version history")
        self.version_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.version_btn.clicked.connect(self.open_version_window)

        # feedback button
        self.feedback_btn = QPushButton()
        self.feedback_btn.setFixedSize(34, 34)
        self.feedback_btn.setIcon(QIcon(get_icon_path("feedback")))  # you can use a 📨 or 💬 icon
        self.feedback_btn.setIconSize(QSize(18, 18))
        self.feedback_btn.setToolTip("Send feedback")
        self.feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.feedback_btn.clicked.connect(self.send_feedback)

        # exit button
        self.exit_btn = QPushButton()
        self.exit_btn.setFixedSize(34, 34)
        self.exit_btn.setIcon(QIcon(get_icon_path("exit")))
        self.exit_btn.setIconSize(QSize(18, 18))
        self.exit_btn.setToolTip("Exit application")
        self.exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exit_btn.clicked.connect(self.close_app)

        # shared style
        button_style = """
            QPushButton {
                border-radius: 17px;
                background-color: rgba(255,255,255,0.08);
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.18);
            }
            QPushButton:pressed {
                background-color: rgba(255,255,255,0.28);
            }
        """
        self.version_btn.setStyleSheet(button_style)
        self.feedback_btn.setStyleSheet(button_style)
        self.exit_btn.setStyleSheet(button_style)

        buttons_layout.addWidget(self.version_btn)
        buttons_layout.addWidget(self.feedback_btn)
        buttons_layout.addWidget(self.exit_btn)

        # ✅ Add buttons *before* footer
        main.addLayout(buttons_layout)
        main.addWidget(footer)


    # ---- Actions ----
    def open_toolstring_editor_app(self):
        self.toolstring_app = ToolStringEditor()
        self.toolstring_app.show()
        self.close()

    def open_pce_app(self):
        self.pce_app = PCEEditor()
        self.pce_app.show()
        self.close()

    def open_sgstxt_app(self):
        self.sgstxt_app = SGSTXTApp()
        self.sgstxt_app.show()
        self.close()

    def open_calculations_app(self):
        self.calculations_app = WirelineCalculatorApp()
        self.calculations_app.show()
        self.close()

    def open_simulator_app(self):
        self.simulator_app = WirelineSimulatorApp()
        self.simulator_app.show()
        self.close()

    def open_version_window(self):
        from ui.windows.ui_version_window import VersionWindow
        self.version_window = VersionWindow()
        self.version_window.show()

    def close_app(self):
        self.close()

    def send_feedback(self):
        recipients = "Adam.MohdTaufik@deleum.com,adam.m.taufik@gmail.com"
        subject = "Deleum WireHub App - Feedback"
        body = "Hi Adam,\n\nI’d like to share some feedback about the WireHub App:\n\n"
        mailto_link = f"mailto:{recipients}?subject={subject}&body={body}"
        QDesktopServices.openUrl(QUrl(mailto_link))
