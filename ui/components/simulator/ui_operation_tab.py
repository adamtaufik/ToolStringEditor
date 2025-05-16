from PyQt6.QtWidgets import (QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import math

from utils.styles import GROUPBOX_STYLE


class OperationTab(QWidget):
    operationChanged = pyqtSignal(str)  # "RIH", "POOH", or "STOP"
    speedChanged = pyqtSignal(int)  # Current speed in ft/min

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_depth = 0
        self.max_depth = 100
        self.trajectory_data = None
        self.current_theme = "Deleum"
        self.operation = None
        self.use_metric = False
        self.init_ui()
        self.connect_signals()
        self.trajectory_ax = None  # Added to store 3D axis reference
        # Connect to the trajectory_updated signal

        input_tab = parent.input_tab
        input_tab.trajectory_updated.connect(self.update_trajectory_view)
        input_tab.units_toggled.connect(self.handle_units_toggle)

    def init_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)  # Split left and right

        # LEFT SIDE: vertical splitter with control panel and trajectory
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        control_panel = self.create_control_panel()
        trajectory_panel = self.create_trajectory_panel()
        left_splitter.addWidget(control_panel)
        left_splitter.addWidget(trajectory_panel)
        left_splitter.setSizes([200, 300])

        # RIGHT SIDE: only tool string visualization
        right_panel = self.create_tool_visualization_panel()

        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([600, 400])

        layout = QHBoxLayout(self)
        layout.addWidget(main_splitter)

    def handle_units_toggle(self, use_metric):
        self.use_metric = use_metric
        # Convert current depth display
        if hasattr(self, 'current_depth'):
            self.depth_counter()
        # self.update_visualizations(
        #         current_depth=self.current_depth,
        #         trajectory_data=self.trajectory_data,
        #         params=visualization_params,
        #         operation=self.operation
        #     )

    def depth_counter(self):
        # if self.use_metric:
        #     self.depth_label.setText(f"{self.current_depth * 0.3048:.1f} m")
        # else:
        #     self.depth_label.setText(f"{self.current_depth:.1f} ft")

        if self.use_metric:
            self.depth_label.setText(f"{self.current_depth:.1f} m")
        else:
            self.depth_label.setText(f"{self.current_depth/0.3048:.1f} ft")

    def create_trajectory_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Well Trajectory Overview"))
        self.trajectory_canvas = FigureCanvasQTAgg(Figure(figsize=(18, 9)))

        # Connect mouse and scroll events
        self.trajectory_canvas.mpl_connect('button_press_event', self.on_trajectory_press)
        self.trajectory_canvas.mpl_connect('button_release_event', self.on_trajectory_release)
        self.trajectory_canvas.mpl_connect('motion_notify_event', self.on_trajectory_motion)
        self.trajectory_canvas.mpl_connect('scroll_event', self.on_trajectory_scroll)

        layout.addWidget(self.trajectory_canvas)
        return panel

    def update_trajectory_view(self, trajectory_data):

        try:

            self.trajectory_data = trajectory_data
            if not self.trajectory_data:
                return

            fig = self.trajectory_canvas.figure
            fig.clear()
            self.trajectory_ax = fig.add_subplot(111, projection='3d')  # Store axis reference

            ax = self.trajectory_ax
            mds = self.trajectory_data['mds']
            tvd = self.trajectory_data['tvd']
            north = self.trajectory_data['north']
            east = self.trajectory_data['east']

            ax.plot(north, east, tvd, 'b-', linewidth=2, label='Well Path')

            if hasattr(self, 'current_depth'):
                idx = np.argmin(np.abs(np.array(mds) - self.current_depth))
                # print('idx:', idx, 'Current depth:', round(self.current_depth,2), [north[idx]], [east[idx]], [tvd[idx]])
                ax.plot([north[idx]], [east[idx]], [tvd[idx]], 'ro', markersize=10, label='Tool Position')

            ax.set_zlim(max(tvd), 0)
            ax.set_xlabel('North (ft)')
            ax.set_ylabel('East (ft)')
            ax.set_zlabel('TVD (ft)')
            ax.set_title("Well Trajectory Overview")
            ax.legend()

            # Update labels based on units after drawing
            if self.use_metric:
                ax.set_xlabel('North (m)')
                ax.set_ylabel('East (m)')
                ax.set_zlabel('TVD (m)')
            else:
                ax.set_xlabel('North (ft)')
                ax.set_ylabel('East (ft)')
                ax.set_zlabel('TVD (ft)')

            self.trajectory_canvas.draw()

        except Exception as e:
            print('Update trajectory view Error:', e)

    # --- Event Handlers for 3D Interaction ---
    def on_trajectory_press(self, event):
        if self.trajectory_ax is None or event.inaxes != self.trajectory_ax:
            return
        self.drag_start = {
            'x': event.x,
            'y': event.y,
            'button': event.button,
            'azim': self.trajectory_ax.azim,
            'elev': self.trajectory_ax.elev,
            'xlim': self.trajectory_ax.get_xlim(),
            'ylim': self.trajectory_ax.get_ylim()
        }

    def on_trajectory_release(self, event):
        if hasattr(self, 'drag_start'):
            del self.drag_start

    def on_trajectory_motion(self, event):
        if not hasattr(self, 'drag_start') or self.trajectory_ax is None or event.inaxes != self.trajectory_ax:
            return
        start = self.drag_start
        dx = event.x - start['x']
        dy = event.y - start['y']

        # Rotation (Left Click & Drag)
        if start['button'] == 1:
            scale = 0.5
            self.trajectory_ax.azim = start['azim'] + dx * scale
            self.trajectory_ax.elev = start['elev'] - dy * scale  # Inverted Y

        # Panning (Right Click & Drag)
        elif start['button'] == 3:
            # Calculate scale based on current view span instead of dist
            xlim = self.trajectory_ax.get_xlim()
            ylim = self.trajectory_ax.get_ylim()
            x_span = xlim[1] - xlim[0]
            scale = x_span * 0.001  # Adjust sensitivity here

            delta_x = dx * scale
            delta_y = -dy * scale  # Inverted Y
            self.trajectory_ax.set_xlim([lim - delta_x for lim in start['xlim']])
            self.trajectory_ax.set_ylim([lim - delta_y for lim in start['ylim']])

        self.trajectory_canvas.draw_idle()

    def on_trajectory_scroll(self, event):
        if self.trajectory_ax is None or event.inaxes != self.trajectory_ax:
            return

        # Determine zoom direction
        scale_factor = 0.9 if event.button == 'up' else 1.1

        # Get current view limits
        xlim = self.trajectory_ax.get_xlim()
        ylim = self.trajectory_ax.get_ylim()
        zlim = self.trajectory_ax.get_zlim()

        # Calculate new limits centered around current view
        def adjust_limits(lim):
            center = np.mean(lim)
            span = (lim[1] - lim[0]) * scale_factor
            return (center - span / 2, center + span / 2)

        # Apply new limits
        self.trajectory_ax.set_xlim(adjust_limits(xlim))
        self.trajectory_ax.set_ylim(adjust_limits(ylim))
        self.trajectory_ax.set_zlim(adjust_limits(zlim))

        self.trajectory_canvas.draw_idle()

    def create_control_panel(self):
        panel = QWidget()
        layout = QHBoxLayout(panel)

        # Control Group
        control_group = QGroupBox("RSU Panel")
        control_group.setStyleSheet(GROUPBOX_STYLE)
        control_layout = QVBoxLayout()

        # Operation Buttons
        btn_layout = QHBoxLayout()
        self.rih_btn = QPushButton("Run In Hole")
        self.pooh_btn = QPushButton("Pull Out of Hole")
        self.stop_btn = QPushButton("Stop")
        btn_layout.addWidget(self.rih_btn)
        btn_layout.addWidget(self.pooh_btn)
        btn_layout.addWidget(self.stop_btn)

        # Speed Control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 300)
        self.speed_slider.setValue(60)
        self.speed_label = QLabel("60 ft/min")
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)

        # Displays
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Current Depth:"))
        self.depth_label = QLabel("0 ft")
        depth_layout.addWidget(self.depth_label)

        tension_layout = QHBoxLayout()
        tension_layout.addWidget(QLabel("Tension:"))
        self.tension_label = QLabel("0 lbs")
        tension_layout.addWidget(self.tension_label)

        # Assemble control group
        control_layout.addLayout(btn_layout)
        control_layout.addLayout(speed_layout)
        control_layout.addLayout(depth_layout)
        control_layout.addLayout(tension_layout)
        control_group.setLayout(control_layout)

        # Lubricator Visualization
        self.lubricator_canvas = FigureCanvasQTAgg(Figure(figsize=(4, 3)))

        layout.addWidget(control_group)
        layout.addWidget(self.lubricator_canvas)
        layout.addStretch()

        return panel

    def create_tool_visualization_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("Tool String in Wellbore"))
        self.tool_canvas = FigureCanvasQTAgg(Figure(figsize=(4, 8)))
        layout.addWidget(self.tool_canvas)
        return panel

    def connect_signals(self):
        self.rih_btn.clicked.connect(lambda: self.operationChanged.emit("RIH"))
        self.pooh_btn.clicked.connect(lambda: self.operationChanged.emit("POOH"))
        self.stop_btn.clicked.connect(lambda: self.operationChanged.emit("STOP"))
        self.speed_slider.valueChanged.connect(self.handle_speed_change)

    def handle_speed_change(self, value):
        self.speed_label.setText(f"{value} ft/min")
        self.speedChanged.emit(value)

    def update_visualizations(self, current_depth, trajectory_data, params, operation):

        try:

            self.current_depth = current_depth
            self.trajectory_data = trajectory_data
            self.params = params
            self.operation = operation

            self.update_lubricator_view()
            self.update_tool_view()
            self.update_trajectory_view(self.trajectory_data)
            self.depth_counter()
            self.handle_units_toggle(self.use_metric)

        except Exception as e:
            print('Update vis error:', e)

    def update_lubricator_view(self):

        fig = self.lubricator_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Lubricator drawing code (same as original)
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
        sheave_radius = 15

        wellhead_x = 100
        wellhead_bottom = 20
        christmas_tree_bottom = wellhead_bottom + wellhead_height
        pce_bottom = christmas_tree_bottom + christmas_tree_height
        lubricator_bottom = pce_bottom + pce_height

        # Draw all components (same as original)
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
            rotation_angle = (self.current_depth * 50) % 360  # 3x faster rotation
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
                [pp_y + 8, rsu_y + 8],
                color='black', linewidth=3)

        # Updated wire path that goes through both sheaves
        # From drum to turn sheave (horizontal)
        ax.plot([wire_start_x, turn_sheave_x],
                [wire_start_y, turn_sheave_y - sheave_radius],
                color='#8b4513', linewidth=2)

        # From turn sheave to top sheave (vertical)
        ax.plot([turn_sheave_x + sheave_radius, top_sheave_x - sheave_radius],
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

        ax.set_xlim(rsu_x - 200, wellhead_x + wellhead_width + 20)
        ax.set_ylim(0, lubricator_bottom + lubricator_height + 20)
        ax.axis('off')
        ax.set_aspect('equal')
        self.lubricator_canvas.draw()

    def update_tool_view(self):
        """Update the tool string visualization with real-time parameters"""
        try:
            fig = self.tool_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)

            if not self.params or not self.trajectory_data:
                self.tool_canvas.draw()
                return

            # Unpack parameters
            STUFFING_BOX = -self.params['stuffing_box']
            FLUID_DENSITY = self.params['fluid_density']
            FLUID_LEVEL = self.params['fluid_level']
            PRESSURE = self.params['pressure']
            FRICTION_COEFF = self.params['friction_coeff']
            BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)

            TOOL_WEIGHT = self.params['tool_weight']
            TOOL_AVG_DIAMETER = self.params['tool_avg_diameter']
            TOOL_LENGTH = self.params['tool_length']

            WIRE_DIAMETER = self.params['wire_diameter']

            if self.use_metric:
                depth_unit = "m"
                WIRE_WEIGHT_PER_FT = self.params['wire_weight'] * 3.28084  # lbs/m
                wire_weight_unit = "lbs/m"
                # WIRE_DIAMETER = self.params['wire_diameter'] * 25.4  # mm
            else:
                depth_unit = "ft"
                WIRE_WEIGHT_PER_FT = self.params['wire_weight']  # lbs/ft
                wire_weight_unit = "lbs/ft"
                # WIRE_DIAMETER = self.params['wire_diameter']  # inches

            # Geometry constants
            WELL_WIDTH = 25
            TUBING_WIDTH = WELL_WIDTH - 10
            CENTER_X = WELL_WIDTH / 2
            STATIC_FRICTION_FACTOR = 1.2
            max_depth = self.trajectory_data['mds'][-1]

            # Calculate wire friction for each segment (like in update_tension_plot)
            mds = [float(md) for md in self.trajectory_data['mds']]
            inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]
            wire_friction = []

            for i in range(len(mds) - 2, -1, -1):
                delta_L = mds[i+1] - mds[i]
                theta_avg = math.radians((inclinations[i+1] + inclinations[i]) / 2)
                avg_depth = (mds[i+1] + mds[i]) / 2

                # Calculate segment buoyancy
                if avg_depth >= FLUID_LEVEL:
                    wire_submerged = WIRE_WEIGHT_PER_FT * delta_L * BUOYANCY_FACTOR
                else:
                    wire_submerged = WIRE_WEIGHT_PER_FT * delta_L

                normal_force = wire_submerged * math.sin(theta_avg)
                friction = FRICTION_COEFF * normal_force
                wire_friction.append(friction)

            wire_friction = wire_friction[::-1]  # Reverse to top-to-bottom order

            # Current well geometry
            if self.current_depth > 0:
                idx = np.argmin(np.abs(np.array(self.trajectory_data['mds']) - self.current_depth))
                current_inclination = self.trajectory_data['inclinations'][idx]
                current_azimuth = self.trajectory_data['azimuths'][idx]

                # Calculate cumulative wire friction up to current depth
                cumulative_wire_friction = -sum(wire_friction[:idx]) if wire_friction else 0

                # Weight calculations
                wire_in_hole = min(self.current_depth, max_depth)
                wire_weight = wire_in_hole * WIRE_WEIGHT_PER_FT
                total_weight = TOOL_WEIGHT + wire_weight

                # Buoyancy calculations
                if self.current_depth >= FLUID_LEVEL:
                    tool_area = math.pi * (TOOL_AVG_DIAMETER/12/2) ** 2
                    tool_displacement = (tool_area * TOOL_LENGTH)
                    tool_displacement_gal = tool_displacement * 7.48052
                    buoyancy_weight = tool_displacement_gal * FLUID_DENSITY

                    submerged_length = max(self.current_depth - FLUID_LEVEL, 0)
                    buoyancy_reduction = -buoyancy_weight -submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
                    submerged_weight = total_weight + buoyancy_reduction
                else:
                    buoyancy_reduction = 0
                    submerged_weight = total_weight

                # Effective weight components
                inclination_rad = math.radians(current_inclination)
                effective_weight = submerged_weight * math.cos(inclination_rad)

                # Pressure force
                wire_area = math.pi * (WIRE_DIAMETER / 2) ** 2
                pressure_force = -PRESSURE * wire_area

                effective_friction = 0  # Initialize default value

                # FRICTION CALCULATION
                # if current_inclination > 0.0:  # Only in deviated wells
                normal_force = submerged_weight * math.sin(math.radians(current_inclination))
                friction_magnitude = FRICTION_COEFF * normal_force

                if self.operation == "POOH":
                    effective_friction = friction_magnitude - STUFFING_BOX  # Friction opposes POOH (positive)
                    self.last_operation_direction = 'POOH'
                else:
                    effective_friction = -friction_magnitude + STUFFING_BOX  # Friction opposes RIH (negative)
                    self.last_operation_direction = 'RIH'

                # Final tension calculation
                # Apply cumulative wire friction
                tension_without_wire = effective_weight + pressure_force + effective_friction
                if self.operation == "POOH":
                    tension = max(tension_without_wire - cumulative_wire_friction, 0)
                else:
                    tension = max(tension_without_wire + cumulative_wire_friction, 0)

                self.tension_label.setText(f"{tension:.1f} lbs")

                # Draw well components
                casing = plt.Rectangle((0, 0), WELL_WIDTH, max_depth,
                                       linewidth=2, edgecolor='gray', facecolor='#f0f0f0')
                ax.add_patch(casing)

                # Fluid column
                if FLUID_LEVEL < max_depth:
                    fluid = plt.Rectangle((5, FLUID_LEVEL), TUBING_WIDTH,
                                          max_depth - FLUID_LEVEL,
                                          linewidth=0, edgecolor='none', facecolor='#e6f3ff')
                    ax.add_patch(fluid)
                ax.plot([5, 5 + TUBING_WIDTH], [FLUID_LEVEL, FLUID_LEVEL],
                        color='#4682B4', linewidth=1, linestyle='--')

                # Draw tubing
                tubing = plt.Rectangle((5, 0), TUBING_WIDTH, max_depth,
                                       linewidth=1, edgecolor='darkgray', facecolor='none')
                ax.add_patch(tubing)

                if self.current_depth > 0:
                # Wireline visualization
                    ax.plot([CENTER_X, CENTER_X], [0, self.current_depth],
                            color='#8b4513', linewidth=2)

                # Tool visualization
                socket_height = 40
                socket = plt.Rectangle(
                    (CENTER_X - 3, self.current_depth), 6, socket_height,
                    linewidth=2, edgecolor='darkgray', facecolor='#646464')
                ax.add_patch(socket)

                # Parameter display
                param_text = (
                    f"Current Downhole Parameters:\n"
                    f"• Depth: {self.current_depth:.1f} {depth_unit}\n"
                    f"• Tool Weight: {round(TOOL_WEIGHT,1)} lbs\n"
                    f"• Wire Weight: {WIRE_WEIGHT_PER_FT:.3f} {wire_weight_unit}\n"
                    f"• Buoyancy Reduction: {buoyancy_reduction:.1f} lbs\n"
                    f"• Effective Weight: {effective_weight:.1f} lbs\n"
                    f"• Pressure Force: {pressure_force:.1f} lbs\n"
                    f"• Stuffing Box Friction: {STUFFING_BOX} lbs\n"
                    f"• Wire Friction: {cumulative_wire_friction:+.1f} lbs\n"
                    f"• Tool String Friction: {effective_friction:+.1f} lbs\n"
                    f"----------------------------------"
                    f"• Net Tension: {tension:.1f} lbs\n"
                    f"• Inclination: {current_inclination:.1f}°\n"
                    f"• Azimuth: {current_azimuth:.1f}°"
                )
                ax.text(WELL_WIDTH + 70, 50, param_text,
                        bbox=dict(facecolor='white', alpha=0.9,
                                  edgecolor='gray', boxstyle='round'),
                        fontsize=9, verticalalignment='top')

                # Depth markers
                for depth_mark in range(0, int(max_depth) + 1, 1000):
                    ax.plot([WELL_WIDTH, WELL_WIDTH + 10], [depth_mark, depth_mark],
                            color='black', linewidth=1)
                ax.text(WELL_WIDTH + 15, depth_mark - 10, f"{depth_mark} ft")

                # Configure axes
                ax.set_xlim(-10, WELL_WIDTH + 180)
                ax.set_ylim(max_depth, 0)  # Inverted depth axis

                # Update axis labels
                if self.use_metric:
                    ax.set_ylabel(f"Depth ({depth_unit}-MD)", fontweight='bold')
                else:
                    ax.set_ylabel(f"Depth ({depth_unit}-MD)", fontweight='bold')

                ax.grid(True, axis='y', linestyle='--', alpha=0.5)
                ax.set_xticks([])
                ax.set_title(f"Tool String Weight Calculation\n"
                             f"Fluid: {FLUID_DENSITY} ppg, Pressure: {PRESSURE} psi",
                             pad=20)

                self.tool_canvas.draw()

        except Exception as e:
            print(f"Tool view update error: {str(e)}")
            self.tool_canvas.draw()
