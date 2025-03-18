import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.ui_mainwindow import MainWindow




if __name__ == "__main__":
    app = QApplication([])

    # # ✅ Set a universal font
    font_selected = "Roboto"
    modern_font = QFont(font_selected)
    modern_font.setPointSize(10)  # Adjust size as needed
    app.setFont(modern_font)

    # ✅ Apply style ONLY to tooltips
    app.setStyleSheet("""
        QToolTip {
            background-color: black;
            color: white;
            border: 1px solid gray;
            padding: 5px;
            font-size: 12px;
        }
    """)

    window = MainWindow()
    window.show()

    exit_code = app.exec()  # ✅ Store exit code
    del window  # ✅ Explicitly delete window before exit
    sys.exit(exit_code)

