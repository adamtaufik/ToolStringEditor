# styles.py
from utils.path_finder import get_icon_path
DARK_STYLE = """
    QMainWindow, SGSFGSApp, SGSTXTApp, HydrostaticPressureApp, WirelineCalculatorApp {
        background: qlineargradient(
            x1: 0, y1: 0,
            x2: 1, y2: 1,
            stop: 0 #1a1a1a,
            stop: 1 #0f0f0f
        );
    }

    CustomTitleBar {
        background-color: rgba(20, 20, 20, 0.9);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    QTabWidget::pane {
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(30, 30, 30, 0.7);
        border-radius: 6px;
    }

    QTabBar::tab {
        background: rgba(60, 60, 60, 0.6);
        color: #f0f0f0;
        padding: 8px 14px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-family: "Segoe UI";
        font-weight: 500;
    }

    QTabBar::tab:selected {
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.25);
        color: white;
    }

    QTabBar::tab:!selected {
        margin-top: 2px;
    }

    QToolTip {
        background-color: rgba(40, 40, 40, 0.95);
        color: #f0f0f0;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 5px;
        font-size: 12px;
        border-radius: 4px;
    }

    QToolButton {
        color: #f0f0f0;
        padding: 6px;
        font-weight: bold;
        background-color: transparent;
    }
    QToolButton:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    QWidget#ToolLibrary {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    QFrame#DropZone {
        background: rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    QLineEdit, QComboBox {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #f0f0f0;
        padding: 5px;
        border-radius: 8px;
        font-family: "Segoe UI";
    }

    QLineEdit::placeholder {
        color: rgba(255, 255, 255, 0.4);
    }

    QPushButton {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 8px;
        padding: 6px 12px;
        color: #f0f0f0;
        font-weight: 600;
        font-family: "Segoe UI";
    }

    QPushButton:hover {
        background: rgba(255, 255, 255, 0.22);
    }

    QLabel {
        color: #f5f5f5;
        font-family: "Segoe UI";
    }

    QScrollBar:vertical {
        background: rgba(255, 255, 255, 0.05);
        width: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:vertical {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background: rgba(255, 255, 255, 0.35);
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background: rgba(255, 255, 255, 0.05);
        height: 12px;
        border-radius: 6px;
    }

    QScrollBar::handle:horizontal {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        min-width: 20px;
    }

    QScrollBar::handle:horizontal:hover {
        background: rgba(255, 255, 255, 0.35);
    }
"""

DELEUM_STYLE = """
    QMainWindow, SGSFGSApp, SGSTXTApp, HydrostaticPressureApp, WirelineCalculatorApp, WirelineSimulatorApp {
        background: qlineargradient(
            x1: 0, y1: 0,
            x2: 1, y2: 1,
            stop: 0 #4a0012,
            stop: 1 #2b0008
        );
    }

    CustomTitleBar {
        background-color: rgba(93, 0, 20, 0.3); /* Deep wine tint */
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }

    QTabWidget::pane {
        border: 1px solid #76797C;
        background: rgba(45, 45, 45, 230);
        border-radius: 4px;
    }

    QTabBar::tab {
        background: rgba(65, 65, 65, 230);
        color: white;
        padding: 8px;
        border: 1px solid #76797C;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-family: "Segoe UI";
        font-weight: 500;
    }

    QTabBar::tab:selected {
        background: rgba(85, 85, 85, 230);
        border-color: #76797C;
    }

    QTabBar::tab:!selected {
        margin-top: 2px;
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
        font-family: "Segoe UI";
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
        font-weight: 600;
        font-family: "Segoe UI";
    }

    QPushButton:hover {
        background: rgba(255, 255, 255, 0.25);
    }

    QLabel {
        color: white; 
        font-family: "Segoe UI";
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

COMBO_STYLE = f"""
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
                image: url("{get_icon_path('down_arrow').replace("\\", "/")}");
                width: 12px;
                height: 12px;
            }}
            
            QComboBox::down-arrow:on {{
                image: url("{get_icon_path('up_arrow').replace("\\", "/")}");
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

COMBO_STYLE_BLACK = f"""
            QComboBox {{
                border: 1px solid #aaa;
                border-radius: 6px;
                padding: 5px 10px;
                background-color: #f9f9f9;
                color: black;
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
                image: url("{get_icon_path('down_arrow').replace("\\", "/")}");
                width: 12px;
                height: 12px;
            }}

            QComboBox::down-arrow:on {{
                image: url("{get_icon_path('up_arrow').replace("\\", "/")}");
            }}

            QComboBox QAbstractItemView {{
                border: 1px solid #aaa;
                border-radius: 6px;
                selection-background-color: #87CEFA;
                selection-color: black;
                background-color: #fff;
                color: black;
                font-size: 10pt;
            }}
            """

SIDEBAR_STYLE = """
            #sidebar {
                background-color: #1e1e2f;
                border-right: 1px solid #2e2e3e;
            }
            QPushButton#toggleButton {
                color: white;
                background-color: #2b2b3d;
                border: none;
                padding: 8px;
                border-radius: 6px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton#toggleButton:hover {
                background-color: #3b3b50;
            }
            QPushButton#menuItem {
                color: white;
                background-color: transparent;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
                text-align: left;
            }
            QPushButton#menuItem:hover {
                background-color: #3c3c4f;
            }
        """

TOGGLE_BUTTON = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 0px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                font-size: 10pt;
                color: white;
                padding: 5px 10px;
                backdrop-filter: blur(6px);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

MAIN_MENU_BUTTON = """
                QPushButton {
                    background-color: #f1f1f1;
                    color: #800020;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0e0e6;
                }
            """

HELP_WINDOW = """
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLabel#pageLabel {
                font-size: 14px;
                color: #555555;
                padding: 4px 8px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """

DROPZONE_STYLE = """
            background-color: white; 
            border: 0px solid gray; 
            border-radius: 10px;
        """

DROPZONE_HEADERS = """
            font-weight: bold; 
            font-size: 8pt;
            background-color: #f0f0f0; 
            border: 0px white;
            border-bottom: 2px solid #A9A9A9; 
            color: black;
            border-radius: 5px;
            """

# Set the stylesheet for all group boxes to have white background
GROUPBOX_STYLE = """
            QGroupBox {
                color: white;
                border: 1px solid white;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            """
MODERN_GROUPBOX_STYLE = """
QGroupBox {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    color: {text_color};
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    margin-top: 5px;
    padding: 25px 0px 0px 0px; /* Top padding added to make space for title */
}}

QGroupBox::title {{
    background-color: transparent;
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 0px;
    margin: 10px;
}}

QGroupBox::frame {{
    background: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 rgba(255, 255, 255, 0.2),
        stop: 1 rgba(255, 255, 255, 0.05)
    );
    border-radius: 10px;
}}
"""

TEMPLATE_BUTTON = """
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """

ACTION_BUTTON = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
"""

DELETE_BUTTON = """
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """

CHECKBOX_STYLE = """
            QCheckBox {
                color: white;
            }
            """