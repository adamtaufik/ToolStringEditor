import sys
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

screen = QGuiApplication.primaryScreen()
if screen:
    geometry = screen.availableGeometry()
    screen_width = geometry.width()
    screen_height = geometry.height()
else:
    screen_width = 1920
    screen_height = 1080

def get_height():
    return screen_height

def get_width():
    return screen_width


def get_primary_screen_geometry():
    """Return the available geometry of the primary screen (excluding taskbar)."""
    app = QApplication.instance() or QApplication(sys.argv)
    screen = QGuiApplication.primaryScreen()
    if screen:
        geometry = screen.availableGeometry()  # excludes taskbar/docks
        return geometry.width(), geometry.height()
    return 1920, 1080  # fallback


def get_screen_width():
    """Get current screen width dynamically."""
    width, _ = get_primary_screen_geometry()
    return width


def get_screen_height():
    """Get current screen height dynamically."""
    _, height = get_primary_screen_geometry()
    return height