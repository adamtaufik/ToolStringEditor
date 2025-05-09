from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout, QMenu, QApplication
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QCursor, QDrag, QColor, QPalette, QAction

FEEDBACK_STYLE = """background-color: rgba(163, 163, 163, 1);
                border-radius: 5px !important;
                border: 0px solid #555 !important;"""

class DraggableButton(QPushButton):
    def __init__(self, tool_name, dropzone=None, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.tool_name = tool_name
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
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

        # Full style
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

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setStyleSheet(FEEDBACK_STYLE)
        self.text_label.setStyleSheet(FEEDBACK_STYLE)

    def leaveEvent(self, event):
        self.setStyleSheet(self.default_stylesheet)
        self.text_label.setStyleSheet("background-color: lightgray;")


    def mousePressEvent(self, event):
        """Change cursor to grabbing hand when starting drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))  # ✊ Grabbing cursor
        super().mousePressEvent(event)  # Ensure built-in behavior

    def mouseMoveEvent(self, event):
        """Initiate drag when moving the mouse while holding the tool."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.tool_name)
            drag.setMimeData(mime_data)

            # **Create Drag Pixmap**
            pixmap = QPixmap(self.size())  # Capture button appearance
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())  # Cursor stays at click position

            drag.exec(Qt.DropAction.CopyAction)
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))  # 🖕 Restore hand cursor after drop

    def mouseReleaseEvent(self, event):
        """Reset cursor after drag completes."""
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))  # 🔄 Ensure cursor stays a hand

    def contextMenuEvent(self, event):
        """Show right-click menu with 'Add to DropZone'."""
        menu = QMenu(self)
        add_action = QAction("Add to DropZone", self)
        add_action.triggered.connect(lambda: self.dropzone.add_tool(self.tool_name))
        menu.addAction(add_action)
        menu.exec(event.globalPos())
