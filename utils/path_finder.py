import os
import sys

def get_path(relative_path):
    """Get absolute path to resource, working for development and PyInstaller."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Ensure base path is always the project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    joined_path = os.path.join(base_path, relative_path)
    return joined_path

def get_icon_path(name):
    return get_path(os.path.join("assets", "icons", f"{name}.png"))

def get_resource_path(name):
    return get_path(os.path.join("assets", "resources", name))

def get_image_path(name):

    if "X-Over" in name:
        name = "X-Over"  # Normalize X-Over naming
    name = name.replace('"','').replace("'","")
    image_path = get_path(os.path.join("assets", "images", f"{name}.png"))

    if os.path.exists(image_path):
        return image_path
    else:
        return get_path(os.path.join("assets", "images", "Dummy Image.png"))
