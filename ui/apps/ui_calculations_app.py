import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox, QHBoxLayout

from features.calculator.MDtoTVD_tab import MDtoTVDTab
from features.calculator.hydrostatic_tab import HydrostaticTab
from features.calculator.shear_pin_tab import ShearPinTab
from features.calculator.weight_tab import WeightTab
from features.calculator.wirefall_tab import WirefallTab
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.theme_manager import apply_theme, toggle_theme

# Wirefall Data Table
data = [
    ("2 3/8\"", "0.092\"", 10),
    ("2 3/8\"", "0.108\"", 8),
    ("2 7/8\"", "0.092\"", 12),
    ("2 7/8\"", "0.108\"", 10),
    ("2 7/8\"", "0.125\"", 8),
    ("3 1/2\"", "0.092\"", 16),
    ("3 1/2\"", "0.108\"", 15),
    ("3 1/2\"", "0.125\"", 7),
]
df = pd.DataFrame(data, columns=["Tubing O.D.", "Wire Size", "Wire Fall/1000'"])

class WirelineCalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wireline Calculator")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)

        # Top-level vertical layout (entire window)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # ✅ Custom Frameless Title Bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            "Wireline Calculator"
        )
        root_layout.addWidget(self.title_bar)

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(WirefallTab(data), "Wirefall")
        self.tabs.addTab(HydrostaticTab(), "Hydrostatic Pressure")
        self.tabs.addTab(WeightTab(), "Tool String Weight")
        self.tabs.addTab(ShearPinTab(), "Shear Pins")
        self.tabs.addTab(MDtoTVDTab(), "MD to TVD")
        # self.set_tab_stylesheet(self.tabs)  # Apply styling to tabs

        # ✅ Toolbar-style sidebar (left) for Save/Load
        items = [
            (get_icon_path('save'), "Save", lambda: QMessageBox.information(self, "Save", "Save not implemented yet."),
             "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load", lambda: QMessageBox.information(self, "Load", "Load not implemented yet."),
             "Open a file (Ctrl+O)"),
        ]
        self.sidebar = SidebarWidget(self, items)

        # Wrap main content with outer layout
        content_wrapper_layout = QVBoxLayout()
        content_wrapper_layout.addWidget(self.tabs)

        # ✅ Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        content_wrapper_layout.addWidget(footer)

        # ✅ Left sidebar + main content wrapper
        full_horizontal_layout = QHBoxLayout()
        full_horizontal_layout.addWidget(self.sidebar)
        full_horizontal_layout.addLayout(content_wrapper_layout)

        root_layout.addLayout(full_horizontal_layout)

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )
