import os
import subprocess
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, 
    QComboBox, QToolBar, QToolButton, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from editor.loading_worker import LoadingDialog, LoadingWorker  # ✅ Import the loading animation worker
from editor.logic_export import export_to_excel
from PyQt6.QtGui import QAction, QKeySequence, QCursor
from ui.ui_dropzone import DropZone
from ui.ui_tool_library import ToolLibrary
from ui.ui_database_window import DatabaseWindow
from ui.ui_version_window import VersionWindow
from ui.ui_help_window import HelpWindow
from database.logic_saveload import save_configuration, load_configuration

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.current_file_name = None  # Track last saved or loaded filename
        self.setWindowTitle("Deleum Tool String Editor")
        self.showMaximized()
        self.setStyleSheet("background-color: #800020;")  # Burgundy color

        # **Create Main Widget**
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # **Main Layout**
        main_layout = QVBoxLayout(central_widget)
        
        main_layout.setContentsMargins(0, 5, 0, 0)

        # ✅ **Initialize DropZone FIRST**
        self.drop_zone = DropZone(self)  

        # ✅ **Create Toolbar**
        self.create_toolbar()

        # ✅ **Set up UI Components**
        self.setup_ui(main_layout)

        # self.setStyleSheet("""
        #     QToolTip {
        #         color: white;
        #     }
        # """)

    def setup_ui(self, main_layout):
        """Sets up the main UI layout."""

        # **Content Layouts**
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # **Sidebar Container (Tool Library)**
        sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(sidebar_container)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        # **Tool Library**
        self.tool_library_label = QLabel("Tool Library")
        self.tool_library_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        self.sidebar_layout.addWidget(self.tool_library_label)

        self.tool_library = ToolLibrary(self)  # ✅ Initialize Tool Library
        self.sidebar_layout.addWidget(self.tool_library)

        sidebar_container.setLayout(self.sidebar_layout)
        sidebar_container.setFixedWidth(220)
        content_layout.addWidget(sidebar_container)

        # **Drop Zone**
        content_layout.addWidget(self.drop_zone)

        # **Right Sidebar (Well Details & Summary)**
        input_layout = self.setup_right_sidebar()
        content_layout.addLayout(input_layout)

        main_layout.addLayout(content_layout)

        # ✅ **Footer**
        self.setup_footer(main_layout)

        # ✅ **Populate Tools**
        self.tool_library.populate_tool_list("All Tools")

    def setup_right_sidebar(self):
        """Creates the right sidebar for well details & summary."""
        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(15)

        line_edit_style = """
            QLineEdit {
                color: white;
                border: 1px solid white;
                padding: 5px;
                background-color: transparent;
                border-radius: 5px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.7);
            }
        """

        self.client_name = QLineEdit(placeholderText="Client Name", styleSheet=line_edit_style)
        input_layout.addWidget(self.client_name)

        self.location = QLineEdit(placeholderText="Location", styleSheet=line_edit_style)
        input_layout.addWidget(self.location)

        self.well_no = QLineEdit(placeholderText="Well No.", styleSheet=line_edit_style)
        input_layout.addWidget(self.well_no)

        self.well_type = QComboBox()
        self.well_type.addItems(["Oil Producer", "Gas Producer", "Water Injection", "Gas Injection"])
        self.well_type.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: transparent;
                border: 1px solid white;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
            }
        """)
        input_layout.addWidget(self.well_type)

        self.operation_details = QLineEdit(placeholderText="Operation Details", styleSheet=line_edit_style)
        input_layout.addWidget(self.operation_details)

        self.summary_label = QLabel("Max OD: \t\t0.000\"\nTotal Length: \t0.00 ft\nTotal Weight: \t0.00 lbs")
        self.summary_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        input_layout.addWidget(self.summary_label)

        return input_layout

    def setup_footer(self, main_layout):
        """Creates the footer layout."""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        footer_label = QLabel("Created by Adam Mohd Taufik - Operation Engineer  |  Version 1.0 (16/03/2025)")
        footer_label.setStyleSheet("font: italic; font-size: 10pt; color: white; padding: 5px;")
        footer_layout.addWidget(footer_label, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(footer_layout)

    def create_toolbar(self):
        """Creates a toolbar with buttons and keyboard shortcuts."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
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
        """)
        toolbar.setIconSize(QSize(24, 24))

        # ✅ Define actions with tooltips
        actions = {
            "Save": (self.save_configuration, "Save the current file (Ctrl+S)", QKeySequence("Ctrl+S")),
            "Load": (self.load_configuration, "Open a file (Ctrl+O)", QKeySequence("Ctrl+O")),
            "Clear": (self.drop_zone.clear_tools, "Clear all tools"),
            "Export": (self.export_configuration, "Export the tool string"),
            "Tool Database": (self.show_database_window, "Open tool database"),
            "Help": (self.show_help_window, "Open help documentation"),
            "Version History": (self.show_version_window, "View version history"),
            "Exit": (self.close, "Exit application")
        }

        for text, (func, tooltip, *shortcut) in actions.items():
            action = QAction(text, self)
            action.setToolTip(tooltip)  # ✅ Set tooltip
            action.triggered.connect(func)

            if shortcut:  # ✅ Assign shortcut if available
                action.setShortcut(shortcut[0])

            toolbar.addAction(action)

            toolbar.addAction(action)
            self.addAction(action)  # ✅ Ensure shortcuts work even when the toolbar is hidden
    
        for child in toolbar.findChildren(QToolButton):
            child.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
        self.addToolBar(toolbar)

    def export_configuration(self):
        """Exports the current tool string to an Excel file in a separate thread."""

        # Suggest filename based on client + location or last saved file
        default_name = self.current_file_name or f"{self.location.text()}_{self.well_no.text()}_{self.operation_details.text()}".replace(" ", "_")
        default_path = os.path.join(os.getcwd(), default_name)  # Set default path

        # ✅ Check if DropZone is empty
        if not self.drop_zone.tool_widgets:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Export Error")
            msg_box.setText("The tool string is empty. Please add tools before exporting.")
            msg_box.setStyleSheet("background-color: lightgray; color: black")
            msg_box.exec()
            return  # ✅ Stop export process if empty

        file_dialog = QFileDialog()
        excel_path, _ = file_dialog.getSaveFileName(self, "Save Excel File", default_path, "Excel Files (*.xlsx)")

        if not excel_path:
            return  # ✅ Exit if user cancels

        pdf_path = excel_path.replace(".xlsx", ".pdf")
        final_directory = os.path.dirname(excel_path)  # ✅ Extract directory

        # ✅ **Start Loading Animation in a Separate Thread**
        self.loading_worker = LoadingWorker(self)
        self.loading_worker.start()

        # ✅ **Start Export in a Background Thread**
        self.export_thread = ExportWorker(self, excel_path, pdf_path, final_directory)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.start()

    def on_export_finished(self, final_directory):
        """Called when the export thread is finished."""

        # ✅ **Stop Loading Animation Safely**
        if hasattr(self, 'loading_worker'):
            self.loading_worker.stop_dialog()

        # ✅ Show success message
        msg = QMessageBox(self)
        msg.setWindowTitle("Export Successful")
        msg.setText(
            f"Tool string exported successfully!\n\n📂 Folder location:\n{final_directory}\n\nWould you like to open the folder?")

        msg.setStyleSheet("""
            QMessageBox {
                background-color: #f0f0f0;
            }
            QLabel {                  
                background-color: #f0f0f0;
                color: black;  /* Ensure text is readable */
            }
            QPushButton {
                background-color: white;
            }
            QPushButton:hover {
                background-color: #d6d6d6;
            }
        """)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        # ✅ Show dialog and check user response
        response = msg.exec()

        # ✅ Open actual save directory if user clicks "Yes"
        if response == QMessageBox.StandardButton.Yes:
            subprocess.Popen(f'explorer "{final_directory}"')

    def save_configuration(self):

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Configuration", self.current_file_name or "", "JSON Files (*.json)"
        )
        if file_name:
            self.current_file_name = file_name  # Store the file name
            save_configuration(
                file_name,
                self.client_name.text(),
                self.location.text(),
                self.well_no.text(),
                self.well_type.currentText(),
                self.operation_details.text(),
                self.drop_zone
            )

            # ✅ Set the window title to show the saved file name
            base_name = os.path.basename(file_name)
            self.setWindowTitle(f"Deleum Tool String Editor - {base_name}")

    def load_configuration(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Configuration", "", "JSON Files (*.json)")

        if file_name:
            self.current_file_name = file_name  # Store the file name
            load_configuration(
                file_name,
                self.client_name,
                self.location,
                self.well_no,
                self.well_type,
                self.operation_details,
                self.drop_zone
            )

            # ✅ Set the window title to show the current file name
            base_name = os.path.basename(file_name)  # Extract just the filename
            self.setWindowTitle(f"Deleum Tool String Editor - {base_name}")

    def show_database_window(self):
        self.database_window = DatabaseWindow()
        self.database_window.show()

    def show_version_window(self):
        self.version_window = VersionWindow()
        self.version_window.show()

    def show_help_window(self):
        self.help_window = HelpWindow()
        self.help_window.show()

    def closeEvent(self, event):
        """Ensure proper cleanup on exit to prevent crashes."""
        self.deleteLater()  # ✅ Explicitly delete the window
        event.accept()


class ExportWorker(QThread):
    """Handles the export process in a separate thread."""
    finished = pyqtSignal(str)  # ✅ Emit the directory as a string

    def __init__(self, parent, excel_path, pdf_path, final_directory):
        super().__init__(parent)
        self.parent = parent
        self.excel_path = excel_path
        self.pdf_path = pdf_path
        self.final_directory = final_directory  # ✅ Save the directory

    def run(self):
        """Runs the export logic in a background thread."""
        print('running export_to_excel')
        export_to_excel(self.excel_path, self.pdf_path,
                        self.parent.client_name.text(),
                        self.parent.location.text(),
                        self.parent.well_no.text(),
                        self.parent.well_type.currentText(),
                        self.parent.operation_details.text(),
                        self.parent.drop_zone)

        self.finished.emit(self.final_directory)  # ✅ Emit directory when done