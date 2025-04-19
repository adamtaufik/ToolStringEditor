from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton, QLabel, QHBoxLayout, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
import math

class MDTVDConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MD to TVD Converter")
        self.setMinimumSize(700, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Mode selector
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["MD + TVD", "MD + Inclination"])
        self.mode_selector.currentIndexChanged.connect(self.update_table_headers)
        layout.addWidget(QLabel("Select Input Mode:"))
        layout.addWidget(self.mode_selector)

        # Table
        self.table = QTableWidget(5, 2)
        self.update_table_headers()
        layout.addWidget(self.table)

        # Button
        convert_button = QPushButton("Convert to TVD")
        convert_button.clicked.connect(self.perform_conversion)
        layout.addWidget(convert_button)

        # Output label
        self.result_label = QLabel("Results will be shown here.")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def update_table_headers(self):
        mode = self.mode_selector.currentText()
        if mode == "MD + TVD":
            self.table.setHorizontalHeaderLabels(["MD (ft)", "TVD (ft)"])
        else:
            self.table.setHorizontalHeaderLabels(["MD (ft)", "Inclination (deg)"])
        self.result_label.setText("")

    def perform_conversion(self):
        mode = self.mode_selector.currentText()
        md_list, second_col = [], []

        try:
            for row in range(self.table.rowCount()):
                md_item = self.table.item(row, 0)
                second_item = self.table.item(row, 1)

                if md_item and second_item:
                    md = float(md_item.text())
                    value = float(second_item.text())
                    md_list.append(md)
                    second_col.append(value)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")
            return

        if len(md_list) < 2:
            QMessageBox.warning(self, "Not Enough Data", "Please enter at least 2 rows of data.")
            return

        if mode == "MD + TVD":
            result = self.linear_interpolation(md_list, second_col)
        else:
            result = self.minimum_curvature(md_list, second_col)

        self.result_label.setText(result)

    def linear_interpolation(self, md_list, tvd_list):
        output = "Interpolated TVD Values (Linear):\n"
        for i in range(len(md_list) - 1):
            output += f"MD: {md_list[i]:.1f} ft, TVD: {tvd_list[i]:.2f} ft\n"
        output += f"MD: {md_list[-1]:.1f} ft, TVD: {tvd_list[-1]:.2f} ft"
        return output

    def minimum_curvature(self, md_list, incl_list):
        tvd_list = [0.0]
        output = "Calculated TVD using Minimum Curvature:\n"
        for i in range(1, len(md_list)):
            delta_md = md_list[i] - md_list[i - 1]
            incl1 = math.radians(incl_list[i - 1])
            incl2 = math.radians(incl_list[i])

            dogleg = math.acos(
                math.cos(incl1) * math.cos(incl2) + math.sin(incl1) * math.sin(incl2)
            )

            rf = 1 if dogleg == 0 else (2 / dogleg) * math.tan(dogleg / 2)
            delta_tvd = delta_md * rf * math.cos((incl1 + incl2) / 2)
            tvd = tvd_list[-1] + delta_tvd
            tvd_list.append(tvd)
            output += f"MD: {md_list[i]:.1f} ft, TVD: {tvd:.2f} ft\n"

        return output
