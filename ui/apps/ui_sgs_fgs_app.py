from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QSpinBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QShortcut, QKeySequence, QGuiApplication, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from features.sgs_fgs.calculations import validate_table_data, calculate_gradients
from features.sgs_fgs.plot import plot_survey
from features.sgs_fgs.export import export_to_pdf
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.get_resource_path import get_icon_path
from utils.styles import combo_style
from utils.theme_manager import apply_theme, toggle_theme


class SGSFGSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SGS / FGS Interpretation Tool")
        self.setMinimumSize(1200, 600)
        self.init_ui()
        self.sidebar_expanded = False

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

    def init_ui(self):

        main_container = QVBoxLayout(self)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        main_layout = QHBoxLayout(self)  # Horizontal to place sidebar + main content

        items = [
            (get_icon_path('save'), "Save", lambda: QMessageBox.information(self, "Save", "Save not implemented yet."), "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load", lambda: QMessageBox.information(self, "Load", "Load not implemented yet."), "Open a file (Ctrl+O)"),
            (get_icon_path('plot'), "Plot", self.plot_graph, "Plot a graph from the current data"),
            (get_icon_path('copy'), "Copy as Image", self.copy_graph_to_clipboard, "Copy current graph as PNG"),
            (get_icon_path('export'), "Export", lambda: export_to_pdf(self.canvas, self.table, self), "Generate a PDF report"),
            # (get_icon_path('home'), "Main Menu", self.return_to_main_menu, "Return to the main menu"),
        ]

        self.sidebar = SidebarWidget(self, items)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(),"SGS/FGS Data Interpreter")

        main_container.addWidget(self.title_bar)

        main_layout.addWidget(self.sidebar)

        # --- Main content ---
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)

        # Title
        title = QLabel("Static & Flowing Gradient Survey Interpretation")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        # Controls (survey type + row selector)
        control_layout = QHBoxLayout()
        self.survey_type = QComboBox()
        self.survey_type.setStyleSheet(combo_style)
        self.survey_type.setCursor(Qt.CursorShape.PointingHandCursor)
        self.survey_type.addItems(["Static Gradient Survey (SGS)", "Flowing Gradient Survey (FGS)"])
        self.row_selector = QSpinBox()
        self.row_selector.setCursor(Qt.CursorShape.PointingHandCursor)
        self.row_selector.setRange(1, 100)
        self.row_selector.setValue(5)
        self.row_selector.valueChanged.connect(self.update_table_rows)

        control_layout.addWidget(self.survey_type)
        control_layout.addStretch()
        control_layout.addWidget(QLabel("Number of Rows:"))
        control_layout.addWidget(self.row_selector)
        content_layout.addLayout(control_layout)

        # Table + Plot
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
        copy_shortcut.activated.connect(self.copy_to_clipboard)
        self.style_gradient_columns()

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)


        # Buttons
        button_layout_table = QHBoxLayout()
        for text, slot in [
            ("Paste from Excel", self.paste_from_clipboard),
            ("Clear Table", self.clear_table),
        ]:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            button_layout_table.addWidget(btn)

        button_layout_plot = QHBoxLayout()
        for text, slot in [
            ("Plot Graph", self.plot_graph),
            ("Copy Graph to Clipboard", self.copy_graph_to_clipboard),
            # ("Export to CSV", lambda: export_to_csv(self.table, self)),
            ("Export to PDF", lambda: export_to_pdf(self.canvas, self.table, self)),
        ]:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            button_layout_plot.addWidget(btn)

        # content_layout.addLayout(button_layout_table)

        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table)
        table_layout.addLayout(button_layout_table)
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas)
        plot_layout.addLayout(button_layout_plot)
        table_plot_layout = QHBoxLayout()
        table_plot_layout.addLayout(table_layout)
        table_plot_layout.addLayout(plot_layout)
        content_layout.addLayout(table_plot_layout)

        # ✅ **Footer**
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        content_layout.addWidget(footer)

        content_layout.setContentsMargins(5,0,5,0)

        main_layout.addWidget(self.content_widget)
        self.setLayout(main_layout)
        main_container.addLayout(main_layout)


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
            tvd_list, pressure_list, temperature_list = validate_table_data(self.table)

            ax = self.figure.add_subplot(111)

            plot_survey(ax, tvd_list, pressure_list, self.survey_type.currentText(), temperature_list)
            self.canvas.draw()

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def return_to_main_menu(self):
        from ui.windows.ui_start_window import StartWindow
        self.start_window = StartWindow(app_icon=self.windowIcon())
        self.start_window.show()
        self.close()

    def paste_from_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            data = clipboard.text()
            rows = data.strip().split('\n')

            needed_rows = len(rows)
            self.row_selector.setValue(needed_rows)
            self.table.setRowCount(needed_rows)

            self.table.blockSignals(True)

            for i, row in enumerate(rows):
                cells = row.split('\t')
                for j, cell in enumerate(cells):
                    if j < self.table.columnCount():
                        self.table.setItem(i, j, QTableWidgetItem(cell.strip()))

            # Clear first gradient row
            self.table.setItem(0, 3, QTableWidgetItem(""))
            self.table.setItem(0, 4, QTableWidgetItem(""))

            self.style_gradient_columns()

            self.recalculate_gradients()

            self.table.blockSignals(False)


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

    def copy_graph_to_clipboard(self):
        """Copy the matplotlib figure to clipboard as image."""
        try:
            # Convert canvas to image
            self.canvas.draw()  # Ensure it's up to date
            width, height = self.canvas.get_width_height()
            buf = self.canvas.buffer_rgba()
            image = QImage(buf, width, height, QImage.Format.Format_RGBA8888)

            # Set image to clipboard
            QGuiApplication.clipboard().setImage(image)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Copied")
            msg_box.setText("📋 Graph copied to clipboard successfully!")
            msg_box.setStyleSheet("""
                QMessageBox {
                    color: black;
                }
                QMessageBox QLabel {
                    color: black;
                }
                QPushButton {
                    color: black;
                    border: 1px solid black;
                    padding: 5px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #c9c9c9;
                    cursor: pointer;
                }
            """)

            reply = msg_box.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy graph:\n{str(e)}")

    def recalculate_gradients(self):

        self.style_gradient_columns()

        try:
            tvd_list, pressure_list, temperature_list = validate_table_data(self.table)
            pressure_gradients = calculate_gradients(tvd_list, pressure_list)

            self.table.blockSignals(True)

            # Pressure gradient
            for i, gradient in enumerate(pressure_gradients, start=1):
                if i < self.table.rowCount():

                    abs_gradient = abs(gradient)
                    if abs_gradient <= 0.10:
                        cell_color = 'pink'
                    elif abs_gradient <= 0.39:
                        cell_color = 'lightgreen'
                    elif abs_gradient <= 0.46:
                        cell_color = 'lightblue'
                    else:
                        cell_color = 'lightgrey'

                    self.table.setItem(i, 3, QTableWidgetItem(f"{gradient:.4f}"))
                    item = self.table.item(i, 3)
                    item.setBackground(QColor(cell_color))

            # Temperature gradient
            for i in range(1, len(tvd_list)):
                try:
                    temp_grad = ((temperature_list[i] - temperature_list[i - 1]) /
                                 (tvd_list[i] - tvd_list[i - 1])) * 100
                    self.table.setItem(i, 4, QTableWidgetItem(f"{temp_grad:.2f}"))
                    item = self.table.item(i, 4)
                    item.setBackground(QColor("lightblue"))
                except ZeroDivisionError:
                    self.table.setItem(i, 4, QTableWidgetItem("∞"))
                    item = self.table.item(i, 4)
                    item.setBackground(QColor("lightgray"))

            self.table.blockSignals(False)

        except Exception:
            self.table.blockSignals(False)

    def style_gradient_columns(self):
        # pass
        try:
            for row in range(self.table.rowCount()):
                for col in [3, 4]:  # Gradient columns
                    if not self.table.item(row, col):
                        self.table.setItem(row, col, QTableWidgetItem(""))

                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("lightgray"))  # <- most reliable
        except Exception as e:
            print(f"Error in style_gradient_columns: {e}")


    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,  # ✅ exists now
            summary_widget=None
        )
