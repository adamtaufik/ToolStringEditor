from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QGridLayout, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class WeightTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Inputs section
        input_layout = self.create_input_section()
        main_layout.addLayout(input_layout)

        # Formula display
        formula_layout = self.create_formula_section()
        main_layout.addLayout(formula_layout)

    def create_input_section(self):
        input_layout = QGridLayout()

        # Wire size selection
        self.wire_combo = QComboBox()
        self.wire_combo.addItems(["0.092\"", "0.108\"", "0.125\""])

        # Pressure input
        self.pressure_input = QLineEdit()
        self.pressure_input.setPlaceholderText("Enter pressure in psi")

        # Unit toggle
        self.unit_toggle = QPushButton("Units: psi")
        self.unit_toggle.setCheckable(True)

        # Calculate button
        self.calculate_btn = QPushButton("Calculate Weight")
        self.calculate_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)

        # Output labels
        self.cross_section_label = QLabel("Cross Sectional Area: -")
        self.balance_weight_label = QLabel("Balance Weight (Neglecting Friction): -")

        # Add to layout
        input_layout.addWidget(QLabel("Wire Size:"), 0, 0)
        input_layout.addWidget(self.wire_combo, 0, 1)
        input_layout.addWidget(QLabel("Well Pressure:"), 1, 0)
        input_layout.addWidget(self.pressure_input, 1, 1)
        input_layout.addWidget(self.unit_toggle, 1, 2)
        input_layout.addWidget(self.calculate_btn, 2, 0, 1, 3)
        input_layout.addWidget(self.cross_section_label, 3, 0, 1, 3)
        input_layout.addWidget(self.balance_weight_label, 4, 0, 1, 3)

        return input_layout

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

        formula_layout.addWidget(QLabel("\nCalculation Breakdown:"))
        formula_layout.addWidget(self.formula_display)
        formula_layout.addWidget(copy_btn)

        return formula_layout

    def setup_connections(self):
        self.unit_toggle.clicked.connect(self.toggle_units)
        self.calculate_btn.clicked.connect(self.calculate_balance_weight)

    def toggle_units(self):
        if self.unit_toggle.isChecked():
            self.unit_toggle.setText("Units: kPa")
        else:
            self.unit_toggle.setText("Units: psi")

    def calculate_balance_weight(self):
        try:
            # Get inputs
            wire_size = self.wire_combo.currentText()
            diameter = float(wire_size.strip('"'))
            pressure = float(self.pressure_input.text())

            # Convert units if needed
            if self.unit_toggle.text() == "Units: kPa":
                pressure *= 0.145038  # Convert kPa to psi

            # Calculations
            radius = diameter / 2
            cross_section = 3.14159 * (radius ** 2)
            balance_weight = cross_section * pressure

            # Update UI
            self.cross_section_label.setText(f"Cross Sectional Area: {cross_section:.6f} in²")
            self.balance_weight_label.setText(f"Balance Weight: {balance_weight:.2f} lbs")

            # Format formula display
            self.formula_display.setHtml(self.generate_formula_html(
                diameter, radius, cross_section, pressure, balance_weight
            ))

        except ValueError:
            self.formula_display.setHtml(
                "<div style='color: red;'>Please enter valid numeric values.</div>"
            )

    def generate_formula_html(self, diameter, radius, area, pressure, weight):
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

            <div class="formula">Wire Diameter = <i>d</i> = {diameter}\"</div>
            <div class="formula">Radius = <i>r</i> = <i>d</i>/2 = {diameter}/2 = {radius}\"</div>
            <div class="formula">Cross Sectional Area = π<i>r</i><sup>2</sup> = π({radius})<sup>2</sup> = {area:.6f} in<sup>2</sup></div>

            <div class="formula">Pressure = <i>P</i> = {pressure:.2f} psi</div>

            <div class="result">Balance Weight (Neglecting Friction)</div>
            <div class="formula"><i>W</i> = <i>A</i> × <i>P</i></div>
            <div class="formula"><span class="overline">   </span> = {area:.6f} × {pressure:.2f}</div>
            <div class="formula"><span class="overline">   </span> = {weight:.2f} lbs</div>
        """