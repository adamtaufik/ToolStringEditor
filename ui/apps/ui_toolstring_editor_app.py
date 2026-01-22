# ui/apps/ui_toolstring_editor_app.py
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from ui.components.ui_base_editor import BaseEditor
from ui.components.inputs import AngleInput
from ui.components.toolstring_editor.ui_dropzone import DropZone
from ui.components.toolstring_editor.ui_tool_library import ToolLibrary
from ui.components.toolstring_editor.ui_summary import SummaryWidget
from ui.components.ui_footer import FooterWidget
from ui.windows.ui_database_window import DatabaseWindow
from database.file_io import save_configuration, load_configuration
from features.editors.ts_export_manager import export_configuration
from utils.path_finder import get_icon_path
from utils.screen_info import get_width, get_height, get_screen_width, get_screen_height


class ToolStringEditor(BaseEditor):
    """Tool String Editor window."""

    def __init__(self):
        # Define sidebar items first (don't reference self.drop_zone here)
        sidebar_items = [
            (get_icon_path('save'), "Save", lambda: save_configuration(self), "Save the current file (Ctrl+S)",
             "Ctrl+S"),
            (get_icon_path('load'), "Load", lambda: load_configuration(self), "Open a file (Ctrl+O)", "Ctrl+O"),
            (get_icon_path('copy'), "Copy as Image", self.copy_dropzone_to_clipboard,
             "Copy current tool config as PNG (Ctrl+C)", "Ctrl+C"),
            (get_icon_path('clear'), "Clear", self.clear_tools, "Clear all tools"),  # Changed to use method
            (get_icon_path('export'), "Export", lambda: export_configuration(self), "Export to Excel"),
            (get_icon_path('help'), "Help", self.show_help_window, "Open help documentation"),
            (get_icon_path('database'), "Tool Database", self.show_database_window, "Open tool database")
        ]

        # Call super().__init__() FIRST
        super().__init__(
            window_title="Tool String Editor",
            sidebar_items=sidebar_items,
            drop_zone_class=DropZone,
            tool_library_class=ToolLibrary,
            summary_widget_class=SummaryWidget
        )

    def setup_editor_ui(self):
        """Sets up the ToolStringEditor-specific UI."""
        # Create drop zone now that super().__init__() is complete
        self.drop_zone = self.create_drop_zone()

        content_layout = self.setup_common_sidebar("Tool Library", drop_zone_width=784)

        # Add angle input for ToolStringEditor
        self.max_angle = AngleInput()

        # Right Sidebar
        self.right_panel = self.setup_common_right_sidebar(fixed_width=150)
        content_layout.addWidget(self.right_panel)

        self.editor_layout.addLayout(content_layout)

        # Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        self.editor_layout.addWidget(footer)

        # Start with sidebar invisible (opacity 0)
        self.right_panel.setGraphicsEffect(QGraphicsOpacityEffect(self.right_panel))
        self.right_panel.graphicsEffect().setOpacity(0.0)

        # Populate tools and fade in sidebar
        self.tool_library.update_tool_list()
        self.fade_right_sidebar(True, delay=300)

        # Detect screen size
        screen_width = get_screen_width()
        screen_height = get_screen_height()

        # Full-screen
        if screen_width/screen_height < 2:
            QTimer.singleShot(0, self._maximize_after_init)

    def _maximize_after_init(self):
        """Ensure the window properly maximizes after initialization."""
        self.showMaximized()
        if hasattr(self, "title_bar"):
            self.title_bar.maximized = True
            self.title_bar.maximize_btn.setText("🗗")


    def clear_tools(self):
        """Clear all tools from drop zone."""
        if hasattr(self, 'drop_zone') and self.drop_zone:
            self.drop_zone.clear_tools()

    def show_database_window(self):
        self.database_window = DatabaseWindow("Tool")
        self.database_window.show()