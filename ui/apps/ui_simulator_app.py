import math

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QPushButton,
                             QDoubleSpinBox, QSlider, QSplitter, QMessageBox, QComboBox, QTableWidget, QCheckBox,
                             QApplication, QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from scipy.interpolate import interp1d

from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.styles import GROUPBOX_STYLE
from utils.theme_manager import toggle_theme, apply_theme


class WirelineSimulatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wireline Operations Simulator")
        self.resize(1300, 700)

        # Central widget to hold everything
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout for the central widget
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # Custom Frameless Title Bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            "Wireline Operations Simulator"  # Updated title to match window
        )
        root_layout.addWidget(self.title_bar)

        # Create main content area (sidebar + tabs)
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar with actions
        sidebar_items = [
            (get_icon_path('save'), "Save", lambda: QMessageBox.information(self, "Save", "Save not implemented yet."),
             "Save the current file (Ctrl+S)"),
            (get_icon_path('load'), "Load", lambda: QMessageBox.information(self, "Load", "Load not implemented yet."),
             "Open a file (Ctrl+O)"),
        ]
        self.sidebar = SidebarWidget(self, sidebar_items)
        content_layout.addWidget(self.sidebar)

        # Tab widget for main content
        self.tabs = QTabWidget()
        self.create_main_operation_tab()
        self.create_input_tab()
        self.create_weight_vs_depth_tab()
        content_layout.addWidget(self.tabs)

        root_layout.addWidget(content_area)

        # Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        root_layout.addWidget(footer)

        # Simulation timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.update_simulation)
        self.sim_speed = 1.0
        self.current_depth = 0
        self.operation = None
        self.max_depth = 1000

        # Default values for wire and tool
        self.wire_weight = 0.021  # Will be updated when combo box changes
        self.wire_diameter = 0.108
        self.tool_weight = 150

        # Fluid properties
        self.fluid_density = 8.5  # ppg
        self.buoyancy_factor = 1 - (self.fluid_density / 65.4)
        self.pressure = 500  # psi
        self.FRICTION_COEFF = 0.3

        # Initialize trajectory data with default vertical well
        self.trajectory_data = {
            'mds': [0, 10000],
            'tvd': [0, 10000],
            'inclinations': [0, 0],
            'azimuths': [45, 45],
            'north': [0, 0],
            'east': [0, 0]
        }
        


    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )

    def create_input_tab(self):
        """Create the input configuration tab with all parameters"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)  # Main horizontal layout


        # Left side: Tool, Fluid properties, and Well Conditions in equal sizes
        left_side = QWidget()
        left_layout = QVBoxLayout(left_side)
        left_layout.setContentsMargins(0, 0, 0, 0)  # Remove default margins

        # Tool string group
        tool_group = QGroupBox("Tool String Configuration")
        tool_group.setStyleSheet(GROUPBOX_STYLE)
        tool_layout = QVBoxLayout()

        # [Rest of your tool group setup remains the same...]
        # Wire size selection
        wire_size_layout = QHBoxLayout()
        wire_size_layout.addWidget(QLabel("Wire Size:"))
        self.wire_size_combo = QComboBox()
        self.wire_size_combo.addItems(["0.092", "0.108", "0.125", "0.140", "0.160"])
        self.wire_size_combo.setCurrentText("0.108")
        self.wire_size_combo.currentTextChanged.connect(self.update_wire_properties)
        wire_size_layout.addWidget(self.wire_size_combo)
        tool_layout.addLayout(wire_size_layout)

        # [Rest of your existing code for wire weight, tool weight, etc...]
        # Wire weight display
        wire_weight_layout = QHBoxLayout()
        wire_weight_layout.addWidget(QLabel("Wire Weight:"))
        self.wire_weight_label = QLabel("0.021 lbs/ft")
        wire_weight_layout.addWidget(self.wire_weight_label)
        tool_layout.addLayout(wire_weight_layout)

        # Tool string weight input
        tool_weight_layout = QHBoxLayout()
        tool_weight_layout.addWidget(QLabel("Tool String Weight:"))
        self.tool_weight_input = QDoubleSpinBox()
        self.tool_weight_input.setRange(0, 1000)
        self.tool_weight_input.setValue(150)
        self.tool_weight_input.setSuffix(" lbs")
        tool_weight_layout.addWidget(self.tool_weight_input)
        tool_layout.addLayout(tool_weight_layout)
        tool_group.setLayout(tool_layout)
        left_layout.addWidget(tool_group, stretch=1)  # Equal stretch for all groups

        # Fluid Properties Group
        fluid_group = QGroupBox("Fluid Properties")
        fluid_group.setStyleSheet(GROUPBOX_STYLE)
        fluid_layout = QVBoxLayout()

        # [Rest of your fluid properties setup...]
        # Fluid density input
        fluid_density_layout = QHBoxLayout()
        fluid_density_layout.addWidget(QLabel("Fluid Density:"))
        self.fluid_density_input = QDoubleSpinBox()
        self.fluid_density_input.setRange(0, 20)
        self.fluid_density_input.setValue(8.5)
        self.fluid_density_input.setSuffix(" ppg")
        self.fluid_density_input.valueChanged.connect(self.update_fluid_properties)
        fluid_density_layout.addWidget(self.fluid_density_input)
        fluid_layout.addLayout(fluid_density_layout)

        # Fluid level input
        fluid_level_layout = QHBoxLayout()
        fluid_level_layout.addWidget(QLabel("Fluid Level:"))
        self.fluid_level_input = QDoubleSpinBox()
        self.fluid_level_input.setRange(0, 10000)
        self.fluid_level_input.setValue(300)
        self.fluid_level_input.setSuffix(" ft")
        fluid_level_layout.addWidget(self.fluid_level_input)
        fluid_layout.addLayout(fluid_level_layout)
        fluid_group.setLayout(fluid_layout)
        left_layout.addWidget(fluid_group, stretch=1)  # Equal stretch for all groups

        # Well Conditions Group
        well_group = QGroupBox("Well Conditions")
        well_group.setStyleSheet(GROUPBOX_STYLE)
        well_layout = QVBoxLayout()

        # [Rest of your well conditions setup...]
        # Well pressure input
        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Well Pressure:"))
        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(0, 10000)
        self.pressure_input.setValue(500)
        self.pressure_input.setSuffix(" psi")
        pressure_layout.addWidget(self.pressure_input)
        well_layout.addLayout(pressure_layout)

        # Friction coefficient input
        friction_layout = QHBoxLayout()
        friction_layout.addWidget(QLabel("Friction Coefficient:"))
        self.friction_input = QDoubleSpinBox()
        self.friction_input.setRange(0, 1)
        self.friction_input.setValue(0.3)
        self.friction_input.setSingleStep(0.05)
        friction_layout.addWidget(self.friction_input)
        well_layout.addLayout(friction_layout)
        well_group.setLayout(well_layout)
        left_layout.addWidget(well_group, stretch=1)  # Equal stretch for all groups

        # Checkbox group
        checkbox_group = QGroupBox("Survey Options")
        checkbox_group.setStyleSheet(GROUPBOX_STYLE)
        checkbox_layout = QVBoxLayout()

        # [Rest of your checkbox setup...]
        # Create checkboxes in a horizontal layout
        checkboxes_layout = QHBoxLayout()
        self.tvd_checkbox = QCheckBox("Use Custom TVD")
        self.incl_checkbox = QCheckBox("Use Custom Inclination")
        self.azim_checkbox = QCheckBox("Use Custom Azimuth")

        checkboxes_layout.addWidget(self.tvd_checkbox)
        checkboxes_layout.addWidget(self.incl_checkbox)
        checkboxes_layout.addWidget(self.azim_checkbox)
        checkbox_layout.addLayout(checkboxes_layout)
        checkbox_group.setLayout(checkbox_layout)
        left_layout.addWidget(checkbox_group)

        # Add unit toggle button to the left side layout
        unit_toggle_btn = QPushButton("Toggle Units (ft ↔ m)")
        unit_toggle_btn.clicked.connect(self.toggle_units)
        left_layout.addWidget(unit_toggle_btn)

        left_layout.addStretch()
        main_layout.addWidget(left_side)

        # Right side: Survey tables arranged horizontally with equal widths
        survey_group = QGroupBox("MD to TVD Survey")
        survey_group.setStyleSheet(GROUPBOX_STYLE)
        survey_layout = QVBoxLayout()
        survey_layout.setContentsMargins(0, 0, 0, 0)

        # [Rest of your survey tables setup...]
        # Create a horizontal layout for the tables
        tables_layout = QHBoxLayout()
        tables_layout.setContentsMargins(0, 0, 0, 0)

        # MD Table
        md_group = QGroupBox("MD")
        md_group.setStyleSheet(GROUPBOX_STYLE)
        md_layout = QVBoxLayout()
        md_paste_btn = QPushButton("Paste MD Data")
        md_paste_btn.clicked.connect(lambda: self.paste_table_data(self.md_table))
        md_layout.addWidget(md_paste_btn)
        self.md_table = QTableWidget()
        self.md_table.setColumnCount(1)
        self.md_table.setHorizontalHeaderLabels(["MD (ft)"])
        self.md_table.setRowCount(20)
        md_layout.addWidget(self.md_table)
        md_group.setLayout(md_layout)
        tables_layout.addWidget(md_group, stretch=1)  # Equal stretch for all tables

        # TVD Table
        tvd_group = QGroupBox("TVD")
        tvd_group.setStyleSheet(GROUPBOX_STYLE)
        tvd_layout = QVBoxLayout()
        tvd_paste_btn = QPushButton("Paste TVD Data")
        tvd_paste_btn.clicked.connect(lambda: self.paste_table_data(self.tvd_table))
        tvd_layout.addWidget(tvd_paste_btn)
        self.tvd_table = QTableWidget()
        self.tvd_table.setColumnCount(1)
        self.tvd_table.setHorizontalHeaderLabels(["TVD (ft)"])
        self.tvd_table.setRowCount(20)
        self.tvd_table.setEnabled(False)
        tvd_layout.addWidget(self.tvd_table)
        tvd_group.setLayout(tvd_layout)
        tables_layout.addWidget(tvd_group, stretch=1)  # Equal stretch for all tables

        # Inclination Table
        incl_group = QGroupBox("Inclination")
        incl_group.setStyleSheet(GROUPBOX_STYLE)
        incl_layout = QVBoxLayout()
        incl_paste_btn = QPushButton("Paste Inclination Data")
        incl_paste_btn.clicked.connect(lambda: self.paste_table_data(self.incl_table))
        incl_layout.addWidget(incl_paste_btn)
        self.incl_table = QTableWidget()
        self.incl_table.setColumnCount(1)
        self.incl_table.setHorizontalHeaderLabels(["Inclination (deg)"])
        self.incl_table.setRowCount(20)
        self.incl_table.setEnabled(False)
        incl_layout.addWidget(self.incl_table)
        incl_group.setLayout(incl_layout)
        tables_layout.addWidget(incl_group, stretch=1)  # Equal stretch for all tables

        # Azimuth Table
        azim_group = QGroupBox("Azimuth")
        azim_group.setStyleSheet(GROUPBOX_STYLE)
        azim_layout = QVBoxLayout()
        azim_paste_btn = QPushButton("Paste Azimuth Data")
        azim_paste_btn.clicked.connect(lambda: self.paste_table_data(self.azim_table))
        azim_layout.addWidget(azim_paste_btn)
        self.azim_table = QTableWidget()
        self.azim_table.setColumnCount(1)
        self.azim_table.setHorizontalHeaderLabels(["Azimuth (deg)"])
        self.azim_table.setRowCount(20)
        self.azim_table.setEnabled(False)
        azim_layout.addWidget(self.azim_table)
        azim_group.setLayout(azim_layout)
        tables_layout.addWidget(azim_group, stretch=1)  # Equal stretch for all tables

        survey_layout.addLayout(tables_layout)

        # Generate button
        generate_btn = QPushButton("Generate Well Trajectory")
        generate_btn.clicked.connect(self.generate_trajectory_from_tables)
        survey_layout.addWidget(generate_btn)

        # Checkbox connections
        self.tvd_checkbox.stateChanged.connect(
            lambda state: self.tvd_table.setEnabled(state == Qt.CheckState.Checked.value))
        self.incl_checkbox.stateChanged.connect(
            lambda state: self.incl_table.setEnabled(state == Qt.CheckState.Checked.value))
        self.azim_checkbox.stateChanged.connect(
            lambda state: self.azim_table.setEnabled(state == Qt.CheckState.Checked.value))

        survey_group.setLayout(survey_layout)
        main_layout.addWidget(survey_group)

        self.tabs.addTab(tab, "Input Panel")

        # Initialize properties
        self.update_wire_properties()
        self.update_fluid_properties()

    def paste_table_data(self, table):
        """Paste clipboard data into table, removing commas from numbers"""
        clipboard = QApplication.clipboard()
        data = clipboard.text()

        if not data:
            return

        # Split data into rows and cells
        rows = data.split('\n')

        # Clear existing selection
        table.clearSelection()

        # Get current position or start from (0, 0)
        current_row = table.currentRow() if table.currentRow() >= 0 else 0
        current_col = table.currentColumn() if table.currentColumn() >= 0 else 0

        for i, row in enumerate(rows):
            if not row.strip():
                continue

            if current_row + i >= table.rowCount():
                table.insertRow(table.rowCount())

            cells = row.split('\t')
            for j, cell in enumerate(cells):
                if current_col + j >= table.columnCount():
                    continue

                # Remove any commas from the cell content
                cleaned_cell = cell.replace(',', '').strip()

                # Try to convert to float if it's a number
                try:
                    float_val = float(cleaned_cell)
                    item = QTableWidgetItem(str(float_val))
                except ValueError:
                    item = QTableWidgetItem(cleaned_cell)

                table.setItem(current_row + i, current_col + j, item)

    def generate_trajectory_from_tables(self):
        """Generate well trajectory from the table data"""
        # Get MD data
        md_data = []
        for row in range(self.md_table.rowCount()):
            item = self.md_table.item(row, 0)
            if item and item.text():
                try:
                    md_data.append(float(item.text()))
                except ValueError:
                    QMessageBox.warning(self, "Invalid Data", f"Invalid MD value in row {row + 1}")
                    return

        if not md_data:
            QMessageBox.warning(self, "No Data", "Please enter MD values")
            return

        # Ensure MD values are strictly increasing
        if not all(md_data[i] < md_data[i + 1] for i in range(len(md_data) - 1)):
            QMessageBox.warning(self, "Invalid Data", "MD values must be strictly increasing")
            return

        # ... (rest of the existing code)

        # Get TVD data (or use MD if checkbox not checked)
        if self.tvd_checkbox.isChecked():
            tvd_data = []
            for row in range(self.tvd_table.rowCount()):
                item = self.tvd_table.item(row, 0)
                if item and item.text():
                    try:
                        tvd_data.append(float(item.text()))
                    except ValueError:
                        QMessageBox.warning(self, "Invalid Data", f"Invalid TVD value in row {row + 1}")
                        return
        else:
            tvd_data = md_data.copy()  # Default to MD if not using custom TVD

        # Get Inclination data (or calculate from MD/TVD if checkbox not checked)
        if self.incl_checkbox.isChecked():
            incl_data = []
            for row in range(self.incl_table.rowCount()):
                item = self.incl_table.item(row, 0)
                if item and item.text():
                    try:
                        incl_data.append(float(item.text()))
                    except ValueError:
                        QMessageBox.warning(self, "Invalid Data", f"Invalid Inclination value in row {row + 1}")
                        return
        else:
            # Calculate inclination from MD and TVD
            incl_data = [0.0] * len(md_data)
            for i in range(1, len(md_data)):
                delta_md = md_data[i] - md_data[i - 1]
                delta_tvd = tvd_data[i] - tvd_data[i - 1]
                if delta_md > 0:
                    incl_data[i] = np.degrees(np.arccos(delta_tvd / delta_md))

        # Get Azimuth data (or use 45° if checkbox not checked)
        if self.azim_checkbox.isChecked():
            azim_data = []
            for row in range(self.azim_table.rowCount()):
                item = self.azim_table.item(row, 0)
                if item and item.text():
                    try:
                        azim_data.append(float(item.text()))
                    except ValueError:
                        QMessageBox.warning(self, "Invalid Data", f"Invalid Azimuth value in row {row + 1}")
                        return
        else:
            azim_data = [45.0] * len(md_data)  # Default to 45° if not using custom azimuth

        # Store the trajectory data
        self.trajectory_data = {
            'mds': md_data,
            'tvd': tvd_data,
            'inclinations': incl_data,
            'azimuths': azim_data
        }

        # Calculate north/east coordinates
        self.calculate_north_east()

        # Update the trajectory visualization
        self.update_trajectory_view()

        QMessageBox.information(self, "Success", "Well trajectory generated successfully")

    def calculate_north_east(self):
        """Calculate north and east coordinates from the trajectory data"""
        if not hasattr(self, 'trajectory_data'):
            return

        mds = self.trajectory_data['mds']
        tvd = self.trajectory_data['tvd']
        incl = self.trajectory_data['inclinations']
        azim = self.trajectory_data['azimuths']

        north = [0.0]
        east = [0.0]

        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i - 1]
            rad_inc = np.radians(incl[i])
            rad_azim = np.radians(azim[i])

            north.append(north[i - 1] + np.sin(rad_inc) * np.cos(rad_azim) * delta_md)
            east.append(east[i - 1] + np.sin(rad_inc) * np.sin(rad_azim) * delta_md)

        # Update trajectory data
        self.trajectory_data['north'] = north
        self.trajectory_data['east'] = east

    def create_main_operation_tab(self):
        """Create the main operation tab with all visualizations"""
        tab = QWidget()
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        # Controls group
        control_group = QGroupBox("RSU Panel")
        control_group.setStyleSheet(GROUPBOX_STYLE)
        control_group_layout = QVBoxLayout()

        # RIH/POOH buttons
        btn_layout = QHBoxLayout()
        self.rih_btn = QPushButton("Run In Hole")
        self.pooh_btn = QPushButton("Pull Out of Hole")
        self.stop_btn = QPushButton("Stop")
        btn_layout.addWidget(self.rih_btn)
        btn_layout.addWidget(self.pooh_btn)
        btn_layout.addWidget(self.stop_btn)

        # Speed control with real-time display
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 200)  # 200 ft/min max
        self.speed_slider.setValue(60)

        self.speed_label = QLabel("60 ft/min")
        self.speed_slider.valueChanged.connect(lambda: self.speed_label.setText(f"{self.speed_slider.value()} ft/min"))

        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)

        # Depth display
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Current Depth:"))
        self.depth_label = QLabel("0 ft")
        depth_layout.addWidget(self.depth_label)

        # Tension display
        tension_layout = QHBoxLayout()
        tension_layout.addWidget(QLabel("Tension:"))
        self.tension_label = QLabel("0 lbs")
        tension_layout.addWidget(self.tension_label)

        control_group_layout.addLayout(btn_layout)
        control_group_layout.addLayout(speed_layout)
        control_group_layout.addLayout(depth_layout)
        control_group_layout.addLayout(tension_layout)
        control_group.setLayout(control_group_layout)

        # Lubricator visualization
        self.lubricator_canvas = FigureCanvasQTAgg(Figure(figsize=(4, 3)))

        control_layout.addWidget(control_group)
        control_layout.addWidget(self.lubricator_canvas)
        control_layout.addStretch()

        # Right side: Visualizations
        vis_panel = QWidget()
        vis_layout = QVBoxLayout(vis_panel)

        # Create a splitter for the two main visualizations
        vis_splitter = QSplitter(Qt.Orientation.Vertical)

        # Tool string visualization
        tool_vis_widget = QWidget()
        tool_vis_layout = QVBoxLayout(tool_vis_widget)
        self.tool_canvas = FigureCanvasQTAgg(Figure(figsize=(4, 8)))
        tool_vis_layout.addWidget(QLabel("Tool String in Wellbore"))
        tool_vis_layout.addWidget(self.tool_canvas)

        # Well trajectory visualization
        trajectory_vis_widget = QWidget()
        trajectory_vis_layout = QVBoxLayout(trajectory_vis_widget)
        self.trajectory_canvas = FigureCanvasQTAgg(Figure(figsize=(8, 4)))
        trajectory_vis_layout.addWidget(QLabel("Well Trajectory Overview"))
        trajectory_vis_layout.addWidget(self.trajectory_canvas)

        vis_splitter.addWidget(control_panel)
        vis_splitter.addWidget(trajectory_vis_widget)
        vis_splitter.setSizes([400, 600])

        vis_layout.addWidget(vis_splitter)

        # Add both sides to main splitter
        # main_splitter.addWidget(control_panel)
        main_splitter.addWidget(vis_panel)
        main_splitter.addWidget(tool_vis_widget)
        main_splitter.setSizes([500, 500])

        # Set the main layout
        tab_layout = QHBoxLayout(tab)
        tab_layout.addWidget(main_splitter)

        self.tabs.addTab(tab, "Operation View")

        # Connect buttons
        self.rih_btn.clicked.connect(self.start_rih)
        self.pooh_btn.clicked.connect(self.start_pooh)
        self.stop_btn.clicked.connect(self.stop_movement)

    def update_trajectory_view(self):
        """Update the well trajectory visualization with current trajectory data"""
        fig = self.trajectory_canvas.figure
        fig.clear()

        if not hasattr(self, 'trajectory_data'):
            return

        ax = fig.add_subplot(111, projection='3d')

        # Get trajectory data
        mds = self.trajectory_data['mds']
        tvd = self.trajectory_data['tvd']
        north = self.trajectory_data['north']
        east = self.trajectory_data['east']
        inclinations = self.trajectory_data['inclinations']
        azimuths = self.trajectory_data['azimuths']

        # Plot trajectory
        ax.plot(north, east, tvd, 'b-', linewidth=2, label='Well Path')

        # Plot current tool position
        if hasattr(self, 'current_depth'):
            # Find closest MD to current depth
            idx = np.argmin(np.abs(np.array(mds) - self.current_depth))
            ax.plot([north[idx]], [east[idx]], [tvd[idx]], 'ro', markersize=10, label='Tool Position')

            # Update current inclination and azimuth
            self.current_inclination = inclinations[idx]
            self.current_azimuth = azimuths[idx]

        # Formatting
        ax.set_zlim(max(tvd), 0)  # Inverted depth
        ax.set_xlabel('North (ft)')
        ax.set_ylabel('East (ft)')
        ax.set_zlabel('TVD (ft)')
        ax.set_title("Well Trajectory Overview")
        ax.legend()

        self.trajectory_canvas.draw()

    def start_rih(self):
        """Start run-in-hole operation"""
        self.sim_timer.start(100)  # Update every 100ms
        self.operation = "RIH"
        self.is_moving = True  # Add this if not already present

    def start_pooh(self):
        """Start pull-out-of-hole operation"""
        self.sim_timer.start(100)
        self.operation = "POOH"
        self.is_moving = True  # Add this if not already present

    def stop_movement(self):
        """Stop all movement"""
        self.sim_timer.stop()
        self.is_moving = False  # Add this if not already present

    def update_visualizations(self):
        """Update all visualizations based on current state"""
        self.update_lubricator_view()
        self.update_tool_view()
        self.update_trajectory_view()

    def update_lubricator_view(self):
        """Update the surface equipment visualization with proper PCE stack and RSU"""
        fig = self.lubricator_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Equipment dimensions
        wellhead_width = 30
        wellhead_height = 20
        christmas_tree_height = 25
        lubricator_height = 240
        lubricator_width = 25
        pce_height = 40
        pce_width = 30
        drum_radius = 20
        rsu_width = 50
        rsu_height = 60
        pp_width = 100
        pp_height = 60
        sheave_radius = 15  # Radius for both sheaves

        # Base positions
        wellhead_x = 100
        wellhead_bottom = 20
        christmas_tree_bottom = wellhead_bottom + wellhead_height
        pce_bottom = christmas_tree_bottom + christmas_tree_height
        lubricator_bottom = pce_bottom + pce_height

        # Draw wellhead
        wellhead = plt.Rectangle((wellhead_x, wellhead_bottom),
                                 wellhead_width, wellhead_height,
                                 linewidth=2, edgecolor='black', facecolor='#555555')
        ax.add_patch(wellhead)

        # Draw christmas tree
        christmas_tree = plt.Rectangle((wellhead_x + (wellhead_width - 20) / 2, christmas_tree_bottom),
                                       20, christmas_tree_height,
                                       linewidth=2, edgecolor='darkgreen', facecolor='#006400')
        ax.add_patch(christmas_tree)

        # Draw PCE stack (pressure control equipment)
        pce = plt.Rectangle((wellhead_x + (wellhead_width - pce_width) / 2, pce_bottom),
                            pce_width, pce_height,
                            linewidth=2, edgecolor='black', facecolor='#777777')
        ax.add_patch(pce)

        # Draw lubricator (3x taller)
        lubricator = plt.Rectangle((wellhead_x + (wellhead_width - lubricator_width) / 2, lubricator_bottom),
                                   lubricator_width, lubricator_height,
                                   linewidth=2, edgecolor='black', facecolor='#999999')
        ax.add_patch(lubricator)


        # Draw RSU (reel service unit) on the side
        rsu_x = wellhead_x - 320
        rsu_y = wellhead_bottom + 40
        rsu = plt.Rectangle((rsu_x, rsu_y), rsu_width, rsu_height,
                            linewidth=2, edgecolor='black', facecolor='#aaaaaa')
        ax.add_patch(rsu)

        # Draw Power Pack on the side
        pp_x = rsu_x - 150
        pp_y = wellhead_bottom + 40
        pp = plt.Rectangle((pp_x, pp_y), pp_width, pp_height,
                            linewidth=2, edgecolor='black', facecolor='#aaaaaa')
        ax.add_patch(pp)

        # Draw drum with rotation
        drum_center_x = rsu_x + rsu_width - drum_radius - 5
        drum_center_y = rsu_y + rsu_height / 2

        # Calculate rotation angle based on wire movement (3x faster rotation)
        rotation_angle = 0
        if hasattr(self, 'current_depth'):
            rotation_angle = (self.current_depth * 3) % 360  # 3x faster rotation
            if hasattr(self, 'operation'):
                # Reverse direction for POOH
                rotation_angle *= -50

        drum = plt.Circle((drum_center_x, drum_center_y), drum_radius,
                          linewidth=2, edgecolor='black', facecolor='#cccccc')
        ax.add_patch(drum)

        # Draw drum spokes (rotating)
        for i in range(4):
            angle = np.radians(rotation_angle + i * 90)
            end_x = drum_center_x + drum_radius * np.cos(angle)
            end_y = drum_center_y + drum_radius * np.sin(angle)
            ax.plot([drum_center_x, end_x], [drum_center_y, end_y],
                    'k-', linewidth=2)

        # Calculate wire path points
        drum_center_x = rsu_x + rsu_width - drum_radius - 5
        drum_center_y = rsu_y + rsu_height / 2

        # Wire starts tangent from top of drum
        wire_start_angle = np.radians(90)
        wire_start_x = drum_center_x + drum_radius * np.cos(wire_start_angle)
        wire_start_y = drum_center_y + drum_radius * np.sin(wire_start_angle)

        # First sheave position (where wire changes from horizontal to vertical)
        turn_sheave_x = wellhead_x - 30
        turn_sheave_y = wire_start_y - 15
        turn_sheave = plt.Circle((turn_sheave_x, turn_sheave_y), sheave_radius,
                                 linewidth=1, edgecolor='black', facecolor='#dddddd')
        ax.add_patch(turn_sheave)

        # Second sheave position (at top of lubricator)
        top_sheave_x = wellhead_x
        top_sheave_y = lubricator_bottom + lubricator_height
        top_sheave = plt.Circle((top_sheave_x, top_sheave_y), sheave_radius,
                                linewidth=1, edgecolor='black', facecolor='#dddddd')
        ax.add_patch(top_sheave)

        ax.plot([pp_x + pp_width, rsu_x],
                [pp_y+8, rsu_y+8],
                color='black', linewidth=3)

        # Updated wire path that goes through both sheaves
        # From drum to turn sheave (horizontal)
        ax.plot([wire_start_x, turn_sheave_x],
                [wire_start_y, turn_sheave_y-sheave_radius],
                color='#8b4513', linewidth=2)

        # From turn sheave to top sheave (vertical)
        ax.plot([turn_sheave_x+sheave_radius, top_sheave_x-sheave_radius],
                [turn_sheave_y, top_sheave_y],
                color='#8b4513', linewidth=2)

        # Draw load cell (between PCE and lubricator)
        load_cell_x = wellhead_x + (wellhead_width - 15) / 2
        load_cell_y = pce_bottom + pce_height - 5
        load_cell = plt.Rectangle((load_cell_x, load_cell_y), 15, 10,
                                  linewidth=1, edgecolor='red', facecolor='#ffcccc')
        ax.add_patch(load_cell)

        # Draw wireline valve (on PCE stack)
        valve_x = wellhead_x + wellhead_width / 2 - 5
        valve_y = pce_bottom + pce_height - 15
        valve = plt.Rectangle((valve_x, valve_y), 10, 10,
                              linewidth=1, edgecolor='blue', facecolor='#ccccff')
        ax.add_patch(valve)

        # Add operation status
        if hasattr(self, 'operation'):
            status_text = f"{self.operation} at {self.speed_slider.value()} ft/min"
            ax.text(rsu_x - 100, rsu_y + rsu_height + 20, status_text,
                    ha='center', color='red', fontweight='bold')

        # Formatting
        ax.set_xlim(rsu_x - 200, wellhead_x + wellhead_width + 20)
        ax.set_ylim(0, lubricator_bottom + lubricator_height + 20)
        ax.axis('off')
        ax.set_aspect('equal')

        self.lubricator_canvas.draw()

    def update_tool_view(self):
        """Update the tool string visualization with refined weight display"""
        fig = self.tool_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Get current input values
        TOOL_WEIGHT = self.tool_weight_input.value()
        WIRE_WEIGHT_PER_FT = self.wire_weight  # From update_wire_properties()
        WIRE_DIAMETER = self.wire_diameter  # From update_wire_properties()
        FLUID_DENSITY = self.fluid_density_input.value()
        FLUID_LEVEL = self.fluid_level_input.value()
        PRESSURE = self.pressure_input.value()
        FRICTION_COEFF = self.friction_input.value()
        
        # Constants
        WELL_WIDTH = 25
        TUBING_WIDTH = WELL_WIDTH - 10
        CENTER_X = WELL_WIDTH / 2
        BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)
        STATIC_FRICTION_FACTOR = 1.2

        # Get current inclination and azimuth from trajectory data
        current_inclination = self.get_current_inclination()
        current_azimuth = self.get_current_azimuth()

        current_depth = getattr(self, 'current_depth', 0)
        max_depth = getattr(self, 'max_depth', 10000)
        is_moving = getattr(self, 'is_moving', False)
        moving_down = getattr(self, 'moving_down', False)

        # Initialize friction-related variables
        normal_force = 0
        friction_magnitude = 0
        effective_friction = 0

        # Weight calculations
        wire_in_hole = min(current_depth, max_depth)
        wire_weight = wire_in_hole * WIRE_WEIGHT_PER_FT
        total_weight = TOOL_WEIGHT + wire_weight

        # Pressure force
        wire_area = math.pi * (WIRE_DIAMETER / 2) ** 2
        pressure_force = PRESSURE * wire_area

        # Buoyancy
        if current_depth > FLUID_LEVEL:
            submerged_length = current_depth - FLUID_LEVEL
            buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
            submerged_weight = total_weight - buoyancy_reduction
        else:
            buoyancy_reduction = 0
            submerged_weight = total_weight

        try:
            # CORRECTED: Effective vertical weight component
            inclination_rad = math.radians(current_inclination)
            effective_weight = submerged_weight * math.cos(inclination_rad)
        except Exception as e:
            print(e)

        # FRICTION CALCULATION
        if current_inclination > 0.0:  # Only in deviated wells
            normal_force = submerged_weight * math.sin(math.radians(current_inclination))
            friction_magnitude = FRICTION_COEFF * normal_force

            if is_moving:
                # MOVING - friction always opposes motion
                if hasattr(self, 'operation'):
                    if self.operation == "RIH":
                        effective_friction = -friction_magnitude  # Friction opposes RIH (negative)
                        self.last_operation_direction = 'RIH'
                    elif self.operation == "POOH":
                        effective_friction = friction_magnitude  # Friction opposes POOH (positive)
                        self.last_operation_direction = 'POOH'
            else:
                # STATIC - friction resists last movement direction
                if hasattr(self, 'last_operation_direction'):
                    if self.last_operation_direction == 'RIH':
                        effective_friction = -friction_magnitude * STATIC_FRICTION_FACTOR
                    else:
                        effective_friction = friction_magnitude * STATIC_FRICTION_FACTOR
                else:
                    effective_friction = 0

        # TENSION CALCULATION
        tension = (effective_weight - pressure_force) + effective_friction
        tension = max(tension, 0)

        try:
            # Update display
            if hasattr(self, 'tension_label'):
                self.tension_label.setText(f"{tension:.1f} lbs") # Changed from direct label access

            # Update movement history
            if is_moving:
                self.last_moved_down = moving_down

            # Draw well components
            casing = plt.Rectangle((0, 0), WELL_WIDTH, max_depth,
                                   linewidth=2, edgecolor='gray', facecolor='#f0f0f0')
            ax.add_patch(casing)

            # Draw fluid column and label
            if FLUID_LEVEL < max_depth:
                fluid = plt.Rectangle((5, FLUID_LEVEL), TUBING_WIDTH,
                                      max_depth - FLUID_LEVEL,
                                      linewidth=0, edgecolor='none', facecolor='#e6f3ff')
                ax.add_patch(fluid)
                ax.plot([5, 5 + TUBING_WIDTH], [FLUID_LEVEL, FLUID_LEVEL],
                        color='#4682B4', linewidth=1, linestyle='--')

                fluid_text = ax.text(WELL_WIDTH + 20, FLUID_LEVEL - 10,
                                     f"Fluid Level: \n{FLUID_LEVEL} ft",
                                     color='#4682B4', zorder=10)

            # Draw tubing
            tubing = plt.Rectangle((5, 0), TUBING_WIDTH, max_depth,
                                   linewidth=1, edgecolor='darkgray', facecolor='none')
            ax.add_patch(tubing)

            if current_depth > 0:
                # Wire line
                ax.plot([CENTER_X, CENTER_X], [0, current_depth],
                        color='#8b4513', linewidth=2)

                # Rope socket
                socket_height = 40
                socket = plt.Rectangle(
                    (CENTER_X - 3, current_depth), 6, socket_height,
                    linewidth=2, edgecolor='darkgray', facecolor='#646464')
                ax.add_patch(socket)

                # Parameter display
                param_x = WELL_WIDTH + 70
                param_y = 50

                movement_status = "Moving ↓" if (is_moving and moving_down) else \
                    "Moving ↑" if (is_moving and not moving_down) else \
                        "Static"

                info_text = ("Current Downhole Parameters:\n"
                             f"• Depth: {current_depth:.1f} ft\n"
                             f"• Tool Mass: {TOOL_WEIGHT} lbs\n"
                             f"• Wire Weight: {wire_weight:.1f} lbs\n"
                             f"• Buoyancy Effect: -{buoyancy_reduction:.1f} lbs\n"
                             f"• Effective Tool Weight: -{effective_weight:.1f} lbs\n"
                             f"• Pressure Force: -{pressure_force:.1f} lbs\n"
                             f"• Friction Force: {effective_friction:+.1f} lbs\n"
                             f"• Net Tension: {tension:.1f} lbs\n"
                             f"• Inclination: {current_inclination:.1f}°\n"
                             f"• Azimuth: {current_azimuth:.1f}°")

                param_box = ax.text(param_x, param_y, info_text,
                                    bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray', boxstyle='round'),
                                    fontsize=9, verticalalignment='top', zorder=5)

            # Depth markers
            for depth_mark in range(0, int(max_depth) + 1, 1000):
                ax.plot([WELL_WIDTH, WELL_WIDTH + 10], [depth_mark, depth_mark],
                        color='black', linewidth=1)
                ax.text(WELL_WIDTH + 15, depth_mark - 10, f"{depth_mark} ft", zorder=5)

            # Configure axes
            ax.set_xlim(-10, WELL_WIDTH + 180)
            ax.set_ylim(max_depth, 0)
            ax.set_ylabel("Depth (ft-MD)", fontweight='bold')
            ax.grid(True, axis='y', linestyle='--', alpha=0.5)
            ax.set_xticks([])
            ax.set_title(f"Tool String Weight Calculation\nFluid: {FLUID_DENSITY} ppg, Pressure: {PRESSURE} psi", pad=20)

            self.tool_canvas.draw()

        except Exception as e:
            print(e)

    def get_current_inclination(self):
        """Return inclination at current depth from trajectory data"""
        if hasattr(self, 'trajectory_data') and hasattr(self, 'current_depth'):
            # Find closest point in trajectory data
            idx = np.argmin(np.abs(np.array(self.trajectory_data['mds']) - self.current_depth))
            return self.trajectory_data['inclinations'][idx]
        return 0.0

    def get_current_azimuth(self):
        """Return azimuth at current depth from trajectory data"""
        if hasattr(self, 'trajectory_data') and hasattr(self, 'current_depth'):
            # Find closest point in trajectory data
            idx = np.argmin(np.abs(np.array(self.trajectory_data['mds']) - self.current_depth))
            return self.trajectory_data['azimuths'][idx]
        return 45.0

    def calculate_dls(self):
        """Calculate dogleg severity at current depth"""
        # Implement DLS calculation
        return 0.0  # Placeholder

    def update_wire_properties(self):
        """Calculate and update wire weight when size changes"""
        wire_od = float(self.wire_size_combo.currentText())
        # Calculate wire weight: OD^2 * 8/3 (lbs/ft)
        wire_weight = (wire_od ** 2) * (8/3)
        self.wire_weight = wire_weight
        self.wire_diameter = wire_od
        self.wire_weight_label.setText(f"{wire_weight:.4f} lbs/ft")
        self.update_calculations()

    def update_fluid_properties(self):
        """Update fluid-related calculations when inputs change"""
        self.fluid_density = self.fluid_density_input.value()
        self.fluid_level = self.fluid_level_input.value()
        self.buoyancy_factor = 1 - (self.fluid_density / 65.4)  # 65.4 ppg = steel density
        self.update_calculations()

    def update_calculations(self):
        """Trigger recalculation when inputs change"""
        if hasattr(self, 'current_depth'):
            self.update_tool_view()

    def update_simulation(self):
        """Update the simulation state with zero-tension safety check"""
        try:
            speed = self.speed_slider.value() * self.sim_speed

            if self.operation == "RIH":
                self.current_depth += speed / 600  # Convert ft/min to ft per 100ms
                # Ensure we don't go beyond max depth
                if hasattr(self, 'trajectory_data'):
                    self.current_depth = min(self.current_depth, self.trajectory_data['mds'][-1])
            elif self.operation == "POOH":
                self.current_depth -= speed / 600
                self.current_depth = max(0, self.current_depth)

            self.depth_label.setText(f"{self.current_depth:.1f} ft")
            self.update_visualizations()

            # Only update plots if they exist
            if hasattr(self, 'tension_depth_canvas') and hasattr(self, 'incl_depth_canvas'):
                self.update_combined_plots()

        except Exception as e:
            print(f"Error in simulation update: {e}")

    def calculate_current_tension(self):
        """Calculate current tension with all factors"""
        # Get current parameters
        TOOL_WEIGHT = self.tool_weight_input.value()
        WIRE_WEIGHT_PER_FT = self.wire_weight
        inclination_rad = math.radians(self.current_inclination)

        # Weight calculations
        wire_in_hole = min(self.current_depth, self.max_depth)
        wire_weight = wire_in_hole * WIRE_WEIGHT_PER_FT
        total_weight = TOOL_WEIGHT + wire_weight

        # Buoyancy
        if self.current_depth > self.fluid_level_input.value():
            submerged_length = self.current_depth - self.fluid_level_input.value()
            buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - self.buoyancy_factor)
            submerged_weight = total_weight - buoyancy_reduction
        else:
            submerged_weight = total_weight

        # Effective vertical weight
        effective_weight = submerged_weight * math.cos(inclination_rad)

        # Pressure force
        wire_area = math.pi * (self.wire_diameter / 2) ** 2
        pressure_force = self.pressure_input.value() * wire_area

        # Friction
        if self.current_inclination > 1.0:
            normal_force = submerged_weight * math.sin(inclination_rad)
            friction_magnitude = self.friction_input.value() * normal_force
            effective_friction = -friction_magnitude if self.operation == "RIH" else friction_magnitude
        else:
            effective_friction = 0

        return max(effective_weight - pressure_force + effective_friction, 0)


    def update_weight_vs_depth_plot(self):
        """Update the weight vs depth plot with current parameters"""
        fig = self.weight_depth_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Get parameters
        TOOL_WEIGHT = self.tool_weight_input.value()
        WIRE_WEIGHT_PER_FT = self.wire_weight
        WIRE_DIAMETER = self.wire_diameter
        FLUID_DENSITY = self.fluid_density_input.value()
        FLUID_LEVEL = self.fluid_level_input.value()
        PRESSURE = self.pressure_input.value()
        FRICTION_COEFF = self.friction_input.value()
        BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)

        # Use max depth from trajectory data if available, otherwise default to 10000
        max_depth = self.trajectory_data['mds'][-1] if hasattr(self, 'trajectory_data') else 10000
        depths = np.arange(0, max_depth + 100, 100)  # 100 ft intervals

        # Calculate weights for RIH and POOH at each depth
        rih_weights = []
        pooh_weights = []

        for depth in depths:
            # Weight calculations
            wire_weight = depth * WIRE_WEIGHT_PER_FT
            total_weight = TOOL_WEIGHT + wire_weight

            # Buoyancy
            if depth > FLUID_LEVEL:
                submerged_length = depth - FLUID_LEVEL
                buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
                submerged_weight = total_weight - buoyancy_reduction
            else:
                submerged_weight = total_weight

            # Get inclination at this depth
            if hasattr(self, 'trajectory_data'):
                idx = np.argmin(np.abs(self.trajectory_data['mds'] - depth))
                inclination = self.trajectory_data['inclinations'][idx]
            else:
                inclination = 0.0

            inclination_rad = math.radians(inclination)

            # Effective vertical weight component
            effective_weight = submerged_weight * math.cos(inclination_rad)

            # Pressure force
            wire_area = math.pi * (WIRE_DIAMETER / 2) ** 2
            pressure_force = PRESSURE * wire_area

            # Friction (only in deviated sections)
            if inclination > 1.0:
                normal_force = submerged_weight * math.sin(inclination_rad)
                friction_magnitude = FRICTION_COEFF * normal_force
                rih_friction = -friction_magnitude  # Friction opposes RIH
                pooh_friction = friction_magnitude  # Friction opposes POOH
            else:
                rih_friction = pooh_friction = 0

            # Calculate final tensions
            rih_tension = max(effective_weight - pressure_force + rih_friction, 0)
            pooh_tension = max(effective_weight - pressure_force + pooh_friction, 0)

            rih_weights.append(rih_tension)
            pooh_weights.append(pooh_tension)

        # Plot the curves with depth on y-axis (inverted)
        ax.plot(rih_weights, depths, 'b-', label='RIH Tension')
        ax.plot(pooh_weights, depths, 'r-', label='POOH Tension')

        # Add current position marker if available
        if hasattr(self, 'current_depth') and self.current_depth <= max_depth:
            current_idx = np.argmin(np.abs(depths - self.current_depth))
            ax.plot(rih_weights[current_idx], depths[current_idx], 'bo', markersize=8, label='Current RIH')
            ax.plot(pooh_weights[current_idx], depths[current_idx], 'ro', markersize=8, label='Current POOH')
            ax.axhline(y=self.current_depth, color='gray', linestyle='--', alpha=0.5)

        # Formatting
        ax.set_xlabel('Tension (lbs)')
        ax.set_ylabel('Depth (ft MD)')
        ax.set_title('Tension vs Depth Profile')
        ax.grid(True)
        ax.legend()

        # Invert y-axis to show depth increasing downward
        ax.set_ylim(max_depth, 0)

        # Adjust x-axis to show from 0 to max tension + 10%
        max_tension = max(max(rih_weights), max(pooh_weights))
        ax.set_xlim(0, max_tension * 1.1 if max_tension > 0 else 1000)

        self.weight_depth_canvas.draw()

    def create_weight_vs_depth_tab(self):
        """Create a tab showing weight vs depth and inclination/DLS vs depth plots side-by-side"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Create horizontal splitter for side-by-side plots
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left plot: Tension vs Depth
        tension_widget = QWidget()
        tension_layout = QVBoxLayout(tension_widget)
        self.tension_depth_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 6)))
        tension_layout.addWidget(self.tension_depth_canvas)
        tension_layout.addWidget(QLabel("Tension vs Depth"))

        # Right plot: Inclination/DLS vs Depth
        incl_widget = QWidget()
        incl_layout = QVBoxLayout(incl_widget)
        self.incl_depth_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 6)))
        incl_layout.addWidget(self.incl_depth_canvas)
        incl_layout.addWidget(QLabel("Inclination & DLS vs Depth"))

        splitter.addWidget(tension_widget)
        splitter.addWidget(incl_widget)
        splitter.setSizes([400, 400])

        # Add calculate button at bottom
        calculate_btn = QPushButton("Update All Plots")
        calculate_btn.clicked.connect(self.update_combined_plots)

        main_layout.addWidget(splitter)
        main_layout.addWidget(calculate_btn)

        # Initialize empty plots
        self.tension_depth_canvas.draw()
        self.incl_depth_canvas.draw()

        self.tabs.addTab(tab, "Weight vs Depth")

    def update_combined_plots(self):
        """Update both tension and inclination/DLS plots"""
        try:
            if hasattr(self, 'trajectory_data'):
                self.update_tension_depth_plot()
                # self.update_inclination_dls_plot()
        except Exception as e:
            print(f"Error updating tension_depth plots: {e}")
        try:
            if hasattr(self, 'trajectory_data'):
                # self.update_tension_depth_plot()
                self.update_inclination_dls_plot()
        except Exception as e:
            print(f"Error updating inclination_dls plots: {e}")

    def update_tension_depth_plot(self):
        fig = self.tension_depth_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if not hasattr(self, 'trajectory_data'):
            return

        # Ensure data is float
        mds = [float(md) for md in self.trajectory_data['mds']]
        inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]
        max_depth = float(mds[-1])
        depth_points = np.linspace(0, max_depth, 100)

        # Get parameters (ensure they're floats)
        TOOL_WEIGHT = float(self.tool_weight_input.value())
        WIRE_WEIGHT_PER_FT = float(self.wire_weight)
        WIRE_DIAMETER = float(self.wire_diameter)
        FLUID_DENSITY = float(self.fluid_density_input.value())
        FLUID_LEVEL = float(self.fluid_level_input.value())
        PRESSURE = float(self.pressure_input.value())
        FRICTION_COEFF = float(self.friction_input.value())
        BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)

        # Interpolate inclinations
        incl_interp = interp1d(mds, inclinations, kind='linear', fill_value='extrapolate')
        incl_at_points = incl_interp(depth_points)

        # Calculate weights
        rih_weights, pooh_weights = [], []
        for depth, inclination in zip(depth_points, incl_at_points):
            wire_weight = depth * WIRE_WEIGHT_PER_FT
            total_weight = TOOL_WEIGHT + wire_weight

            # Buoyancy (ensure depth is a single float)
            submerged_length = max(depth - FLUID_LEVEL, 0)  # Avoid negative
            buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
            submerged_weight = total_weight - buoyancy_reduction

            # Effective weight (inclination in radians)
            inclination_rad = math.radians(inclination)
            effective_weight = submerged_weight * math.cos(inclination_rad)

            # Pressure force
            wire_area = math.pi * (WIRE_DIAMETER / 2) ** 2
            pressure_force = PRESSURE * wire_area

            # Friction (only in deviated sections)
            if inclination > 1.0:
                normal_force = submerged_weight * math.sin(inclination_rad)
                friction_magnitude = FRICTION_COEFF * normal_force
                rih_friction = -friction_magnitude  # Opposes RIH
                pooh_friction = friction_magnitude  # Opposes POOH
            else:
                rih_friction = pooh_friction = 0

            # Final tensions
            rih_tension = max(effective_weight - pressure_force + rih_friction, 0)
            pooh_tension = max(effective_weight - pressure_force + pooh_friction, 0)
            rih_weights.append(rih_tension)
            pooh_weights.append(pooh_tension)

        # Plotting (depth on y-axis, inverted)
        ax.plot(rih_weights, depth_points, 'b-', label='RIH Tension')
        ax.plot(pooh_weights, depth_points, 'r-', label='POOH Tension')

        # Current position marker
        if hasattr(self, 'current_depth'):
            current_depth = float(self.current_depth)
            if current_depth <= max_depth:
                current_idx = np.argmin(np.abs(depth_points - current_depth))
                ax.plot(rih_weights[current_idx], depth_points[current_idx], 'bo', label='Current RIH')
                ax.plot(pooh_weights[current_idx], depth_points[current_idx], 'ro', label='Current POOH')
                ax.axhline(y=current_depth, color='gray', linestyle='--', alpha=0.5)

        # Formatting
        ax.set_xlabel('Tension (lbs)')
        ax.set_ylabel('Depth (ft MD)')
        ax.set_title('Tension vs Depth Profile')
        ax.grid(True)
        ax.legend()
        ax.set_ylim(max_depth, 0)  # Inverted y-axis
        self.tension_depth_canvas.draw()

    def update_inclination_dls_plot(self):
        """Update the inclination and DLS vs depth plot with depth on the y-axis"""
        fig = self.incl_depth_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if not hasattr(self, 'trajectory_data'):
            return

        # Ensure all data is converted to float (critical fix)
        mds = np.array([float(md) for md in self.trajectory_data['mds']])  # Convert to numpy array
        inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]
        max_depth = float(mds[-1])

        # Calculate DLS (Dog Leg Severity) in °/100ft
        dls_values = []
        for i in range(len(mds)):
            if i == 0:
                dls = 0.0  # Surface point has no DLS
            else:
                delta_md = float(mds[i]) - float(mds[i - 1])  # Ensure float subtraction
                delta_inc = float(inclinations[i]) - float(inclinations[i - 1])
                dls = abs(delta_inc) / delta_md * 100 if delta_md != 0 else 0.0
            dls_values.append(dls)

        # Create twin axis for DLS
        ax2 = ax.twiny()

        # Plot inclination (primary x-axis)
        ax.plot(inclinations, mds, 'g-', label='Inclination')
        ax.set_ylabel('Depth (ft MD)')
        ax.set_xlabel('Inclination (°)', color='g')
        ax.tick_params(axis='x', labelcolor='g')

        # Plot DLS (secondary x-axis)
        ax2.plot(dls_values, mds, 'm--', label='DLS')
        ax2.set_xlabel('DLS (°/100ft)', color='m')
        ax2.tick_params(axis='x', labelcolor='m')

        # Add current position marker if available
        if hasattr(self, 'current_depth') and self.current_depth <= max_depth:
            current_depth = float(self.current_depth)  # Ensure float
            idx = np.argmin(np.abs(mds - current_depth))  # Now works with numpy array
            ax.axhline(y=mds[idx], color='gray', linestyle='--', alpha=0.5)
            ax.plot(inclinations[idx], mds[idx], 'go', markersize=8, label='Current Inclination')
            ax2.plot(dls_values[idx], mds[idx], 'mo', markersize=8, label='Current DLS')

        # Formatting
        ax.set_title('Inclination & DLS vs Depth')
        ax.grid(True)
        ax.set_ylim(max_depth, 0)  # Invert y-axis for depth increasing down

        # Combine legends
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc='upper right')

        self.incl_depth_canvas.draw()

    def toggle_units(self):
        """Toggle between feet and meters for all inputs"""
        self.use_metric = not self.use_metric

        # Update all length-related inputs
        inputs_to_convert = [
            (self.fluid_level_input, 0.3048),  # ft to m conversion factor
            (self.md_table, 0.3048),
            (self.tvd_table, 0.3048),
            # Add other length inputs as needed
        ]

        for widget, factor in inputs_to_convert:
            self.convert_widget_units(widget, factor)

        # Update unit labels
        self.update_unit_labels()

    def convert_widget_units(self, widget, factor):
        """Convert values in a widget between feet and meters"""
        if isinstance(widget, QDoubleSpinBox):
            current_value = widget.value()
            if self.use_metric:
                widget.setValue(current_value * factor)  # Convert to meters
            else:
                widget.setValue(current_value / factor)  # Convert to feet
        elif isinstance(widget, QTableWidget):
            for row in range(widget.rowCount()):
                for col in range(widget.columnCount()):
                    item = widget.item(row, col)
                    if item and item.text():
                        try:
                            value = float(item.text())
                            if self.use_metric:
                                new_value = value * factor
                            else:
                                new_value = value / factor
                            item.setText(f"{new_value:.2f}")
                        except ValueError:
                            pass

    def update_unit_labels(self):
        """Update all unit labels in the interface"""
        unit = "m" if self.use_metric else "ft"

        # Update spinbox suffixes
        self.fluid_level_input.setSuffix(f" {unit}")

        # Update table headers
        self.md_table.setHorizontalHeaderLabels([f"MD ({unit})"])
        self.tvd_table.setHorizontalHeaderLabels([f"TVD ({unit})"])

        # Update other labels as needed

    def get_value_in_feet(self, value):
        """Convert input value to feet if it's in meters"""
        if self.use_metric:
            return value / 0.3048  # Convert meters to feet
        return value

    def get_table_values_in_feet(self, table):
        """Get all values from a table converted to feet"""
        values = []
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.text():
                try:
                    value = float(item.text())
                    values.append(self.get_value_in_feet(value))
                except ValueError:
                    values.append(0.0)
        return values