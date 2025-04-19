from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QGridLayout, QToolBar, QToolButton, QSizePolicy, QListWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QCursor

from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.get_resource_path import get_icon_path
from utils.styles import GLASSMORPHISM_STYLE, DELEUM_STYLE


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

        main_container = QVBoxLayout(self)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        outer_layout = QVBoxLayout()
        content_layout = QHBoxLayout()
        main_layout = QVBoxLayout()

        items = [
            (get_icon_path('save'), "Save", lambda: QMessageBox.information(self, "Save", "Save not implemented yet."), "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load", lambda: QMessageBox.information(self, "Load", "Load not implemented yet."), "Open a file (Ctrl+O)"),
            # (get_icon_path('plot'), "Plot", self.plot_graph, "Plot a graph from the current data"),
            # (get_icon_path('export'), "Export", lambda: export_to_pdf(self.canvas, self.table, self), "Generate a PDF report"),
        ]

        self.sidebar = SidebarWidget(self, items)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            "Hydrostatic Pressure Calculator"
        )

        main_container.addWidget(self.title_bar)

        content_layout.addWidget(self.sidebar)
        input_width = 120

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        self.apply_theme()

        # Title
        title = QLabel("Hydrostatic Pressure Calculator")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Grid layout for dual unit input
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)

        grid.addWidget(QLabel("Pressure Gradient/Density"), 0, 0)
        grid.addWidget(QLabel("True Vertical Depth (TVD)"), 1, 0)

        # Left (API)
        self.gradient_psi_ft = QLineEdit()
        self.gradient_psi_ft.setFixedWidth(input_width)
        self.gradient_psi_ft.setPlaceholderText("e.g. 0.433")
        self.depth_ft = QLineEdit()
        self.depth_ft.setFixedWidth(input_width)
        self.depth_ft.setPlaceholderText("e.g. 1000")
        grid.addWidget(self.gradient_psi_ft, 0, 1)
        grid.addWidget(self.depth_ft, 1, 1)
        grid.addWidget(QLabel("psi/ft"), 0, 2)
        grid.addWidget(QLabel("ft"), 1, 2)

        # Right (Metric)
        self.gradient_kpa_m = QLineEdit()
        self.gradient_kpa_m.setFixedWidth(input_width)
        self.depth_m = QLineEdit()
        self.depth_m.setFixedWidth(input_width)
        grid.addWidget(self.gradient_kpa_m, 0, 3)
        grid.addWidget(self.depth_m, 1, 3)
        grid.addWidget(QLabel("kPa/m"), 0, 4)
        grid.addWidget(QLabel("m"), 1, 4)

        main_layout.addLayout(grid)


        # Connect inputs for auto conversion
        self.gradient_psi_ft.textChanged.connect(self.update_gradient_metric)
        self.gradient_kpa_m.textChanged.connect(self.update_gradient_api)
        self.depth_ft.textChanged.connect(self.update_depth_metric)
        self.depth_m.textChanged.connect(self.update_depth_api)

        # ✅ Output label
        self.result_label = QLabel("Hydrostatic Pressure: — psi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 14pt; margin-top: 20px")
        main_layout.addWidget(self.result_label)

        # ✅ Calculate button
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
        calculate_btn.clicked.connect(self.calculate_pressure)
        main_layout.addWidget(calculate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacing(10)
        content_layout.addLayout(main_layout, stretch=3)

        # ✅ Sidebar for fluid selection on the right
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

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


        sidebar_layout.addWidget(sidebar_label)
        sidebar_layout.addWidget(self.fluid_list)
        content_layout.addLayout(sidebar_layout, stretch=1)

        outer_layout.addLayout(content_layout)
        # ✅ Set final layout
        self.setLayout(outer_layout)


        main_container.addLayout(outer_layout)

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

    def calculate_pressure(self):
        try:
            psi_ft = float(self.gradient_psi_ft.text())
            ft = float(self.depth_ft.text())
            psi = psi_ft * ft
            self.result_label.setText(f"Hydrostatic Pressure: {psi:,.2f} psi")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numeric values for gradient and depth.")

    def return_to_main_menu(self):
        from ui.windows.ui_start_window import StartWindow  # ⬅️ move import here to avoid circular import
        self.start_window = StartWindow(app_icon=self.windowIcon())
        self.start_window.show()
        self.close()

    def apply_theme(self):
        """Applies the current theme."""
        if self.current_theme == "Dark":
            self.setStyleSheet(GLASSMORPHISM_STYLE)
        else:
            self.setStyleSheet(DELEUM_STYLE)