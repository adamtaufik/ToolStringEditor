import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, working for development and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Ensure base path is always the project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    joined_path = os.path.join(base_path, relative_path)
    return joined_path
