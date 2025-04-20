import os

# PyQt6 core modules
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPixmap, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog,
    QLabel, QComboBox, QMessageBox, QFrame
)

# Database & Editor logic
from database.file_io import save_configuration, load_configuration
from editor.loading_worker import LoadingWorker

# UI Components
from ui.components.inputs import AngleInput, LimitedTextEdit
from ui.components.ui_footer import FooterWidget
from ui.components.workers import ExportWorker
from ui.components.ui_dropzone import DropZone
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_summary import SummaryWidget
from ui.components.ui_titlebar import CustomTitleBar
from ui.components.ui_tool_library import ToolLibrary

# Windows
from ui.windows.ui_database_window import DatabaseWindow
from ui.windows.ui_help_window import HelpWindow
from ui.windows.ui_version_window import VersionWindow

# Utils
from utils.check_file import is_file_open
from utils.get_resource_path import get_icon_path
from utils.styles import MESSAGEBOX_STYLE
from utils.theme_manager import toggle_theme, apply_theme


class ToolStringEditor(QMainWindow):
    """Main application window."""
    MIN_WINDOW_HEIGHT = 670  # ✅ Minimum height of the window
    TOOLBAR_HEIGHT = 30  # ✅ Fixed toolbar height
    FOOTER_HEIGHT = 30  # ✅ Fixed footer height
    icon_size = 264

    def __init__(self):
        super().__init__()

        self.current_file_name = None  # Track last saved or loaded filename
        # self.setWindowTitle("Deleum Tool String Editor")
        self.setMinimumHeight(self.MIN_WINDOW_HEIGHT)  # ✅ Set minimum resizable height

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # **Create Main Widget**
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Replace QVBoxLayout in editor with full vertical layout
        main_container = QVBoxLayout(central_widget)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        self.drop_zone = DropZone(self)

        # }
        items = [
            (get_icon_path('save'), "Save", self.save_configuration, "Save the current file (Ctrl+S)", "Ctrl+S"),
            (get_icon_path('load'), "Load", self.load_configuration, "Open a file (Ctrl+O)", "Ctrl+O"),
            (get_icon_path('clear'), "Clear", self.drop_zone.clear_tools, "Clear all tools"),
            (get_icon_path('export'), "Export", self.export_configuration, "Export the tool string"),
            (get_icon_path('help'), "Help", self.show_help_window, "Open help documentation"),
            (get_icon_path('database'), "Tool Database", self.show_database_window, "Open tool database")
        ]


        self.sidebar = SidebarWidget(self, items)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(),"Tool String Editor")

        main_container.addWidget(self.title_bar)

        # Below title bar: Main layout (Sidebar + Content)
        main_body = QHBoxLayout()
        main_body.setContentsMargins(0, 0, 0, 0)

        main_body.addWidget(self.sidebar)

        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 5, 0, 0)

        # ✅ **Set up UI Components**
        self.setup_ui(editor_layout)

        main_body.addLayout(editor_layout)

        main_container.addLayout(main_body)


    def setup_ui(self, editor_layout):
        """Sets up the main UI layout."""

        content_layout = QHBoxLayout()

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

        content_layout.addSpacing(5)

        # **Right Sidebar (Well Details & Summary)**
        input_layout = self.setup_right_sidebar()
        content_layout.addLayout(input_layout)

        editor_layout.addLayout(content_layout)

        # ✅ **Footer**
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button  # ✅ now this won't crash
        editor_layout.addWidget(footer)

        # ✅ **Populate Tools**
        self.tool_library.populate_tool_list("All Tools")

        # ✅ Apply theme to icons immediately
        self.summary_widget.update_icon_colors(self.current_theme)

    def return_to_main_menu(self):
        from ui.windows.ui_start_window import StartWindow  # ⬅️ move import here to avoid circular import
        self.start_window = StartWindow(app_icon=self.windowIcon())
        self.start_window.show()
        self.close()

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
        self.max_angle = AngleInput()
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

        little_layout = QHBoxLayout()
        little_layout.setContentsMargins(0, 0, 0, 0)
        little_layout.setSpacing(5)

        little_layout.addWidget(self.well_no)
        little_layout.addWidget(self.max_angle)
        input_layout.addLayout(little_layout)

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

    def set_icon(self, label, image_path, new_color):
        """Loads an icon, recolors black to the given color while keeping transparency, and sets it to QLabel."""
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap.scaled(self.icon_size, self.icon_size, Qt.AspectRatioMode.KeepAspectRatio))

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,  # ✅ exists now
            summary_widget=self.summary_widget
        )

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
        if is_file_open(excel_path):
            # print(f"⚠️ The file {excel_path} is open in Excel. Please close it and try again.")

            print(f"Excel is currently open. Please close any Excel windows and try again.")

            # ✅ Show success message
            msg_error = QMessageBox(self)
            msg_error.setWindowTitle("Export failed")
            # msg_error.setText(f"⚠️ The file {excel_path} is open in Excel. Please close it and try again.")

            msg_error.setText(f"Excel is currently open. Please close any Excel windows and try again.")

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

    def on_export_finished(self, final_directory):
        """Called when the export thread is finished."""

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
                self.max_angle.text(),
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
                self.max_angle,
                self.well_type,
                self.operation_details,
                self.comments,  # ✅ Load comments
                self.drop_zone
            )

            # ✅ Set the window title to show the current file name
            base_name = os.path.basename(file_name)  # Extract just the filename
            # self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(),f"Deleum Tool String Editor - {base_name}")
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

