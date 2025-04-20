# styles.py
from utils.get_resource_path import get_icon_path

DARK_STYLE = """
    QMainWindow {
        background: #1e1e1e;
    }
    SGSFGSApp, HydrostaticPressureApp {
        background: #1e1e1e;
    }

    CustomTitleBar {
        background-color: #2c2c2c;
        border-bottom: 1px solid #3c3c3c;
    }

    QToolTip {
        background-color: #2b2b2b;
        color: #f0f0f0;
        border: 1px solid #444;
        padding: 5px;
        font-size: 12px;
        border-radius: 4px;
    }

    QToolButton {
        color: #f0f0f0;
        padding: 5px;
        font-weight: bold;
        background-color: transparent;
    }
    QToolButton:hover {
        background: #3a3a3a;
        color: #ffffff;
    }

    QWidget#ToolLibrary {
        background: #252526;
        border-radius: 12px;
        border: 1px solid #3e3e42;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.3);
    }

    QFrame#DropZone {
        background: #2d2d30;
        border-radius: 12px;
        border: 1px solid #444;
    }
    
    QLineEdit, QComboBox {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.4);
        color: white;
        padding: 5px;
        border-radius: 8px;
    }

    QLineEdit::placeholder {
        color: #888;
    }

    QPushButton {
        background: #3a3a3a;
        border: 1px solid #555;
        border-radius: 10px;
        padding: 5px;
        color: #f0f0f0;
    }

    QPushButton:hover {
        background: #4a4a4a;
    }

    QLabel {
        color: #f0f0f0;
    }
"""


DELEUM_STYLE = """
    QMainWindow {
        background: #3d000f;
    }
    SGSFGSApp {
        background: #3d000f;
    }
    HydrostaticPressureApp {
        background: #3d000f;
    }
    
    CustomTitleBar {
    background-color: rgba(93, 0, 20, 0.3); /* Deep wine tint */
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }

    QToolTip {
        background-color: #3d000f;
        color: white;
        border: 1px solid gray;
        padding: 5px;
        font-size: 12px;
        border-radius: 2px;
    }

    QToolButton {
        color: white;
        padding: 5px;
        font-weight: bold;
    }
    QToolButton:hover {
        background-color: #750024;
        color: white;
    }

    QWidget#ToolLibrary {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
    }

    QFrame#DropZone {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    QLineEdit, QComboBox {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.4);
        color: white;
        padding: 5px;
        border-radius: 8px;
    }

    QLineEdit::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }

    QPushButton {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        padding: 5px;
        color: white;
    }

    QPushButton:hover {
        background: rgba(255, 255, 255, 0.25);
    }

    QLabel {
        color: white; 
    }

"""

MESSAGEBOX_STYLE = """
                QMessageBox {
                    background-color: #f0f0f0;
                }
                QLabel {                  
                    background-color: #f0f0f0;
                    color: black;  /* Ensure text is readable */
                }
                QPushButton {
                    background-color: white;
                    border: 1px solid gray;
                    color: black;
                    min-width: 100px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #d6d6d6;
                }
            """

down_arrow = get_icon_path('down_arrow')
up_arrow = get_icon_path('up_arrow')

combo_style = f"""
QComboBox {{
    border: 1px solid #aaa;
    border-radius: 6px;
    padding: 5px 10px;
    background-color: #f9f9f9;
    color: #333;
    font-size: 10pt;
}}

QComboBox:hover {{
    border: 1px solid #555;
}}

QComboBox::drop-down {{
    border: none;
    background-color: transparent;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: url("{down_arrow.replace("\\", "/")}");
    width: 12px;
    height: 12px;
}}

QComboBox::down-arrow:on {{
    image: url("{up_arrow.replace("\\", "/")}");
}}

QComboBox QAbstractItemView {{
    border: 1px solid #aaa;
    border-radius: 6px;
    selection-background-color: #87CEFA;
    selection-color: black;
    background-color: #fff;
    font-size: 10pt;
}}
"""