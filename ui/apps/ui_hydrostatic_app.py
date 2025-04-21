from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QGridLayout, QListWidget
)
from PyQt6.QtCore import Qt

from features.hydrostatic.calculations import calculate_pressure
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.theme_manager import apply_theme, toggle_theme


class HydrostaticPressureApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hydrostatic Pressure Calculator")
        self.setMinimumSize(600, 400)

        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: 'Segoe UI';
                color: #800020;
            }
            QLineEdit, QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)
        self.init_ui()

    def init_ui(self):
        # Top-level vertical layout (entire window)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Container for sidebar + main content
        main_content_layout = QHBoxLayout()

        # Layout for title + input section + result + calculate button
        calculator_layout = QVBoxLayout()

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # ✅ Custom Frameless Title Bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            "Hydrostatic Pressure Calculator"
        )
        root_layout.addWidget(self.title_bar)

        # ✅ Toolbar-style sidebar (left) for Save/Load
        items = [
            (get_icon_path('save'), "Save", lambda: QMessageBox.information(self, "Save", "Save not implemented yet."),
             "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load", lambda: QMessageBox.information(self, "Load", "Load not implemented yet."),
             "Open a file (Ctrl+O)"),
        ]
        self.sidebar = SidebarWidget(self, items)

        # ✅ Title Label
        title_label = QLabel("Hydrostatic Pressure Calculator")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calculator_layout.addWidget(title_label)

        # ✅ Input Fields Grid (API & Metric)
        input_grid = QGridLayout()
        input_grid.setHorizontalSpacing(20)

        input_grid.addWidget(QLabel("Pressure Gradient/Density"), 0, 0)
        input_grid.addWidget(QLabel("True Vertical Depth (TVD)"), 1, 0)

        input_width = 120
        # Left side: API units
        self.gradient_psi_ft = QLineEdit()
        self.gradient_psi_ft.setFixedWidth(input_width)
        self.gradient_psi_ft.setPlaceholderText("e.g. 0.433")
        self.depth_ft = QLineEdit()
        self.depth_ft.setFixedWidth(input_width)
        self.depth_ft.setPlaceholderText("e.g. 1000")
        input_grid.addWidget(self.gradient_psi_ft, 0, 1)
        input_grid.addWidget(self.depth_ft, 1, 1)
        input_grid.addWidget(QLabel("psi/ft"), 0, 2)
        input_grid.addWidget(QLabel("ft"), 1, 2)

        # Right side: Metric units
        self.gradient_kpa_m = QLineEdit()
        self.gradient_kpa_m.setFixedWidth(input_width)
        self.depth_m = QLineEdit()
        self.depth_m.setFixedWidth(input_width)
        input_grid.addWidget(self.gradient_kpa_m, 0, 3)
        input_grid.addWidget(self.depth_m, 1, 3)
        input_grid.addWidget(QLabel("kPa/m"), 0, 4)
        input_grid.addWidget(QLabel("m"), 1, 4)

        calculator_layout.addLayout(input_grid)

        # ✅ Auto unit conversion
        self.gradient_psi_ft.textChanged.connect(self.update_gradient_metric)
        self.gradient_kpa_m.textChanged.connect(self.update_gradient_api)
        self.depth_ft.textChanged.connect(self.update_depth_metric)
        self.depth_m.textChanged.connect(self.update_depth_api)

        # ✅ Output Label
        self.result_label = QLabel("Hydrostatic Pressure: — psi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14pt; margin-top: 20px")
        calculator_layout.addWidget(self.result_label)

        # ✅ Calculate Button
        calculate_btn = QPushButton("Calculate")
        calculate_btn.setFixedSize(180, 45)
        calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)
        calculate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        calculate_btn.clicked.connect(lambda: calculate_pressure(self))
        calculator_layout.addWidget(calculate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # ✅ Right sidebar for selecting fluids
        fluid_sidebar_layout = QVBoxLayout()
        fluid_sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        fluid_sidebar_layout.setContentsMargins(10, 10, 10, 10)

        sidebar_label = QLabel("Common Fluids")
        sidebar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")

        self.fluid_list = QListWidget()
        self.fluid_list.addItems([
            "Fresh Water - 0.433 psi/ft",
            "Seawater - 0.445 psi/ft",
            "Mud (10 ppg) - 0.52 psi/ft",
            "Oil (Light) - 0.35 psi/ft",
            "Brine - 0.48 psi/ft"
        ])
        self.fluid_list.itemClicked.connect(self.set_common_fluid)
        self.fluid_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #f0e0e6;
            }
        """)
        self.fluid_list.setCursor(Qt.CursorShape.PointingHandCursor)

        fluid_sidebar_layout.addWidget(sidebar_label)
        fluid_sidebar_layout.addWidget(self.fluid_list)

        # Add calculator and fluid sidebar to the main content layout
        main_content_layout.addSpacing(10)
        main_content_layout.addLayout(calculator_layout, stretch=3)
        main_content_layout.addLayout(fluid_sidebar_layout, stretch=1)

        # Wrap main content with outer layout (excluding left toolbar sidebar)
        content_wrapper_layout = QVBoxLayout()
        content_wrapper_layout.addLayout(main_content_layout)

        # ✅ Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        content_wrapper_layout.addWidget(footer)

        # ✅ Left sidebar + main content wrapper
        full_horizontal_layout = QHBoxLayout()
        full_horizontal_layout.addWidget(self.sidebar)
        full_horizontal_layout.addLayout(content_wrapper_layout)

        root_layout.addLayout(full_horizontal_layout)

    def update_gradient_metric(self):
        try:
            psi_ft = float(self.gradient_psi_ft.text())
            self.gradient_kpa_m.blockSignals(True)
            self.gradient_kpa_m.setText(f"{psi_ft * 2.3066587:.3f}")
            self.gradient_kpa_m.blockSignals(False)
        except ValueError:
            pass

    def update_gradient_api(self):
        try:
            kpa_m = float(self.gradient_kpa_m.text())
            self.gradient_psi_ft.blockSignals(True)
            self.gradient_psi_ft.setText(f"{kpa_m / 2.3066587:.3f}")
            self.gradient_psi_ft.blockSignals(False)
        except ValueError:
            pass

    def update_depth_metric(self):
        try:
            ft = float(self.depth_ft.text())
            self.depth_m.blockSignals(True)
            self.depth_m.setText(f"{ft * 0.3048:.2f}")
            self.depth_m.blockSignals(False)
        except ValueError:
            pass

    def update_depth_api(self):
        try:
            m = float(self.depth_m.text())
            self.depth_ft.blockSignals(True)
            self.depth_ft.setText(f"{m / 0.3048:.2f}")
            self.depth_ft.blockSignals(False)
        except ValueError:
            pass

    def set_common_fluid(self, item):
        text = item.text()
        if "-" in text:
            psi_ft_value = text.split("-")[-1].strip().split()[0]
            self.gradient_psi_ft.setText(psi_ft_value)

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,  # ✅ exists now
            summary_widget=None
        )
