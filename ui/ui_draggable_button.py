from PyQt6.QtWidgets import QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QCursor, QDrag, QColor, QPalette

feedback_style = "background-color: rgba(163, 163, 163, 1);"

class DraggableButton(QPushButton):
    """A button that can be dragged to DropZone."""
    def __init__(self, tool_name, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)  # Adjust size as needed
        self.tool_name = tool_name

        # ✅ **Override Parent Styles & Set Light Gray Background**
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor("lightgray"))
        self.setPalette(palette)

        # ✅ Ensure it always shows the Open hand
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

        # ✅ Create layout to hold the image and text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # ✅ Tool Name Label
        self.text_label = QLabel(self.tool_name, self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.text_label.setStyleSheet("background-color: lightgray;")
        layout.addWidget(self.text_label)

        self.setLayout(layout)

        # ✅ **Force Light Gray Background**
        self.setStyleSheet("""
            QPushButton {
                background-color: lightgray !important;
                border-radius: 5px;
                padding: 5px;
                color: black !important;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.9) !important;  /* Slightly darker on hover */
            }
        """)

    def enterEvent(self, event):
        """Ensure cursor is always a hand when hovering over the tool."""
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setStyleSheet(feedback_style)
        self.text_label.setStyleSheet(feedback_style)

    def leaveEvent(self, event):
        self.setStyleSheet("background-color: lightgray;")
        self.text_label.setStyleSheet("background-color: lightgray;")

    def mousePressEvent(self, event):
        """Change cursor to grabbing hand when starting drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))  # ✊ Grabbing cursor

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
