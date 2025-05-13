import math
import numpy as np
import mplcursors
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QApplication, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from scipy.interpolate import interp1d


class PlotsTab(QWidget):
    updateRequested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.use_metric = False
        self.setup_ui()
        self.current_depth = 0
        self.trajectory_data = None
        self.tool_weight = 150
        self.stuffing_box = 50
        self.wire_weight = 0.1
        self.wire_diameter = 0.108
        self.fluid_density = 8.5
        self.fluid_level = 0
        self.pressure = 500
        self.friction_coeff = 0.3
        # Initialize data storage for info panel
        self.rih_weights = None
        self.depth_points_tension = None
        self.max_overpulls = None
        self.depth_points_overpull = None

    def setup_ui(self):
        layout = QHBoxLayout(self)
        all_plots_layout = QVBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Helper function to create plot widgets with copy buttons
        def create_plot_widget(canvas, title):
            widget = QWidget()
            plot_layout = QVBoxLayout(widget)
            plot_layout.addWidget(canvas)
            plot_layout.addWidget(QLabel(title))

            # Add copy button
            copy_btn = QPushButton("Copy to Clipboard")
            copy_btn.clicked.connect(lambda: self.copy_plot_to_clipboard(canvas))
            plot_layout.addWidget(copy_btn)

            return widget

        # Create plot widgets with copy buttons
        self.tension_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 6)))
        tension_widget = create_plot_widget(self.tension_canvas, "Tension vs Depth")

        self.overpull_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 6)))
        overpull_widget = create_plot_widget(self.overpull_canvas, "Maximum Overpull vs Depth")

        self.incl_canvas = FigureCanvasQTAgg(Figure(figsize=(5, 6)))
        incl_widget = create_plot_widget(self.incl_canvas, "Inclination & DLS vs Depth")

        # Info panel setup
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.total_depth_label = QLabel("Total depth: ... ft (... m)")
        self.max_incl_label = QLabel("Max inclination: ...° at ... ft (... m)")
        self.tool_weight_label = QLabel("Tool string weight in air: ... lbs")
        self.stuffing_box_label = QLabel("Stuffing box friction: ... lbs")
        self.pressure_label = QLabel("Pressure: ... psi")
        self.separator1 = QLabel("_________________________")
        self.min_tension_label = QLabel("The minimum predicted cable tension in normal running conditions is ... lbf with the toolstring at a measured depth of ... ft (... m) during RIH.")
        self.separator2 = QLabel("_________________________")
        self.overpull_label = QLabel("The maximum available overpull at ... ft (... m) based on 50% of cable breaking strength is ... lbf. The weight indicator reading will then be ... lbf.")

        self.min_tension_label.setWordWrap(True)
        self.overpull_label.setWordWrap(True)

        info_layout.addWidget(self.total_depth_label)
        info_layout.addWidget(self.stuffing_box_label)
        info_layout.addWidget(self.max_incl_label)
        info_layout.addWidget(self.tool_weight_label)
        info_layout.addWidget(self.pressure_label)
        info_layout.addWidget(self.separator1)
        info_layout.addWidget(self.min_tension_label)
        info_layout.addWidget(self.separator2)
        info_layout.addWidget(self.overpull_label)
        info_layout.addStretch()

        splitter.addWidget(tension_widget)
        splitter.addWidget(overpull_widget)
        splitter.addWidget(incl_widget)
        # splitter.addWidget(info_widget)
        splitter.setSizes([300, 300, 300, 400])
        all_plots_layout.addWidget(splitter)

        self.update_btn = QPushButton("Update All Plots")
        self.update_btn.clicked.connect(self.updateRequested.emit)
        all_plots_layout.addWidget(self.update_btn)

        layout.addLayout(all_plots_layout)
        layout.addWidget(info_widget)

    def handle_units_toggle(self, use_metric):
        """Called when units change in main application"""
        self.use_metric = use_metric
        if self.trajectory_data and hasattr(self, 'params'):
            self.update_plots(self.trajectory_data, self.params)

    def copy_plot_to_clipboard(self, canvas):
        """Copy the specified plot canvas to system clipboard"""
        try:
            pixmap = canvas.grab()
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)
            self.update_btn.setText("Plot copied!")
            QTimer.singleShot(2000, lambda: self.update_btn.setText("Update All Plots"))
        except Exception as e:
            print(f"Error copying plot: {e}")

    def update_plots(self, trajectory_data, params):
        self.trajectory_data = trajectory_data
        self.tool_weight = params['tool_weight']
        self.stuffing_box = params['stuffing_box']
        self.wire_diameter = params['wire_diameter']
        self.fluid_density = params['fluid_density']
        self.fluid_level = params['fluid_level']
        self.pressure = params['pressure']
        self.friction_coeff = params['friction_coeff']
        self.current_depth = params['current_depth']

        if self.use_metric:
            self.depth_unit = "m"
            self.wire_weight = params['wire_weight'] * 3.28084
            self.wire_weight_unit = "lbs/m"
        else:
            self.depth_unit = "ft"
            self.wire_weight = params['wire_weight']  # lbs/ft
            self.wire_weight_unit = "lbs/ft"

        self.update_tension_plot()
        self.update_overpull_plot()
        self.update_inclination_plot()
        self.update_info_labels()

    def update_info_labels(self):
        # Total depth
        if self.trajectory_data and self.trajectory_data.get('mds'):
            max_depth = float(self.trajectory_data['mds'][-1])
            if self.use_metric:
                max_depth_ft = max_depth / 0.3048
                self.total_depth_label.setText(
                    f"Total depth: {max_depth:.1f} m ({max_depth_ft:.1f} ft)"
                )
            else:
                max_depth_m = max_depth * 0.3048
                self.total_depth_label.setText(
                    f"Total depth: {max_depth:.1f} ft ({max_depth_m:.1f} m)"
                )

        # Max inclination
        if self.trajectory_data and self.trajectory_data.get('inclinations'):
            inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]
            max_incl = max(inclinations)
            idx = inclinations.index(max_incl)
            depth_ft = float(self.trajectory_data['mds'][idx])
            depth_m = depth_ft * 0.3048
            self.max_incl_label.setText(f"Max inclination: {max_incl:.1f}° at {depth_ft:.1f} ft ({depth_m:.1f} m)")
        else:
            self.max_incl_label.setText("Max inclination: N/A")

        # Tool weight and pressure
        self.tool_weight_label.setText(f"Tool string weight in air: {self.tool_weight} lbs")
        self.pressure_label.setText(f"Pressure: {self.pressure} psi")

        self.stuffing_box_label.setText(f"Stuffing box friction: {self.stuffing_box} lbs")

        # Minimum RIH tension
        if self.rih_weights is not None and self.depth_points_tension is not None:
            min_tension = min(self.rih_weights)
            idx = np.argmin(self.rih_weights)
            depth_ft = self.depth_points_tension[idx]
            depth_m = depth_ft * 0.3048
            self.min_tension_label.setText(
                f"The minimum predicted cable tension in normal running conditions is {min_tension:.1f} lbf "
                f"with the toolstring at a measured depth of {depth_ft:.1f} ft ({depth_m:.1f} m) during RIH.")
        else:
            self.min_tension_label.setText("Minimum tension data not available.")

        # Max overpull info
        breaking_strength = 3200  # lbs
        safe_pull_pct = 50
        if self.max_overpulls is not None and self.depth_points_overpull is not None:
            min_idx = np.argmin(self.max_overpulls)
            overpull = self.max_overpulls[min_idx]
            depth_ft = self.depth_points_overpull[min_idx]
            depth_m = depth_ft * 0.3048
            wis_reading = (safe_pull_pct/100)*breaking_strength - overpull
            self.overpull_label.setText(
                f"The maximum available overpull at {depth_ft:.1f} ft ({depth_m:.1f} m) "
                f"based on {safe_pull_pct}% of cable breaking strength is {overpull:.1f} lbf.\n"
                f"The weight indicator reading will then be {wis_reading:.1f} lbf.")
        else:
            self.overpull_label.setText("Overpull data not available.")

    def update_tension_plot(self):
        fig = self.tension_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        if not self.trajectory_data:
            return

        mds = [float(md) for md in self.trajectory_data['mds']]
        # inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]
        max_depth = float(mds[-1])
        depth_points = np.linspace(0, max_depth, 100)

        buoyancy_factor = 1 - (self.fluid_density / 65.4)
        # incl_interp = interp1d(mds, inclinations, kind='linear', fill_value='extrapolate')
        # incl_at_points = incl_interp(depth_points)

        rih_weights, pooh_weights = [], []

        idx = np.argmin(np.abs(np.array(self.trajectory_data['mds']) - self.current_depth))
        current_inclination = self.trajectory_data['inclinations'][idx]

        # for depth, inc in zip(mds, inclinations):
        for idx in range(len(self.trajectory_data['inclinations'])):
            depth = mds[idx]
            inc = self.trajectory_data['inclinations'][idx]

            wire_in_hole = depth
            total_weight = self.tool_weight + self.wire_weight * wire_in_hole

            wire_weight = depth * self.wire_weight
            submerged_length = max(depth - self.fluid_level, 0)
            buoyancy = submerged_length * self.wire_weight * (1 - buoyancy_factor)
            submerged_weight = total_weight - buoyancy

            inc_rad = math.radians(inc)
            effective_weight = submerged_weight * math.cos(inc_rad)

            area = math.pi * (self.wire_diameter / 2) ** 2
            pressure_force = self.pressure * area

            normal_force = submerged_weight * math.sin(inc_rad)
            rih_friction = -self.friction_coeff * normal_force - self.stuffing_box
            pooh_friction = self.friction_coeff * normal_force + self.stuffing_box

            rih_tension = max(effective_weight - pressure_force + rih_friction, 0)
            pooh_tension = max(effective_weight - pressure_force + pooh_friction, 0)
            rih_weights.append(rih_tension)
            pooh_weights.append(pooh_tension)

            # if 30 < idx < 32:
            #     print('From plot:')
            #     print(f'{depth} m: {inc} degrees')
            #     print('EW:',effective_weight)
            #     print('WW:',self.wire_weight)
            #     print('TW:',total_weight)
            #     print('PF:',pressure_force)
            #     print('NF:',normal_force)
            #     print('SW:',submerged_weight)
            #     print('IR:',inc_rad)
            #     print('RF:',rih_friction)
            #     print('PF:',pooh_friction)
            #     print(f'RIH={rih_tension}')
            #     print(f'POOH={pooh_tension}\n')

        # Plotting (depth on y-axis, inverted)
        rih_line, = ax.plot(rih_weights, mds, 'b-', label='RIH Tension')
        pooh_line, = ax.plot(pooh_weights, mds, 'r-', label='POOH Tension')

        # Add cursor hover functionality
        cursor_rih = mplcursors.cursor(rih_line, hover=True)
        cursor_pooh = mplcursors.cursor(pooh_line, hover=True)

        @cursor_rih.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                depth_ft = depth / 0.3048
                text = f'RIH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m ({depth_ft:.1f} ft)'
            else:
                depth_m = depth * 0.3048
                text = f'RIH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft ({depth_m:.1f} m)'
            sel.annotation.set_text(text)

        @cursor_pooh.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                depth_ft = depth / 0.3048
                text = f'POOH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m ({depth_ft:.1f} ft)'
            else:
                depth_m = depth * 0.3048
                text = f'POOH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft ({depth_m:.1f} m)'
            sel.annotation.set_text(text)

        # @cursor_pooh.connect("add")
        # def _(sel):
        #     sel.annotation.set_text(f'POOH: {sel.target[0]:.1f} lbs\nDepth: {sel.target[1]:.1f} ft')
        #     sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

        idx = np.argmin(np.abs(np.array(self.trajectory_data['mds']) - self.current_depth))
        ax.plot(rih_weights[idx], mds[idx], 'bo')
        ax.plot(pooh_weights[idx], mds[idx], 'ro')
        ax.axhline(self.current_depth, color='gray', linestyle='--')

        ax.set_xlabel("Tension (lbs)")
        ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
        ax.set_title("Tension vs Depth Profile")
        ax.grid(True)
        ax.legend()
        ax.set_ylim(max_depth, 0)
        if min(rih_weights) > 0:
            ax.set_xlim(left=0)
        self.tension_canvas.draw()

        self.depth_points_tension = depth_points
        self.rih_weights = rih_weights
        self.pooh_weights = pooh_weights

    def update_overpull_plot(self):
        try:
            fig = self.overpull_canvas.figure
            fig.clear()
            ax = fig.add_subplot(111)

            if not hasattr(self, 'trajectory_data'):
                return

            # Ensure data is float
            mds = [float(md) for md in self.trajectory_data['mds']]
            inclinations = [float(inc) for inc in self.trajectory_data['inclinations']]

            max_depth = float(mds[-1])
            depth_points = np.linspace(0, max_depth, 100)

            # Get parameters
            TOOL_WEIGHT = float(self.tool_weight)
            WIRE_WEIGHT_PER_FT = self.wire_weight
            WIRE_DIAMETER = self.wire_diameter
            FLUID_DENSITY = float(self.fluid_density)
            FLUID_LEVEL = float(self.fluid_level)
            PRESSURE = float(self.pressure)
            FRICTION_COEFF = float(self.friction_coeff)
            BUOYANCY_FACTOR = 1 - (FLUID_DENSITY / 65.4)

            # Max allowable overpull force
            breaking_strength = 3200  # lbs
            safe_pull_limit = 0.5 * breaking_strength  # 50% of MBS = 1600 lbs

            # Interpolate inclinations
            incl_interp = interp1d(mds, inclinations, kind='linear', fill_value='extrapolate')
            incl_at_points = incl_interp(depth_points)

            max_overpulls = []

            for depth, inclination in zip(depth_points, incl_at_points):
                wire_weight = depth * WIRE_WEIGHT_PER_FT
                total_weight = TOOL_WEIGHT + wire_weight

                # Buoyancy
                submerged_length = max(depth - FLUID_LEVEL, 0)
                buoyancy_reduction = submerged_length * WIRE_WEIGHT_PER_FT * (1 - BUOYANCY_FACTOR)
                submerged_weight = total_weight - buoyancy_reduction

                # Effective weight
                inclination_rad = math.radians(inclination)
                effective_weight = submerged_weight * math.cos(inclination_rad)

                # Pressure force
                wire_area = math.pi * (WIRE_DIAMETER / 2) ** 2
                pressure_force = PRESSURE * wire_area

                # Friction (only in deviated sections)
                if inclination > 1.0:
                    normal_force = submerged_weight * math.sin(inclination_rad)
                    pooh_friction = FRICTION_COEFF * normal_force
                else:
                    pooh_friction = 0

                pooh_tension = max(effective_weight - pressure_force + pooh_friction, 0)

                # Max overpull = safe limit - POOH tension
                max_overpull = max(safe_pull_limit - pooh_tension, 0)
                max_overpulls.append(max_overpull)

            # Plotting
            overpull_line, = ax.plot(max_overpulls, depth_points, 'g-', label='Max Overpull (lbs)')

            # Add cursor hover functionality
            cursor_overpull = mplcursors.cursor(overpull_line, hover=True)

            @cursor_overpull.connect("add")
            def _(sel):
                sel.annotation.set_text(f'Overpull: {sel.target[0]:.1f} lbs\nDepth: {sel.target[1]:.1f} ft')
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

            # Current position marker
            if hasattr(self, 'current_depth'):
                current_depth = float(self.current_depth)
                if current_depth <= max_depth:
                    current_idx = np.argmin(np.abs(depth_points - current_depth))
                    ax.plot(max_overpulls[current_idx], depth_points[current_idx], 'go', label='Current Max Overpull')
                    ax.axhline(y=current_depth, color='gray', linestyle='--', alpha=0.5)

            ax.set_xlabel('Max Overpull (lbs)')
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
            ax.set_title('Maximum Overpull vs Depth')
            ax.grid(True)
            ax.legend()
            ax.set_ylim(max_depth, 0)
            ax.set_xlim(left=0)
            self.overpull_canvas.draw()

            self.depth_points_overpull = depth_points
            self.max_overpulls = max_overpulls

        except Exception as e:
            print('Update max overpull error:', e)

    def update_inclination_plot(self):
        try:

            """Update the inclination and DLS vs depth plot with depth on the y-axis"""
            fig = self.incl_canvas.figure
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
                    dls = 0.0
                else:
                    delta_md = mds[i] - mds[i-1]
                    delta_inc = inclinations[i] - inclinations[i-1]

                    if self.use_metric:  # Calculate DLS in °/30m
                        dls = (abs(delta_inc) / (delta_md / 30.48)) if delta_md != 0 else 0.0
                    else:  # Calculate DLS in °/100ft
                        dls = (abs(delta_inc) / delta_md) * 100 if delta_md != 0 else 0.0
                dls_values.append(dls)

            # Create twin axis for DLS
            ax2 = ax.twiny()

            # Plot inclination (primary x-axis)
            inc_line, = ax.plot(inclinations, mds, 'g-', label='Inclination')
            dls_line, = ax2.plot(dls_values, mds, 'm--', label='DLS')

            ax2.set_xlabel('DLS (°/30m)' if self.use_metric else 'DLS (°/100ft)')

            # Add cursor hover functionality
            cursor_inc = mplcursors.cursor(inc_line, hover=True)
            cursor_dls = mplcursors.cursor(dls_line, hover=True)

            @cursor_inc.connect("add")
            def _(sel):
                sel.annotation.set_text(f'Inclination: {sel.target[0]:.1f}°\nDepth: {sel.target[1]:.1f} ft')
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

            @cursor_dls.connect("add")
            def _(sel):
                sel.annotation.set_text(f'DLS: {sel.target[0]:.1f}°/100ft\nDepth: {sel.target[1]:.1f} ft')
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

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
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")

            self.incl_canvas.draw()

        except Exception as e:
            print('Update inclination plot Error:', e)