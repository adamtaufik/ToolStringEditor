import sys

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

screen = QGuiApplication.primaryScreen()
if screen:
    geometry = screen.availableGeometry()
    screen_width = geometry.width()
    screen_height = geometry.height()

def get_height():
    return screen_height

def get_width():
    return screen_height