import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QSpinBox, QApplication,
    QSizePolicy, QTextEdit, QSplitter, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from ui.windows.ui_messagebox_window import MessageBoxWindow
from utils.path_finder import get_icon_path
from utils.styles import COMBO_STYLE
from utils.theme_manager import apply_theme, toggle_theme
import re
import matplotlib.dates as mdates


class TripleDragDropWidget(QWidget):
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setAcceptDrops(True)

        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Top gauge section
        self.top_label = QLabel("Drag & Drop Top Gauge Data File (.txt)")
        self.top_drop = self.create_drop_area("Top Gauge Data\n(.txt)")
        layout.addWidget(self.create_group_box("TOP GAUGE", self.top_drop, self.top_label), 0, 0)

        # Bottom gauge section
        self.bottom_label = QLabel("Drag & Drop Bottom Gauge Data File (.txt)")
        self.bottom_drop = self.create_drop_area("Bottom Gauge Data\n(.txt)")
        layout.addWidget(self.create_group_box("BOTTOM GAUGE", self.bottom_drop, self.bottom_label), 0, 1)

        # Timesheet section
        self.timesheet_label = QLabel("Drag & Drop Survey Timesheet (.xls/.xlsx)")
        self.timesheet_drop = self.create_drop_area("Survey Timesheet\n(.xls/.xlsx)")
        layout.addWidget(self.create_group_box("TIMESHEET", self.timesheet_drop, self.timesheet_label), 0, 2)

        # Status labels
        self.top_status = QLabel("No top gauge data loaded")
        self.top_status.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.top_status, 1, 0)

        self.bottom_status = QLabel("No bottom gauge data loaded")
        self.bottom_status.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.bottom_status, 1, 1)

        self.timesheet_status = QLabel("No timesheet loaded")
        self.timesheet_status.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.timesheet_status, 1, 2)

        # Process button
        self.process_btn = QPushButton("Process Files")
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.process_btn.clicked.connect(self.process_files)
        layout.addWidget(self.process_btn, 2, 0, 1, 3)

        # Store file paths
        self.top_file_path = None
        self.bottom_file_path = None
        self.timesheet_file_path = None

    def create_group_box(self, title, widget, label):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.addWidget(label)
        group_layout.addWidget(widget)
        return group

    def create_drop_area(self, text):
        drop_area = QLabel(text)
        drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_area.setStyleSheet("""
            QLabel {
                border: 3px dashed #aaa;
                border-radius: 15px;
                font: bold 12pt 'Segoe UI';
                padding: 30px;
                background-color: rgba(240, 240, 240, 100);
            }
        """)
        drop_area.setMinimumSize(200, 180)
        drop_area.setAcceptDrops(True)
        drop_area.dragEnterEvent = self.dragEnterEvent
        drop_area.dragLeaveEvent = self.dragLeaveEvent
        drop_area.dropEvent = lambda event: self.dropEvent(event, drop_area)
        return drop_area

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for drop_area in [self.top_drop, self.bottom_drop, self.timesheet_drop]:
                drop_area.setStyleSheet("""
                    QLabel {
                        border: 3px dashed #3498db;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 230, 255, 150);
                    }
                """)

    def dragLeaveEvent(self, event):
        for drop_area in [self.top_drop, self.bottom_drop, self.timesheet_drop]:
            drop_area.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)

    def dropEvent(self, event: QDropEvent, drop_area):
        # Reset all drop area styles
        for area in [self.top_drop, self.bottom_drop, self.timesheet_drop]:
            area.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)

        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()

            # Determine which drop area received the file
            if drop_area == self.top_drop and file_path.endswith('.txt'):
                self.top_file_path = file_path
                filename = file_path.split('/')[-1]
                self.top_status.setText(f"Top gauge: {filename}")
                self.top_drop.setText(f"Loaded:\n{filename}")
                self.top_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)
            elif drop_area == self.bottom_drop and file_path.endswith('.txt'):
                self.bottom_file_path = file_path
                filename = file_path.split('/')[-1]
                self.bottom_status.setText(f"Bottom gauge: {filename}")
                self.bottom_drop.setText(f"Loaded:\n{filename}")
                self.bottom_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)
            elif drop_area == self.timesheet_drop and file_path.endswith(('.xls', '.xlsx')):
                self.timesheet_file_path = file_path
                filename = file_path.split('/')[-1]
                self.timesheet_status.setText(f"Timesheet: {filename}")
                self.timesheet_drop.setText(f"Loaded:\n{filename}")
                self.timesheet_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)
            else:
                QMessageBox.warning(self, "Invalid File", "Please drop the correct file type in each area")

            # Enable process button if all files are loaded
            self.process_btn.setEnabled(
                self.top_file_path is not None and
                self.bottom_file_path is not None and
                self.timesheet_file_path is not None
            )

    def process_files(self):
        if self.top_file_path and self.bottom_file_path and self.timesheet_file_path:
            self.callback(self.top_file_path, self.bottom_file_path, self.timesheet_file_path)


class SGSTXTApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SGS / FGS txt processing")
        self.setMinimumSize(1400, 800)
        self.current_theme = "Deleum"
        self.init_ui()
        self.sidebar_expanded = False
        self.station_timings = []
        self.top_data = []
        self.bottom_data = []

    def init_ui(self):
        main_container = QVBoxLayout(self)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        items = [
            (get_icon_path('save'), "Save", self.save_file, "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load Top", lambda: self.open_file_dialog('top'), "Open top gauge data file"),
            (get_icon_path('load'), "Load Bottom", lambda: self.open_file_dialog('bottom'),
             "Open bottom gauge data file"),
            (get_icon_path('load'), "Load Timesheet", lambda: self.open_file_dialog('timesheet'), "Open timesheet")
        ]

        self.sidebar = SidebarWidget(self, items)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(), "SGS/FGS txt processing")

        main_container.addWidget(self.title_bar)
        main_layout.addWidget(self.sidebar)

        # Main content area
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Triple drag and drop area
        self.drag_drop_widget = TripleDragDropWidget(self.process_all_files, self)
        content_layout.addWidget(self.drag_drop_widget, 1)

        # Results display area
        self.results_container = QWidget()
        self.results_layout = QHBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)

        # Graph area - will contain two stacked graphs
        self.graph_widget = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_layout.setContentsMargins(0, 0, 0, 0)

        # Table area
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(12)  # 12 columns for both gauges
        self.table_widget.setHorizontalHeaderLabels([
            "Station", "Depth (ft)", "Start Time", "End Time", "Duration (min)",
            "High P (T)", "Low P (T)", "Med P (T)", "High T (T)", "Low T (T)", "Med T (T)",
            "High P (B)", "Low P (B)", "Med P (B)", "High T (B)", "Low T (B)", "Med T (B)"
        ])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)

        # Create copy button
        self.copy_button = QPushButton("Copy Statistics")
        self.copy_button.setFixedWidth(150)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.copy_button.clicked.connect(self.copy_statistics)
        self.copy_button.setEnabled(False)  # Disabled until data is loaded

        # Add widgets to table container
        table_layout.addWidget(self.table_widget)
        table_layout.addWidget(self.copy_button, 0, Qt.AlignmentFlag.AlignRight)

        # Add widgets to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.graph_widget)
        splitter.addWidget(table_container)
        splitter.setSizes([500, 500])
        self.results_layout.addWidget(splitter)

        content_layout.addWidget(self.results_container, 3)
        self.results_container.hide()

        # Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        content_layout.addWidget(footer)

        main_layout.addWidget(self.content_widget)
        main_container.addLayout(main_layout)
        self.setLayout(main_container)

        # Apply theme after UI is set up
        apply_theme(self, self.current_theme)

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )

    def open_file_dialog(self, file_type):
        if file_type == 'top':
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Top Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.drag_drop_widget.top_file_path = file_path
                filename = file_path.split('/')[-1]
                self.drag_drop_widget.top_status.setText(f"Top gauge: {filename}")
                self.drag_drop_widget.top_drop.setText(f"Loaded:\n{filename}")
                self.drag_drop_widget.top_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)
        elif file_type == 'bottom':
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Bottom Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.drag_drop_widget.bottom_file_path = file_path
                filename = file_path.split('/')[-1]
                self.drag_drop_widget.bottom_status.setText(f"Bottom gauge: {filename}")
                self.drag_drop_widget.bottom_drop.setText(f"Loaded:\n{filename}")
                self.drag_drop_widget.bottom_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)
        else:  # timesheet
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Survey Timesheet", "",
                "Excel Files (*.xls *.xlsx)"
            )
            if file_path:
                self.drag_drop_widget.timesheet_file_path = file_path
                filename = file_path.split('/')[-1]
                self.drag_drop_widget.timesheet_status.setText(f"Timesheet: {filename}")
                self.drag_drop_widget.timesheet_drop.setText(f"Loaded:\n{filename}")
                self.drag_drop_widget.timesheet_drop.setStyleSheet("""
                    QLabel {
                        border: 3px solid #2ecc71;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 255, 200, 150);
                    }
                """)

        # Enable process button if all files are loaded
        self.drag_drop_widget.process_btn.setEnabled(
            self.drag_drop_widget.top_file_path is not None and
            self.drag_drop_widget.bottom_file_path is not None and
            self.drag_drop_widget.timesheet_file_path is not None
        )

    def save_file(self):
        MessageBoxWindow.message_simple(self, "Save", "Save functionality will be implemented here")

    def process_all_files(self, top_file_path, bottom_file_path, timesheet_file_path):
        try:
            # Process timesheet to get station timings
            self.station_timings = self.process_excel_timesheet(timesheet_file_path)

            # Process both gauge data files
            self.top_data = self.process_sgs_txt_file(top_file_path)
            self.bottom_data = self.process_sgs_txt_file(bottom_file_path)

            # Generate AS2 files for both gauges
            self.generate_as2_file(top_file_path, self.top_data)
            self.generate_as2_file(bottom_file_path, self.bottom_data)

            if self.top_data and self.bottom_data and self.station_timings:
                # Show both graph and table
                self.show_results(top_file_path, bottom_file_path)

                # Populate table with station timings and gauge data
                self.populate_station_table()
            else:
                QMessageBox.critical(self, "Error", "Failed to process one or more files")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process files:\n{str(e)}")

    def generate_as2_file(self, input_file_path, data):
        """Generate AS2 formatted file from processed data with right-aligned columns"""
        try:
            # Determine output file path
            if input_file_path.endswith('.txt'):
                output_file_path = input_file_path.replace('.txt', '.AS2')
            else:
                output_file_path = input_file_path + '.AS2'

            if not data:
                # Create empty file if no data
                with open(output_file_path, 'w'):
                    pass
            else:
                # Calculate maximum column widths
                max_pressure_width = max(len(f"{p:.2f}") for _, p, _ in data)
                max_temp_width = max(len(f"{t:.3f}") for _, _, t in data)

                with open(output_file_path, 'w') as f:
                    for dt, pressure, temperature in data:
                        date_str = dt.strftime("%d/%m/%Y")
                        time_str = dt.strftime("%H:%M:%S")

                        # Format numbers with fixed decimals and right-align
                        pressure_str = f"{pressure:.2f}".rjust(max_pressure_width)
                        temp_str = f"{temperature:.3f}".rjust(max_temp_width)

                        # Maintain fixed spacing between columns
                        line = f"{date_str}  {time_str}  {pressure_str}     {temp_str}  \n"
                        f.write(line)

            # Show success message
            filename = output_file_path.split('/')[-1]
            QMessageBox.information(
                self,
                "File Created",
                f"Successfully created AS2 file:\n{filename}",
                QMessageBox.StandardButton.Ok
            )
            return output_file_path

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create AS2 file:\n{str(e)}")
            return None

    def process_sgs_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()

            # Find where data starts
            data_start = 0
            for i, line in enumerate(lines):
                if "Date" in line and "Time" in line and "Press" in line:
                    data_start = i + 2  # Skip header and unit line
                    break

            if data_start == 0:
                QMessageBox.critical(self, "Error", "Could not find data headers in file")
                return None

            # Parse data
            data = []
            for line in lines[data_start:]:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue

                try:
                    date_str = parts[0].replace("-", "/")
                    time_str = parts[1]
                    date_time = datetime.datetime.strptime(
                        f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S"
                    )
                    pressure = float(parts[2])
                    temperature = float(parts[3])
                    data.append((date_time, pressure, temperature))
                except ValueError:
                    continue

            return data if data else None

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process data file:\n{str(e)}")
            return None

    def process_excel_timesheet(self, file_path):
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, header=None, engine='openpyxl')
            else:
                df = pd.read_excel(file_path, header=None, engine='xlrd')

            # Find the date
            date_value = None
            for i in range(len(df)):
                cell_value = str(df.iloc[i, 2])
                if "Date :" in cell_value:
                    date_match = re.search(r'Date :\s*(\d{2}\.\d{2}\.\d{4})', cell_value)
                    if date_match:
                        date_value = datetime.datetime.strptime(date_match.group(1), "%d.%m.%Y").date()
                    break

            # Find the start of the data table
            data_start = None
            for i in range(len(df)):
                cell_value = str(df.iloc[i, 3])
                if 'ATM' in cell_value:
                    data_start = i + 1
                    break

            if data_start is None:
                QMessageBox.critical(self, "Error", "Could not find data table in timesheet")
                return []

            # Extract station data
            stations = []
            i = data_start
            while i < len(df):
                station_type = str(df.iloc[i, 3]).strip() if pd.notna(df.iloc[i, 3]) else ""
                depth = df.iloc[i, 4]
                duration = df.iloc[i, 5]
                start_time = df.iloc[i, 6]
                end_time = df.iloc[i, 8]

                # Skip if any critical value is missing
                if pd.isna(start_time) or pd.isna(end_time):
                    i += 1
                    continue

                # Convert times to 4-digit strings
                if isinstance(start_time, (int, float)):
                    start_time = f"{int(start_time):04d}"
                else:
                    start_time = str(start_time).strip().replace(':', '')[:4]

                if isinstance(end_time, (int, float)):
                    end_time = f"{int(end_time):04d}"
                else:
                    end_time = str(end_time).strip().replace(':', '')[:4]

                # Create datetime objects
                try:
                    start_dt = datetime.datetime.combine(
                        date_value,
                        datetime.time(int(start_time[:2]), int(start_time[2:]))
                    )
                    end_dt = datetime.datetime.combine(
                        date_value,
                        datetime.time(int(end_time[:2]), int(end_time[2:]))
                    )

                    if station_type != 'ATM':
                        stations.append({
                            'station': station_type,
                            'depth': depth,
                            'start': start_dt,
                            'end': end_dt,
                            'duration': duration
                        })
                except ValueError:
                    pass

                i += 1
                # Stop when we hit an empty row or end of table
                if i >= len(df) or (pd.isna(df.iloc[i, 3]) and not stations):
                    break

            return stations

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process timesheet:\n{str(e)}")
            return []

    def show_results(self, top_file_path, bottom_file_path):
        # Hide drag and drop, show results
        self.drag_drop_widget.hide()
        self.results_container.show()

        # Create stacked graphs
        self.show_stacked_graphs(top_file_path, bottom_file_path)

    def show_stacked_graphs(self, top_file_path, bottom_file_path):
        # Clear previous graph
        while self.graph_layout.count():
            child = self.graph_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create figure with two subplots
        fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        fig.subplots_adjust(hspace=0.1)  # Reduce space between plots

        # Plot top gauge data
        if self.top_data:
            times_top = [item[0] for item in self.top_data]
            pressures_top = [item[1] for item in self.top_data]
            temps_top = [item[2] for item in self.top_data]

            # Plot pressure
            ax_top.plot(times_top, pressures_top, 'b-', label='Pressure (kPaa)', linewidth=1.5)
            ax_top.set_ylabel('Pressure (kPaa)', color='b', fontsize=10)
            ax_top.tick_params(axis='y', labelcolor='b')
            ax_top.grid(True, linestyle='--', alpha=0.7)
            ax_top.set_title(f"Top Gauge - {top_file_path.split('/')[-1]}", fontsize=10)

            # Add temperature on secondary axis
            ax_top2 = ax_top.twinx()
            ax_top2.plot(times_top, temps_top, 'r-', label='Temperature (°C)', linewidth=1.5)
            ax_top2.set_ylabel('Temperature (°C)', color='r', fontsize=10)
            ax_top2.tick_params(axis='y', labelcolor='r')

        # Plot bottom gauge data
        if self.bottom_data:
            times_bottom = [item[0] for item in self.bottom_data]
            pressures_bottom = [item[1] for item in self.bottom_data]
            temps_bottom = [item[2] for item in self.bottom_data]

            # Plot pressure
            ax_bottom.plot(times_bottom, pressures_bottom, 'b-', label='Pressure (kPaa)', linewidth=1.5)
            ax_bottom.set_ylabel('Pressure (kPaa)', color='b', fontsize=10)
            ax_bottom.tick_params(axis='y', labelcolor='b')
            ax_bottom.grid(True, linestyle='--', alpha=0.7)
            ax_bottom.set_title(f"Bottom Gauge - {bottom_file_path.split('/')[-1]}", fontsize=10)
            ax_bottom.set_xlabel('Time', fontsize=10)

            # Add temperature on secondary axis
            ax_bottom2 = ax_bottom.twinx()
            ax_bottom2.plot(times_bottom, temps_bottom, 'r-', label='Temperature (°C)', linewidth=1.5)
            ax_bottom2.set_ylabel('Temperature (°C)', color='r', fontsize=10)
            ax_bottom2.tick_params(axis='y', labelcolor='r')

        # Format x-axis for both plots
        ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax_bottom.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        fig.autofmt_xdate()

        # Highlight station timings on both graphs
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.station_timings)))
        for idx, station in enumerate(self.station_timings):
            ax_top.axvspan(
                station['start'],
                station['end'],
                alpha=0.2,
                color=colors[idx],
                label=f"{station['station']} - {station['depth']}ft"
            )
            ax_bottom.axvspan(
                station['start'],
                station['end'],
                alpha=0.2,
                color=colors[idx],
                label=f"{station['station']} - {station['depth']}ft"
            )

        # Add legend to top plot only
        lines_top, labels_top = ax_top.get_legend_handles_labels()
        lines_top2, labels_top2 = ax_top2.get_legend_handles_labels()
        ax_top.legend(lines_top + lines_top2, labels_top + labels_top2, loc='upper left', fontsize=8)

        fig.tight_layout()

        # Add to Qt widget
        canvas = FigureCanvas(fig)
        self.graph_layout.addWidget(canvas)

    def populate_station_table(self):
        # Set column count and headers
        self.table_widget.setColumnCount(17)  # 16 columns total
        self.table_widget.setHorizontalHeaderLabels([
            "Station", "Depth (ft)", "Start Time", "End Time", "Duration (min)",
            "High P (T)", "Low P (T)", "Med P (T)", "High T (T)", "Low T (T)", "Med T (T)",
            "High P (B)", "Low P (B)", "Med P (B)", "High T (B)", "Low T (B)", "Med T (B)"
        ])

        self.table_widget.setRowCount(len(self.station_timings))

        for row, station in enumerate(self.station_timings):
            # Station info columns
            station_item = QTableWidgetItem(station['station'])
            self.table_widget.setItem(row, 0, station_item)

            depth_item = QTableWidgetItem(str(station['depth']) if not pd.isna(station['depth']) else "N/A")
            self.table_widget.setItem(row, 1, depth_item)

            start_item = QTableWidgetItem(station['start'].strftime("%H:%M:%S"))
            self.table_widget.setItem(row, 2, start_item)

            end_item = QTableWidgetItem(station['end'].strftime("%H:%M:%S"))
            self.table_widget.setItem(row, 3, end_item)

            duration_item = QTableWidgetItem(str(station['duration']))
            self.table_widget.setItem(row, 4, duration_item)

            # Top gauge statistics
            top_station_data = [
                point for point in self.top_data
                if station['start'] <= point[0] <= station['end']
            ]

            if top_station_data:
                top_pressures = [item[1] for item in top_station_data]
                top_temps = [item[2] for item in top_station_data]

                # Pressure stats
                high_p_top = max(top_pressures)
                low_p_top = min(top_pressures)
                med_p_top = np.median(top_pressures)

                # Temperature stats
                high_t_top = max(top_temps)
                low_t_top = min(top_temps)
                med_t_top = np.median(top_temps)

                # Add to table
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{high_p_top:.2f}"))
                self.table_widget.setItem(row, 6, QTableWidgetItem(f"{low_p_top:.2f}"))
                self.table_widget.setItem(row, 7, QTableWidgetItem(f"{med_p_top:.2f}"))
                self.table_widget.setItem(row, 8, QTableWidgetItem(f"{high_t_top:.2f}"))
                self.table_widget.setItem(row, 9, QTableWidgetItem(f"{low_t_top:.2f}"))
                self.table_widget.setItem(row, 10, QTableWidgetItem(f"{med_t_top:.2f}"))
            else:
                for col in range(5, 11):
                    self.table_widget.setItem(row, col, QTableWidgetItem("N/A"))

            # Bottom gauge statistics
            bottom_station_data = [
                point for point in self.bottom_data
                if station['start'] <= point[0] <= station['end']
            ]

            if bottom_station_data:
                bottom_pressures = [item[1] for item in bottom_station_data]
                bottom_temps = [item[2] for item in bottom_station_data]

                # Pressure stats
                high_p_bottom = max(bottom_pressures)
                low_p_bottom = min(bottom_pressures)
                med_p_bottom = np.median(bottom_pressures)

                # Temperature stats
                high_t_bottom = max(bottom_temps)
                low_t_bottom = min(bottom_temps)
                med_t_bottom = np.median(bottom_temps)

                # Add to table
                self.table_widget.setItem(row, 11, QTableWidgetItem(f"{high_p_bottom:.2f}"))
                self.table_widget.setItem(row, 12, QTableWidgetItem(f"{low_p_bottom:.2f}"))
                self.table_widget.setItem(row, 13, QTableWidgetItem(f"{med_p_bottom:.2f}"))
                self.table_widget.setItem(row, 14, QTableWidgetItem(f"{high_t_bottom:.2f}"))
                self.table_widget.setItem(row, 15, QTableWidgetItem(f"{low_t_bottom:.2f}"))
                self.table_widget.setItem(row, 16, QTableWidgetItem(f"{med_t_bottom:.2f}"))
            else:
                for col in range(11, 17):
                    self.table_widget.setItem(row, col, QTableWidgetItem("N/A"))

        # Enable copy button now that we have data
        self.copy_button.setEnabled(True)
        self.table_widget.resizeColumnsToContents()

    def copy_statistics(self):
        """Copy pressure and temperature statistics to clipboard"""
        clipboard = QApplication.clipboard()

        # Get statistics data (columns 5-16)
        stats_data = []
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(5, 17):  # Columns 5 to 16
                item = self.table_widget.item(row, col)
                row_data.append(item.text() if item else "")
            stats_data.append("\t".join(row_data))

        # Format as tab-separated values
        text_data = "\n".join(stats_data)

        # Set to clipboard
        clipboard.setText(text_data)

        # Show confirmation
        QMessageBox.information(
            self,
            "Copied",
            "All gauge statistics copied to clipboard!",
            QMessageBox.StandardButton.Ok
        )