from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QSpinBox, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
# from ui.ui_start_window import StartWindow

from logic.sgs_fgs_calculations import validate_table_data, calculate_gradients
from plotting.sgs_fgs_plot import plot_survey
from logic.export_sgs_fgs import export_to_csv, export_to_pdf

class SGSFGSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SGS / FGS Interpretation Tool")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        title = QLabel("Static & Flowing Gradient Survey Interpretation")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        control_layout = QHBoxLayout()

        self.survey_type = QComboBox()
        self.survey_type.addItems(["Static Gradient Survey (SGS)", "Flowing Gradient Survey (FGS)"])
        control_layout.addWidget(self.survey_type)

        self.row_selector = QSpinBox()
        self.row_selector.setRange(1, 100)
        self.row_selector.setValue(5)
        self.row_selector.valueChanged.connect(self.update_table_rows)
        control_layout.addWidget(QLabel("Number of Rows:"))
        control_layout.addWidget(self.row_selector)

        main_layout.addLayout(control_layout)

        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["TVD (ft)", "Pressure (psi)", "Gradient (psi/ft)"])
        self.table.cellChanged.connect(self.recalculate_gradients)

        main_layout.addWidget(self.table)

        button_layout = QHBoxLayout()

        paste_button = QPushButton("Paste from Excel")
        paste_button.clicked.connect(self.paste_from_clipboard)
        button_layout.addWidget(paste_button)

        plot_button = QPushButton("Plot Graph")
        plot_button.clicked.connect(self.plot_graph)
        button_layout.addWidget(plot_button)

        export_csv_button = QPushButton("Export to CSV")
        export_csv_button.clicked.connect(lambda: export_to_csv(self.table, self))
        button_layout.addWidget(export_csv_button)

        export_pdf_button = QPushButton("Export to PDF")
        export_pdf_button.clicked.connect(lambda: export_to_pdf(self.canvas, self.table, self))
        button_layout.addWidget(export_pdf_button)

        clear_button = QPushButton("Clear Table")
        clear_button.clicked.connect(self.clear_table)
        button_layout.addWidget(clear_button)

        return_button = QPushButton("Return to Main Menu")
        return_button.clicked.connect(self.return_to_main_menu)
        button_layout.addWidget(return_button)

        main_layout.addLayout(button_layout)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def update_table_rows(self):
        rows = self.row_selector.value()
        self.table.setRowCount(rows)

    def clear_table(self):
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                self.table.setItem(row, col, QTableWidgetItem(""))
        self.figure.clear()
        self.canvas.draw()

    def plot_graph(self):
        try:
            tvd_list, pressure_list = validate_table_data(self.table)
            gradients = calculate_gradients(tvd_list, pressure_list)

            for i, gradient in enumerate(gradients, start=1):
                if i < self.table.rowCount():
                    self.table.setItem(i, 2, QTableWidgetItem(str(gradient)))

            ax = self.figure.add_subplot(111)
            plot_survey(ax, tvd_list, pressure_list, self.survey_type.currentText(), trendline=True)
            self.canvas.draw()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def return_to_main_menu(self):
        from ui.ui_start_window import StartWindow  # ⬅️ move import here to avoid circular import
        self.start_window = StartWindow(app_icon=self.windowIcon())
        self.start_window.show()
        self.close()

    def paste_from_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            data = clipboard.text()
            rows = data.strip().split('\n')

            needed_rows = len(rows)
            self.row_selector.setValue(needed_rows)  # 🔧 Sync spinbox with clipboard rows
            self.table.setRowCount(needed_rows)

            for i, row in enumerate(rows):
                cells = row.split('\t')
                for j, cell in enumerate(cells):
                    if j < self.table.columnCount():
                        self.table.setItem(i, j, QTableWidgetItem(cell.strip()))

            self.table.setItem(0, 2, QTableWidgetItem(""))

        except Exception as e:
            QMessageBox.critical(self, "Paste Failed", f"Could not paste data:\n{str(e)}")

    def recalculate_gradients(self):
        try:
            tvd_list, pressure_list = validate_table_data(self.table)
            gradients = calculate_gradients(tvd_list, pressure_list)

            self.table.blockSignals(True)
            for i, gradient in enumerate(gradients, start=1):
                if i < self.table.rowCount():
                    self.table.setItem(i, 2, QTableWidgetItem(str(gradient)))
            self.table.blockSignals(False)
            # self.table.setItem(0, 2, QTableWidgetItem(""))
        except Exception:
            self.table.blockSignals(False)
