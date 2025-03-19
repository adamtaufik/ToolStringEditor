import os
import sys
import time

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QFont, QPixmap, QIcon
from ui.ui_mainwindow import MainWindow
from utils.get_resource_path import get_resource_path

if __name__ == "__main__":
    app = QApplication([])

    # ✅ Set Application Icon (For Taskbar & Title Bar)
    icon_path = get_resource_path(os.path.join("assets", "images", "logo_full_qTd_icon.ico"))
    app_icon = QIcon(icon_path)  # Replace with your actual icon path
    app.setWindowIcon(app_icon)

    # ✅ Create a Splash Screen
    splash_path = get_resource_path(os.path.join("assets", "images", "splash.png"))
    splash_image = QPixmap(splash_path)  # Replace with your splash screen image
    splash = QSplashScreen(splash_image)
    splash.show()

    # ✅ Set "Loading..." font size
    loading_font = QFont("Roboto", 14, QFont.Weight.Bold)  # Increased font size
    splash.setFont(loading_font)  # Apply the font to the message

    # ✅ Simulate Loading Process
    for _ in range(100):
        time.sleep(0.02)  # Adjust loading time
        splash.showMessage(f"Loading... {_}%", alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)

    # # ✅ Set a universal font
    font_selected = "Roboto"
    modern_font = QFont(font_selected)
    modern_font.setPointSize(10)  # Adjust size as needed
    app.setFont(modern_font)


    window = MainWindow()
    window.setWindowIcon(app_icon)
    splash.finish(window)  # Close splash when main window is ready
    window.show()

    exit_code = app.exec()  # ✅ Store exit code
    del window  # ✅ Explicitly delete window before exit
    sys.exit(exit_code)

