# styles.py

GLASSMORPHISM_STYLE = """
    QMainWindow {
        background: rgba(255, 255, 255, 0.1);
    }

    QToolTip {
        background-color: black;
        color: white;
        border: 1px solid gray;
        padding: 5px;
        font-size: 12px;
        border-radius: 2px;
    }
    
    QToolBar {
        background: rgba(255, 255, 255, 0.2);
        spacing: 5px;
    }

    QToolButton {
        color: white;
        padding: 5px;
        font-weight: bold;
    }
    QToolButton:hover {
        background: rgba(255, 255, 255, 0.25);
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

DELEUM_STYLE = """
    QMainWindow {
        background: #800020;
    }
    
    QToolTip {
        background-color: #800020;
        color: white;
        border: 1px solid gray;
        padding: 5px;
        font-size: 12px;
        border-radius: 2px;
    }

    QToolBar {
        background-color: #5a001a;
        spacing: 5px;
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