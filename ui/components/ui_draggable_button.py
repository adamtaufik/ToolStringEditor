from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout, QMenu, QApplication, QToolTip
from PyQt6.QtCore import Qt, QMimeData, QTimer
from PyQt6.QtGui import QPixmap, QCursor, QDrag, QColor, QPalette, QAction
from reportlab.platypus.paraparser import sizeDelta

FEEDBACK_STYLE = """background-color: rgba(163, 163, 163, 1);
                border-radius: 5px !important;
                border: 0px solid #555 !important;"""

class DraggableButton(QPushButton):
    def __init__(self, tool_name, dropzone=None, description:str|None=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.tool_name = tool_name
        self.description = (description or "").strip()
        self.dropzone = dropzone

        # Set initial palette and cursor
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor("lightgray"))
        self.setPalette(palette)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

        # Layout for label
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.text_label = QLabel(self.tool_name, self)
        font = self.text_label.font()
        size = 10
        if 'X-Over' in self.tool_name:
            size = 8
        font.setPointSize(size)  # Set the desired font size
        self.text_label.setFont(font)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

        # Style
        self.default_stylesheet = """
            QPushButton {
                background-color: lightgray !important;
                border-radius: 5px !important;
                border: 0px solid #555 !important;
                padding: 5px;
                color: black !important;
                text-align: left;
            }
        """
        self.setStyleSheet(self.default_stylesheet)
        self.text_label.setStyleSheet("background-color: lightgray;")

        # Delayed tooltip timer (≈1.5 s = “a few seconds” feel without feeling laggy)
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.setInterval(6000)
        self._tooltip_timer.timeout.connect(self._show_delayed_tooltip)

        # Set a default tooltip as well (fallback if OS uses default delays)
        if self.description:
            self.setToolTip(self.description)

    # --- Tooltip helpers ---
    def _show_delayed_tooltip(self):
        text = self.description or self.tool_name
        QToolTip.showText(QCursor.pos(), text, self)

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setStyleSheet(FEEDBACK_STYLE)
        self.text_label.setStyleSheet(FEEDBACK_STYLE)
        # start delayed tooltip
        self._tooltip_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_stylesheet)
        self.text_label.setStyleSheet("background-color: lightgray;")
        # stop tooltip if leaving early
        self._tooltip_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    # --- Drag behavior ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.tool_name)
            drag.setMimeData(mime_data)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())
            drag.exec(Qt.DropAction.CopyAction)

            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        add_action = QAction("Add to DropZone", self)
        if self.dropzone is not None:
            add_action.triggered.connect(lambda: self.dropzone.add_tool(self.tool_name))
        menu.addAction(add_action)
        menu.exec(event.globalPos())
