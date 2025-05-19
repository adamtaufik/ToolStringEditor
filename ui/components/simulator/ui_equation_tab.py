# ui_equation_tab.py
import math

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QScrollArea
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from features.simulator.calculations import calculate_wire_friction


class EquationTab(QWidget):
    def __init__(self, operation_tab, parent=None):
        super().__init__(parent)
        self.operation_tab = operation_tab
        self.setup_ui()
        # Update equations when tab is shown
        self.operation_tab.params_updated.connect(self.draw_equations)

    def setup_ui(self):
        self.figure = Figure(figsize=(12, 15))  # Wider figure to accommodate two columns
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.axis('off')

        self.draw_equations()

        canvas_wrapper = QWidget()
        canvas_layout = QVBoxLayout(canvas_wrapper)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.canvas)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(canvas_wrapper)

        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def showEvent(self, event):
        self.draw_equations()
        super().showEvent(event)

    def draw_equations(self):

        try:

            ax = self.ax
            ax.clear()
            ax.axis('off')

            if not hasattr(self.operation_tab, 'params') or not self.operation_tab.params:
                return

            if not self.operation_tab.params or not self.operation_tab.trajectory_data:
                self.ax.text(0.5, 0.5, "No data available", ha='center')
                self.canvas.draw()
                return

            params = self.operation_tab.params
            use_metric = self.operation_tab.use_metric
            current_depth = self.operation_tab.current_depth

            # Inclination (degrees)
            mds = [float(md) for md in self.operation_tab.trajectory_data['mds']]
            idx = np.argmin(np.abs(np.array(mds) - current_depth))

            # Cumulative Wire Friction (N)
            cumulative_friction, _ = calculate_wire_friction(
                self.operation_tab.trajectory_data, params, current_depth, use_metric
            )

            # Tool Volume (m³)
            tool_diameter_in = params['tool_avg_diameter']
            tool_diameter_ft = tool_diameter_in / 12
            tool_area_ft2 = math.pi * (tool_diameter_ft / 2) ** 2
            tool_length_ft = params['tool_length']
            tool_volume_gal = tool_area_ft2 * tool_length_ft * 7.48052

            # Wire Area (m²)
            wire_diameter = params['wire_diameter']
            A_wire_in2 = math.pi * (wire_diameter / 2) ** 2
            A_wire_ft2 = math.pi * (wire_diameter / 12 / 2) ** 2

            # Reynolds Number
            density_ppg = params['fluid_density']
            density_slug = density_ppg * 0.0160185
            density_ppcf = density_ppg * 0.13368
            speed_ftmin = self.operation_tab.speed
            speed_fts = speed_ftmin / 60
            dyn_viscosity = 0.00002093
            Re = density_slug * speed_fts * tool_diameter_ft / dyn_viscosity

            friction_coeff = params['friction_coeff']

            # Fluid Drag
            Cd = 0.82
            A_tool = np.pi * (tool_diameter_ft / 2) ** 2

            laminar_fd = 3 * np.pi * dyn_viscosity * tool_diameter_ft * speed_fts
            turbulent_fd = 0.5 * Cd * density_ppcf * A_tool * speed_fts**2


            # Depth
            if use_metric:
                L = current_depth
                wire_weight_per_length = params['wire_weight'] * 3.28084
            else:
                L = current_depth * 3.28084
                wire_weight_per_length = params['wire_weight']

            # Wire and Tool Weight
            tool_weight = params['tool_weight']
            wire_weight = wire_weight_per_length * L
            total_weight = tool_weight + wire_weight

            # Submerged Weight
            fluid_level = params['fluid_level']
            submerged = L >= fluid_level
            if submerged:
                submerged_length = L - fluid_level
            else:
                submerged_length = 0
                tool_volume_gal = 0

            wire_volume_submerged_gal = submerged_length * A_wire_ft2 * 7.48052
            Wb = (tool_volume_gal + wire_volume_submerged_gal) * density_ppg

            submerged_weight = total_weight - Wb

            theta = float(self.operation_tab.trajectory_data['inclinations'][idx])

            N = submerged_weight * np.sin(np.radians(theta))
            Ff = friction_coeff * N

            stuffing_box = params['stuffing_box']
            total_friction = Ff + cumulative_friction + stuffing_box

            Weff = submerged_weight * np.cos(np.radians(theta))

            # Pressure Force
            P = params['pressure']
            Fp = P * A_wire_in2

            T_pooh = max(Weff - Fp + total_friction + turbulent_fd, 0)
            T_rih = max(Weff - Fp - total_friction - turbulent_fd, 0)

            equations = [

                (r"\mathbf{Projected Area of Tool String:}",
                 r"A_{\text{tool face}} = \pi \left( \frac{D}{2} \right)^2",
                 # fr"A = \frac{{{tool_diameter_in:.3f}}}{{12}} \, \text{{in}} = \mathbf{{{tool_diameter_ft:.3f}}} \, \text{{ft}}",
                 fr"A_{{tool face}} = \pi \left( \frac{{{tool_diameter_ft:.3f}}}{{2}} \right)^2 = \mathbf{{{A_tool:.5f}}} \, \text{{ft}}^2"),

                (r"\mathbf{Fluid Drag Force:}",
                 r"F_d = \frac{1}{2} C_d \rho A v^2",
                 fr"F_d = \frac{{1}}{{2}} \times {Cd} \times {density_slug:.3f} \times {A_tool:.5f} \times {speed_fts:.2f}^2 = \mathbf{{{turbulent_fd:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Tool String + Wire Weight (in air):}",
                 r"W_{\text{air}} = W_{\text{air}} + w_{\text{wire}} \cdot L_{\text{wire}}",
                 fr"W_{{\text{{air}}}} = {tool_weight:.1f} + {wire_weight_per_length:.3f} \cdot {L:.1f} = \mathbf{{{total_weight:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Tool String Volume:}",
                 r"V_{\text{tool string}} = A_{\text{tool face}} \times L_{\text{tool}}",
                 fr"V_{{tool string}} = {A_tool:.3f} \times {tool_length_ft} \times {7.48052} \left( \frac{{gal}}{{ft^3}} \right) = \mathbf{{{tool_volume_gal:.3f}}} \, \text{{gal}}"),

                (r"\mathbf{Submerged Wire Length:}",
                 r"L_{\text{sub wire}} = L_{\text{submerged wire}} - Fluid Level",
                 fr"L_{{sub_wire}} = {L:.1f} - {fluid_level:.1f} = \mathbf{{{submerged_length:.1f}}} \, \text{{ft}}"),

                (r"\mathbf{Submerged Wire Volume:}",
                 r"A = \pi \left( \frac{D}{2} \right)^2",
                 fr"A = {submerged_length:.1f} \times {(A_wire_ft2):.5f} \times {7.48052} = \mathbf{{{wire_volume_submerged_gal:.3f}}} \, \text{{gal}}"),

                (r"\mathbf{Buoyancy Force:}",
                 r"F_b = V \cdot \rho_{\text{fluid}}",
                 fr"F_b = ({tool_volume_gal:.3f} + {wire_volume_submerged_gal:.3f}) \cdot {density_ppg:.3f} = \mathbf{{{Wb:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Submerged Weight:}",
                 r"W_{\text{sub}} = W_{\text{air}} - F_{\text{b}}",
                 fr"W_{{sub}} = {total_weight:.2f} - {Wb:.2f} = \mathbf{{{submerged_weight:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Normal Force:}",
                 r"N = W_{\text{sub}} \cdot \sin(\theta)",
                 fr"N = {submerged_weight:.2f} \cdot \sin({theta:.1f}^\circ) = \mathbf{{{N:.2f}}} \, \text{{N}}"),

                (r"\mathbf{Friction Force on Tool String:}",
                 r"F_f = \mu \cdot N",
                 fr"F_f = {friction_coeff} \cdot {N:.2f} = \mathbf{{{Ff:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Friction Force Along Wire:}",
                 r"F_f = \Sigma (Wire Weight \cdot \delta l \cdot \sin(\theta))",
                 fr"F_f = {cumulative_friction:.2f} \, \text{{lbf (computer calculated along trajectory)}}"),

                (r"\mathbf{Total Friction:}",
                 r"\Sigma F_f =  (Wire Weight \cdot \delta l \cdot \sin(\theta))",
                 fr"\Sigma F_f = {Ff:.2f} + {cumulative_friction:.2f} + {stuffing_box:.2f} = \mathbf{{{total_friction:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Effective Weight:}",
                 r"W_{\text{eff}} = W \cdot \cos(\theta)",
                 fr"W_{{\text{{eff}}}} = {submerged_weight:.2f} \cdot \cos({theta}^\circ) = \mathbf{{{Weff:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Pressure Force:}",
                 r"F_p = -P \cdot A_{\text{wire}}",
                 fr"F_p = -{P} \cdot {A_wire_in2:.5f} = \mathbf{{{Fp:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Tension (POOH):}",
                 r"T = \max\left(W_{\text{eff}} + F_p + F_f - \Sigma F_{f,\text{wire}} + F_d, 0\right)",
                 fr"T = \max({Weff:.2f} - {Fp:.2f} + {Ff:.2f} + {turbulent_fd:.5f}, 0) = \mathbf{{{T_pooh:.2f}}} \, \mathbf{{lbf}}"),

                (r"\mathbf{Tension (RIH):}",
                 r"T = \max\left(W_{\text{eff}} + F_p - F_f + \Sigma F_{f,\text{wire}} - F_d, 0\right)",
                 fr"T = \max({Weff:.2f} - {Fp:.2f} - {total_friction:.2f} - {turbulent_fd:.5f}, 0) = \mathbf{{{T_rih:.2f}}} \, \mathbf{{lbf}}"),
            ]

            spacing = 0.05
            split_index = (len(equations) + 1) // 2  # Split into two roughly equal parts
            equations_left = equations[:split_index]
            equations_right = equations[split_index:]

            # Draw left column equations
            for i, (title, general, substituted) in enumerate(equations_left):
                y = 1 - i * 2 * spacing
                ax.text(0.01, y, fr"${title} \quad {general}$", fontsize=9, va='top')
                ax.text(0.05, y - spacing, fr"${substituted}$", fontsize=8, va='top', color='gray')

            # Draw right column equations
            for j, (title, general, substituted) in enumerate(equations_right):
                y = 1 - j * 2 * spacing
                ax.text(0.5, y, fr"${title} \quad {general}$", fontsize=10, va='top')
                ax.text(0.54, y - spacing, fr"${substituted}$", fontsize=9, va='top', color='gray')

            # Adjust canvas height based on the longer column
            max_per_column = max(len(equations_left), len(equations_right))
            self.canvas.setMinimumHeight(100 + max_per_column * 70)
            self.canvas.draw()

        except Exception as e:
            print(e)