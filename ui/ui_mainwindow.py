import os
import psutil

from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QCursor, QPixmap, QColor, QPainter
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel,
    QComboBox, QToolBar, QToolButton, QMessageBox, QPushButton, QFrame, QTextEdit
)

from database.logic_saveload import save_configuration, load_configuration
from editor.loading_worker import LoadingWorker
from editor.logic_export import export_to_excel
from ui.ui_database_window import DatabaseWindow
from ui.ui_dropzone import DropZone
from ui.ui_help_window import HelpWindow
from ui.ui_summary import SummaryWidget
from ui.ui_tool_library import ToolLibrary
from ui.ui_version_window import VersionWindow
from utils.get_resource_path import get_resource_path
from utils.styles import GLASSMORPHISM_STYLE, DELEUM_STYLE, MESSAGEBOX_STYLE


class MainWindow(QMainWindow):
    """Main application window."""
    MIN_WINDOW_HEIGHT = 670  # ✅ Minimum height of the window
    TOOLBAR_HEIGHT = 30  # ✅ Fixed toolbar height
    FOOTER_HEIGHT = 30  # ✅ Fixed footer height
    icon_size = 264
    
    def __init__(self):
        super().__init__()

        self.current_file_name = None  # Track last saved or loaded filename
        self.setWindowTitle("Deleum Tool String Editor")
        self.setMinimumHeight(self.MIN_WINDOW_HEIGHT)  # ✅ Set minimum resizable height
        # ✅ Start maximized properly using a delayed approach
        QTimer.singleShot(0, self.force_maximize)

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        self.apply_theme()

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
        self.tool_library_label.setStyleSheet("font-weight: bold; color: white; font-size: 16px;")
        self.sidebar_layout.addWidget(self.tool_library_label)

        self.tool_library = ToolLibrary(self)  # ✅ Initialize Tool Library
        self.sidebar_layout.addWidget(self.tool_library)

        sidebar_container.setLayout(self.sidebar_layout)
        sidebar_container.setFixedWidth(230)
        content_layout.addWidget(sidebar_container)

        # **Drop Zone**
        content_layout.addWidget(self.drop_zone)
        self.drop_zone.setFixedWidth(900)

        # **Right Sidebar (Well Details & Summary)**
        input_layout = self.setup_right_sidebar()
        content_layout.addLayout(input_layout)

        main_layout.addLayout(content_layout)

        # ✅ **Footer**
        self.setup_footer(main_layout)

        # ✅ **Populate Tools**
        self.tool_library.populate_tool_list("All Tools")

        # ✅ Apply theme to icons immediately
        self.summary_widget.update_icon_colors(self.current_theme)


    def force_maximize(self):
        """Forces the window to maximize properly after the UI initializes."""
        self.showNormal()  # Reset window state
        self.showMaximized()  # Apply true maximization

    def setup_right_sidebar(self):
        """Creates the right sidebar for well details & summary."""

        # right_sidebar_layout = QVBoxLayout()

        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        input_layout.setContentsMargins(10, 0, 10, 0)
        input_layout.setSpacing(10)
        # input_layout.setFixedWidth(230)

        self.well_details_label = QLabel("Well Details")
        self.well_details_label.setStyleSheet("font: bold; font-size: 12pt;")
        input_layout.addWidget(self.well_details_label)

        self.client_name = QLineEdit(placeholderText="Client Name")
        self.location = QLineEdit(placeholderText="Location")
        self.well_no = QLineEdit(placeholderText="Well No.")
        self.operation_details = QLineEdit(placeholderText="Operation Details")

        self.well_type = QComboBox()
        self.well_type.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.well_type.addItems([
            "Oil Producer",
            "Gas Producer",
            "Water Injection",
            "Gas Injection",
            "Development Well",
            "Exploration Well",
            "CCUS Well"])
        self.well_type.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: transparent;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
            }
        """)

        input_layout.addWidget(self.client_name)
        input_layout.addWidget(self.location)
        input_layout.addWidget(self.well_no)
        input_layout.addWidget(self.well_type)
        input_layout.addWidget(self.operation_details)

        # **Separator Line**
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setStyleSheet("background-color: white; height: 1px;")  # Make the line white and thick
        input_layout.addWidget(line1)

        self.summary_label = QLabel("Summary")
        self.summary_label.setStyleSheet("font: bold; font-size: 12pt;")
        input_layout.addWidget(self.summary_label)

        self.summary_widget = SummaryWidget(self.drop_zone)
        input_layout.addWidget(self.summary_widget)

        # **Separator Line**
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setStyleSheet("background-color: white; height: 1px;")  # Make the line white and thick
        input_layout.addWidget(line2)

        # Use this custom widget in your sidebar setup
        self.comments = LimitedTextEdit(max_lines=5)
        input_layout.addWidget(self.comments, alignment=Qt.AlignmentFlag.AlignTop)

        input_layout.setContentsMargins(3, 10, 8, 0)

        return input_layout

    def load_summary_icons(self):
        """Loads and updates summary icons based on the current theme."""

        # ✅ Determine correct color based on theme
        if self.current_theme in ["Deleum", "Glassmorphism"]:
            icon_color = QColor("white")  # 🔹 Dark themes → Make black parts WHITE
        else:
            icon_color = QColor("black")  # 🔹 Light themes → Keep black parts BLACK

        # ✅ Define icon paths
        icon_paths = {
            "od": get_resource_path("assets/images/icon_od.png"),
            "length": get_resource_path("assets/images/icon_length.png"),
            "weight": get_resource_path("assets/images/icon_weight.png")
        }

        # ✅ Apply colorized icons
        self.set_icon(self.icon_od, icon_paths["od"], icon_color)
        self.set_icon(self.icon_length, icon_paths["length"], icon_color)
        self.set_icon(self.icon_weight, icon_paths["weight"], icon_color)

    def set_icon(self, label, image_path, new_color):
        """Loads an icon, recolors black to the given color while keeping transparency, and sets it to QLabel."""
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            print(f"⚠️ WARNING: Icon not found at {image_path}")
            return

        # ✅ Create a new pixmap with the same size as original
        colored_pixmap = QPixmap(pixmap.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)  # ✅ Keep transparency

        # ✅ Recolor only black parts while preserving transparency
        painter = QPainter(colored_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)  # Draw original icon

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(colored_pixmap.rect(), new_color)  # Apply color ONLY to non-transparent areas

        painter.end()  # ✅ Finish painting

        # ✅ Set the final recolored icon to the QLabel
        label.setPixmap(colored_pixmap.scaled(self.icon_size, self.icon_size, Qt.AspectRatioMode.KeepAspectRatio))

    def setup_footer(self, main_layout):
        """Creates the footer layout with theme toggle."""
        footer_layout = QHBoxLayout()

        # ✅ Theme Toggle Button (Lower Left)
        self.theme_button = QPushButton("Theme: Deleum")
        self.theme_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                font-size: 10pt;
            }
            QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.theme_button.setFixedHeight(self.FOOTER_HEIGHT)
        footer_layout.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignLeft)

        footer_layout.addStretch()  # Pushes text to the right

        # ✅ Footer Text (Lower Right)
        footer_label = QLabel("Created by Adam Mohd Taufik - Operations Engineer  |  Version 1.0 (20/03/2025)")
        footer_label.setStyleSheet("font-size: 10pt; color: white; padding: 5px;")
        footer_label.setFixedHeight(self.FOOTER_HEIGHT)
        footer_layout.addWidget(footer_label, alignment=Qt.AlignmentFlag.AlignRight)

        footer_layout.setContentsMargins(3, 0, 3, 3)

        main_layout.addLayout(footer_layout)

    def create_toolbar(self):
        """Creates a toolbar with buttons and keyboard shortcuts."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setFixedHeight(self.TOOLBAR_HEIGHT)

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
            action.setToolTip(tooltip)
            action.triggered.connect(func)

            if shortcut:
                action.setShortcut(shortcut[0])

            toolbar.addAction(action)  # ✅ Ensure actions are added to the toolbar
            self.addAction(action)  # ✅ Ensure shortcuts work even when the toolbar is hidden

        for child in toolbar.findChildren(QToolButton):
            child.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.addToolBar(toolbar)

    def toggle_theme(self):
        """Toggles between Glassmorphism and Deleum themes."""
        if self.current_theme == "Deleum":
            self.current_theme = "Dark"
            self.setStyleSheet(GLASSMORPHISM_STYLE)
            self.theme_button.setText("Theme: Dark")  # ✅ Update button text
        else:
            self.current_theme = "Deleum"
            self.setStyleSheet(DELEUM_STYLE)
            self.theme_button.setText("Theme: Deleum")  # ✅ Update button text

        # ✅ Update Summary Icons with New Theme
        self.summary_widget.update_icon_colors(self.current_theme)

    def apply_theme(self):
        """Applies the current theme."""
        if self.current_theme == "Dark":
            self.setStyleSheet(GLASSMORPHISM_STYLE)
        else:
            self.setStyleSheet(DELEUM_STYLE)

    def export_configuration(self):
        """Exports the current tool string to an Excel file in a separate thread."""

        # Suggest filename based on client + location or last saved file
        default_name = self.current_file_name or f"{self.location.text()}_{self.well_no.text()}_{self.operation_details.text()}".replace(" ", "_")
        default_path = os.path.join(os.getcwd(), default_name.replace(".json",""))  # Set default path

        # ✅ Check if DropZone is empty
        if not self.drop_zone.tool_widgets:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Export Error")
            msg_box.setText("The tool string is empty. Please add tools before exporting.")

            msg_box.setStyleSheet(MESSAGEBOX_STYLE)
            msg_box.exec()
            return  # ✅ Stop export process if empty

        file_dialog = QFileDialog()
        excel_path, _ = file_dialog.getSaveFileName(self, "Save Excel File", default_path, "Excel Files (*.xlsx)")

        if not excel_path:
            return  # ✅ Exit if user cancels

        # Before saving
        if self.is_file_open(excel_path):
            print(f"⚠️ The file {excel_path} is open in Excel. Please close it and try again.")

            # ✅ Show success message
            msg_error = QMessageBox(self)
            msg_error.setWindowTitle("Export failed")
            msg_error.setText(f"⚠️ The file {excel_path} is open in Excel. Please close it and try again.")

            msg_error.setStyleSheet(MESSAGEBOX_STYLE)
            msg_error.setIcon(QMessageBox.Icon.Warning)

            msg_error.exec()

            return  # Stop execution

        pdf_path = excel_path.replace(".xlsx", ".pdf")
        final_directory = os.path.dirname(excel_path)  # ✅ Extract directory

        # ✅ **Start Loading Animation in a Separate Thread**
        self.loading_worker = LoadingWorker(self)
        self.loading_worker.start()

        # ✅ **Start Export in a Background Thread**
        self.export_thread = ExportWorker(self, excel_path, pdf_path, final_directory)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.start()

    def is_file_open(self, file_path):
        """Check if a file is open in another program."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if "EXCEL.EXE" in proc.info['name'].upper():
                    return True  # Excel is open, likely locking the file
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

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

        msg.setStyleSheet(MESSAGEBOX_STYLE)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        # ✅ Show dialog and check user response
        response = msg.exec()

        # ✅ Open actual save directory if user clicks "Yes"
        if response == QMessageBox.StandardButton.Yes:
            try:
                os.startfile(final_directory)  # ✅ Opens the correct folder
            except Exception as e:
                print(f"⚠️ ERROR: Unable to open folder: {e}")

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
                self.comments.toPlainText(),  # ✅ Save comments
                self.drop_zone
            )

            # ✅ Set the window title to show the saved file name
            base_name = os.path.basename(file_name)
            self.setWindowTitle(f"Deleum Tool String Editor - {base_name}")

            # ✅ Show success message
            msg_save = QMessageBox(self)
            msg_save.setWindowTitle("Save Successful")
            msg_save.setText("Tool string saved successfully!")

            msg_save.setStyleSheet(MESSAGEBOX_STYLE)
            msg_save.setIcon(QMessageBox.Icon.Information)

            msg_save.exec()

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
                self.comments,  # ✅ Load comments
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
        print(f"The client name being sent to the function is:\n{self.parent.client_name.text()}\n")
        print(f"The comments being sent to the function is:\n{self.parent.comments.toPlainText()}\n")
        export_to_excel(self.excel_path, self.pdf_path,
                        self.parent.client_name.text(),
                        self.parent.location.text(),
                        self.parent.well_no.text(),
                        self.parent.well_type.currentText(),
                        self.parent.operation_details.text(),
                        self.parent.comments.toPlainText(),
                        self.parent.drop_zone)

        self.finished.emit(self.final_directory)  # ✅ Emit directory when done

class LimitedTextEdit(QTextEdit):
    def __init__(self, max_lines=5):
        super().__init__()
        self.max_lines = max_lines
        self.setPlaceholderText(f"Remarks (max {max_lines} lines)")
        self.setFixedHeight(5 * 20)  # Approx height for 5 lines
        self.textChanged.connect(self.limit_lines)

        # **Apply Rounded Border Style**
        self.setStyleSheet("""
            QTextEdit {
                border-radius: 8px;
                padding: 5px;
                background-color: white;
            }
        """)

    def limit_lines(self):
        """Restrict text to a maximum of `max_lines` lines."""
        text = self.toPlainText()
        lines = text.split("\n")

        if len(lines) > self.max_lines:
            # Keep only the first `max_lines` lines
            self.setPlainText("\n".join(lines[:self.max_lines]))

            # Move cursor to end of text
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.setTextCursor(cursor)
