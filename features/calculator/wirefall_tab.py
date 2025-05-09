from PyQt6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, \
    QHBoxLayout, QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import pandas as pd

class WirefallTab(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.df = pd.DataFrame(data, columns=["Tubing O.D.", "Wire Size", "Wire Fall/1000'"])
        print(self.df)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Inputs section
        input_layout = self.create_input_section()
        layout.addLayout(input_layout)

        # Formula display
        formula_layout = self.create_formula_section()
        layout.addLayout(formula_layout)

    def create_input_section(self):
        input_layout = QGridLayout()

        # Create and add all input widgets
        self.depth_input = QLineEdit()
        self.length_input = QLineEdit()
        self.unit_toggle_btn = QPushButton("Units: ft")
        self.unit_toggle_btn.setCheckable(True)
        self.unit_toggle_btn.clicked.connect(self.toggle_units)

        self.tubing_combo = QComboBox()
        self.tubing_combo.addItems(sorted(self.df["Tubing O.D."].unique()))

        self.wire_combo = QComboBox()
        self.wire_combo.addItems(sorted(self.df["Wire Size"].unique()))

        # Add to layout
        input_layout.addWidget(QLabel("Top of Rope Socket Depth:"), 0, 0)
        input_layout.addWidget(self.depth_input, 0, 1)
        input_layout.addWidget(self.unit_toggle_btn, 0, 2)

        input_layout.addWidget(QLabel("Length of Wire Left in Hole:"), 1, 0)
        input_layout.addWidget(self.length_input, 1, 1)

        input_layout.addWidget(QLabel("Wire Size:"), 2, 0)
        input_layout.addWidget(self.wire_combo, 2, 1)

        input_layout.addWidget(QLabel("Tubing Size:"), 3, 0)
        input_layout.addWidget(self.tubing_combo, 3, 1)

        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.clicked.connect(self.calculate_wirefall)
        input_layout.addWidget(self.calculate_btn, 4, 0, 1, 3)

        # Output labels
        self.output_fall_per_1000 = QLabel("Wire Fall Back per 1000': -")
        self.output_total_fall = QLabel("Wire Fall Back Total: -")
        self.output_top_wire = QLabel("Top of Wire (Approximate): -")

        input_layout.addWidget(self.output_fall_per_1000, 5, 0, 1, 3)
        input_layout.addWidget(self.output_total_fall, 6, 0, 1, 3)
        input_layout.addWidget(self.output_top_wire, 7, 0, 1, 3)

        print('input layout good')
        return input_layout

    def create_formula_section(self):
        formula_layout = QVBoxLayout()

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

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self.copy_formula)

        formula_layout.addWidget(QLabel("\nCalculation Breakdown:"))
        formula_layout.addWidget(self.formula_display)
        formula_layout.addWidget(copy_button)

        print('formula layout good')
        return formula_layout


    def toggle_units(self):
        if self.unit_toggle_btn.isChecked():
            self.unit_toggle_btn.setText("Units: m")
        else:
            self.unit_toggle_btn.setText("Units: ft")

    def calculate_wirefall(self):
        try:
            depth = float(self.depth_input.text())
            wire_left = float(self.length_input.text())
            if self.unit_toggle_btn.text() == "Units: m":
                depth *= 3.28084
                wire_left *= 3.28084

            tubing = self.tubing_combo.currentText()
            wire = self.wire_combo.currentText()

            row = self.df[(self.df["Tubing O.D."] == tubing) & (self.df["Wire Size"] == wire)]
            if row.empty:
                self.formula_display.setHtml("<div style='color: red;'>No data for this combination.</div>")
                return

            fall_per_1000 = row.iloc[0]["Wire Fall/1000'"]
            total_fall = (fall_per_1000 / 1000) * wire_left
            top_wire = (depth - wire_left) + total_fall

            self.output_fall_per_1000.setText(f"Wire Fall Back per 1000': {fall_per_1000} ft")
            self.output_total_fall.setText(f"Wire Fall Back Total: {total_fall:.2f} ft")
            self.output_top_wire.setText(f"Top of Wire (Approximate): {top_wire:.2f} ft")

            self.formula_display.setHtml(f"""
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
                            margin: 0 3px;
                        }}
                        .frac > span {{
                            display: block;
                            padding: 0.1em;
                        }}
                        .frac span.bottom {{
                            border-top: 1px solid;
                        }}
                        .frac span.symbol {{
                            display: none;
                        }}
                        .overline {{
                            text-decoration: overline;
                        }}
                        .unit {{
                            font-style: italic;
                        }}
                    </style>

                    <div class="result">Wire Fall Back Total</div>
                    <div class="formula">
                        <i>F</i><sub>total</sub> = 
                        <span class="frac">
                            <span>{fall_per_1000}</span>
                            <span class="bottom">1000</span>
                            <span class="symbol">/</span>
                        </span>
                        × {wire_left:.2f}
                    </div>
                    <div class="formula"><span class="overline">        </span> = {total_fall:.2f} <span class="unit">ft</span></div>

                    <div class="result">Top of Wire (Approximate)</div>
                    <div class="formula"><i>T</i> = ( {depth:.2f} − {wire_left:.2f} ) + {total_fall:.2f}</div>
                    <div class="formula"><span class="overline">                 </span> = {top_wire:.2f} <span class="unit">ft</span></div>
                """)

        except ValueError:
            self.formula_display.setHtml("<div style='color: red;'>Please enter valid numeric inputs.</div>")

    def copy_formula(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.formula_display.toPlainText())