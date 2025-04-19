from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QSpinBox, QFileDialog, QApplication
)
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QColor, QShortcut, QKeySequence
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
        self.setMinimumSize(1200, 600)
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

        # Layout to split table and plot side by side
        content_layout = QHBoxLayout()
        print('a')

        # Table setup
        self.table = QTableWidget(5, 5)
        self.table.setFixedWidth(500)
        self.table.setHorizontalHeaderLabels([
            "TVD (ft)", "Pressure (psi)", "Temperature\n(°F)",
            "Pressure\nGradient (psi/ft)", "Temperature\nGradient\n(°F/100ft)"
        ])
        self.table.cellChanged.connect(self.recalculate_gradients)

        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self.table)
        paste_shortcut.activated.connect(self.paste_from_clipboard)
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.table)
        copy_shortcut.activated.connect(self.copy_to_clipboard)  # You can define this later

        print('b')
        # Enable word wrap for header labels
        # self.table.horizontalHeader().setWordWrap(True)
        self.style_gradient_columns()

        content_layout.addWidget(self.table)

        print('c')
        # Plot canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        content_layout.addWidget(self.canvas, stretch=1)
        print('d')
        main_layout.addLayout(content_layout)

        # Buttons layout
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
        print('e')

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        print('init_ui complete')

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
            print('1')
            tvd_list, pressure_list, temperature_list = validate_table_data(self.table)
            print('2')
            gradients = calculate_gradients(tvd_list, pressure_list)

            # Calculate and populate pressure gradients
            for i, gradient in enumerate(gradients, start=1):
                if i < self.table.rowCount():
                    self.table.setItem(i, 3, QTableWidgetItem(f"{gradient:.4f}"))

            # Calculate and populate temperature gradients
            for i in range(1, len(tvd_list)):
                try:
                    temp_grad = ((temperature_list[i] - temperature_list[i - 1]) /
                                 (tvd_list[i] - tvd_list[i - 1])) * 100
                    self.table.setItem(i, 4, QTableWidgetItem(f"{temp_grad:.2f}"))
                except ZeroDivisionError:
                    self.table.setItem(i, 4, QTableWidgetItem("∞"))

            print('5')
            ax = self.figure.add_subplot(111)
            trendline = self.survey_type.currentText() != "Flowing Gradient Survey (FGS)"

            print('6')

            plot_survey(ax, tvd_list, pressure_list, self.survey_type.currentText(), trendline, temperature_list, fgs_temp_list=None)
            # plot_survey(ax, tvd_list, pressure_list, self.survey_type.currentText(), trendline, temperature_list, fgs_temp_list=fgs_temp)
            self.canvas.draw()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def return_to_main_menu(self):
        from ui.ui_start_window import StartWindow
        self.start_window = StartWindow(app_icon=self.windowIcon())
        self.start_window.show()
        self.close()

    def paste_from_clipboard(self):
        print("Pasting started")
        try:
            clipboard = QApplication.clipboard()
            data = clipboard.text()
            rows = data.strip().split('\n')

            needed_rows = len(rows)
            print(f"Pasting {needed_rows} rows")
            self.row_selector.setValue(needed_rows)
            self.table.setRowCount(needed_rows)

            self.table.blockSignals(True)

            for i, row in enumerate(rows):
                print(f"Row {i}: {row}")
                cells = row.split('\t')
                for j, cell in enumerate(cells):
                    if j < self.table.columnCount():
                        print(f"Setting cell ({i},{j}): {cell.strip()}")
                        self.table.setItem(i, j, QTableWidgetItem(cell.strip()))

            self.table.setItem(0, 3, QTableWidgetItem(""))  # clear first gradient cell
            self.table.blockSignals(False)

            print("Calling style_gradient_columns")
            self.style_gradient_columns()
            print("Calling recalculate_gradients")
            self.recalculate_gradients()

        except Exception as e:
            self.table.blockSignals(False)
            QMessageBox.critical(self, "Paste Failed", f"Could not paste data:\n{str(e)}")
            print(f"Exception during paste: {e}")

    def copy_to_clipboard(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        copied_text = ""

        for range_ in selected_ranges:
            for row in range(range_.topRow(), range_.bottomRow() + 1):
                row_text = []
                for col in range(range_.leftColumn(), range_.rightColumn() + 1):
                    item = self.table.item(row, col)
                    row_text.append(item.text() if item else "")
                copied_text += '\t'.join(row_text) + '\n'

        QApplication.clipboard().setText(copied_text.strip())

    def recalculate_gradients(self):

        self.style_gradient_columns()

        try:
            tvd_list, pressure_list, temperature_list = validate_table_data(self.table)
            pressure_gradients = calculate_gradients(tvd_list, pressure_list)

            self.table.blockSignals(True)

            # Pressure gradient
            for i, gradient in enumerate(pressure_gradients, start=1):
                if i < self.table.rowCount():
                    self.table.setItem(i, 3, QTableWidgetItem(f"{gradient:.4f}"))

            # Temperature gradient
            for i in range(1, len(tvd_list)):
                try:
                    temp_grad = ((temperature_list[i] - temperature_list[i - 1]) /
                                 (tvd_list[i] - tvd_list[i - 1])) * 100
                    self.table.setItem(i, 4, QTableWidgetItem(f"{temp_grad:.2f}"))
                except ZeroDivisionError:
                    self.table.setItem(i, 4, QTableWidgetItem("∞"))

            self.table.blockSignals(False)

        except Exception:
            self.table.blockSignals(False)

    def style_gradient_columns(self):
        pass
        # try:
        #     for row in range(self.table.rowCount()):
        #         for col in [3, 4]:  # Gradient columns
        #             if not self.table.item(row, col):
        #                 self.table.setItem(row, col, QTableWidgetItem(""))
        #
        #             item = self.table.item(row, col)
        #             if item:
        #                 item.setBackground(QColor("lightgray"))  # <- most reliable
        # except Exception as e:
        #     print(f"Error in style_gradient_columns: {e}")



