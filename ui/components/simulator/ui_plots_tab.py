import textwrap
import numpy as np
import mplcursors
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QApplication, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import tempfile

from features.simulator import plot
from features.simulator.export import PDFExporter


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
        self.params = {}

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
        self.export_btn.clicked.connect(self.handle_export_click)

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

        if not params:  # Add parameter validation
            print("Error: No parameters provided")
            return

        self.params = params.copy()

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

        self.rih_weights, self.pooh_weights, self.depth_points_tension = plot.plot_tension(
            self.trajectory_data,
            self.params,
            self.current_depth,
            self.use_metric,
            self.tension_canvas
        )

        # Setup tension plot cursors
        ax = self.tension_canvas.figure.axes[0]
        self.rih_line = ax.lines[0]
        self.pooh_line = ax.lines[1]

        cursor_rih = mplcursors.cursor(self.rih_line, hover=True)

        @cursor_rih.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                text = f'RIH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m'
            else:
                text = f'RIH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft'
            sel.annotation.set_text(text)

        cursor_pooh = mplcursors.cursor(self.pooh_line, hover=True)

        @cursor_pooh.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                text = f'POOH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m'
            else:
                text = f'POOH: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft'
            sel.annotation.set_text(text)

        # Update overpull plot
        self.max_overpulls = plot.plot_overpull(
            self.pooh_weights,
            self.depth_points_tension,
            self.breaking_strength,
            self.safe_operating_load,
            self.current_depth,
            self.use_metric,
            self.overpull_canvas
        )

        # Setup overpull cursor
        ax_overpull = self.overpull_canvas.figure.axes[0]
        overpull_line = ax_overpull.lines[0]
        cursor_overpull = mplcursors.cursor(overpull_line, hover=True)

        @cursor_overpull.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                text = f'Overpull: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} m'
            else:
                text = f'Overpull: {sel.target[0]:.1f} lbs\nDepth: {depth:.1f} ft'
            sel.annotation.set_text(text)

        # Update inclination plot
        self.dls_values = plot.plot_inclination_dls(
            self.trajectory_data,
            self.use_metric,
            self.current_depth,
            self.incl_canvas
        )

        # Setup inclination/DLS cursors
        ax_incl = self.incl_canvas.figure.axes[0]
        incl_line = ax_incl.lines[0]
        cursor_incl = mplcursors.cursor(incl_line, hover=True)

        @cursor_incl.connect("add")
        def _(sel):
            depth = sel.target[1]
            if self.use_metric:
                text = f'Inclination: {sel.target[0]:.1f}°\nDepth: {depth:.1f} m'
            else:
                text = f'Inclination: {sel.target[0]:.1f}°\nDepth: {depth:.1f} ft'
            sel.annotation.set_text(text)

        ax_dls = self.incl_canvas.figure.axes[0].twiny()
        dls_line = ax_dls.lines[0] if ax_dls.lines else None
        if dls_line:
            cursor_dls = mplcursors.cursor(dls_line, hover=True)

            @cursor_dls.connect("add")
            def _(sel):
                depth = sel.target[1]
                if self.use_metric:
                    text = f'DLS: {sel.target[0]:.1f}°/30m\nDepth: {depth:.1f} m'
                else:
                    text = f'DLS: {sel.target[0]:.1f}°/100ft\nDepth: {depth:.1f} ft'
                sel.annotation.set_text(text)

        self.update_info_labels()


    def update_info_labels(self):

        if not hasattr(self, 'params') or not self.params:
            return  # Don't crash if params not loaded

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

    # Add this method to PlotsTab:
    def handle_export_click(self):
        exporter = PDFExporter(self)
        exporter.export_to_pdf(
            self.trajectory_data,
            self.params,
            self.use_metric,
            self.generate_trajectory_image,
            self.generate_plot_image,
            self.get_info_text,
            self.dls_values
        )


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