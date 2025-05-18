import math
import textwrap
from datetime import datetime

import numpy as np
import mplcursors
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QApplication, QHBoxLayout,
                             QFileDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import tempfile
import os

from utils.path_finder import get_icon_path, get_path


class PlotsTab(QWidget):
    updateRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.use_metric = False
        self.setup_ui()
        self.current_depth = 0
        self.trajectory_data = None
        self.tool_weight = 150
        self.stuffing_box = 50
        self.wire_weight = 0.1
        self.wire_diameter = 0.108
        self.breaking_strength = 2550
        self.fluid_density = 8.5
        self.fluid_level = 0
        self.pressure = 500
        self.buoyancy = 0
        self.surface_buoyancy = 0
        self.friction_coeff = 0.3
        # Initialize data storage for info panel
        self.rih_weights = None
        self.dls_values = None
        self.depth_points_tension = None
        self.max_overpulls = None
        self.depth_points_overpull = None

        input_tab = parent.input_tab
        input_tab.units_toggled.connect(self.handle_units_toggle)

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

        self.speed_label = QLabel("Wire speed: ... ft/min")
        self.total_depth_label = QLabel("Total depth: ... ft (... m)")
        self.max_incl_label = QLabel("Max inclination: ...° at ... ft (... m)")
        self.max_dls_label = QLabel("Max DLS: ...°/...ft at ... ft (... m)")
        self.pressure_label = QLabel("WHP: ... psi")
        self.separator1 = QLabel("_________________________")
        self.C1_label = QLabel("The minimum predicted cable tension in normal running conditions is ... lbf with the toolstring at a measured depth of ... ft (... m) during RIH.")
        self.separator2 = QLabel("_________________________")
        self.MD1_label = QLabel("The maximum available overpull at ... ft (... m) based on 50% of cable breaking strength is ... lbf. The weight indicator reading will then be ... lbf.")
        self.separator3 = QLabel("_________________________")
        self.T1_label = QLabel("The current tool string weight in air is ... lbs (... kg).")
        self.T2_label = QLabel("The minimum weight required at surface is ... lbs. This is the minimum weight needed to overcome the current well head pressure of ... psi, stuffing box friction of ... lbf and buoyant force of ... lbf")
        self.T5_label = QLabel("The current tool weight is ... % of the wire breaking strength.")

        self.separator4 = QLabel("_________________________")
        self.export_btn = QPushButton("Export to PDF")
        self.export_btn.clicked.connect(self.export_to_pdf)

        self.C1_label.setWordWrap(True)
        self.T2_label.setWordWrap(True)
        self.MD1_label.setWordWrap(True)

        info_layout.addWidget(self.speed_label)
        info_layout.addWidget(self.total_depth_label)
        info_layout.addWidget(self.max_incl_label)
        info_layout.addWidget(self.max_dls_label)
        info_layout.addWidget(self.pressure_label)
        info_layout.addWidget(self.separator1)
        info_layout.addWidget(self.C1_label)
        info_layout.addWidget(self.separator2)
        info_layout.addWidget(self.MD1_label)
        info_layout.addWidget(self.separator3)
        info_layout.addWidget(self.T1_label)
        info_layout.addWidget(self.T2_label)
        info_layout.addWidget(self.T5_label)
        info_layout.addStretch()
        info_layout.addWidget(self.separator4)
        info_layout.addWidget(self.export_btn)

        splitter.addWidget(tension_widget)
        splitter.addWidget(overpull_widget)
        splitter.addWidget(incl_widget)
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
        self.tool_avg_diameter = params['tool_avg_diameter']
        self.speed = params['speed']
        self.tool_length = params['tool_length']
        self.stuffing_box = params['stuffing_box']
        self.wire_diameter = params['wire_diameter']
        self.safe_operating_load = params['safe_operating_load']
        self.breaking_strength = params['breaking_strength']
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

        self.speed_label.setText(f"Wire speed: {self.speed} ft/min")

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
            depth = float(self.trajectory_data['mds'][idx])

            if self.use_metric:
                depth_ft = depth / 0.3048
                self.max_incl_label.setText(f"Max inclination: {max_incl:.1f}° at {depth:.1f} m ({depth_ft:.1f} ft)")
            else:
                depth_m = depth * 0.3048
                self.max_incl_label.setText(f"Max inclination: {max_incl:.1f}° at {depth:.1f} ft ({depth_m:.1f} m)")
        else:
            self.max_incl_label.setText("Max inclination: N/A")

        # Max DLS
        if self.dls_values:
            dls_list = [float(dls) for dls in self.dls_values]
            max_dls = max(dls_list)
            idx = dls_list.index(max_dls)
            depth = float(self.trajectory_data['mds'][idx-1])

            if self.use_metric:
                depth_ft = depth / 0.3048
                self.max_dls_label.setText(f"Max DLS: {max_dls:.1f}°/100ft at {depth:.1f} m ({depth_ft:.1f} ft)")
            else:
                depth_m = depth * 0.3048
                self.max_dls_label.setText(f"Max DLS: {max_dls:.1f}°/100ft at {depth:.1f} ft ({depth_m:.1f} m)")
        else:
            self.max_dls_label.setText("Max DLS: N/A")

        # Tool weight and pressure
        self.T1_label.setText(f"The current tool string weight in air is {self.tool_weight} lbs ({(self.tool_weight*0.453592):.1f} kg).")
        self.T5_label.setText(f"The current tool weight is {(self.tool_weight/self.breaking_strength * 100):.1f} % of the wire breaking strength.")
        self.pressure_label.setText(f"WHP: {self.pressure} psi")

        # Minimum RIH tension
        if self.rih_weights is not None and self.depth_points_tension is not None:
            min_tension = min(self.rih_weights)
            surface_weight = self.rih_weights[0]
            idx = np.argmin(self.rih_weights)
            depth = self.depth_points_tension[idx]

            if self.use_metric:
                depth_ft = depth / 0.3048
                depth_m = depth
            else:
                depth_m = depth * 0.3048
                depth_ft = depth

            self.T2_label.setText(
                f"The minimum weight required at surface is {surface_weight} lbs. "
                f"This is the minimum weight needed to overcome the current well head pressure of {self.pressure} psi, "
                f"stuffing box friction of {self.stuffing_box} lbf and buoyant force of {self.buoyancy} lbf")
            self.C1_label.setText(
                f"The minimum predicted cable tension in normal running conditions is {min_tension:.1f} lbf "
                f"with the toolstring at a measured depth of {depth_ft:.1f} ft ({depth_m:.1f} m) during RIH.")
        else:
            self.C1_label.setText("Minimum tension data not available.")

        # Max overpull info
        breaking_strength = self.breaking_strength  # lbs
        safe_pull_pct = self.safe_operating_load
        if self.max_overpulls is not None and self.depth_points_overpull is not None:
            min_idx = np.argmin(self.max_overpulls)
            overpull = self.max_overpulls[min_idx]
            depth = self.depth_points_overpull[min_idx]

            if self.use_metric:
                depth_ft = depth / 0.3048
                depth_m = depth
            else:
                depth_m = depth * 0.3048
                depth_ft = depth

            self.MD1_label.setText(
                f"The maximum available overpull at {depth_ft:.1f} ft ({depth_m:.1f} m) "
                f"based on {safe_pull_pct}% of wire breaking strength is {overpull:.1f} lbf.\n"
                f"The weight indicator reading will then be {breaking_strength*safe_pull_pct/100:.1f} lbf.")
        else:
            self.MD1_label.setText("Overpull data not available.")

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

        rih_weights, pooh_weights = [], []

        # for depth, inc in zip(mds, inclinations):
        for idx in range(len(self.trajectory_data['inclinations'])):
            depth = mds[idx]
            inc = self.trajectory_data['inclinations'][idx]

            wire_in_hole = depth

            total_weight = self.tool_weight + self.wire_weight * wire_in_hole

            if depth >= self.fluid_level:
                tool_area = math.pi * (self.tool_avg_diameter/12/2) ** 2
                tool_displacement = (tool_area * self.tool_length)
                tool_displacement_gal = tool_displacement * 7.48052
                buoyancy_weight = tool_displacement_gal * self.fluid_density

                submerged_length = max(depth - self.fluid_level, 0)
                self.buoyancy = buoyancy_weight + submerged_length * self.wire_weight * (1 - buoyancy_factor)
                if idx == 0:
                    self.surface_buoyancy = self.buoyancy
                submerged_weight = total_weight - self.buoyancy
            else:
                self.buoyancy = 0
                submerged_weight = total_weight

            inc_rad = math.radians(inc)
            effective_weight = submerged_weight * math.cos(inc_rad)

            area = math.pi * (self.wire_diameter / 2) ** 2
            pressure_force = self.pressure * area

            # --- FLUID DRAG CALCULATION BASED ON FLOW REGIME ---
            speed_ft_min = self.speed  # ft/min
            v = speed_ft_min / 60  # ft/s

            tool_diameter_ft = self.tool_avg_diameter / 12
            projected_area = math.pi * (tool_diameter_ft / 2) ** 2

            # Convert fluid density from ppg to slug/ft³
            fluid_density_slug = self.fluid_density * 0.0160185

            # Assume dynamic viscosity in lb·s/ft² (for water ~1 cP)
            mu = 0.00002093

            # Reynolds number
            Re = fluid_density_slug * v * tool_diameter_ft / mu

            # Decide drag model
            if Re < 2300:
                # Laminar (Stokes drag, proportional to velocity)
                # F_d = 3 * pi * mu * D * v
                drag_force = 3 * math.pi * mu * tool_diameter_ft * v
            else:
                # Turbulent (Quadratic drag)
                Cd = 0.82  # for long cylinder moving axially
                drag_force = 0.5 * Cd * self.fluid_density * projected_area * v ** 2

            normal_force = submerged_weight * math.sin(inc_rad)
            rih_friction = -self.friction_coeff * normal_force - self.stuffing_box
            pooh_friction = self.friction_coeff * normal_force + self.stuffing_box

            rih_tension = max(effective_weight - pressure_force + rih_friction - drag_force, 0)
            pooh_tension = max(effective_weight - pressure_force + pooh_friction + drag_force, 0)

            rih_weights.append(rih_tension)
            pooh_weights.append(pooh_tension)

        wire_friction = []

        # Process segments from bottom to top
        for i in range(len(mds) - 2, -1, -1):
            delta_L = mds[i + 1] - mds[i]
            theta_avg = math.radians((self.trajectory_data['inclinations'][i + 1] + self.trajectory_data['inclinations'][i]) / 2)
            avg_depth = (mds[i + 1] + mds[i]) / 2

            # Calculate segment buoyancy
            if avg_depth >= self.fluid_level:
                wire_submerged = self.wire_weight * delta_L * buoyancy_factor
            else:
                wire_submerged = self.wire_weight * delta_L

            # Segment contributions
            normal_force = wire_submerged * math.sin(theta_avg)
            friction = self.friction_coeff * normal_force

            wire_friction.append(friction)

        wire_friction = wire_friction[::-1]

        for i in range(len(wire_friction)):
            rih_weights[i+1] -= sum(wire_friction[:i])
            pooh_weights[i+1] += sum(wire_friction[:i])

        # Plotting (depth on y-axis, inverted)
        self.rih_line, = ax.plot(rih_weights, mds, 'b-', label='RIH Tension')
        self.pooh_line, = ax.plot(pooh_weights, mds, 'r-', label='POOH Tension')

        # Add cursor hover functionality
        cursor_rih = mplcursors.cursor(self.rih_line, hover=True)
        cursor_pooh = mplcursors.cursor(self.pooh_line, hover=True)

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

            # Check if required data is available
            if not self.trajectory_data or self.pooh_weights is None:
                return

            # Get depth points and POOH tensions from tension plot data
            mds = [float(md) for md in self.trajectory_data['mds']]
            pooh_weights = self.pooh_weights
            max_depth = float(mds[-1])

            # Calculate safe pull limit correctly (accounting for percentage)
            safe_pull_limit = (self.safe_operating_load / 100) * self.breaking_strength
            # Calculate max overpull at each depth
            max_overpulls = [max(safe_pull_limit - pooh, 0) for pooh in pooh_weights]

            # Plotting
            overpull_line, = ax.plot(max_overpulls, mds, 'r-', label='Max Overpull (lbs)')

            # Cursor hover functionality with unit conversions
            cursor_overpull = mplcursors.cursor(overpull_line, hover=True)

            @cursor_overpull.connect("add")
            def _(sel):
                depth = sel.target[1]
                if self.use_metric:
                    depth_ft = depth / 0.3048
                    text = f'Overpull: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m ({depth_ft:.1f} ft)'
                else:
                    depth_m = depth * 0.3048
                    text = f'Overpull: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft ({depth_m:.1f} m)'
                sel.annotation.set_text(text)
                sel.annotation.get_bbox_patch().set(fc="white", alpha=0.8)

            # Current depth marker
            if hasattr(self, 'current_depth'):
                current_depth = float(self.current_depth)
                if current_depth <= max_depth:
                    idx = np.argmin(np.abs(np.array(mds) - current_depth))
                    ax.plot(max_overpulls[idx], mds[idx], 'ro', label='Current Max Overpull')
                    ax.axhline(current_depth, color='gray', linestyle='--', alpha=0.5)

            # Axis labels and formatting
            ax.set_xlabel('Max Overpull (lbs)')
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
            ax.set_title('Maximum Overpull vs Depth')
            ax.grid(True)
            ax.legend()
            ax.set_ylim(max_depth, 0)  # Invert depth axis
            ax.set_xlim(left=0)
            self.overpull_canvas.draw()

            # Store data for info panel
            self.depth_points_overpull = mds
            self.max_overpulls = max_overpulls

        except Exception as e:
            print('Error updating overpull plot:', e)

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
            self.dls_values = []
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
                self.dls_values.append(dls)

            # Create twin axis for DLS
            ax2 = ax.twiny()

            # Plot inclination (primary axis)
            inc_line, = ax.plot(inclinations, mds, 'b-', label='Inclination')

            # Plot DLS as step function (horizontal segments between depth points)
            if len(mds) >= 2:
                # Use DLS values from index 1 onward (skip initial 0)
                dls_for_plot = self.dls_values[1:]
                # Use starting depth of each interval (exclude last MD)
                mds_for_plot = mds[:-1]
                dls_line, = ax2.step(
                    dls_for_plot, mds_for_plot,
                    where='post', linestyle='-', color='r', label='DLS'
                )
            else:
                # Not enough data for steps
                dls_line, = ax2.plot([], [], 'r-', label='DLS')

            ax2.set_xlabel('DLS (°/30m)' if self.use_metric else 'DLS (°/100ft)')

            # Add cursor hover functionality
            cursor_inc = mplcursors.cursor(inc_line, hover=True)
            cursor_dls = mplcursors.cursor(dls_line, hover=True) if len(mds) >= 2 else None

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
                ax.plot(inclinations[idx], mds[idx], 'bo', markersize=8, label='Current Inclination')

                if len(mds) >= 2:
                    ax2.plot(self.dls_values[idx], mds[idx], 'ro', markersize=8, label='Current DLS')

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
            print('Update inclination/DLS plot Error:', e)

    def generate_trajectory_image(self):
        """Generates a 3D trajectory plot image with equal axis scaling"""
        if not self.trajectory_data:
            return None

        fig = Figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111, projection='3d')

        try:
            mds = self.trajectory_data['mds']
            if self.use_metric:
                tvd = np.array([tvd * 3.281 for tvd in self.trajectory_data['tvd']])
            else:
                tvd = np.array([tvd / 3.281 for tvd in self.trajectory_data['tvd']])
            north = np.array(self.trajectory_data['north'])
            east = np.array(self.trajectory_data['east'])

            # Convert units if metric is enabled
            if self.use_metric:
                north *= 0.3048
                east *= 0.3048
                tvd *= 0.3048
                unit_label = 'm'
            else:
                unit_label = 'ft'

            # Plot well path and casing as tubes if there are sufficient points
            if len(north) > 1:
                points = np.vstack([north, east, tvd]).T
                tangents = np.zeros_like(points)
                tangents[1:-1] = points[2:] - points[:-2]
                tangents[0] = points[1] - points[0]
                tangents[-1] = points[-1] - points[-2]
                tangents /= np.linalg.norm(tangents, axis=1, keepdims=True) + 1e-8

                normals = np.zeros_like(tangents)
                binormals = np.zeros_like(tangents)

                # Compute radii for casing and well path tubes
                tube_radius = (0.15 if self.use_metric else 0.5) * 500  # Casing radius
                well_tube_radius = tube_radius * 0.5  # Well path radius (half of casing)

                for i in range(len(tangents)):
                    tangent = tangents[i]
                    up = np.array([0, 0, 1])
                    normal = np.cross(tangent, up)
                    if np.linalg.norm(normal) < 1e-6:
                        up = np.array([1, 0, 0])
                        normal = np.cross(tangent, up)
                    normal /= np.linalg.norm(normal) + 1e-8
                    binormal = np.cross(tangent, normal)
                    binormal /= np.linalg.norm(binormal) + 1e-8
                    normals[i] = normal
                    binormals[i] = binormal

                # Generate well path tube
                theta = np.linspace(0, 2 * np.pi, 20)
                X_well = np.zeros((len(theta), len(points)))
                Y_well = np.zeros((len(theta), len(points)))
                Z_well = np.zeros((len(theta), len(points)))

                for i in range(len(points)):
                    x_well = points[i, 0] + well_tube_radius * (
                                normals[i, 0] * np.cos(theta) + binormals[i, 0] * np.sin(theta))
                    y_well = points[i, 1] + well_tube_radius * (
                                normals[i, 1] * np.cos(theta) + binormals[i, 1] * np.sin(theta))
                    z_well = points[i, 2] + well_tube_radius * (
                                normals[i, 2] * np.cos(theta) + binormals[i, 2] * np.sin(theta))
                    X_well[:, i] = x_well
                    Y_well[:, i] = y_well
                    Z_well[:, i] = z_well

                ax.plot_surface(X_well, Y_well, Z_well, color='navy', alpha=1.0, linewidth=0)

                # Generate casing tube
                X_casing = np.zeros((len(theta), len(points)))
                Y_casing = np.zeros((len(theta), len(points)))
                Z_casing = np.zeros((len(theta), len(points)))

                for i in range(len(points)):
                    x_casing = points[i, 0] + tube_radius * (
                                normals[i, 0] * np.cos(theta) + binormals[i, 0] * np.sin(theta))
                    y_casing = points[i, 1] + tube_radius * (
                                normals[i, 1] * np.cos(theta) + binormals[i, 1] * np.sin(theta))
                    z_casing = points[i, 2] + tube_radius * (
                                normals[i, 2] * np.cos(theta) + binormals[i, 2] * np.sin(theta))
                    X_casing[:, i] = x_casing
                    Y_casing[:, i] = y_casing
                    Z_casing[:, i] = z_casing

                ax.plot_surface(X_casing, Y_casing, Z_casing, color='lightgray', alpha=0.5, linewidth=0)

                # Create proxy artists for the legend
                from matplotlib.lines import Line2D
                well_proxy = Line2D([0], [0], color='navy', lw=4, label='Tubing')
                casing_proxy = Line2D([0], [0], color='lightgray', lw=4, alpha=0.5, label='Casing')
                ax.legend(handles=[well_proxy, casing_proxy])

            # Calculate axis ranges
            north_min, north_max = np.min(north), np.max(north)
            east_min, east_max = np.min(east), np.max(east)
            tvd_min, tvd_max = np.min(tvd), np.max(tvd)

            # Get maximum range among all axes
            ranges = [
                north_max - north_min,
                east_max - east_min,
                tvd_max - tvd_min
            ]
            max_range = max(ranges)

            # Calculate midpoints
            north_center = (north_max + north_min) * 0.5
            east_center = (east_max + east_min) * 0.5
            tvd_center = (tvd_max + tvd_min) * 0.5

            # Set equal limits for all axes
            ax.set_xlim(north_center - max_range / 2, north_center + max_range / 2)
            ax.set_ylim(east_center - max_range / 2, east_center + max_range / 2)
            ax.set_zlim(tvd_center + max_range / 2, tvd_center - max_range / 2)  # Inverted for TVD

            # Add axis labels
            ax.set_xlabel(f'North ({unit_label})')
            ax.set_ylabel(f'East ({unit_label})')
            ax.set_zlabel(f'TVD ({unit_label})')
            ax.set_title("Well Trajectory Overview")

            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            fig.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            return temp_file.name

        except Exception as e:
            print(f"Error generating trajectory image: {e}")
            return None

    def export_to_pdf(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save PDF Report", "", "PDF Files (*.pdf)"
            )
            if not file_path:
                return

            # Generate temporary plot images
            trajectory_img = self.generate_trajectory_image()
            tension_img = self.generate_plot_image('tension')
            inclination_img = self.generate_plot_image('inclination')
            overpull_img = self.generate_plot_image('overpull')

            # Header/footer definitions
            def draw_header(canvas, page_num, width, height):
                canvas.setFont("Helvetica-Bold", 14)
                canvas.drawString(40, height - 40, "Deleum Oilfield Services Sdn. Bhd.")
                logo_path = get_icon_path("logo_full")
                if os.path.exists(logo_path):
                    logo = ImageReader(logo_path)
                    canvas.drawImage(logo, width - 120, height - 60,
                                     width=80, height=40, preserveAspectRatio=True, mask='auto')
                canvas.line(30, height - 70, width - 30, height - 70)

            def draw_footer(canvas, page_num, width, height):
                canvas.setFont("Helvetica", 10)
                date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

                # Split into date and page number components
                date_text = f"Report generated: {date_str}"
                page_text = f"Page {page_num}"

                # Draw date centered
                canvas.drawCentredString(width / 2, 60, date_text)

                # Draw page number aligned to right margin (40px from right edge)
                canvas.drawRightString(width - 40, 60, page_text)

                # Draw software logo
                wirehub_path = get_path(os.path.join("assets", "backgrounds", "title.png"))
                if os.path.exists(wirehub_path):
                    wirehub = ImageReader(wirehub_path)
                    canvas.drawImage(wirehub, 40, 30,
                                     width=100, height=50, preserveAspectRatio=True, mask='auto')

                # Keep existing footer line
                canvas.line(30, 80, width - 30, 80)

            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            page_number = 1

            # Add trajectory plot as first page
            if trajectory_img:
                # Draw header/footer
                draw_header(c, page_number, width, height)
                draw_footer(c, page_number, width, height)

                # Add main titles
                c.setFillColorRGB(0.6, 0, 0.1)  # Burgundy color
                c.setFont("Helvetica-Bold", 24)
                c.drawCentredString(width / 2, height - 100, "Deleum WireHub")
                c.setFillColorRGB(0, 0, 0)  # Reset to black
                c.setFont("Helvetica-Bold", 20)
                c.drawCentredString(width / 2, height - 140, "Wireline Operation Simulation")

                # Two-column layout
                col_x = [50, width / 2 + 20]
                line_height = 14
                current_y = height - 180

                # Column 1 content
                col1 = [
                    "Project: ...",
                    "Prepared by: ...",
                    "Client: ...",
                    f"Simulation Date: {datetime.now().strftime('%Y-%m-%d')}",
                    "Field: ...",
                    "Location: ..."
                ]
                c.setFont("Helvetica", 12)
                for line in col1:
                    c.drawString(col_x[0], current_y, line)
                    current_y -= line_height

                # Column 2 content
                current_y = height - 180
                col2 = [
                    "Well: ...",
                    "Wire: ...",
                    "Tool String: ...",
                    "Weak Point: ...",
                    "Country: Malaysia"
                ]
                for line in col2:
                    c.drawString(col_x[1], current_y, line)
                    current_y -= line_height

                # Calculate image position
                lowest_y = height - 180 - (len(col1) * line_height) - 40
                img = ImageReader(trajectory_img)
                img_w, img_h = img.getSize()
                aspect = img_h / img_w

                # Dynamic image scaling
                max_width = width - 100
                max_height = lowest_y - 130  # Account for title and footer
                plot_width = min(max_width, max_height / aspect)
                plot_height = plot_width * aspect

                # Draw trajectory title and image
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, lowest_y - 20, "Well Trajectory Overview")
                c.drawImage(img, 50, lowest_y - 10 - plot_height,
                            width=plot_width, height=plot_height)

                c.showPage()
                page_number += 1

            draw_header(c, page_number, width, height)
            draw_footer(c, page_number, width, height)

            # Proceed with other plots
            plot_order = [
                ('tension', 'Tension Analysis'),
                ('inclination', 'Trajectory Analysis'),
                ('overpull', 'Overpull Analysis')
            ]

            y_pos = height - 100
            for plot_type, title in plot_order:
                img_path = locals().get(f"{plot_type}_img")
                if not img_path:
                    continue

                img = ImageReader(img_path)
                img_w, img_h = img.getSize()
                aspect = img_h / img_w
                plot_width = width - 100
                plot_height = plot_width * aspect

                if y_pos - plot_height < 150:
                    c.showPage()
                    page_number += 1
                    draw_header(c, page_number, width, height)
                    draw_footer(c, page_number, width, height)
                    y_pos = height - 100

                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos - 20, title)
                y_pos -= 40

                c.drawImage(img, 50, y_pos - plot_height, width=plot_width, height=plot_height)
                y_pos -= plot_height + 40

                # Add text section if applicable
                if plot_type == 'tension':
                    text_section = self.get_info_text('tension')
                    y_pos = self.add_text_section(c, text_section, y_pos, width, height, page_number)
                elif plot_type == 'inclination':
                    text_section = self.get_info_text('inclination')
                    y_pos = self.add_text_section(c, text_section, y_pos, width, height, page_number)

            # Add general info section
            text_section = self.get_info_text('general')
            self.add_text_section(c, text_section, y_pos, width, height, page_number)

            # Add Input Data page
            c.showPage()
            page_number += 1
            draw_header(c, page_number, width, height)
            draw_footer(c, page_number, width, height)

            # --- Input Data Page Content ---
            y_pos = height - 100
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, y_pos, "Input Data")
            # Underline title
            c.line(width / 2 - 50, y_pos - 5, width / 2 + 50, y_pos - 5)
            y_pos -= 40

            # Well Parameters Section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Well Parameters")
            c.setFont("Helvetica", 10)
            y_pos -= 20

            # Well Depth
            if self.trajectory_data and self.trajectory_data.get('mds'):
                max_depth = float(self.trajectory_data['mds'][-1])
                if self.use_metric:
                    max_depth_ft = max_depth / 0.3048
                    depth_str = f"Well Depth: {max_depth:.1f} m ({max_depth_ft:.1f} ft)"
                else:
                    max_depth_m = max_depth * 0.3048
                    depth_str = f"Well Depth: {max_depth:.1f} ft ({max_depth_m:.1f} m)"
                c.drawString(60, y_pos, depth_str)
                y_pos -= 15

            # Other parameters
            params = [
                f"Wire Speed: {self.speed} ft/min",
                f"Stuffing Box Friction: {self.stuffing_box} lbf",
                f"Wellhead Pressure: {self.pressure} psi",
                f"Safe Operating Load: {self.safe_operating_load}%",
                f"Friction Coefficient: {self.friction_coeff}"
            ]
            for param in params:
                c.drawString(60, y_pos, param)
                y_pos -= 15
            y_pos -= 10

            # Wireline Data Section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Wireline Data")
            c.setFont("Helvetica", 10)
            y_pos -= 20

            wire_data = [
                f"Diameter: {self.wire_diameter}\"",
                f"Weight: {self.wire_weight} {self.wire_weight_unit}",
                f"Breaking Strength: {self.breaking_strength} lbs"
            ]
            for data in wire_data:
                c.drawString(60, y_pos, data)
                y_pos -= 15
            y_pos -= 10

            # Tool String Section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Tool String")
            c.setFont("Helvetica", 10)
            y_pos -= 20

            # Calculate displacement volume
            tool_radius_ft = (self.tool_avg_diameter / 12) / 2
            tool_vol = math.pi * (tool_radius_ft ** 2) * self.tool_length
            displacement_gal = tool_vol * 7.48052  # ft³ to gallons

            tool_data = [
                f"Length: {self.tool_length} {'m' if self.use_metric else 'ft'}",
                f"Weight: {self.tool_weight} lbs",
                f"Displacement: {displacement_gal:.1f} gallons"
            ]
            for data in tool_data:
                c.drawString(60, y_pos, data)
                y_pos -= 15
            y_pos -= 10

            # Fluid Data Section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_pos, "Well Fluid Input")
            c.setFont("Helvetica", 10)
            y_pos -= 20

            fluid_level = self.fluid_level * (0.3048 if self.use_metric else 1)
            fluid_data = [
                f"Fluid Level: {fluid_level:.1f} {'m' if self.use_metric else 'ft'}",
                "Rheology Model: Newtonian",
                f"Density: {self.fluid_density} ppg"
            ]
            for data in fluid_data:
                c.drawString(60, y_pos, data)
                y_pos -= 15

            # Add Survey Data page(s)
            if self.trajectory_data and 'mds' in self.trajectory_data and \
                    'inclinations' in self.trajectory_data and hasattr(self, 'dls_values'):

                # Calculate how many rows fit per page
                rows_per_page = 45  # Adjust based on your font size and page layout
                mds = self.trajectory_data['mds']
                rows_per_page = len(mds)
                total_rows = len(mds)
                num_pages = math.ceil(total_rows / rows_per_page)

                for page_idx in range(num_pages):
                    c.showPage()
                    page_number += 1
                    draw_header(c, page_number, width, height)
                    draw_footer(c, page_number, width, height)

                    # Table title
                    y_pos = height - 100
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(width / 2, y_pos, "Survey Data")
                    c.line(width / 2 - 50, y_pos - 5, width / 2 + 50, y_pos - 5)
                    y_pos -= 30

                    # Column headers
                    col_widths = [100, 100, 100, 100]  # MD, Inclination, DLS
                    headers = ["MD ({})".format("m" if self.use_metric else "ft"),
                               "TVD ({})".format("m" if self.use_metric else "ft"),
                               "Inclination (°)",
                               "DLS (°/{})".format("30m" if self.use_metric else "100ft")]

                    # Draw header row
                    x_pos = 50
                    c.setFont("Helvetica-Bold", 10)
                    for i, header in enumerate(headers):
                        c.drawString(x_pos, y_pos, header)
                        x_pos += col_widths[i]

                    y_pos -= 20
                    c.line(50, y_pos, width - 50, y_pos)  # Header underline

                    # Draw table rows
                    c.setFont("Helvetica", 9)
                    start_row = page_idx * rows_per_page
                    end_row = min((page_idx + 1) * rows_per_page, total_rows)

                    print('mds:', mds)
                    print('tvds:', self.trajectory_data['tvd'])
                    for row_idx in range(start_row, end_row):
                        y_pos -= 15
                        if y_pos < 150:  # Prevent overlapping with footer
                            c.showPage()
                            page_number += 1
                            draw_header(c, page_number, width, height)
                            draw_footer(c, page_number, width, height)
                            y_pos = height - 80  # Reset Y position for new page

                        # Get data for current row
                        md = float(mds[row_idx])
                        tvd = float(self.trajectory_data['tvd'][row_idx])
                        incl = float(self.trajectory_data['inclinations'][row_idx])
                        dls = self.dls_values[row_idx] if row_idx < len(self.dls_values) else 0.0

                        # Format numbers
                        md_str = "{:.1f}".format(md)
                        tvd_str = "{:.1f}".format(tvd)
                        incl_str = "{:.1f}".format(incl)
                        dls_str = "{:.1f}".format(dls) if dls else "-"

                        # Draw cells
                        x_pos = 50
                        c.drawString(x_pos, y_pos, md_str)
                        x_pos += col_widths[0]
                        c.drawString(x_pos, y_pos, tvd_str)
                        x_pos += col_widths[1]
                        c.drawString(x_pos, y_pos, incl_str)
                        x_pos += col_widths[2]
                        c.drawString(x_pos, y_pos, dls_str)

                        # Draw row line
                        c.line(50, y_pos - 5, width - 50, y_pos - 5)

            c.save()

            # Cleanup temporary files
            if trajectory_img: os.remove(trajectory_img)
            if tension_img: os.remove(tension_img)
            if inclination_img: os.remove(inclination_img)
            if overpull_img: os.remove(overpull_img)

            self.update_btn.setText("Exported PDF!")
            QTimer.singleShot(2000, lambda: self.update_btn.setText("Update All Plots"))

        except Exception as e:
            print(f"Error exporting PDF: {e}")

    def add_text_section(self, canvas, text_lines, y_pos, width, height, page_number):
        """Adds formatted text section to PDF"""
        canvas.setFont("Helvetica", 10)

        canvas.setFont("Helvetica", 10)
        text_obj = canvas.beginText(50, y_pos)

        for line in text_lines:
            if line.startswith("•"):
                text_obj.setFont("Helvetica-Bold", 10)
                text_obj.textOut('• ')
                text_obj.setFont("Helvetica", 10)
                text_obj.textLine(line[2:])
            else:
                text_obj.textLine(line)

            y_pos -= 14  # Reduced spacing for better fit

        canvas.drawText(text_obj)
        return y_pos

    def get_info_text(self, section='all'):
        """Returns formatted text with bullet points and wrapping"""
        text_wrapper = textwrap.TextWrapper(width=90, break_long_words=False)

        sections = {
            'general': [
                self.speed_label.text(),
                self.pressure_label.text(),
                self.total_depth_label.text()
            ],
            'tension': [
                self.T1_label.text(),
                self.T2_label.text(),
                self.T5_label.text(),
                self.C1_label.text()
            ],
            'inclination': [
                self.max_incl_label.text(),
                self.max_dls_label.text(),
                self.MD1_label.text()
            ]
        }

        formatted = {}
        for key in sections:
            formatted[key] = []
            for text in sections[key]:
                wrapped = text_wrapper.wrap(text)
                formatted[key].append(f"• {wrapped[0]}")
                for line in wrapped[1:]:
                    formatted[key].append(f"  {line}")

        if section == 'all':
            return [item for sublist in formatted.values() for item in sublist]
        return formatted.get(section, [])

    def generate_plot_image(self, plot_type):
        """Generates a temporary image file for the specified plot without current markers"""
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)

        if plot_type == 'tension':
            if not hasattr(self, 'rih_weights') or not self.trajectory_data:
                return None
            mds = [float(md) for md in self.trajectory_data['mds']]
            ax.plot(self.rih_weights, mds, 'b-', label='RIH Tension')
            ax.plot(self.pooh_weights, mds, 'r-', label='POOH Tension')
            ax.set_xlabel("Tension (lbs)")
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
            ax.set_title("Tension vs Depth Profile")
            ax.set_ylim(float(mds[-1]), 0)
            ax.grid(True)
            ax.legend()

        elif plot_type == 'overpull':
            if not hasattr(self, 'max_overpulls'):
                return None
            mds = [float(md) for md in self.trajectory_data['mds']]
            ax.plot(self.max_overpulls, mds, 'r-', label='Max Overpull')
            ax.set_xlabel("Overpull (lbs)")
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
            ax.set_title("Maximum Overpull vs Depth")
            ax.set_ylim(float(mds[-1]), 0)
            ax.grid(True)
            ax.legend()

        elif plot_type == 'inclination':
            if not hasattr(self, 'trajectory_data'):
                return None
            mds = [float(md) for md in self.trajectory_data['mds']]
            incs = [float(inc) for inc in self.trajectory_data['inclinations']]

            ax.plot(incs, mds, 'b-', label='Inclination')
            ax.set_ylabel("Depth (m MD)" if self.use_metric else "Depth (ft MD)")
            ax.set_title("Inclination & DLS vs Depth")
            ax.grid(True)
            ax.set_ylim(float(mds[-1]), 0)

            # Add DLS
            ax2 = ax.twiny()
            if len(mds) > 1 and hasattr(self, 'dls_values'):
                dls = self.dls_values[1:]  # Skip first element
                depths = mds[:-1]
                ax2.step(dls, depths, 'r-', where='post', label='DLS')
            ax2.set_xlabel('DLS (°/30m)' if self.use_metric else 'DLS (°/100ft)')

            # Combine legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        else:
            return None

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        fig.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        return temp_file.name
