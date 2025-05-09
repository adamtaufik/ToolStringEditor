from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
                             QLabel, QComboBox, QCheckBox, QPushButton, QTextEdit, QApplication)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ShearPinTab(QWidget):
    def __init__(self):
        super().__init__()
        self.material_properties = {
            "Brass": 45000,  # psi
            "Steel": 60000,  # psi
            "Aluminium": 30000  # psi
        }
        self.pin_sizes = {
            "1/8\"": 0.125,
            "5/32\"": 0.15625,
            "3/16\"": 0.1875,
            "1/4\"": 0.25,
            "5/16\"": 0.3125,
            "3/8\"": 0.375
        }
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Input Section
        input_layout = self.create_input_section()
        main_layout.addLayout(input_layout)

        # Formula Display
        formula_layout = self.create_formula_section()
        main_layout.addLayout(formula_layout)

    def create_input_section(self):
        input_layout = QGridLayout()

        # Pin Size Selection
        self.pin_size_combo = QComboBox()
        self.pin_size_combo.addItems(self.pin_sizes.keys())

        # Material Selection
        self.material_combo = QComboBox()
        self.material_combo.addItems(self.material_properties.keys())

        # Holding Points Checkbox
        self.holding_points_check = QCheckBox("Two Holding Points (Double Shear)")
        self.holding_points_check.setChecked(True)

        # Calculate Button
        self.calculate_btn = QPushButton("Calculate Shear Force")
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)

        # Result Label
        self.result_label = QLabel("Shear Force Required: -")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Add to layout
        input_layout.addWidget(QLabel("Shear Pin Size:"), 0, 0)
        input_layout.addWidget(self.pin_size_combo, 0, 1)
        input_layout.addWidget(QLabel("Material:"), 1, 0)
        input_layout.addWidget(self.material_combo, 1, 1)
        input_layout.addWidget(self.holding_points_check, 2, 0, 1, 2)
        input_layout.addWidget(self.calculate_btn, 3, 0, 1, 2)
        input_layout.addWidget(self.result_label, 4, 0, 1, 2)

        return input_layout

    def create_formula_section(self):
        formula_layout = QVBoxLayout()

        # Formula Display
        self.formula_display = QTextEdit()
        self.formula_display.setReadOnly(True)
        self.formula_display.setFont(QFont("Cambria Math", 10))
        self.formula_document = self.formula_display.document()
        self.formula_document.setDefaultStyleSheet("""
            body { 
                font-family: 'Cambria Math', 'Times New Roman', serif;
                font-size: 12pt;
            }
        """)

        # Copy Button
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
        copy_btn.clicked.connect(self.copy_to_clipboard)

        formula_layout.addWidget(QLabel("\nCalculation Breakdown:"))
        formula_layout.addWidget(self.formula_display)
        formula_layout.addWidget(copy_btn)

        return formula_layout

    def setup_connections(self):
        self.calculate_btn.clicked.connect(self.calculate_shear_force)

    def calculate_shear_force(self):
        try:
            # Get inputs
            pin_size = self.pin_size_combo.currentText()
            material = self.material_combo.currentText()
            diameter = self.pin_sizes[pin_size]
            tensile_strength = self.material_properties[material]
            double_shear = self.holding_points_check.isChecked()

            # Calculations
            radius = diameter / 2
            area = 3.14159 * (radius ** 2)
            shear_strength = tensile_strength * 0.6  # Shear strength ≈ 60% of tensile
            shear_force = area * shear_strength

            # Apply double shear if needed
            if double_shear:
                shear_force *= 2
                shear_type = "Double Shear"
                holding_points = "2"
            else:
                shear_type = "Single Shear"
                holding_points = "1"

            # Update UI
            self.result_label.setText(f"Shear Force Required: {shear_force:,.2f} lbs ({shear_type})")

            # Generate and display formula
            self.formula_display.setHtml(self.generate_formula_html(
                pin_size, diameter, material, tensile_strength,
                radius, area, shear_strength, shear_force,
                holding_points, shear_type
            ))

        except Exception as e:
            self.formula_display.setHtml(f"""
                <div style='color: red; font-weight: bold;'>
                    Error in calculation: {str(e)}
                </div>
            """)

    def generate_formula_html(self, pin_size, diameter, material, tensile_strength,
                              radius, area, shear_strength, shear_force,
                              holding_points, shear_type):
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
                    margin: 10px 0 15px 0;
                    font-size: 14pt;
                }}
                .frac {{
                    display: inline-block;
                    position: relative;
                    vertical-align: middle;
                    letter-spacing: 0.001em;
                    text-align: center;
                }}
                .frac > span {{
                    display: block;
                    padding: 0.1em;
                }}
                .frac span.bottom {{
                    border-top: 1px solid;
                }}
                .overline {{
                    text-decoration: overline;
                }}
                .input-param {{
                    margin-bottom: 10px;
                }}
            </style>

            <div class="result">Shear Pin Calculation</div>

            <div class="formula input-param"><b>Input Parameters:</b></div>
            <div class="formula">Pin Size = {pin_size} (d = {diameter:.4f}\")</div>
            <div class="formula">Material = {material} (σ<sub>t</sub> = {tensile_strength:,} psi)</div>
            <div class="formula">Holding Points = {holding_points} ({shear_type})</div>

            <div class="formula"><b>Calculations:</b></div>
            <div class="formula">
                A = πr² = π × 
                <span class="frac">
                    <span>{diameter:.4f}</span>
                    <span class="bottom">2</span>
                </span>² = {area:.6f} in²
            </div>
            <div class="formula">τ = 0.6 × σ<sub>t</sub> = 0.6 × {tensile_strength:,} = {shear_strength:,.0f} psi</div>
            <div class="formula">F = A × τ = {area:.6f} × {shear_strength:,.0f}</div>
            <div class="formula"><span class="overline">        </span> = {area * shear_strength:,.2f} lbs (single shear)</div>

            <div class="result">Final Shear Force = {shear_force:,.2f} lbs ({shear_type})</div>
        """

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.formula_display.toPlainText())