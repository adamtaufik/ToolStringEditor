from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class HydrostaticTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Calculator section
        calculator_layout = self.create_calculator_section()
        main_layout.addLayout(calculator_layout, stretch=3)

        # Fluid list section
        fluid_sidebar = self.create_fluid_sidebar()
        main_layout.addWidget(fluid_sidebar, stretch=1)

    def create_calculator_section(self):
        calculator_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Hydrostatic Pressure Calculator")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calculator_layout.addWidget(title_label)

        # Input grid
        input_grid = self.create_input_grid()
        calculator_layout.addLayout(input_grid)

        # Result label
        self.result_label = QLabel("Hydrostatic Pressure: — psi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14pt; margin-top: 20px")
        calculator_layout.addWidget(self.result_label)

        # Calculate button
        self.calculate_btn = self.create_calculate_button()
        calculator_layout.addWidget(self.calculate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        calculator_layout.addStretch()
        return calculator_layout

    def create_input_grid(self):
        input_grid = QGridLayout()
        input_grid.setHorizontalSpacing(20)

        # Input fields
        self.gradient_psi_ft = QLineEdit()
        self.gradient_psi_ft.setFixedWidth(120)
        self.gradient_psi_ft.setPlaceholderText("e.g. 0.433")

        self.depth_ft = QLineEdit()
        self.depth_ft.setFixedWidth(120)
        self.depth_ft.setPlaceholderText("e.g. 1000")

        self.gradient_kpa_m = QLineEdit()
        self.gradient_kpa_m.setFixedWidth(120)

        self.depth_m = QLineEdit()
        self.depth_m.setFixedWidth(120)

        # Add to grid
        input_grid.addWidget(QLabel("Pressure Gradient/Density"), 0, 0)
        input_grid.addWidget(QLabel("True Vertical Depth (TVD)"), 1, 0)

        input_grid.addWidget(self.gradient_psi_ft, 0, 1)
        input_grid.addWidget(self.depth_ft, 1, 1)
        input_grid.addWidget(QLabel("psi/ft"), 0, 2)
        input_grid.addWidget(QLabel("ft"), 1, 2)

        input_grid.addWidget(self.gradient_kpa_m, 0, 3)
        input_grid.addWidget(self.depth_m, 1, 3)
        input_grid.addWidget(QLabel("kPa/m"), 0, 4)
        input_grid.addWidget(QLabel("m"), 1, 4)

        return input_grid

    def create_calculate_button(self):
        btn = QPushButton("Calculate")
        btn.setFixedSize(180, 45)
        btn.setStyleSheet("""
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
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def create_fluid_sidebar(self):
        sidebar = QWidget()
        sidebar.setMinimumWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        sidebar_label = QLabel("Common Fluids")
        sidebar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(sidebar_label)

        # Fluid list
        self.fluid_list = QListWidget()
        self.fluid_list.addItems([
            "Fresh Water - 0.433 psi/ft",
            "Seawater - 0.445 psi/ft",
            "Mud (10 ppg) - 0.52 psi/ft",
            "Oil (Light) - 0.35 psi/ft",
            "Brine - 0.48 psi/ft"
        ])
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
        layout.addWidget(self.fluid_list)

        return sidebar

    def setup_connections(self):
        """Connect all signals and slots"""
        self.gradient_psi_ft.textChanged.connect(self.update_gradient_metric)
        self.gradient_kpa_m.textChanged.connect(self.update_gradient_api)
        self.depth_ft.textChanged.connect(self.update_depth_metric)
        self.depth_m.textChanged.connect(self.update_depth_api)
        self.fluid_list.itemClicked.connect(self.set_common_fluid)
        self.calculate_btn.clicked.connect(self.calculate_hydrostatic_pressure)

    # Calculation methods
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

    def calculate_hydrostatic_pressure(self):
        try:
            psi_ft = float(self.gradient_psi_ft.text())
            ft = float(self.depth_ft.text())
            psi = psi_ft * ft
            self.result_label.setText(f"Hydrostatic Pressure: {psi:,.2f} psi")
        except ValueError:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numeric values for gradient and depth.")