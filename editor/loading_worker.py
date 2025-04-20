from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QMovie
import os
from utils.get_resource_path import get_resource_path


class LoadingDialog(QDialog):
    """Displays a loading animation while exporting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporting...")

        # ✅ **Set background color to light gray**
        self.setStyleSheet("background-color: rgba(240, 240, 240, 255); border-radius: 0px;")

        # ✅ **Remove title bar and make it frameless**
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        # ✅ **Layout & GIF Label**
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.setContentsMargins(10, 10, 10, 10)

        # ✅ **Load & Scale GIF**
        gif_path = get_resource_path(os.path.join("assets", "resources", "new_loading.gif"))
        print(f"Finding GIF at: {gif_path}")

        self.movie = QMovie(gif_path)

        if not self.movie.isValid():
            print("❌ ERROR: Invalid GIF File - Check File Path or Format")
            return  # Prevent crash if GIF is invalid
        else:
            print("✅ GIF is valid")

        # self.movie.setScaledSize(self.movie.currentPixmap().size().scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        self.label.setMovie(self.movie)
        self.movie.start()

        # ✅ **Set window size to match the GIF**
        # self.setFixedSize(100, 100)

    def stop(self):
        """Stops the loading animation and closes the dialog."""
        print("Stopping LoadingDialog()")
        self.movie.stop()
        self.accept()


class LoadingWorker(QThread):
    """Runs the loading dialog in the main thread while exporting in the background."""

    start_signal = pyqtSignal()  # ✅ Signal to show the dialog
    stop_signal = pyqtSignal()  # ✅ Signal to stop the dialog

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loading_dialog = LoadingDialog(parent)  # ✅ Create the dialog in the main thread
        # ✅ Connect signals
        self.start_signal.connect(self.loading_dialog.show)
        self.stop_signal.connect(self.loading_dialog.stop)

    def run(self):
        """Shows the loading dialog while exporting."""
        self.start_signal.emit()
        self.exec()  # ✅ Keep the thread running

    def stop_dialog(self):
        """Stops and closes the loading dialog safely."""
        self.stop_signal.emit()  # ✅ Close dialog safely
        self.quit()  # ✅ Stop the thread
