import os
import sys
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont, QIcon, QGuiApplication

from ui.windows.ui_start_window import StartWindow
from ui.windows.ui_video_splash import VideoSplashScreen
from utils.path_finder import get_path

# -------------------------
# Worker for Microsoft Login
# -------------------------
class LoginWorker(QThread):
    finished = pyqtSignal(dict)

    def run(self):
        from auth.microsoft_login import login_with_microsoft
        result = login_with_microsoft()
        self.finished.emit(result)

# -------------------------
# Initialization Manager
# -------------------------
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
        self.timer.start(50)

    def process_tasks(self):
        if self.current_task >= self.total_tasks:
            self.timer.stop()
            return

        task = self.tasks[self.current_task]
        progress = int((self.current_task + 1) / self.total_tasks * 100)
        self.splash.update_message(f"{task['message']}\nProgress: {progress}%")
        QApplication.processEvents()
        time.sleep(task["duration"] / 1000)
        self.current_task += 1

# -------------------------
# Main Application
# -------------------------
main_window = None  # global reference to prevent GC

def show_trial_check_and_start_window(user_name, user_email):
    global main_window

    # Trial Check
    expiration_date = datetime(2026, 1, 15)
    today = datetime.today()
    days_left = (expiration_date - today).days

    if days_left < 0:
        QMessageBox.critical(
            splash,
            "Trial Expired",
            "The free trial period has ended.\nPlease contact Adam to continue using the app.",
        )
        sys.exit(0)
    else:
        QMessageBox.information(
            splash,
            "Free Trial",
            f"Valid until {expiration_date.strftime('%d %B %Y')}.\nDays remaining: {days_left} day(s).",
        )

    # Initialization
    app.setFont(QFont("Roboto", 10))
    init_manager = InitializationManager(splash)
    init_manager.start_initialization()

    # Keep splash responsive during initialization
    while init_manager.timer.isActive():
        app.processEvents()

    # Start main window
    splash.update_message("Starting application...")
    QApplication.processEvents()
    main_window = StartWindow(app_icon=app_icon)
    splash.close()
    main_window.show()

if __name__ == "__main__":
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    # App icon
    icon_path = get_path(os.path.join("assets", "icons", "logo_full_qTd_icon.ico"))
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # Splash Screen
    splash = VideoSplashScreen()
    splash.show()
    splash.update_message("Authenticating Microsoft account...")
    QApplication.processEvents()

    # Temporarily remove topmost so login popup is in front
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
    splash.show()

    # -------------------------
    # Start login in background
    # -------------------------
    def on_login_finished(result):
        splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        splash.show()

        if "access_token" not in result:
            QMessageBox.critical(
                splash,
                "Login Failed",
                "Microsoft login was unsuccessful.\nPlease try again."
            )
            sys.exit(0)

        user_name = result["id_token_claims"].get("name", "Unknown User")
        user_email = result["id_token_claims"].get("preferred_username", "Unknown Email")
        print(f"Login successful: {user_name} ({user_email})")

        # Continue with trial check and initialization
        show_trial_check_and_start_window(user_name, user_email)

    login_thread = LoginWorker()
    login_thread.finished.connect(on_login_finished)
    login_thread.start()

    sys.exit(app.exec())
