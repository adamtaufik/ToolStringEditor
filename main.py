import os
import sys
import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QFont, QPixmap, QIcon

from ui.windows.ui_start_window import StartWindow
from utils.path_finder import get_path

if __name__ == "__main__":
    app = QApplication([])

    # ✅ Set Application Icon (For Taskbar & Title Bar)
    icon_path = get_path(os.path.join("assets", "icons", "logo_full_qTd_icon.ico"))
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    # ✅ Create a Splash Screen
    splash_path = get_path(os.path.join("assets", "backgrounds", "splash.png"))
    splash_image = QPixmap(splash_path)
    splash = QSplashScreen(splash_image)
    splash.show()

    # ✅ Set "Loading..." font size
    loading_font = QFont("Roboto", 14, QFont.Weight.Bold)
    splash.setFont(loading_font)

    # ✅ Simulate Loading Process
    for i in range(100):
        time.sleep(0.01)
        splash.showMessage(f"Loading... {i}%", alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

    # ✅ Set universal app font
    app.setFont(QFont("Roboto", 10))

    # ✅ Launch Start Window instead of MainWindow directly
    window = StartWindow(app_icon=app_icon)
    splash.finish(window)
    window.show()

    exit_code = app.exec()
    del window
    sys.exit(exit_code)
