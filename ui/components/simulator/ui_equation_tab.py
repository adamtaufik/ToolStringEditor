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


            # Speed (ft/min or m/min to m/s)
            if use_metric:
                v = (self.operation_tab.speed / 3.28084) / 60  # Convert m/min to m/s
            else:
                v = self.operation_tab.speed * 0.00508  # ft/min to m/s

            # Tool Diameter (inches to meters)
            D = params['tool_avg_diameter'] * 0.0254

            # Viscosity (fixed as per calculations.py)
            mu = 0.001002  # Pa·s


            # Steel Density (kg/m³)
            rho_steel = 7850


            # Wire Weight (N/m)
            if use_metric:
                w = params['wire_weight'] * 4.44822  # lbs/m to N/m
            else:
                w = params['wire_weight'] * 14.5939  # lbs/ft to N/m

            # Depth (meters)
            L = current_depth if use_metric else current_depth * 0.3048

            # Inclination (degrees)
            mds = [float(md) for md in self.operation_tab.trajectory_data['mds']]
            idx = np.argmin(np.abs(np.array(mds) - current_depth))
            theta = float(self.operation_tab.trajectory_data['inclinations'][idx])

            # Tool Weight (N)
            W = params['tool_weight'] * 4.44822  # lbs to N

            # Pressure (Pa)
            P = params['pressure'] * 6894.76  # psi to Pa

            # Wire Area (m²)
            wire_diameter = params['wire_diameter'] * 0.0254
            A_wire = math.pi * (wire_diameter / 2) ** 2

            # Cumulative Wire Friction (N)
            cumulative_friction, _ = calculate_wire_friction(
                self.operation_tab.trajectory_data, params, current_depth, use_metric
            )
            Ff_wire = cumulative_friction * 4.44822  # lbs to N

            vals = {
                'v': v,
                'D': D,
                'mu': mu,
                'rho_steel': rho_steel,
                'w': w,
                'L': L,
                'theta': theta,
                'W': W,
                'P': P,
                'A_wire': A_wire,
                'Ff_wire': Ff_wire
            }



            # Reynolds Number
            density_ppg = params['fluid_density']
            density_slug = density_ppg * 0.0160185
            density_ppcf = density_ppg * 0.13368
            speed_ftmin = self.operation_tab.speed
            speed_fts = speed_ftmin / 60
            tool_diameter_in = params['tool_avg_diameter']
            tool_diameter_ft = tool_diameter_in / 12
            dyn_viscosity = 0.00002093
            Re = density_slug * speed_fts * tool_diameter_ft / dyn_viscosity

            friction_coeff = params['friction_coeff']

            # Fluid Drag
            Cd = 0.82
            A_tool = np.pi * (tool_diameter_ft / 2) ** 2

            laminar_fd = 3 * np.pi * dyn_viscosity * tool_diameter_ft * speed_fts
            turbulent_fd = 0.5 * Cd * density_ppcf * A_tool * speed_fts**2

            BF = 1 - (density_ppg / 65.4)

            # Tool Volume (m³)
            tool_area_ft2 = math.pi * (tool_diameter_ft / 2) ** 2
            tool_length_ft = params['tool_length']
            tool_volume_gal = tool_area_ft2 * tool_length_ft * 7.48052
            Wb = tool_volume_gal * density_ppg
            # wire_weight = vals['w'] * vals['L'] * BF
            # N = vals['W'] * np.sin(np.radians(vals['theta']))
            # Ff = vals['mu_friction'] * N
            # Weff = vals['W'] * np.cos(np.radians(vals['theta']))
            # Fp = -vals['P'] * vals['A_wire']
            # T_pooh = max(Weff + Fp + Ff - vals['Ff_wire'] + laminar_fd, 0)
            # T_rih = max(Weff + Fp - Ff + vals['Ff_wire'] - laminar_fd, 0)

            equations = [
                # (r"\mathbf{Reynolds Number:}",
                #  r"Re = \frac{\rho v D}{\mu}",
                #  fr"Re = \frac{{{density_slug:.1f} \times {speed_fts:.1f} \times {tool_diameter_ft:.3f}}}{{{dyn_viscosity}}} = \mathbf{{{Re:.0f}}}"),

                (r"\mathbf{Projected Area:}",
                 r"A = \pi \left( \frac{D}{2} \right)^2",
                 # fr"A = \frac{{{tool_diameter_in:.3f}}}{{12}} \, \text{{in}} = \mathbf{{{tool_diameter_ft:.3f}}} \, \text{{ft}}",
                 fr"A = \pi \left( \frac{{{tool_diameter_ft:.3f}}}{{2}} \right)^2 = \mathbf{{{A_tool:.5f}}} \, \text{{ft}}^2"),

                # (r"\mathbf{Laminar Drag Force:}",
                #  r"F_d = 3 \pi \mu D v",
                #  fr"F_d = 3 \times \pi \times {dyn_viscosity} \times {tool_diameter_ft:.1f} \times {speed_fts} = \mathbf{{{laminar_fd:.5f}}} \, \text{{lbf}}"),

                (r"\mathbf{Fluid Drag Force:}",
                 r"F_d = \frac{1}{2} C_d \rho A v^2",
                 fr"F_d = \frac{{1}}{{2}} \times {Cd} \times {density_slug:.3f} \times {A_tool:.5f} \times {speed_fts:.2f}^2 = \mathbf{{{turbulent_fd:.2f}}} \, \text{{lbf}}"),

                (r"\mathbf{Buoyancy Factor:}",
                 r"BF = 1 - \frac{\rho_{\text{fluid}}}{\rho_{\text{steel}}}",
                 fr"BF = 1 - \frac{{{density_ppg}}}{{{65.4}}} = \mathbf{{{BF:.4f}}}"),

                (r"\mathbf{Tool Buoyancy Weight:}",
                 r"W_b = V \cdot \rho_{\text{fluid}}",
                 fr"W_b = {tool_volume_gal:.1f} \cdot {density_ppg:.3f} = \mathbf{{{Wb:.2f}}} \, \text{{lbf}}"),

                # To check ------------------------------------------------------

                # (r"\mathbf{Wire Weight Submerged:}",
                #  r"W_{\text{wire}} = w \cdot L \cdot BF",
                #  fr"W_{{\text{{wire}}}} = {vals['w']} \cdot {vals['L']} \cdot {BF:.4f} = \mathbf{{{wire_weight:.2f}}} \, \text{{N}}"),

                # (r"\mathbf{Normal Force:}",
                #  r"N = W \cdot \sin(\theta)",
                #  fr"N = {vals['W']} \cdot \sin({vals['theta']}^\circ) = \mathbf{{{N:.2f}}} \, \text{{N}}"),
                #
                # (r"\mathbf{Friction Force:}",
                #  r"F_f = \mu \cdot N",
                #  fr"F_f = {friction_coeff} \cdot {N:.2f} = \mathbf{{{Ff:.2f}}} \, \text{{N}}"),

                # (r"\mathbf{Effective Weight:}",
                #  r"W_{\text{eff}} = W \cdot \cos(\theta)",
                #  fr"W_{{\text{{eff}}}} = {vals['W']} \cdot \cos({vals['theta']}^\circ) = \mathbf{{{Weff:.2f}}} \, \text{{N}}"),

                # (r"\mathbf{Pressure Force:}",
                #  r"F_p = -P \cdot A_{\text{wire}}",
                #  fr"F_p = -{vals['P']} \cdot {vals['A_wire']} = \mathbf{{{Fp:.2f}}} \, \text{{N}}"),
                #
                # (r"\mathbf{Tension (POOH):}",
                #  r"T = \max\left(W_{\text{eff}} + F_p + F_f - \Sigma F_{f,\text{wire}} + F_d, 0\right)",
                #  fr"T = \max({Weff:.2f} + {Fp:.2f} + {Ff:.2f} - {vals['Ff_wire']} + {laminar_fd:.5f}, 0) = \mathbf{{{T_pooh:.2f}}} \, \mathbf{{N}}"),
                #
                # (r"\mathbf{Tension (RIH):}",
                #  r"T = \max\left(W_{\text{eff}} + F_p - F_f + \Sigma F_{f,\text{wire}} - F_d, 0\right)",
                #  fr"T = \max({Weff:.2f} + {Fp:.2f} - {Ff:.2f} + {vals['Ff_wire']} - {laminar_fd:.5f}, 0) = \mathbf{{{T_rih:.2f}}} \, \mathbf{{N}}"),
            ]

            spacing = 0.07
            split_index = (len(equations) + 1) // 2  # Split into two roughly equal parts
            equations_left = equations[:split_index]
            equations_right = equations[split_index:]

            # Draw left column equations
            for i, (title, general, substituted) in enumerate(equations_left):
                y = 1 - i * 2 * spacing
                ax.text(0.01, y, fr"${title} \quad {general}$", fontsize=10, va='top')
                ax.text(0.05, y - spacing, fr"${substituted}$", fontsize=9, va='top', color='gray')

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