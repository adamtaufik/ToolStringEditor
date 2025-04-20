from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtWidgets import QWidget

class ThemeToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._thumb_pos = 2
        self.clicked_callback = None  # ✅ initialize as a normal attribute
        self.setFixedSize(100, 30)

        self.animation = QPropertyAnimation(self, b"thumb_pos", self)
        self.animation.setDuration(200)


    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_thumb()

    def toggle(self):
        self.setChecked(not self._checked)
        if callable(self.clicked_callback):
            self.clicked_callback(self._checked)

    def _animate_thumb(self):
        start = self._thumb_pos
        end = self.width() - 28 if self._checked else 2
        self.animation.stop()
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()

    def mousePressEvent(self, event):
        self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_color = QColor("#4e5d6c") if not self._checked else QColor("#2ecc71")
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

        # Thumb
        thumb_rect = QRectF(self._thumb_pos, 2, 26, 26)
        painter.setBrush(QColor("white"))
        painter.drawEllipse(thumb_rect)

        # Labels
        painter.setPen(QColor("white"))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "Deleum" if not self._checked else "")
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "Dark" if self._checked else "")

    def get_thumb_pos(self):
        return self._thumb_pos

    def set_thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()

    thumb_pos = pyqtProperty(int, fget=get_thumb_pos, fset=set_thumb_pos)

    # def clicked_callback(self, is_dark):
    #     pass  # placeholder
