from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor


class SpinnerWidget(QWidget):
    """Custom minimalist spinner animation."""

    def __init__(self, parent=None, size=60, line_width=4, color="#0078D7"):
        super().__init__(parent)
        self.size = size
        self.line_width = line_width
        self.color = QColor(color)
        self.angle = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(16)  # ~60 FPS

        self.setFixedSize(self.size + 10, self.size + 10)

    def rotate(self):
        self.angle = (self.angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(5, 5, self.size, self.size)

        pen = QPen(self.color, self.line_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw 270° arc (3/4 circle)
        painter.drawArc(rect, int(self.angle * 16), int(270 * 16))


class LoadingDialog(QDialog):
    """Displays a spinning circle while exporting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporting...")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background-color: rgba(245, 245, 245, 255); border-radius: 12px;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        # ✅ Add spinner
        self.spinner = SpinnerWidget(self, size=60, line_width=5, color="#0078D7")
        layout.addWidget(self.spinner)

        self.setFixedSize(120, 120)

    def stop(self):
        """Stops animation and closes the dialog."""
        print("Stopping LoadingDialog()")
        self.spinner.timer.stop()
        self.accept()


class LoadingWorker(QThread):
    """Runs the loading dialog in the main thread while exporting in the background."""

    start_signal = pyqtSignal()
    stop_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_dialog = LoadingDialog(parent)
        self.start_signal.connect(self.loading_dialog.show)
        self.stop_signal.connect(self.loading_dialog.stop)

    def run(self):
        self.start_signal.emit()
        self.exec()

    def stop_dialog(self):
        self.stop_signal.emit()
        self.quit()
