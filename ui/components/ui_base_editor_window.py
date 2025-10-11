# ui/windows/ui_base_editor_window.py
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QRectF
from PyQt6.QtGui import QGuiApplication, QPainterPath, QRegion, QCursor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsOpacityEffect
)

from ui.components.ui_titlebar import CustomTitleBar
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.windows.ui_messagebox_window import MessageBoxWindow
from utils.theme_manager import toggle_theme, apply_theme


class BaseEditorWindow(QMainWindow):
    """
    A reusable frameless base window for all editor apps.
    Handles:
        - Rounded corners
        - Resize and drag
        - Theme toggle
        - Sidebar and footer
        - Fade animations
    """

    RESIZE_MARGIN = 8

    def __init__(self, title="Editor Window", sidebar_items=None):
        super().__init__()

        # --- Window setup ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # --- Theme ---
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # --- Root layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Title bar ---
        self.title_bar = CustomTitleBar(self, self._toggle_sidebar_visibility, title)
        main_layout.addWidget(self.title_bar)

        # --- Body layout (Sidebar + Main + Right panel) ---
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)
        main_layout.addLayout(self.body_layout)

        # --- Sidebar ---
        self.sidebar = SidebarWidget(self, sidebar_items or [])
        self.body_layout.addWidget(self.sidebar)

        # --- Editor container ---
        self.editor_container = QVBoxLayout()
        self.editor_container.setContentsMargins(0, 5, 0, 0)
        self.body_layout.addLayout(self.editor_container)

        # --- Right panel placeholder ---
        self.right_panel = None

        # --- Footer ---
        self.footer = FooterWidget(self, theme_callback=self._toggle_theme)
        self.theme_button = self.footer.theme_button
        main_layout.addWidget(self.footer)

        # Fade animation setup
        QTimer.singleShot(300, lambda: self._fade_right_panel(True))

        # Enable interactive behavior
        self.setMouseTracking(True)
        self.enable_mouse_tracking(self)

        # For dragging and resizing
        self.resizing = False
        self.resize_dir = None
        self.dragging = False
        self.drag_start_pos = None
        self.normal_geometry = None
        self.is_maximized_by_drag = False

    # -------------------------------------------------------------------------
    #  🧱 ABSTRACT-LIKE METHODS
    # -------------------------------------------------------------------------
    def setup_editor_content(self):
        """
        To be overridden by subclasses.
        Populate editor_container with drop zones, right panels, etc.
        """
        raise NotImplementedError("Subclasses must implement setup_editor_content()")

    # -------------------------------------------------------------------------
    #  🌙 THEME
    # -------------------------------------------------------------------------
    def _toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button
        )

    # -------------------------------------------------------------------------
    #  🎬 SIDEBAR VISIBILITY + FADE
    # -------------------------------------------------------------------------
    def _toggle_sidebar_visibility(self):
        """Called by titlebar menu button."""
        self.sidebar.toggle_sidebar()

    def _fade_right_panel(self, visible: bool):
        if not self.right_panel:
            return
        if not hasattr(self.right_panel, "opacity_effect"):
            self.right_panel.opacity_effect = QGraphicsOpacityEffect(self.right_panel)
            self.right_panel.setGraphicsEffect(self.right_panel.opacity_effect)

        anim = QPropertyAnimation(self.right_panel.opacity_effect, b"opacity")
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.setStartValue(0.0 if visible else 1.0)
        anim.setEndValue(1.0 if visible else 0.0)

        if not visible:
            anim.finished.connect(lambda: self.right_panel.hide())
        else:
            self.right_panel.show()

        anim.start()
        self._fade_anim = anim

    # -------------------------------------------------------------------------
    #  🪟 ROUNDED CORNERS
    # -------------------------------------------------------------------------
    def set_rounded_corners(self, radius=12):
        rect = QRectF(0, 0, float(self.width()), float(self.height()))
        path = QPainterPath()
        path.addRoundedRect(rect, float(radius), float(radius))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_rounded_corners()

    # -------------------------------------------------------------------------
    #  🖱️ DRAGGING & RESIZING
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_pos = event.globalPosition().toPoint()
            self._geo = self.geometry()
            self.drag_start_pos = event.globalPosition().toPoint()
            margin = self.RESIZE_MARGIN
            x, y = event.position().x(), event.position().y()
            w, h = self.width(), self.height()

            # Determine resize direction
            if x <= margin and y <= margin:
                self.resize_dir = "topleft"
            elif x >= w - margin and y <= margin:
                self.resize_dir = "topright"
            elif x <= margin and y >= h - margin:
                self.resize_dir = "bottomleft"
            elif x >= w - margin and y >= h - margin:
                self.resize_dir = "bottomright"
            elif x <= margin:
                self.resize_dir = "left"
            elif x >= w - margin:
                self.resize_dir = "right"
            elif y <= margin:
                self.resize_dir = "top"
            elif y >= h - margin:
                self.resize_dir = "bottom"
            else:
                self.resize_dir = None

            if not self.resize_dir:
                self.dragging = True
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            if self.resize_dir:
                self.resizing = True
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        margin = self.RESIZE_MARGIN
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()

        # Cursor feedback
        if not self.resizing:
            if x <= margin and y <= margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif x >= w - margin and y <= margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif x <= margin and y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif x >= w - margin and y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif x <= margin or x >= w - margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif y <= margin or y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        # Resizing
        if self.resizing:
            delta = event.globalPosition().toPoint() - self._mouse_pos
            geom = QRect(self._geo)
            if "left" in self.resize_dir:
                geom.setLeft(geom.left() + delta.x())
            if "right" in self.resize_dir:
                geom.setRight(geom.right() + delta.x())
            if "top" in self.resize_dir:
                geom.setTop(geom.top() + delta.y())
            if "bottom" in self.resize_dir:
                geom.setBottom(geom.bottom() + delta.y())

            if geom.width() >= self.minimumWidth() and geom.height() >= self.minimumHeight():
                self.setGeometry(geom)
                self.set_rounded_corners()
            return

        # Moving
        if self.dragging:
            global_pos = event.globalPosition().toPoint()
            new_pos = global_pos - self.drag_offset
            self.move(new_pos)

            # Snap maximize
            if global_pos.y() <= 5 and not self.is_maximized_by_drag:
                self.normal_geometry = self.geometry()
                self.showMaximized()
                self.is_maximized_by_drag = True
            elif self.is_maximized_by_drag and global_pos.y() > 50:
                self.showNormal()
                if self.normal_geometry:
                    self.setGeometry(self.normal_geometry)
                self.is_maximized_by_drag = False

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.resize_dir = None
        self.dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def enable_mouse_tracking(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
