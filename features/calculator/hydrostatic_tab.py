from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QMessageBox,
                             QSplitter, QTextEdit, QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QColor


class HydrostaticTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create a horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side container (input + illustration)
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)

        # Input section
        input_widget = QWidget()
        input_widget.setLayout(self.create_input_section())
        left_layout.addWidget(input_widget, stretch=2)

        # Illustration
        self.well_illustration = FluidIllustration()
        left_layout.addWidget(self.well_illustration, stretch=1)

        # Right side (formula)
        formula_widget = QWidget()
        formula_widget.setLayout(self.create_formula_section())

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(formula_widget)

        # Set initial sizes
        splitter.setSizes([500, 400])

        # Add splitter to main layout
        main_layout.addWidget(splitter)

    def create_input_section(self):
        input_layout = QVBoxLayout()

        # Fluid list section (moved to top)
        fluid_group = QWidget()
        fluid_layout = QVBoxLayout(fluid_group)

        sidebar_label = QLabel("Common Fluids")
        sidebar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        fluid_layout.addWidget(sidebar_label)

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
        fluid_layout.addWidget(self.fluid_list)
        input_layout.addWidget(fluid_group)

        # Calculator section
        calculator_group = QWidget()
        calculator_layout = QVBoxLayout(calculator_group)

        # Title
        title_label = QLabel("Hydrostatic Pressure Calculator")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calculator_layout.addWidget(title_label)

        # Input grid
        input_grid = self.create_input_grid()
        calculator_layout.addLayout(input_grid)

        # TVD note
        tvd_note = QLabel("Note: Both Fluid Level and Target Depth must be True Vertical Depth (TVD)")
        tvd_note.setStyleSheet("font-style: italic; color: #666;")
        tvd_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calculator_layout.addWidget(tvd_note)

        # Calculate button
        self.calculate_btn = self.create_calculate_button()
        calculator_layout.addWidget(self.calculate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Result label
        self.result_label = QLabel("Hydrostatic Pressure: — psi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 12pt; margin-top: 10px")
        calculator_layout.addWidget(self.result_label)

        input_layout.addWidget(calculator_group)
        return input_layout

    def create_input_grid(self):
        input_grid = QGridLayout()
        input_grid.setHorizontalSpacing(20)
        input_grid.setVerticalSpacing(10)

        # Input fields
        self.gradient_psi_ft = QLineEdit()
        self.gradient_psi_ft.setFixedWidth(120)
        self.gradient_psi_ft.setPlaceholderText("e.g. 0.433")

        self.fluid_level_ft = QLineEdit()
        self.fluid_level_ft.setFixedWidth(120)
        self.fluid_level_ft.setPlaceholderText("e.g. 500")

        self.target_depth_ft = QLineEdit()
        self.target_depth_ft.setFixedWidth(120)
        self.target_depth_ft.setPlaceholderText("e.g. 1000")

        self.gradient_kpa_m = QLineEdit()
        self.gradient_kpa_m.setFixedWidth(120)

        self.fluid_level_m = QLineEdit()
        self.fluid_level_m.setFixedWidth(120)

        self.target_depth_m = QLineEdit()
        self.target_depth_m.setFixedWidth(120)

        # Add to grid
        input_grid.addWidget(QLabel("Pressure Gradient/Density"), 0, 0)
        input_grid.addWidget(QLabel("Fluid Level (TVD)"), 1, 0)
        input_grid.addWidget(QLabel("Target Depth (TVD)"), 2, 0)

        # Imperial units column
        input_grid.addWidget(self.gradient_psi_ft, 0, 1)
        input_grid.addWidget(self.fluid_level_ft, 1, 1)
        input_grid.addWidget(self.target_depth_ft, 2, 1)
        input_grid.addWidget(QLabel("psi/ft"), 0, 2)
        input_grid.addWidget(QLabel("ft"), 1, 2)
        input_grid.addWidget(QLabel("ft"), 2, 2)

        # Metric units column
        input_grid.addWidget(self.gradient_kpa_m, 0, 3)
        input_grid.addWidget(self.fluid_level_m, 1, 3)
        input_grid.addWidget(self.target_depth_m, 2, 3)
        input_grid.addWidget(QLabel("kPa/m"), 0, 4)
        input_grid.addWidget(QLabel("m"), 1, 4)
        input_grid.addWidget(QLabel("m"), 2, 4)

        return input_grid

    def create_calculate_button(self):
        btn = QPushButton("Calculate")
        btn.setFixedSize(180, 40)
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

    def create_formula_section(self):
        formula_layout = QVBoxLayout()

        # Formula display
        self.formula_display = QTextEdit()
        self.formula_display.setReadOnly(True)
        self.formula_display.setFont(QFont("Cambria Math", 10))

        # Copy button
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setStyleSheet("""
            QPushButton {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        copy_btn.clicked.connect(self.copy_formula)

        formula_layout.addWidget(QLabel("\nCalculation Breakdown:"))
        formula_layout.addWidget(self.formula_display)
        formula_layout.addWidget(copy_btn)

        return formula_layout

    def setup_connections(self):
        """Connect all signals and slots"""
        self.gradient_psi_ft.textChanged.connect(self.update_gradient_metric)
        self.gradient_kpa_m.textChanged.connect(self.update_gradient_api)

        self.fluid_level_ft.textChanged.connect(self.update_fluid_level_metric)
        self.fluid_level_m.textChanged.connect(self.update_fluid_level_api)

        self.target_depth_ft.textChanged.connect(self.update_target_depth_metric)
        self.target_depth_m.textChanged.connect(self.update_target_depth_api)

        self.fluid_list.itemClicked.connect(self.set_common_fluid)
        self.calculate_btn.clicked.connect(self.calculate_hydrostatic_pressure)

    # Conversion methods
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

    def update_fluid_level_metric(self):
        try:
            ft = float(self.fluid_level_ft.text())
            self.fluid_level_m.blockSignals(True)
            self.fluid_level_m.setText(f"{ft * 0.3048:.2f}")
            self.fluid_level_m.blockSignals(False)
        except ValueError:
            pass

    def update_fluid_level_api(self):
        try:
            m = float(self.fluid_level_m.text())
            self.fluid_level_ft.blockSignals(True)
            self.fluid_level_ft.setText(f"{m / 0.3048:.2f}")
            self.fluid_level_ft.blockSignals(False)
        except ValueError:
            pass

    def update_target_depth_metric(self):
        try:
            ft = float(self.target_depth_ft.text())
            self.target_depth_m.blockSignals(True)
            self.target_depth_m.setText(f"{ft * 0.3048:.2f}")
            self.target_depth_m.blockSignals(False)
        except ValueError:
            pass

    def update_target_depth_api(self):
        try:
            m = float(self.target_depth_m.text())
            self.target_depth_ft.blockSignals(True)
            self.target_depth_ft.setText(f"{m / 0.3048:.2f}")
            self.target_depth_ft.blockSignals(False)
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
            fluid_level = float(self.fluid_level_ft.text())
            target_depth = float(self.target_depth_ft.text())

            # Calculate the height of fluid column
            fluid_column_height = max(0, target_depth - fluid_level)

            # Calculate hydrostatic pressure
            psi = psi_ft * fluid_column_height

            self.result_label.setText(f"Hydrostatic Pressure: {psi:,.2f} psi")

            # Update formula display
            self.formula_display.setHtml(self.generate_formula_html(
                psi_ft, fluid_level, target_depth, fluid_column_height, psi
            ))

            # Update well illustration
            self.well_illustration.update_illustration(fluid_level, target_depth, psi)

        except ValueError:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numeric values for all fields.")
            self.formula_display.setHtml(
                "<div style='color: red;'>Please enter valid numeric values for all fields.</div>"
            )


        except ValueError:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numeric values for all fields.")
            self.formula_display.setHtml(
                "<div style='color: red;'>Please enter valid numeric values for all fields.</div>"
            )

    def generate_formula_html(self, gradient, fluid_level, target_depth, column_height, pressure):
        return f"""
            <style>
                .formula {{ 
                    font-family: 'Cambria Math', 'Times New Roman', serif;
                    font-size: 12pt;
                    margin: 5px 0;
                }}
                .result {{
                    font-weight: bold;
                    color: #800020;
                    margin: 10px 0 5px 0;
                }}
                .overline {{
                    text-decoration: overline;
                }}
                sup, sub {{
                    font-size: 0.8em;
                }}
            </style>

            <div class="formula">Pressure Gradient = <i>G</i> = {gradient:.3f} psi/ft</div>
            <div class="formula">Fluid Level = {fluid_level:.1f} ft (TVD)</div>
            <div class="formula">Target Depth = {target_depth:.1f} ft (TVD)</div>

            <div class="formula">Fluid Column Height = Target Depth - Fluid Level</div>
            <div class="formula"><span class="overline">   </span> = {target_depth:.1f} - {fluid_level:.1f}</div>
            <div class="formula"><span class="overline">   </span> = {column_height:.1f} ft</div>

            <div class="result">Hydrostatic Pressure</div>
            <div class="formula"><i>P</i> = <i>G</i> × Height</div>
            <div class="formula"><span class="overline">   </span> = {gradient:.3f} × {column_height:.1f}</div>
            <div class="formula"><span class="overline">   </span> = {pressure:.2f} psi</div>
        """


    def copy_formula(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.formula_display.toPlainText())


class FluidIllustration(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setMinimumSize(200, 400)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        # Default values
        self.fluid_level = 0
        self.target_depth = 1000
        self.pressure = 0
        self.max_depth = 1500  # Default max depth for scaling

    def update_illustration(self, fluid_level, target_depth, pressure):
        self.fluid_level = fluid_level
        self.target_depth = target_depth
        self.pressure = pressure
        self.max_depth = max(target_depth * 1.2, 1500)  # Auto-scale with 20% margin
        self.draw_well()

    def draw_well(self):
        self.scene.clear()

        # Calculate scaling factors
        view_height = self.height()
        scale_factor = view_height / self.max_depth

        # Draw well casing
        well_width = 70
        casing = QGraphicsRectItem(0, 0, well_width, self.max_depth * scale_factor)
        casing.setPen(QPen(Qt.GlobalColor.gray, 2))
        casing.setBrush(QColor(240, 240, 240))
        self.scene.addItem(casing)

        # Draw tubing (smaller rectangle inside casing)
        tubing_width = well_width - 20
        tubing = QGraphicsRectItem(10, 0, tubing_width, self.max_depth * scale_factor)
        tubing.setPen(QPen(Qt.GlobalColor.darkGray, 1))
        tubing.setBrush(Qt.GlobalColor.transparent)
        self.scene.addItem(tubing)

        # Draw fluid column (only if fluid exists)
        if self.target_depth > self.fluid_level:
            fluid_height = (self.target_depth - self.fluid_level) * scale_factor
            fluid_y = self.fluid_level * scale_factor
            fluid = QGraphicsRectItem(10, fluid_y, tubing_width, fluid_height)
            fluid.setPen(QPen(Qt.GlobalColor.blue, 1))
            fluid.setBrush(QColor(30, 144, 255, 150))  # Semi-transparent blue
            self.scene.addItem(fluid)

            # Add fluid level label
            fluid_label = self.scene.addText(f"Fluid Level: {self.fluid_level} ft")
            fluid_label.setPos(well_width + 70, fluid_y)

        # Draw target depth line
        target_y = self.target_depth * scale_factor
        target_line = self.scene.addLine(0, target_y, well_width, target_y, QPen(Qt.GlobalColor.red, 2))

        # Add target depth label
        target_label = self.scene.addText(f"Target Depth: {self.target_depth} ft")
        target_label.setPos(well_width + 70, target_y - 15)

        # Add pressure label
        if self.pressure > 0:
            pressure_label = self.scene.addText(f"{self.pressure:.1f} psi")
            pressure_label.setPos(well_width / 2 - 30, target_y - 30)
            pressure_label.setDefaultTextColor(Qt.GlobalColor.darkRed)

        # Draw depth markers
        for depth_mark in range(0, int(self.max_depth) + 1, 1000):
            y_pos = depth_mark * scale_factor
            self.scene.addLine(well_width, y_pos, well_width + 10, y_pos, QPen(Qt.GlobalColor.black, 1))
            depth_label = self.scene.addText(f"{depth_mark} ft")
            depth_label.setPos(well_width + 15, y_pos - 10)

    def resizeEvent(self, event):
        self.draw_well()
        super().resizeEvent(event)