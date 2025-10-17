import os
import sys
import time
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtGui import QFont, QPixmap, QIcon, QGuiApplication

from auth.microsoft_login import login_with_microsoft
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
        self.timer.start(50)

    def process_tasks(self):
        if self.current_task >= self.total_tasks:
            self.timer.stop()
            return

        task = self.tasks[self.current_task]
        progress = int((self.current_task + 1) / self.total_tasks * 100)
        self.splash.showMessage(
            f"{task['message']}\nProgress: {progress}%",
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
        )
        QApplication.processEvents()
        time.sleep(task["duration"] / 1000)
        self.current_task += 1


if __name__ == "__main__":
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    # Splash Screen
    icon_path = get_path(os.path.join("assets", "icons", "logo_full_qTd_icon.ico"))
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    splash_path = get_path(os.path.join("assets", "backgrounds", "splash.png"))
    splash_image = QPixmap(splash_path)
    splash = QSplashScreen(splash_image)
    splash.show()
    splash.setFont(QFont("Roboto", 12))

    splash.showMessage("Authenticating Microsoft account...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
    QApplication.processEvents()

    # ---- Microsoft Login ----
    result = login_with_microsoft()
    if "access_token" not in result:
        QMessageBox.critical(None, "Login Failed", "Microsoft login was unsuccessful.\nPlease try again.")
        sys.exit(0)

    user_name = result["id_token_claims"].get("name", "Unknown User")
    user_email = result["id_token_claims"].get("preferred_username", "Unknown Email")

    print(f"Login successful: {user_name} ({user_email})")

    # ---- Trial Check ----
    expiration_date = datetime(2025, 12, 31)
    today = datetime.today()
    days_left = (expiration_date - today).days
    if days_left < 0:
        QMessageBox.critical(None, "Trial Expired",
            "The free trial period has ended.\nPlease contact Adam to continue using the app.")
        sys.exit(0)
    else:
        QMessageBox.information(None, "Free Trial",
            f"Valid until {expiration_date.strftime('%d %B %Y')}.\nDays remaining: {days_left} day(s).")

    # ---- Initialization ----
    app.setFont(QFont("Roboto", 10))
    init_manager = InitializationManager(splash)
    init_manager.start_initialization()

    while init_manager.timer.isActive():
        app.processEvents()

    # ---- Start Window ----
    splash.showMessage("Starting application...", Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
    QApplication.processEvents()

    window = StartWindow(app_icon=app_icon)
    splash.finish(window)
    window.show()

    sys.exit(app.exec())
