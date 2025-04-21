from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox

from utils.path_finder import get_icon_path
from utils.styles import MESSAGEBOX_STYLE


class MessageBoxWindow(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)

    def message_simple(self, title, text, icon=None):

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        if isinstance(icon, QMessageBox.Icon):
            msg_box.setIcon(icon)
        elif isinstance(icon, str):
            pixmap = QPixmap(get_icon_path(icon))
            msg_box.setIconPixmap(pixmap.scaled(64, 64))  # Resize if needed

        msg_box.setText(text)
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        msg_box.exec()

    def message_yes_no(self, title, text, icon=None):

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        msg_box.setIcon(icon)  # Use the default warning icon if path is invalid

        # Style: black text, bordered buttons, hover feedback
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        return msg_box.exec()
