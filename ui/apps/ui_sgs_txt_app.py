import datetime
import io

import openpyxl
import pandas as pd
import matplotlib.pyplot as plt
import bisect
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHBoxLayout, QApplication,
    QSplitter, QGridLayout, QGroupBox, QStackedWidget, QTimeEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from ui.windows.ui_messagebox_window import MessageBoxWindow
from utils.path_finder import get_icon_path
from utils.theme_manager import apply_theme, toggle_theme
import re
import matplotlib.dates as mdates


class QuadrupleDragDropWidget(QWidget):
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
        self.top_buttons = self.create_file_buttons("top")
        layout.addWidget(self.create_group_box("TOP GAUGE", self.top_drop, self.top_label, self.top_buttons), 0, 0)

        # Bottom gauge section
        self.bottom_label = QLabel("Drag & Drop Bottom Gauge Data File (.txt)")
        self.bottom_drop = self.create_drop_area("Bottom Gauge Data\n(.txt)")
        self.bottom_buttons = self.create_file_buttons("bottom")
        layout.addWidget(
            self.create_group_box("BOTTOM GAUGE", self.bottom_drop, self.bottom_label, self.bottom_buttons), 0, 1)

        # Timesheet section
        self.timesheet_label = QLabel("Drag & Drop Survey Timesheet (.xls/.xlsx)")
        self.timesheet_drop = self.create_drop_area("Survey Timesheet\n(.xls/.xlsx)")
        self.timesheet_buttons = self.create_file_buttons("timesheet")
        layout.addWidget(
            self.create_group_box("TIMESHEET", self.timesheet_drop, self.timesheet_label, self.timesheet_buttons), 1, 0)

        # TVD Calculation section
        self.tvd_label = QLabel("Drag & Drop TVD Calculation File (.xlsx)")
        self.tvd_drop = self.create_drop_area("TVD Calculation\n(.xlsx)")
        self.tvd_buttons = self.create_file_buttons("tvd")
        layout.addWidget(
            self.create_group_box("TVD CALCULATION", self.tvd_drop, self.tvd_label, self.tvd_buttons), 1, 1)

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
        layout.addWidget(self.process_btn, 2, 0, 1, 2)

        # Store file paths
        self.top_file_path = None
        self.bottom_file_path = None
        self.timesheet_file_path = None
        self.tvd_file_path = None

    def create_group_box(self, title, widget, label, buttons):
        group = QGroupBox(title)
        group_layout = QVBoxLayout(group)
        group_layout.addWidget(label)
        group_layout.addWidget(widget)
        group_layout.addLayout(buttons)
        return group

    def create_file_buttons(self, file_type):
        button_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #aaa;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        browse_btn.setFixedHeight(25)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 3px;
                padding: 3px;
                color: #721c24;
            }
            QPushButton:hover {
                background-color: #f5c6cb;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
            }
        """)
        clear_btn.setFixedHeight(25)
        clear_btn.setEnabled(False)

        # Connect signals
        browse_btn.clicked.connect(lambda: self.browse_file(file_type))
        clear_btn.clicked.connect(lambda: self.clear_file(file_type))

        button_layout.addWidget(browse_btn)
        button_layout.addWidget(clear_btn)

        # FIX: Properly handle all file types including "tvd"
        if file_type == "top":
            self.top_browse_btn = browse_btn
            self.top_clear_btn = clear_btn
        elif file_type == "bottom":
            self.bottom_browse_btn = browse_btn
            self.bottom_clear_btn = clear_btn
        elif file_type == "timesheet":
            self.timesheet_browse_btn = browse_btn
            self.timesheet_clear_btn = clear_btn
        elif file_type == "tvd":  # ADDED: Handle tvd file type
            self.tvd_browse_btn = browse_btn
            self.tvd_clear_btn = clear_btn

        return button_layout

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
        drop_area.dropEvent = lambda event: self.dropEvent(event, drop_area)
        return drop_area

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Only highlight the drop area being dragged over
            widget = self.childAt(event.position().toPoint())
            if widget in [self.top_drop, self.bottom_drop, self.timesheet_drop, self.tvd_drop]:
                widget.setStyleSheet("""
                    QLabel {
                        border: 3px dashed #3498db;
                        border-radius: 15px;
                        font: bold 12pt 'Segoe UI';
                        padding: 30px;
                        background-color: rgba(200, 230, 255, 150);
                    }
                """)

    def dropEvent(self, event: QDropEvent, drop_area):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.handle_file_drop(drop_area, file_path)

    def handle_file_drop(self, drop_area, file_path):
        # Determine which drop area received the file
        if drop_area == self.top_drop and file_path.endswith('.txt'):
            self.set_file("top", file_path)
        elif drop_area == self.bottom_drop and file_path.endswith('.txt'):
            self.set_file("bottom", file_path)
        elif drop_area == self.timesheet_drop and file_path.endswith(('.xls', '.xlsx')):
            self.set_file("timesheet", file_path)
        elif drop_area == self.tvd_drop and file_path.endswith('.xlsx'):
            self.set_file("tvd", file_path)
        else:
            QMessageBox.warning(self, "Invalid File", "Please drop the correct file type in each area")

    def browse_file(self, file_type):
        if file_type == "top":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Top Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.set_file("top", file_path)
        elif file_type == "bottom":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Bottom Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.set_file("bottom", file_path)
        elif file_type == "timesheet":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Survey Timesheet", "",
                "Excel Files (*.xls *.xlsx)"
            )
            if file_path:
                self.set_file("timesheet", file_path)
        elif file_type == "tvd":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open TVD Calculation File", "",
                "Excel Files (*.xlsx)"
            )
            if file_path:
                self.set_file("tvd", file_path)

    def clear_file(self, file_type):
        if file_type == "top":
            self.top_file_path = None
            self.top_drop.setText("Top Gauge Data\n(.txt)")
            self.top_drop.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)
            self.top_clear_btn.setEnabled(False)
        elif file_type == "bottom":
            self.bottom_file_path = None
            self.bottom_drop.setText("Bottom Gauge Data\n(.txt)")
            self.bottom_drop.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)
            self.bottom_clear_btn.setEnabled(False)
        elif file_type == "timesheet":
            self.timesheet_file_path = None
            self.timesheet_drop.setText("Survey Timesheet\n(.xls/.xlsx)")
            self.timesheet_drop.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)
            self.timesheet_clear_btn.setEnabled(False)
        elif file_type == "tvd":
            self.tvd_file_path = None
            self.tvd_drop.setText("TVD Calculation\n(.xlsx)")
            self.tvd_drop.setStyleSheet("""
                QLabel {
                    border: 3px dashed #aaa;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(240, 240, 240, 100);
                }
            """)
            self.tvd_clear_btn.setEnabled(False)

        # Disable process button if not all files are loaded
        self.process_btn.setEnabled(
            self.top_file_path is not None and
            self.bottom_file_path is not None and
            self.timesheet_file_path is not None and
            self.tvd_file_path is not None
        )

    def set_file(self, file_type, file_path):
        filename = file_path.split('/')[-1]

        if file_type == "top":
            self.top_file_path = file_path
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
            self.top_clear_btn.setEnabled(True)
        elif file_type == "bottom":
            self.bottom_file_path = file_path
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
            self.bottom_clear_btn.setEnabled(True)
        elif file_type == "timesheet":
            self.timesheet_file_path = file_path
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
            self.timesheet_clear_btn.setEnabled(True)
        elif file_type == "tvd":
            self.tvd_file_path = file_path
            self.tvd_drop.setText(f"Loaded:\n{filename}")
            self.tvd_drop.setStyleSheet("""
                QLabel {
                    border: 3px solid #2ecc71;
                    border-radius: 15px;
                    font: bold 12pt 'Segoe UI';
                    padding: 30px;
                    background-color: rgba(200, 255, 200, 150);
                }
            """)
            self.tvd_clear_btn.setEnabled(True)

        # Enable process button if all files are loaded
        self.process_btn.setEnabled(
            self.top_file_path is not None and
            self.bottom_file_path is not None and
            self.timesheet_file_path is not None and
            self.tvd_file_path is not None
        )

    def process_files(self):
        if all([self.top_file_path, self.bottom_file_path, self.timesheet_file_path, self.tvd_file_path]):
            self.callback(
                self.top_file_path,
                self.bottom_file_path,
                self.timesheet_file_path,
                self.tvd_file_path
            )

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
        self.top_file_path = None
        self.bottom_file_path = None
        self.timesheet_file_path = None
        self.ahd_tvd_map = {}
        self.events = []
        self.current_canvas = None  # Add this line

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

        # Main content area - using stacked widget for screens
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        # File upload screen
        self.file_upload_widget = QWidget()
        file_upload_layout = QVBoxLayout(self.file_upload_widget)
        file_upload_layout.setContentsMargins(20, 20, 20, 20)

        # Triple drag and drop area
        self.drag_drop_widget = QuadrupleDragDropWidget(self.process_all_files, self)
        file_upload_layout.addWidget(self.drag_drop_widget, 1)

        # Footer
        self.footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = self.footer.theme_button
        file_upload_layout.addWidget(self.footer)

        self.content_stack.addWidget(self.file_upload_widget)

        # Results display screen
        self.results_widget = QWidget()
        results_layout = QVBoxLayout(self.results_widget)
        results_layout.setContentsMargins(20, 20, 20, 20)

        # Navigation bar at top of results
        nav_bar = QWidget()
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(0, 0, 0, 10)

        self.back_button = QPushButton("← Back to File Upload")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.back_button.setFixedHeight(40)
        self.back_button.clicked.connect(self.show_file_upload)
        nav_layout.addWidget(self.back_button)

        results_layout.addWidget(nav_bar)

        # Results content
        results_content = QWidget()
        results_content_layout = QHBoxLayout(results_content)
        results_content_layout.setContentsMargins(0, 0, 0, 0)

        # Graph area - will contain two stacked graphs
        self.graph_widget = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_layout.setContentsMargins(0, 0, 0, 0)

        # Table area - now in a group box
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Create group box for the table
        table_group = QGroupBox("Station Data")
        table_group_layout = QVBoxLayout(table_group)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(19)
        self.table_widget.setHorizontalHeaderLabels([
            "Station", "Depth (ft)", "Start Time", "End Time", "Duration (min)",
            "AHD FTBDF", "TVD FTBDF",
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

        # # Connect item changed signal
        # self.table_widget.itemChanged.connect(self.on_table_item_changed)

        # Add table to group
        table_group_layout.addWidget(self.table_widget)

        # Create button row
        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # Create event section
        event_group = QGroupBox("Events")
        event_layout = QGridLayout(event_group)

        # Event input fields
        self.event_time_edit = QTimeEdit()
        self.event_time_edit.setDisplayFormat("HH:mm:ss")

        self.event_desc_edit = QLineEdit()
        self.event_desc_edit.setPlaceholderText("Enter event description")

        self.add_event_btn = QPushButton("Add Event")
        self.add_event_btn.clicked.connect(self.add_event)
        self.add_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4cae4c;
            }
        """)

        self.remove_event_btn = QPushButton("Remove Selected")
        self.remove_event_btn.clicked.connect(self.remove_event)
        self.remove_event_btn.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #c9302c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

        # Event table
        self.event_table = QTableWidget(0, 2)
        self.event_table.setHorizontalHeaderLabels(["Time", "Event Description"])
        self.event_table.horizontalHeader().setStretchLastSection(True)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Add widgets to layout
        event_layout.addWidget(QLabel("Time:"), 0, 0)
        event_layout.addWidget(self.event_time_edit, 0, 1)
        event_layout.addWidget(QLabel("Description:"), 0, 2)
        event_layout.addWidget(self.event_desc_edit, 0, 3)
        event_layout.addWidget(self.add_event_btn, 0, 4)
        event_layout.addWidget(self.remove_event_btn, 0, 5)
        event_layout.addWidget(self.event_table, 1, 0, 1, 6)

        # Add event section to table container
        table_layout.addWidget(event_group)
        table_layout.addWidget(button_row)

        self.copy_button = QPushButton("Copy Statistics")
        self.copy_button.setFixedWidth(150)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
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

        self.generate_as2_button = QPushButton("Generate AS2 Files")
        self.generate_as2_button.setFixedWidth(150)
        self.generate_as2_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.generate_as2_button.clicked.connect(self.generate_as2_files)
        self.generate_as2_button.setEnabled(False)  # Disabled until data is loaded

        # Inside the button_row section for results screen:
        self.copy_graphs_button = QPushButton("Copy Graphs")
        self.copy_graphs_button.setFixedWidth(150)
        self.copy_graphs_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.copy_graphs_button.clicked.connect(self.copy_graphs)
        self.copy_graphs_button.setEnabled(False)  # Disabled until data is loaded

        # Add it to the button layout BEFORE the generate_as2_button
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.copy_graphs_button)  # NEW BUTTON
        button_layout.addWidget(self.generate_as2_button)

        # Add group to container
        table_layout.addWidget(event_group)
        table_layout.addWidget(table_group)  # Now using group box
        table_layout.addWidget(button_row)

        # Add widgets to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.graph_widget)
        splitter.addWidget(table_container)
        splitter.setSizes([500, 500])
        results_content_layout.addWidget(splitter)

        results_layout.addWidget(results_content, 1)

        # Footer for results screen
        results_footer = FooterWidget(self, theme_callback=self.toggle_theme)
        results_layout.addWidget(results_footer)

        self.content_stack.addWidget(self.results_widget)

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

    def add_event(self):
        """Add a new event to the events list and table"""
        time_val = self.event_time_edit.time()
        time_str = time_val.toString("HH:mm:ss")
        desc = self.event_desc_edit.text().strip()

        if not desc:
            QMessageBox.warning(self, "Missing Description", "Please enter an event description")
            return

        # Get last time from data
        last_time = None
        if self.top_data:
            last_time = self.top_data[-1][0].time()
        elif self.bottom_data:
            last_time = self.bottom_data[-1][0].time()

        # Validate time
        if last_time and time_val > last_time:
            QMessageBox.warning(
                self,
                "Invalid Time",
                f"Event time exceeds last data point time ({last_time.toString('HH:mm:ss')})"
            )
            return

        # Add to events list
        self.events.append((time_str, desc))

        # Add to table
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)
        self.event_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.event_table.setItem(row, 1, QTableWidgetItem(desc))

        # Clear input fields
        self.event_desc_edit.clear()

        # Enable remove button
        self.remove_event_btn.setEnabled(True)

    def remove_event(self):
        """Remove selected event from the events list and table"""
        selected_row = self.event_table.currentRow()
        if selected_row >= 0:
            self.event_table.removeRow(selected_row)
            del self.events[selected_row]

            # Disable remove button if no events left
            if not self.events:
                self.remove_event_btn.setEnabled(False)

    def open_file_dialog(self, file_type):
        if file_type == 'tvd':  # Add this case
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open TVD Calculation File", "",
                "Excel Files (*.xlsx)"
            )
            if file_path:
                self.drag_drop_widget.set_file("tvd", file_path)
        elif file_type == 'top':
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Top Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.drag_drop_widget.set_file("top", file_path)
        elif file_type == 'bottom':
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Bottom Gauge Data File", "",
                "Text Files (*.txt)"
            )
            if file_path:
                self.drag_drop_widget.set_file("bottom", file_path)
        else:  # timesheet
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Survey Timesheet", "",
                "Excel Files (*.xls *.xlsx)"
            )
            if file_path:
                self.drag_drop_widget.set_file("timesheet", file_path)

    def save_file(self):
        MessageBoxWindow.message_simple(self, "Save", "Save functionality will be implemented here")

    def process_all_files(self, top_file_path, bottom_file_path, timesheet_file_path, tvd_file_path):
        try:
            self.top_file_path = top_file_path
            self.bottom_file_path = bottom_file_path
            self.timesheet_file_path = timesheet_file_path
            self.tvd_file_path = tvd_file_path

            # Process TVD file first
            self.tvd_data = self.process_tvd_file(tvd_file_path)

            # Process timesheet to get station timings
            self.station_timings = self.process_excel_timesheet(timesheet_file_path)

            # Process both gauge data files
            self.top_data = self.process_sgs_txt_file(top_file_path)
            self.bottom_data = self.process_sgs_txt_file(bottom_file_path)

            # Reset events when processing new files
            self.events = []
            self.event_table.setRowCount(0)
            self.remove_event_btn.setEnabled(False)

            if self.top_data and self.bottom_data and self.station_timings and self.tvd_data:
                # Show results screen
                self.content_stack.setCurrentIndex(1)

                # Create stacked graphs
                self.show_stacked_graphs(top_file_path, bottom_file_path)

                # Populate table with station timings and gauge data
                self.populate_station_table()
            else:
                QMessageBox.critical(self, "Error", "Failed to process one or more files")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process files:\n{str(e)}")

    def process_tvd_file(self, file_path):
        try:
            # Use data_only=True to get computed values instead of formulas
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb['Autofill']  # Use the 'Autofill' sheet

            # Extract metadata
            tvd_data = {
                'bdf': sheet['D2'].value,
                'sea_level': sheet['D3'].value,
                'location': sheet['I3'].value,
                'well': sheet['I4'].value,
                'ahd_values': [],
                'tvd_values': []
            }

            # Extract AHD from column C (starting at row 9)
            row = 9
            while True:
                ahd_cell = sheet.cell(row=row, column=3).value  # Column C
                tvd_cell = sheet.cell(row=row, column=9).value  # Column I

                # Stop when we find empty cells
                if ahd_cell is None and tvd_cell is None:
                    break

                # Add AHD value if exists
                if ahd_cell is not None:
                    try:
                        # Handle both numbers and strings that represent numbers
                        if isinstance(ahd_cell, str):
                            ahd_cell = float(ahd_cell.replace(',', ''))
                        ahd_value = float(ahd_cell)
                        tvd_data['ahd_values'].append(ahd_value)
                    except (ValueError, TypeError):
                        # Skip if conversion fails
                        pass

                # Add TVD value if exists
                if tvd_cell is not None:
                    try:
                        # Handle both numbers and strings that represent numbers
                        if isinstance(tvd_cell, str):
                            tvd_cell = float(tvd_cell.replace(',', ''))
                        tvd_value = float(tvd_cell)
                        tvd_data['tvd_values'].append(tvd_value)
                    except (ValueError, TypeError):
                        # Skip if conversion fails
                        pass

                row += 1

            return tvd_data

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process TVD file:\n{str(e)}")
            return {}

    def generate_as2_files(self):
        """Generate AS2 files for both top and bottom gauges"""
        if not self.top_data or not self.bottom_data:
            QMessageBox.warning(self, "No Data", "No gauge data available to generate AS2 files")
            return

        try:
            top_as2_path = self.generate_as2_file(self.top_file_path, self.top_data)
            bottom_as2_path = self.generate_as2_file(self.bottom_file_path, self.bottom_data)

            if top_as2_path and bottom_as2_path:
                QMessageBox.information(
                    self,
                    "Files Created",
                    f"Successfully created AS2 files:\n\n"
                    f"Top Gauge: {top_as2_path.split('/')[-1]}\n"
                    f"Bottom Gauge: {bottom_as2_path.split('/')[-1]}",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create AS2 files:\n{str(e)}")

    def generate_as2_file(self, input_file_path, data):
        """Generate AS2 formatted file from processed data with right-aligned columns"""
        # Determine output file path
        if input_file_path.endswith('.txt'):
            output_file_path = input_file_path.replace('.txt', '.AS2')
        else:
            output_file_path = input_file_path + '.AS2'

        if not data:
            # Create empty file if no data
            with open(output_file_path, 'w'):
                pass
            return output_file_path

        # Create event lookup dictionary
        event_dict = {time: desc for time, desc in self.events}

        # Calculate column widths
        max_pressure_width = max(len(f"{p:.2f}") for _, p, _ in data) if data else 0
        max_temp_width = max(len(f"{t:.3f}") for _, _, t in data) if data else 0

        with open(output_file_path, 'w') as f:
            for dt, pressure, temperature in data:
                date_str = dt.strftime("%d/%m/%Y")
                time_str = dt.strftime("%H:%M:%S")

                # Format numbers with fixed decimals and right-align
                temp_str = f"{temperature:.2f}".rjust(max_temp_width)
                pressure_str = f"{pressure:.3f}".rjust(max_pressure_width)

                # Check if there's an event at this time
                event_desc = event_dict.get(time_str, "")

                # Format line with event if exists
                line = f"{date_str}  {time_str}    {temp_str}     {pressure_str}  {event_desc}\n"
                f.write(line)

        return output_file_path

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
                        f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S"
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

    def show_file_upload(self):
        # Switch back to file upload screen
        self.content_stack.setCurrentIndex(0)

    def show_stacked_graphs(self, top_file_path, bottom_file_path):
        # Clear previous graph
        while self.graph_layout.count():
            child = self.graph_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create figure with two subplots and a status bar area
        fig = plt.figure(figsize=(10, 8.5))
        gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 0.1])
        ax_top = fig.add_subplot(gs[0])
        ax_bottom = fig.add_subplot(gs[1], sharex=ax_top)
        ax_status = fig.add_subplot(gs[2])
        ax_status.axis('off')  # Hide axes for status area

        # Plot top gauge data
        if self.top_data:
            times_top = [item[0] for item in self.top_data]
            pressures_top = [item[1] for item in self.top_data]
            temps_top = [item[2] for item in self.top_data]

            # Plot pressure
            ax_top.plot(times_top, pressures_top, 'b-', label='Pressure (psia)', linewidth=1.5)
            ax_top.set_ylabel('Pressure (psia)', color='b', fontsize=10)
            ax_top.tick_params(axis='y', labelcolor='b')
            ax_top.grid(True, linestyle='--', alpha=0.7)
            ax_top.set_title(f"Top Gauge - {top_file_path.split('/')[-1]}", fontsize=10)

            # Add temperature on secondary axis
            ax_top2 = ax_top.twinx()
            ax_top2.plot(times_top, temps_top, 'r-', label='Temperature (°F)', linewidth=1.5)
            ax_top2.set_ylabel('Temperature (°F)', color='r', fontsize=10)
            ax_top2.tick_params(axis='y', labelcolor='r')

        # Plot bottom gauge data
        if self.bottom_data:
            times_bottom = [item[0] for item in self.bottom_data]
            pressures_bottom = [item[1] for item in self.bottom_data]
            temps_bottom = [item[2] for item in self.bottom_data]

            # Plot pressure
            ax_bottom.plot(times_bottom, pressures_bottom, 'b-', label='Pressure (psia)', linewidth=1.5)
            ax_bottom.set_ylabel('Pressure (psia)', color='b', fontsize=10)
            ax_bottom.tick_params(axis='y', labelcolor='b')
            ax_bottom.grid(True, linestyle='--', alpha=0.7)
            ax_bottom.set_title(f"Bottom Gauge - {bottom_file_path.split('/')[-1]}", fontsize=10)

            # Add temperature on secondary axis
            ax_bottom2 = ax_bottom.twinx()
            ax_bottom2.plot(times_bottom, temps_bottom, 'r-', label='Temperature (°F)', linewidth=1.5)
            ax_bottom2.set_ylabel('Temperature (°F)', color='r', fontsize=10)
            ax_bottom2.tick_params(axis='y', labelcolor='r')

        # Format x-axis for both plots
        ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax_bottom.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        fig.autofmt_xdate()

        # Create status text
        self.status_text = ax_status.text(
            0.5, 0.5, "",
            ha="center", va="center",
            fontsize=10,
            transform=ax_status.transAxes
        )

        # Initialize cursor lines
        init_x = self.top_data[0][0] if self.top_data else self.bottom_data[0][0] if self.bottom_data else 0
        self.cursor_vline_top = ax_top.axvline(
            x=init_x, color='k', alpha=0.5, linewidth=1, visible=False
        )
        self.cursor_vline_bottom = ax_bottom.axvline(
            x=init_x, color='k', alpha=0.5, linewidth=1, visible=False
        )

        # Initialize markers for data points
        self.top_p_marker, = ax_top.plot([init_x], [0], 'bo', markersize=6, visible=False)
        self.top_t_marker, = ax_top2.plot([init_x], [0], 'ro', markersize=6, visible=False)
        self.bottom_p_marker, = ax_bottom.plot([init_x], [0], 'bo', markersize=6, visible=False)
        self.bottom_t_marker, = ax_bottom2.plot([init_x], [0], 'ro', markersize=6, visible=False)

        # Store data for quick lookup
        self.top_times = mdates.date2num(times_top) if self.top_data else None
        self.bottom_times = mdates.date2num(times_bottom) if self.bottom_data else None
        self.top_pressures = pressures_top if self.top_data else None
        self.top_temps = temps_top if self.top_data else None
        self.bottom_pressures = pressures_bottom if self.bottom_data else None
        self.bottom_temps = temps_bottom if self.bottom_data else None

        # Highlight station timings on both graphs
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.station_timings)))
        for idx, station in enumerate(self.station_timings):
            ax_top.axvspan(
                station['start'], station['end'],
                alpha=0.2, color=colors[idx],
                label=f"{station['station']} - {station['depth']}ft"
            )
            ax_bottom.axvspan(
                station['start'], station['end'],
                alpha=0.2, color=colors[idx],
                label=f"{station['station']} - {station['depth']}ft"
            )

        # Add legend to top plot only
        lines_top, labels_top = ax_top.get_legend_handles_labels()
        lines_top2, labels_top2 = ax_top2.get_legend_handles_labels()
        ax_top.legend(lines_top + lines_top2, labels_top + labels_top2, loc='upper left', fontsize=8)

        fig.tight_layout()
        canvas = FigureCanvas(fig)
        self.graph_layout.addWidget(canvas)
        self.current_canvas = canvas  # Store reference here
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def on_mouse_move(self, event):
        """Handle mouse movement over the graph"""
        if event.inaxes is None:
            # Hide everything when mouse leaves plot area
            self.cursor_vline_top.set_visible(False)
            self.cursor_vline_bottom.set_visible(False)
            self.top_p_marker.set_visible(False)
            self.top_t_marker.set_visible(False)
            self.bottom_p_marker.set_visible(False)
            self.bottom_t_marker.set_visible(False)
            self.status_text.set_text("")
            self.cursor_vline_top.figure.canvas.draw_idle()
            return

        x = event.xdata
        x_dt = mdates.num2date(x)

        # Update vertical lines
        self.cursor_vline_top.set_xdata([x])
        self.cursor_vline_bottom.set_xdata([x])
        self.cursor_vline_top.set_visible(True)
        self.cursor_vline_bottom.set_visible(True)

        # Initialize status text
        status_lines = [f"Time: {x_dt.strftime('%H:%M:%S')}"]

        # Find and display top gauge values
        if self.top_times is not None:
            idx = np.argmin(np.abs(self.top_times - x))
            closest_time = self.top_times[idx]
            time_diff = abs(closest_time - x)

            # Only show if we're close to actual data point
            if time_diff < 0.0001:  # Matplotlib time units (days)
                top_p = self.top_pressures[idx]
                top_t = self.top_temps[idx]

                # Update markers
                self.top_p_marker.set_data([x], [top_p])
                self.top_t_marker.set_data([x], [top_t])
                self.top_p_marker.set_visible(True)
                self.top_t_marker.set_visible(True)

                status_lines.append(f"Top: Pressure = {top_p:.2f} psia, Temp = {top_t:.2f} °F")
            else:
                self.top_p_marker.set_visible(False)
                self.top_t_marker.set_visible(False)

        # Find and display bottom gauge values
        if self.bottom_times is not None:
            idx = np.argmin(np.abs(self.bottom_times - x))
            closest_time = self.bottom_times[idx]
            time_diff = abs(closest_time - x)

            # Only show if we're close to actual data point
            if time_diff < 0.0001:  # Matplotlib time units (days)
                bottom_p = self.bottom_pressures[idx]
                bottom_t = self.bottom_temps[idx]

                # Update markers
                self.bottom_p_marker.set_data([x], [bottom_p])
                self.bottom_t_marker.set_data([x], [bottom_t])
                self.bottom_p_marker.set_visible(True)
                self.bottom_t_marker.set_visible(True)

                status_lines.append(f"Bottom: Pressure = {bottom_p:.2f} psia, Temp = {bottom_t:.2f} °F")
            else:
                self.bottom_p_marker.set_visible(False)
                self.bottom_t_marker.set_visible(False)

        # Update status text
        self.status_text.set_text("\n".join(status_lines))

        # Redraw canvas
        self.cursor_vline_top.figure.canvas.draw_idle()

    def populate_station_table(self):
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

                # Get AHD and TVD values if available
                if row < len(self.tvd_data['ahd_values']):
                    ahd_value = float(self.tvd_data['ahd_values'][row])
                    tvd_value = float(self.tvd_data['tvd_values'][row])
                else:
                    ahd_value = "N/A"
                    tvd_value = "N/A"

                # Add to table (columns 5 and 6)
                self.table_widget.setItem(row, 5, QTableWidgetItem(f"{ahd_value:.2f}"))
                self.table_widget.setItem(row, 6, QTableWidgetItem(f"{tvd_value:.2f}"))

                # Add to table
                self.table_widget.setItem(row, 7, QTableWidgetItem(f"{high_p_top:.2f}"))
                self.table_widget.setItem(row, 8, QTableWidgetItem(f"{low_p_top:.2f}"))
                self.table_widget.setItem(row, 9, QTableWidgetItem(f"{med_p_top:.2f}"))
                self.table_widget.setItem(row, 10, QTableWidgetItem(f"{high_t_top:.2f}"))
                self.table_widget.setItem(row, 11, QTableWidgetItem(f"{low_t_top:.2f}"))
                self.table_widget.setItem(row, 12, QTableWidgetItem(f"{med_t_top:.2f}"))
            else:
                for col in range(7, 13):
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
                self.table_widget.setItem(row, 13, QTableWidgetItem(f"{high_p_bottom:.2f}"))
                self.table_widget.setItem(row, 14, QTableWidgetItem(f"{low_p_bottom:.2f}"))
                self.table_widget.setItem(row, 15, QTableWidgetItem(f"{med_p_bottom:.2f}"))
                self.table_widget.setItem(row, 16, QTableWidgetItem(f"{high_t_bottom:.2f}"))
                self.table_widget.setItem(row, 17, QTableWidgetItem(f"{low_t_bottom:.2f}"))
                self.table_widget.setItem(row, 18, QTableWidgetItem(f"{med_t_bottom:.2f}"))
            else:
                for col in range(13, 19):
                    self.table_widget.setItem(row, col, QTableWidgetItem("N/A"))

        # Enable buttons now that we have data
        self.copy_button.setEnabled(True)
        self.generate_as2_button.setEnabled(True)
        self.table_widget.resizeColumnsToContents()
        # Enable the new button
        self.copy_graphs_button.setEnabled(True)


    def copy_statistics(self):
        """Copy pressure and temperature statistics to clipboard"""
        clipboard = QApplication.clipboard()

        # Get statistics data (columns 5-16)
        stats_data = []
        for row in range(self.table_widget.rowCount()):
            row_data = []
            for col in range(5, 19):  # Columns 5 to 16
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

    def copy_graphs(self):
        """Copy the current graphs to clipboard as an image"""
        if not self.current_canvas:  # Check if canvas exists
            QMessageBox.warning(self, "No Graphs", "No graphs available to copy")
            return

        try:
            # Create a buffer to save the image
            buf = io.BytesIO()
            self.current_canvas.figure.savefig(buf, format='png', dpi=100)
            buf.seek(0)

            # Create QImage from buffer
            image = QImage()
            image.loadFromData(buf.getvalue(), 'PNG')

            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setImage(image)

            # Show confirmation
            QMessageBox.information(
                self,
                "Copied",
                "Graphs copied to clipboard!",
                QMessageBox.StandardButton.Ok
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy graphs:\n{str(e)}")