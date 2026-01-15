from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QApplication, QSplitter, QComboBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class WireWeightTab(QWidget):
    def __init__(self):
        super().__init__()
        self.slickline_sizes = [
            "0.092\"",
            "0.108\"",
            "0.125\"",
            "0.140\"",
            "0.160\""
        ]
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
        self.wire_od_combo = QComboBox()
        self.wire_od_combo.addItems(self.slickline_sizes)
        self.wire_od_combo.setCurrentText("0.125\"")  # Default

        self.wire_length_input = QLineEdit()
        self.wire_length_input.setPlaceholderText("feet")

        # Calculate button
        self.calculate_btn = QPushButton("Calculate Wire Weight")
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
        self.result_label = QLabel("Wire Weight: -")
        self.result_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Layout
        layout.addWidget(QLabel("Wire OD:"), 0, 0)
        layout.addWidget(self.wire_od_combo, 0, 1)

        layout.addWidget(QLabel("Wire Length:"), 1, 0)
        layout.addWidget(self.wire_length_input, 1, 1)

        layout.addWidget(self.calculate_btn, 2, 0, 1, 2)
        layout.addWidget(self.result_label, 3, 0, 1, 2)

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
        self.calculate_btn.clicked.connect(self.calculate_wire_weight)

    def calculate_wire_weight(self):
        try:
            od_text = self.wire_od_combo.currentText().replace('"', '')
            od = float(od_text)

            length = float(self.wire_length_input.text())

            weight_per_1000ft = (8 / 3) * (od ** 2) * 1000
            total_weight = weight_per_1000ft * (length / 1000)

            self.result_label.setText(
                f"Wire Weight: {total_weight:,.1f} lbs"
            )

            self.formula_display.setHtml(
                self.generate_formula_html(
                    od, length,
                    weight_per_1000ft,
                    total_weight
                )
            )

        except Exception as e:
            self.formula_display.setHtml(
                f"<div style='color:red;font-weight:bold;'>Error: {str(e)}</div>"
            )

    def generate_formula_html(
        self, od, length,
        weight_per_1000ft,
        total_weight
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

        <div class="result">Wire Weight Calculation</div>

        <div class="formula"><b>Input Parameters:</b></div>
        <div class="formula">Wire OD, d = {od:.4f} in</div>
        <div class="formula">Wire Length, L = {length:,.1f} ft</div>

        <div class="formula"><b>Step 1 – Weight per 1000 ft:</b></div>
        <div class="formula">
            w = (8 / 3) × d<sup>2</sup> × 1000
        </div>
        <div class="formula">
            = (8 / 3) × ({od:.4f})<sup>2</sup> × 1000
        </div>
        <div class="formula">
            = {weight_per_1000ft:,.2f} lb / 1000 ft
        </div>

        <div class="formula"><b>Step 2 – Total Wire Weight:</b></div>
        <div class="formula">
            W = w × (L / 1000)
        </div>
        <div class="formula">
            = {weight_per_1000ft:,.2f} × ({length:,.1f} / 1000)
        </div>

        <div class="result">
            Final Wire Weight = {total_weight:,.1f} lbs
        </div>
        """

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.formula_display.toPlainText())
