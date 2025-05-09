from PyQt6.QtWidgets import QMessageBox


def calculate_pressure(self):
    try:
        psi_ft = float(self.gradient_psi_ft.text())
        ft = float(self.depth_ft.text())
        psi = psi_ft * ft
        self.result_label.setText(f"Hydrostatic Pressure: {psi:,.2f} psi")
    except ValueError:
        QMessageBox.warning(self, "Input Error", "Please enter valid numeric values for gradient and depth.")