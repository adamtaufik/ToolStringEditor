from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QPushButton,
                             QDoubleSpinBox, QSlider, QMessageBox)
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QPushButton,
                             QDoubleSpinBox, QSlider, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
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

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )

    def create_input_tab(self):
        """Create the input configuration tab (standalone)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Survey input group
        survey_group = QGroupBox("MD to TVD Survey")
        survey_layout = QVBoxLayout()
        survey_group.setLayout(survey_layout)

        # Tool string group
        tool_group = QGroupBox("Tool String Configuration")
        tool_layout = QVBoxLayout()
        tool_group.setLayout(tool_layout)

        # Fluid properties group
        fluid_group = QGroupBox("Fluid Properties")
        fluid_layout = QVBoxLayout()
        fluid_group.setLayout(fluid_layout)

        layout.addWidget(survey_group)
        layout.addWidget(tool_group)
        layout.addWidget(fluid_group)
        self.tabs.addTab(tab, "Input Panel")

    def create_main_operation_tab(self):
        """Create the main operation tab with all visualizations"""
        tab = QWidget()
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)

        # Controls group
        control_group = QGroupBox("Rig Controls")
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

    def start_rih(self):
        """Start run-in-hole operation"""
        self.sim_timer.start(100)  # Update every 100ms
        self.operation = "RIH"

    def start_pooh(self):
        """Start pull-out-of-hole operation"""
        self.sim_timer.start(100)
        self.operation = "POOH"

    def stop_movement(self):
        """Stop all movement"""
        self.sim_timer.stop()

    def update_simulation(self):
        """Update the simulation state"""
        speed = self.speed_slider.value() * self.sim_speed

        if self.operation == "RIH":
            self.current_depth += speed / 600  # Convert ft/min to ft per 100ms
        else:  # POOH
            self.current_depth -= speed / 600

        self.depth_label.setText(f"{self.current_depth:.1f} ft")
        self.update_visualizations()

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
        sheave_radius = 8  # Radius for both sheaves

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
        rsu_x = wellhead_x - 120
        rsu_y = wellhead_bottom + 40
        rsu = plt.Rectangle((rsu_x, rsu_y), rsu_width, rsu_height,
                            linewidth=2, edgecolor='black', facecolor='#aaaaaa')
        ax.add_patch(rsu)

        # Draw Power Pack on the side
        pp_x = rsu_x - 100
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
        turn_sheave_y = wire_start_y
        turn_sheave = plt.Circle((turn_sheave_x, turn_sheave_y), sheave_radius,
                                 linewidth=1, edgecolor='black', facecolor='#dddddd')
        ax.add_patch(turn_sheave)

        # Second sheave position (at top of lubricator)
        top_sheave_x = wellhead_x + wellhead_width / 2
        top_sheave_y = lubricator_bottom + lubricator_height - sheave_radius
        top_sheave = plt.Circle((top_sheave_x, top_sheave_y), sheave_radius,
                                linewidth=1, edgecolor='black', facecolor='#dddddd')
        ax.add_patch(top_sheave)

        # Updated wire path that goes through both sheaves
        # From drum to turn sheave (horizontal)
        ax.plot([wire_start_x, turn_sheave_x],
                [wire_start_y, turn_sheave_y],
                color='#8b4513', linewidth=2)

        # From turn sheave to top sheave (vertical)
        ax.plot([turn_sheave_x, top_sheave_x],
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
        ax.set_xlim(rsu_x - 20, wellhead_x + wellhead_width + 20)
        ax.set_ylim(0, lubricator_bottom + lubricator_height + 20)
        ax.axis('off')
        ax.set_aspect('equal')

        self.lubricator_canvas.draw()

    def update_tool_view(self):
        """Update the tool string visualization with refined weight display"""
        fig = self.tool_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Constants
        WELL_WIDTH = 25
        TUBING_WIDTH = WELL_WIDTH - 10
        CENTER_X = WELL_WIDTH / 2
        DEFAULT_FLUID_LEVEL = 300  # ft
        TOOL_WEIGHT = 150  # lbs
        WIRE_WEIGHT_PER_FT = 0.021  # lbs/ft for 0.108" slickline
        FLUID_DENSITY = 8.5  # ppg
        BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)  # Steel density = 65.4 ppg

        # Get current survey data
        current_inclination = self.get_current_inclination() if hasattr(self, 'get_current_inclination') else 0.0
        current_azimuth = self.get_current_azimuth() if hasattr(self, 'get_current_azimuth') else 0.0

        # Calculate weights
        wire_in_hole = min(self.current_depth, self.max_depth)
        wire_weight = wire_in_hole * WIRE_WEIGHT_PER_FT
        total_weight = TOOL_WEIGHT + wire_weight

        # Buoyancy calculations
        if self.current_depth > DEFAULT_FLUID_LEVEL:
            submerged_length = self.current_depth - DEFAULT_FLUID_LEVEL
            buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
            tension = total_weight - buoyancy_reduction
        else:
            buoyancy_reduction = 0
            tension = total_weight

        # Update tension in rig controls
        if hasattr(self, 'tension_label'):
            self.tension_label.setText(f"{tension:.1f} lbs")

        # Draw well components
        casing = plt.Rectangle((0, 0), WELL_WIDTH, self.max_depth,
                               linewidth=2, edgecolor='gray', facecolor='#f0f0f0')
        ax.add_patch(casing)

        # Draw fluid column and label (Moved before other elements to ensure visibility)
        if DEFAULT_FLUID_LEVEL < self.max_depth:
            fluid = plt.Rectangle((5, DEFAULT_FLUID_LEVEL), TUBING_WIDTH,
                                  self.max_depth - DEFAULT_FLUID_LEVEL,
                                  linewidth=0, edgecolor='none', facecolor='#e6f3ff')
            ax.add_patch(fluid)
            ax.plot([5, 5 + TUBING_WIDTH], [DEFAULT_FLUID_LEVEL, DEFAULT_FLUID_LEVEL],
                    color='#4682B4', linewidth=1, linestyle='--')

            # Fluid level label with higher z-order
            fluid_text = ax.text(WELL_WIDTH + 20, DEFAULT_FLUID_LEVEL - 10,
                                 f"Fluid Level: \n{DEFAULT_FLUID_LEVEL} ft",
                                 color='#4682B4', zorder=10)  # High z-order ensures visibility

        # Draw tubing
        tubing = plt.Rectangle((5, 0), TUBING_WIDTH, self.max_depth,
                               linewidth=1, edgecolor='darkgray', facecolor='none')
        ax.add_patch(tubing)

        if self.current_depth > 0:
            # Wire line
            ax.plot([CENTER_X, CENTER_X], [0, self.current_depth],
                    color='#8b4513', linewidth=2)

            # Rope socket
            socket_height = 40
            socket = plt.Rectangle(
                (CENTER_X - 3, self.current_depth), 6, socket_height,
                linewidth=2, edgecolor='darkgray', facecolor='#646464')
            ax.add_patch(socket)

            # Fixed parameter display box
            param_x = WELL_WIDTH + 70
            param_y = 50  # Fixed position near top

            info_text = ("Current Downhole Parameters:\n"
                         f"• Depth: {self.current_depth:.1f} ft\n"
                         f"• Tool Weight: {TOOL_WEIGHT} lbs\n"
                         f"• Wire Weight: {wire_weight:.1f} lbs\n"
                         f"• Buoyancy Effect: -{buoyancy_reduction:.1f} lbs\n"
                         f"• Net Tension: {tension:.1f} lbs\n"
                         f"• Inclination: {current_inclination:.1f}°\n"
                         f"• Azimuth: {current_azimuth:.1f}°")

            param_box = ax.text(param_x, param_y, info_text,
                                bbox=dict(facecolor='white', alpha=0.9, edgecolor='gray', boxstyle='round'),
                                fontsize=9, verticalalignment='top', zorder=5)

        # Depth markers and axis setup
        for depth_mark in range(0, int(self.max_depth) + 1, 1000):
            ax.plot([WELL_WIDTH, WELL_WIDTH + 10], [depth_mark, depth_mark],
                    color='black', linewidth=1)
            ax.text(WELL_WIDTH + 15, depth_mark - 10, f"{depth_mark} ft", zorder=5)

        # Configure axes
        ax.set_xlim(-10, WELL_WIDTH + 180)
        ax.set_ylim(self.max_depth, 0)
        ax.set_ylabel("Depth (ft-MD)", fontweight='bold')
        ax.grid(True, axis='y', linestyle='--', alpha=0.5)
        ax.set_xticks([])
        ax.set_title(f"Tool String Weight Calculation\nFluid Density: {FLUID_DENSITY} ppg", pad=20)

        self.tool_canvas.draw()

    def update_trajectory_view(self):
        """Update the well trajectory visualization with simple build-and-hold profile"""
        fig = self.trajectory_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111, projection='3d')

        # Well trajectory parameters
        kickoff_depth = 500  # TVD where build starts (ft)
        max_inclination = 40  # degrees
        max_md = 800  # total measured depth (ft)
        build_rate = max_inclination / (max_md - kickoff_depth)  # degrees/ft

        # Calculate trajectory points
        num_points = 100
        mds = np.linspace(0, max_md, num_points)
        tvd = np.zeros(num_points)
        north = np.zeros(num_points)
        east = np.zeros(num_points)

        for i in range(1, num_points):
            if mds[i] <= kickoff_depth:
                # Vertical section
                tvd[i] = mds[i]
            else:
                # Build section
                build_length = mds[i] - kickoff_depth
                inclination = min(max_inclination, build_length * build_rate)
                rad_inc = np.radians(inclination)

                # Calculate displacement
                delta_md = mds[i] - mds[i - 1]
                tvd[i] = tvd[i - 1] + np.cos(rad_inc) * delta_md
                north[i] = north[i - 1] + np.sin(rad_inc) * delta_md

        # Plot trajectory
        ax.plot(north, east, tvd, 'b-', linewidth=2, label='Well Path')

        # Plot current tool position
        if hasattr(self, 'current_depth'):
            idx = np.argmin(np.abs(tvd - self.current_depth))
            ax.plot([north[idx]], [east[idx]], [tvd[idx]], 'ro', markersize=10, label='Tool Position')

        # Formatting
        ax.set_zlim(max(tvd), 0)  # Inverted depth
        ax.set_xlabel('North (ft)')
        ax.set_ylabel('East (ft)')
        ax.set_zlabel('TVD (ft)')
        ax.set_title(f"Build-and-Hold Well Trajectory\nKOP: {kickoff_depth} ft, Max Angle: {max_inclination}°")
        ax.legend()

        # Add annotations
        ax.text(north[-1], east[-1], tvd[-1],
                f'MD: {max_md} ft\nTVD: {tvd[-1]:.1f} ft',
                color='blue')

        if kickoff_depth > 0:
            kop_idx = np.argmin(np.abs(tvd - kickoff_depth))
            ax.text(north[kop_idx], east[kop_idx], tvd[kop_idx],
                    'Kickoff Point', color='green')

        self.trajectory_canvas.draw()

    def get_current_inclination(self):
        """Return inclination at current depth from survey data"""
        # Implement based on your survey data
        return 0.0  # Placeholder

    def get_current_azimuth(self):
        """Return azimuth at current depth from survey data"""
        # Implement based on your survey data
        return 0.0  # Placeholder

    def calculate_dls(self):
        """Calculate dogleg severity at current depth"""
        # Implement DLS calculation
        return 0.0  # Placeholder


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = WirelineSimulatorApp()
    window.show()
    sys.exit(app.exec())