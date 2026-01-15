from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QMessageBox,
                             QSplitter, QTextEdit, QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter, QPen, QColor


class HydrostaticTab(QWidget):
    PSI_TO_KPA = 6.894757
    KPA_TO_PSI = 1 / 6.894757
    PSI_FT_TO_KPA_M = 2.3066587

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
        left_layout.addWidget(input_widget)

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
        splitter.setSizes([520, 400])

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
            "Oil (Light) - 0.35 psi/ft",
            "Fresh Water - 0.433 psi/ft",
            "Seawater - 0.445 psi/ft",
            "Mud (10 ppg) - 0.52 psi/ft",
            "Brine - 0.48 psi/ft",
            "Gas - 0.06 psi/ft"
        ])
        self.fluid_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f8f8;
                color: black;
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
        self.fluid_list.setFixedHeight(100)

        # Calculator section
        calculator_group = QWidget()
        calculator_layout = QVBoxLayout(calculator_group)

        # Input grid
        input_grid = self.create_input_grid()
        calculator_layout.addLayout(input_grid)

        # TVD note
        tvd_note = QLabel("Note: Both Fluid Level and Target Depth must be True Vertical Depth (TVD)")
        tvd_note.setStyleSheet("font-style: italic; color: #666;")
        tvd_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calculator_layout.addWidget(tvd_note)

        lowerleft_layout = QHBoxLayout()

        # Calculate button
        self.calculate_btn = self.create_calculate_button()
        lowerleft_layout.addWidget(self.calculate_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        result_layout = QVBoxLayout()

        # Result labels
        self.result_label = QLabel("Hydrostatic Pressure: — psi")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 12pt; margin-top: 10px")
        result_layout.addWidget(self.result_label)

        self.diff_label = QLabel("")  # shows only when RP/PB provided
        self.diff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.diff_label.setStyleSheet("font-size: 12pt; color: #0D47A1;")
        result_layout.addWidget(self.diff_label)

        lowerleft_layout.addLayout(result_layout)
        calculator_layout.addLayout(lowerleft_layout)

        input_layout.addWidget(calculator_group)
        return input_layout

    def create_input_grid(self):
        # We'll still create the same QLineEdits, but arrange them vertically per parameter.
        container = QVBoxLayout()
        container.setSpacing(12)

        def make_param_block(title, imp_widget, imp_unit, met_widget, met_unit):
            block = QVBoxLayout()
            block.setSpacing(4)

            # Title label (parameter)
            lbl = QLabel(title)
            lbl.setStyleSheet("font-weight: 600;")
            block.addWidget(lbl)

            # Inputs line (imperial + metric)
            line = QHBoxLayout()
            line.setSpacing(10)

            # Imperial
            imp_box = QHBoxLayout()
            imp_box.setSpacing(5)
            imp_box.addWidget(imp_widget)
            imp_box.addWidget(QLabel(imp_unit))
            line.addLayout(imp_box)

            # Spacer between the two systems (optional)
            line.addSpacing(8)

            # Metric
            met_box = QHBoxLayout()
            met_box.setSpacing(5)
            met_box.addWidget(met_widget)
            met_box.addWidget(QLabel(met_unit))
            line.addLayout(met_box)

            block.addLayout(line)
            return block

        # Core inputs (reuse existing widgets, just positioning changes)
        self.gradient_psi_ft = QLineEdit();
        self.gradient_psi_ft.setFixedWidth(120);
        self.gradient_psi_ft.setPlaceholderText("e.g. 0.433")
        self.fluid_level_ft = QLineEdit();
        self.fluid_level_ft.setFixedWidth(120);
        self.fluid_level_ft.setPlaceholderText("e.g. 500")
        self.target_depth_ft = QLineEdit();
        self.target_depth_ft.setFixedWidth(120);
        self.target_depth_ft.setPlaceholderText("e.g. 1000")

        self.gradient_kpa_m = QLineEdit();
        self.gradient_kpa_m.setFixedWidth(120)
        self.fluid_level_m = QLineEdit();
        self.fluid_level_m.setFixedWidth(120)
        self.target_depth_m = QLineEdit();
        self.target_depth_m.setFixedWidth(120)

        # CITHP / RP (psi & kPa)
        self.cithp_psi = QLineEdit();
        self.cithp_psi.setFixedWidth(120);
        self.cithp_psi.setPlaceholderText("optional")
        self.cithp_kpa = QLineEdit();
        self.cithp_kpa.setFixedWidth(120);
        self.cithp_kpa.setPlaceholderText("optional")

        self.rp_psi = QLineEdit();
        self.rp_psi.setFixedWidth(120);
        self.rp_psi.setPlaceholderText("optional")
        self.rp_kpa = QLineEdit();
        self.rp_kpa.setFixedWidth(120);
        self.rp_kpa.setPlaceholderText("optional")

        # ---- Tooltips ----
        # Gradient
        tip_grad_imp = ("Pressure gradient / density.\n"
                        "Example: Fresh water ≈ 0.433 psi/ft, seawater ≈ 0.445 psi/ft.")
        tip_grad_met = ("Pressure gradient / density.\n"
                        "Example: Fresh water ≈ 10.0 kPa/m, seawater ≈ 10.3 kPa/m.\n"
                        "Auto-syncs with psi/ft.")
        self.gradient_psi_ft.setToolTip(tip_grad_imp)
        self.gradient_kpa_m.setToolTip(tip_grad_met)

        # Fluid level (TVD)
        tip_fl = ("True Vertical Depth (TVD) of fluid level/top of column.\n"
                  "Usually measured from surface reference; smaller number = shallower.")
        self.fluid_level_ft.setToolTip(tip_fl + "\nUnits: feet")
        self.fluid_level_m.setToolTip(tip_fl + "\nUnits: metres")

        # Target depth (TVD)
        tip_td = ("True Vertical Depth (TVD) at which you want the pressure.\n"
                  "Hydrostatic head uses (Target − Fluid Level).")
        self.target_depth_ft.setToolTip(tip_td + "\nUnits: feet")
        self.target_depth_m.setToolTip(tip_td + "\nUnits: metres")


        # CITHP
        tip_cithp = ("Closed-In Tubing Head Pressure (at surface).\n"
                     "Added to hydrostatic component. Leave blank if unknown (treated as 0).")
        self.cithp_psi.setToolTip(tip_cithp + "\nUnits: psi")
        self.cithp_kpa.setToolTip(tip_cithp + "\nUnits: kPa")

        # Reservoir Pressure / Pressure Below (RP/PB)
        tip_rp = ("Reservoir Pressure / Pressure below the target depth.\n"
                  "Optional; if provided, Differential Pressure = RP/PB − HP.")
        self.rp_psi.setToolTip(tip_rp + "\nUnits: psi")
        self.rp_kpa.setToolTip(tip_rp + "\nUnits: kPa")

        # Build stacked blocks
        container.addLayout(make_param_block("Pressure Gradient/Density",
                                             self.gradient_psi_ft, "psi/ft",
                                             self.gradient_kpa_m, "kPa/m"))

        container.addLayout(make_param_block("Fluid Level (TVD)",
                                             self.fluid_level_ft, "ft",
                                             self.fluid_level_m, "m"))

        container.addLayout(make_param_block("Target Depth (TVD)",
                                             self.target_depth_ft, "ft",
                                             self.target_depth_m, "m"))

        container.addLayout(make_param_block("CITHP (at surface)",
                                             self.cithp_psi, "psi",
                                             self.cithp_kpa, "kPa"))

        container.addLayout(make_param_block("Reservoir Pressure / Pressure Below",
                                             self.rp_psi, "psi",
                                             self.rp_kpa, "kPa"))

        return container

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
        # Gradient conversions
        self.gradient_psi_ft.textChanged.connect(self.update_gradient_metric)
        self.gradient_kpa_m.textChanged.connect(self.update_gradient_api)

        # Depth conversions
        self.fluid_level_ft.textChanged.connect(self.update_fluid_level_metric)
        self.fluid_level_m.textChanged.connect(self.update_fluid_level_api)

        self.target_depth_ft.textChanged.connect(self.update_target_depth_metric)
        self.target_depth_m.textChanged.connect(self.update_target_depth_api)

        # New: CITHP conversions
        self.cithp_psi.textChanged.connect(self.update_cithp_metric)
        self.cithp_kpa.textChanged.connect(self.update_cithp_api)

        # New: Reservoir Pressure conversions
        self.rp_psi.textChanged.connect(self.update_rp_metric)
        self.rp_kpa.textChanged.connect(self.update_rp_api)

        self.fluid_list.itemClicked.connect(self.set_common_fluid)
        self.calculate_btn.clicked.connect(self.calculate_hydrostatic_pressure)

    # Conversion methods
    def update_gradient_metric(self):
        try:
            psi_ft = float(self.gradient_psi_ft.text())
            self.gradient_kpa_m.blockSignals(True)
            self.gradient_kpa_m.setText(f"{psi_ft * self.PSI_FT_TO_KPA_M:.3f}")
            self.gradient_kpa_m.blockSignals(False)
        except ValueError:
            pass

    def update_gradient_api(self):
        try:
            kpa_m = float(self.gradient_kpa_m.text())
            self.gradient_psi_ft.blockSignals(True)
            self.gradient_psi_ft.setText(f"{kpa_m / self.PSI_FT_TO_KPA_M:.3f}")
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

    def update_cithp_metric(self):
        try:
            psi = float(self.cithp_psi.text())
            self.cithp_kpa.blockSignals(True)
            self.cithp_kpa.setText(f"{psi * self.PSI_TO_KPA:.2f}")
            self.cithp_kpa.blockSignals(False)
        except ValueError:
            # allow blank or invalid until correction
            if self.cithp_psi.text().strip() == "":
                self.cithp_kpa.blockSignals(True)
                self.cithp_kpa.clear()
                self.cithp_kpa.blockSignals(False)

    def update_cithp_api(self):
        try:
            kpa = float(self.cithp_kpa.text())
            self.cithp_psi.blockSignals(True)
            self.cithp_psi.setText(f"{kpa * self.KPA_TO_PSI:.2f}")
            self.cithp_psi.blockSignals(False)
        except ValueError:
            if self.cithp_kpa.text().strip() == "":
                self.cithp_psi.blockSignals(True)
                self.cithp_psi.clear()
                self.cithp_psi.blockSignals(False)

    def update_rp_metric(self):
        try:
            psi = float(self.rp_psi.text())
            self.rp_kpa.blockSignals(True)
            self.rp_kpa.setText(f"{psi * self.PSI_TO_KPA:.2f}")
            self.rp_kpa.blockSignals(False)
        except ValueError:
            if self.rp_psi.text().strip() == "":
                self.rp_kpa.blockSignals(True)
                self.rp_kpa.clear()
                self.rp_kpa.blockSignals(False)

    def update_rp_api(self):
        try:
            kpa = float(self.rp_kpa.text())
            self.rp_psi.blockSignals(True)
            self.rp_psi.setText(f"{kpa * self.KPA_TO_PSI:.2f}")
            self.rp_psi.blockSignals(False)
        except ValueError:
            if self.rp_kpa.text().strip() == "":
                self.rp_psi.blockSignals(True)
                self.rp_psi.clear()
                self.rp_psi.blockSignals(False)

    def set_common_fluid(self, item):
        text = item.text()
        if "-" in text:
            psi_ft_value = text.split("-")[-1].strip().split()[0]
            self.gradient_psi_ft.setText(psi_ft_value)

    def calculate_hydrostatic_pressure(self):
        try:
            psi_ft = float(self.gradient_psi_ft.text())
            gas_psi_ft = 0.06
            fluid_level = float(self.fluid_level_ft.text())
            target_depth = float(self.target_depth_ft.text())

            # Optional inputs
            cithp_psi = 0.0
            if self.cithp_psi.text().strip():
                cithp_psi = float(self.cithp_psi.text())

            rp_psi = None
            if self.rp_psi.text().strip():
                rp_psi = float(self.rp_psi.text())

            # Calculate the height of fluid column
            fluid_column_height = max(0.0, target_depth - fluid_level)

            # Base hydrostatic (from gradient) + CITHP
            hydrostatic_from_gradient = psi_ft * fluid_column_height
            gas_hydrostatic = gas_psi_ft * fluid_level
            hp_total_psi = hydrostatic_from_gradient + gas_hydrostatic + cithp_psi

            # Update results
            hp_total_kpa = hp_total_psi * self.PSI_TO_KPA
            self.result_label.setText(
                f"Hydrostatic Pressure: {hp_total_psi:,.2f} psi"
            )

            # Differential pressure if RP is provided
            if rp_psi is not None:
                diff_psi = rp_psi - hp_total_psi
                diff_kpa = diff_psi * self.PSI_TO_KPA
                self.diff_label.setText(
                    f"Differential Pressure: {diff_psi:,.2f} psi"
                )
            else:
                self.diff_label.setText("")

            # Update formula display
            self.formula_display.setHtml(self.generate_formula_html(
                psi_ft, fluid_level, target_depth, fluid_column_height,
                hydrostatic_from_gradient, cithp_psi, hp_total_psi, rp_psi
            ))

            # Update well illustration with annotations
            self.well_illustration.update_illustration(
                fluid_level=fluid_level,
                target_depth=target_depth,
                pressure=hp_total_psi,
                cithp=cithp_psi,
                reservoir_pressure=rp_psi
            )

        except ValueError:
            QMessageBox.warning(self, "Input Error",
                                "Please enter valid numeric values for all required fields.")
            self.formula_display.setHtml(
                "<div style='color: red;'>Please enter valid numeric values for all required fields.</div>"
            )

    def generate_formula_html(self, gradient, fluid_level, target_depth, column_height,
                              hydrostatic_from_gradient, cithp, hp_total, rp):
        rp_lines = ""
        diff_lines = ""
        if rp is not None:
            diff = rp - hp_total
            rp_lines = f"""
                <div class="result">Reservoir Pressure / Pressure Below</div>
                <div class="formula"><i>RP</i> = {rp:.2f} psi</div>
            """
            diff_lines = f"""
                <div class="result">Differential Pressure</div>
                <div class="formula"><i>ΔP</i> = <i>RP</i> − <i>HP</i></div>
                <div class="formula"><span class="overline">   </span> = {rp:.2f} − {hp_total:.2f}</div>
                <div class="formula"><span class="overline">   </span> = {diff:.2f} psi</div>
            """

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

            <div class="formula">Liquid Gradient, <i>G</i><sub>liquid</sub> = {gradient:.3f} psi/ft</div>
            <div class="formula">Gas Gradient, <i>G</i><sub>gas</sub> = 0.06 psi/ft</div>
            <div class="formula">Fluid Level = {fluid_level:.1f} ft (TVD)</div>
            <div class="formula">Target Depth = {target_depth:.1f} ft (TVD)</div>
            <div class="formula"><i>P</i><sub>CITHP</sub> = {cithp:.2f} psi</div>

            <div class="result">Column Heights</div>
            <div class="formula">Liquid Column Height, <i>H</i><sub>liquid</sub> = Target Depth − Fluid Level</div>
            <div class="formula"><span class="overline">   </span> = {target_depth:.1f} − {fluid_level:.1f}</div>
            <div class="formula"><span class="overline">   </span> = {column_height:.1f} ft</div>
            <div class="formula">Gas Column Height, <i>H</i><sub>gas</sub> = {fluid_level:.1f} ft</div>

            <div class="result">Hydrostatic Pressure (incl. CITHP)</div>
            <div class="formula"><i>HP</i> = <i>P</i><sub>liquid</sub> + <i>P</i><sub>gas</sub> + <i>P</i><sub>CITHP</sub></div>
            <div class="formula"><i>HP</i> = <i>G</i><sub>liquid</sub> × <i>H</i><sub>liquid</sub> + <i>G</i><sub>gas</sub> × <i>H</i><sub>gas</sub>  + <i>P</i><sub>CITHP</sub></div>
            <div class="formula"><span class="overline">   </span> = ({gradient:.3f} × {column_height:.1f}) + (0.06 × {fluid_level:.1f}) + {cithp:.2f}</div>
            <div class="formula"><span class="overline">   </span> = {hp_total:.2f} psi</div>

            {rp_lines}
            {diff_lines}
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
        self.cithp = 0
        self.reservoir_pressure = None
        self.max_depth = 1500  # Default max depth for scaling

    def update_illustration(self, fluid_level, target_depth, pressure, cithp=0.0, reservoir_pressure=None):
        self.fluid_level = fluid_level
        self.target_depth = target_depth
        self.pressure = pressure
        self.cithp = cithp
        self.reservoir_pressure = reservoir_pressure
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

            # Fluid level label
            fluid_label = self.scene.addText(f"Fluid Level: {self.fluid_level} ft")
            fluid_label.setPos(well_width + 70, fluid_y)

        # Target depth line
        target_y = self.target_depth * scale_factor
        self.scene.addLine(0, target_y, well_width, target_y, QPen(Qt.GlobalColor.red, 2))

        # Target depth label
        target_label = self.scene.addText(f"Target Depth: {self.target_depth} ft")
        target_label.setPos(well_width + 70, target_y - 15)

        # Pressure at target depth label (HP incl. CITHP)
        if self.pressure > 0:
            pressure_label = self.scene.addText(f"{self.pressure:.1f} psi")
            pressure_label.setPos(well_width / 2 - 30, target_y - 30)
            pressure_label.setDefaultTextColor(Qt.GlobalColor.darkRed)

        # CITHP label at surface
        cithp_label = self.scene.addText(f"CITHP: {self.cithp:.1f} psi")
        cithp_label.setDefaultTextColor(QColor(0, 100, 0))  # dark green
        cithp_label.setPos(well_width + 15, 0)  # just above the surface line

        # RP/PB label below target depth (if provided)
        if self.reservoir_pressure is not None:
            rp_label = self.scene.addText(f"Pressure Below: {self.reservoir_pressure:.1f} psi")
            rp_label.setDefaultTextColor(QColor(128, 0, 128))  # purple
            rp_label.setPos(well_width + 15, target_y + 15)
            # small indicator line below target depth
            self.scene.addLine(0, target_y + 12, well_width, target_y + 12, QPen(QColor(128, 0, 128), 1, Qt.PenStyle.DashLine))

        # Depth markers
        for depth_mark in range(0, int(self.max_depth) + 1, 1000):
            y_pos = depth_mark * scale_factor
            self.scene.addLine(well_width, y_pos, well_width + 10, y_pos, QPen(Qt.GlobalColor.black, 1))
            depth_label = self.scene.addText(f"{depth_mark} ft")
            depth_label.setPos(well_width + 15, y_pos - 10)

    def resizeEvent(self, event):
        self.draw_well()
        super().resizeEvent(event)
