from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QApplication, QSplitter
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import math


class SpoolCapacityTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        input_widget = QWidget()
        formula_widget = QWidget()

        input_widget.setLayout(self.create_input_section())
        formula_widget.setLayout(self.create_formula_section())

        splitter.addWidget(input_widget)
        splitter.addWidget(formula_widget)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

    def create_input_section(self):
        layout = QGridLayout()

        # Inputs
        self.drum_width_input = QLineEdit()
        self.drum_od_input = QLineEdit()
        self.flange_od_input = QLineEdit()
        self.wire_od_input = QLineEdit()

        for field in (
            self.drum_width_input,
            self.drum_od_input,
            self.flange_od_input,
            self.wire_od_input,
        ):
            field.setPlaceholderText("inches")

        # Calculate button
        self.calculate_btn = QPushButton("Calculate Spool Capacity")
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
        self.calculate_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Result
        self.result_label = QLabel("Spool Capacity: -")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Layout
        layout.addWidget(QLabel("Drum Width (W):"), 0, 0)
        layout.addWidget(self.drum_width_input, 0, 1)

        layout.addWidget(QLabel("Drum OD (D):"), 1, 0)
        layout.addWidget(self.drum_od_input, 1, 1)

        layout.addWidget(QLabel("Flange OD (F):"), 2, 0)
        layout.addWidget(self.flange_od_input, 2, 1)

        layout.addWidget(QLabel("Wire OD (d):"), 3, 0)
        layout.addWidget(self.wire_od_input, 3, 1)

        layout.addWidget(self.calculate_btn, 4, 0, 1, 2)
        layout.addWidget(self.result_label, 5, 0, 1, 2)

        return layout

    def create_formula_section(self):
        layout = QVBoxLayout()

        self.formula_display = QTextEdit()
        self.formula_display.setReadOnly(True)
        self.formula_display.setFont(QFont("Cambria Math", 10))
        self.formula_display.document().setDefaultStyleSheet("""
            body {
                font-family: 'Cambria Math', 'Times New Roman', serif;
                font-size: 12pt;
            }
        """)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)

        layout.addWidget(QLabel("\nCalculation Breakdown:"))
        layout.addWidget(self.formula_display)
        layout.addWidget(copy_btn)

        return layout

    def setup_connections(self):
        self.calculate_btn.clicked.connect(self.calculate_capacity)

    def calculate_capacity(self):
        try:
            W = float(self.drum_width_input.text())
            D = float(self.drum_od_input.text())
            F = float(self.flange_od_input.text())
            d = float(self.wire_od_input.text())

            radial_build = (F - D) / 2
            mean_diameter = D + radial_build

            capacity_feet = (W * radial_build * mean_diameter) / (4 * d**2)

            self.result_label.setText(
                f"Spool Capacity: {capacity_feet:,.1f} ft"
            )

            self.formula_display.setHtml(
                self.generate_formula_html(
                    W, D, F, d,
                    radial_build,
                    mean_diameter,
                    capacity_feet
                )
            )

        except Exception as e:
            self.formula_display.setHtml(
                f"<div style='color:red;font-weight:bold;'>Error: {str(e)}</div>"
            )

    def generate_formula_html(
        self, W, D, F, d,
        radial_build, mean_diameter,
        capacity_feet
    ):
        return f"""
        <style>
            .formula {{
                font-family: 'Cambria Math', 'Times New Roman', serif;
                font-size: 12pt;
                margin: 6px 0;
            }}
            .result {{
                font-weight: bold;
                color: #800020;
                font-size: 14pt;
                margin-top: 12px;
            }}
        </style>

        <div class="result">Spool Capacity Calculation</div>

        <div class="formula"><b>Input Parameters:</b></div>
        <div class="formula">Drum Width between flanges, W = {W:.3f} in</div>
        <div class="formula">Drum OD, D = {D:.3f} in</div>
        <div class="formula">Flange OD, F = {F:.3f} in</div>
        <div class="formula">Wire OD, d = {d:.4f} in</div>

        <div class="formula"><b>Step 1 – Radial Build:</b></div>
        <div class="formula">
            (F − D) / 2 = ({F:.3f} − {D:.3f}) / 2 = {radial_build:.3f} in
        </div>

        <div class="formula"><b>Step 2 – Mean Diameter:</b></div>
        <div class="formula">
            D + (F − D)/2 = {D:.3f} + {radial_build:.3f} = {mean_diameter:.3f} in
        </div>

        <div class="formula"><b>Step 3 – Capacity (inches):</b></div>
        <div class="formula">
            Capacity =
            (W × Radial Build × Mean Diameter) / (4 × d)
        </div>
        <div class="formula">
            = ({W:.3f} × {radial_build:.3f} × {mean_diameter:.3f}) / (4 × {d:.4f}<sup>2</sup>)
        </div>
        <div class="formula">
            = {capacity_feet:,.1f} ft
        </div>

        <div class="result">
            Final Spool Capacity = {capacity_feet:,.1f} ft
        </div>
        """

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.formula_display.toPlainText())
