import os
import sys
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QFont, QPixmap, QIcon

from ui.windows.ui_start_window import StartWindow
from utils.path_finder import get_path


class InitializationManager:
    def __init__(self, splash):
        self.splash = splash
        self.tasks = [
            {"message": "Loading core components...", "duration": 100},
            {"message": "Initializing database connections...", "duration": 300},
            {"message": "Loading user configuration...", "duration": 200},
            {"message": "Preparing UI assets...", "duration": 400},
            {"message": "Starting application services...", "duration": 300},
        ]
        self.current_task = 0
        self.total_tasks = len(self.tasks)
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_tasks)

    def start_initialization(self):
        self.timer.start(50)  # Update every 50ms

    def process_tasks(self):
        if self.current_task >= self.total_tasks:
            self.timer.stop()
            return

        task = self.tasks[self.current_task]
        progress = int((self.current_task + 1) / self.total_tasks * 100)

        # Update splash screen
        self.splash.showMessage(
            f"{task['message']}\nProgress: {progress}%",
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
        )

        # Simulate real work (replace with actual initialization code)
        QApplication.processEvents()  # Keep UI responsive
        time.sleep(task['duration'] / 1000)  # Replace this with real work

        self.current_task += 1


if __name__ == "__main__":
    app = QApplication([])

    # Set application icon
    icon_path = get_path(os.path.join("assets", "icons", "logo_full_qTd_icon.ico"))
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # Create splash screen
    splash_path = get_path(os.path.join("assets", "backgrounds", "splash.png"))
    splash_image = QPixmap(splash_path)
    splash = QSplashScreen(splash_image)
    splash.show()

    # Set font
    splash_font = QFont("Roboto", 12)
    splash.setFont(splash_font)

    # Initialize and start loading process
    init_manager = InitializationManager(splash)
    init_manager.start_initialization()

    # Set application font while loading
    app.setFont(QFont("Roboto", 10))

    # Create main window
    window = StartWindow(app_icon=app_icon)

    # Wait for initialization to complete
    while init_manager.timer.isActive():
        app.processEvents()

    # Show main window and clean up
    splash.finish(window)
    window.show()

    exit_code = app.exec()
    del window
    sys.exit(exit_code)