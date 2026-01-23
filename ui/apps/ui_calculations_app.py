import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QMessageBox, QHBoxLayout

from features.calculator.MDtoTVD_tab import MDtoTVDTab
from features.calculator.hydrostatic_tab import HydrostaticTab
from features.calculator.perforation_correlation_tab import PerforationOffsetTab
from features.calculator.shear_pin_tab import ShearPinTab
from features.calculator.spool_capacity_tab import SpoolCapacityTab
from features.calculator.toollift_tab import ToolLiftTab
from features.calculator.weight_tab import WeightTab
from features.calculator.wirefall_tab import WirefallTab
# from features.calculator.wirefall_tab import WirefallTab
from features.calculator.wireweight_tab import WireWeightTab
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.screen_info import get_height
from utils.theme_manager import apply_theme, toggle_theme

# Wirefall Data Table
data = [
    ("2 3/8\"", "0.092\"", 10),
    ("2 3/8\"", "0.108\"", 8),
    ("2 3/8\"", "0.125\"", 5),
    ("2 7/8\"", "0.092\"", 12),
    ("2 7/8\"", "0.108\"", 10),
    ("2 7/8\"", "0.125\"", 8),
    ("3 1/2\"", "0.092\"", 16),
    ("3 1/2\"", "0.108\"", 15),
    ("3 1/2\"", "0.125\"", 7),
    ("4 1/2\"", "0.108\"", 27),
    ("4 1/2\"", "0.125\"", 22),
    ("5 1/2\"", "0.108\"", 40),
    ("5 1/2\"", "0.125\"", 35),
    ("7 5/8\"", "0.108\"", 120),
    ("7 5/8\"", "0.125\"", 110),
    ("9 5/8\"", "0.125\"", 300),
]
df = pd.DataFrame(data, columns=["Tubing O.D.", "Wire Size", "Wire Fall/1000'"])

class WirelineCalculatorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wireline Calculator")
        self.setMinimumWidth(1280)
        self.setMinimumHeight(get_height() - 10)  # ✅ Set minimum resizable height

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
        self.tabs.addTab(HydrostaticTab(), "Hydrostatic Pressure")
        self.tabs.addTab(ToolLiftTab(), "Tool Lift Calculation")
        self.tabs.addTab(WirefallTab(data), "Wirefall")
        self.tabs.addTab(WeightTab(), "Tool String Weight")
        self.tabs.addTab(WireWeightTab(), "Wire Weight")
        self.tabs.addTab(ShearPinTab(), "Shear Pins")
        self.tabs.addTab(MDtoTVDTab(), "MD to TVD")
        self.tabs.addTab(SpoolCapacityTab(), "Spool Capacity")
        self.tabs.addTab(PerforationOffsetTab(), "Perforation Correlation")
        self.set_tab_stylesheet(self.tabs)  # Apply styling to tabs

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

    def set_tab_stylesheet(self, tabs: QTabWidget):
        """Apply a modern, premium Fluent-style design to the tabs."""
        accent = "#0078D7"  # Fluent blue accent
        bg_dark = "#1E1E1E"
        bg_light = "#F5F6F7"
        text_light = "#F0F0F0"
        text_dark = "#333333"
        shadow = "rgba(0, 0, 0, 0.15)"

        # Detect theme (you already use self.current_theme)
        is_dark = self.current_theme.lower() in ["dark", "deleum"]
        base_bg = bg_dark if is_dark else bg_light
        text_color = text_light if is_dark else text_dark

        tabs.setStyleSheet(f"""
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}

        QTabBar {{
            background: transparent;
            qproperty-drawBase: 0;
        }}

        QTabBar::tab {{
            background-color: {base_bg};
            color: {text_color};
            border-radius: 10px;
            padding: 8px 24px;
            margin: 6px 4px;
            font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', Arial;
            font-size: 15px;
            font-weight: 500;
            letter-spacing: 0.3px;
            transition: all 150ms ease-in-out;
            box-shadow: 0px 2px 4px {shadow};
        }}

        QTabBar::tab:hover {{
            background-color: {'#2D2D2D' if is_dark else '#E9ECEF'};
            color: {'#FFFFFF' if is_dark else '#111111'};
            transform: translateY(-1px);
        }}

        QTabBar::tab:selected {{
            background-color: {accent};
            color: white;
            font-weight: 600;
            box-shadow: 0px 4px 10px rgba(0, 120, 215, 0.3);
        }}

        QTabBar::tab:!selected {{
            opacity: 0.9;
        }}

        QTabWidget::tab-bar {{
            alignment: center;
        }}
        """)
