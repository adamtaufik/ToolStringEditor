# ui_equation_tab.py
import math
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QScrollArea
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from features.simulator.calculations import calculate_wire_friction

class EquationTab(QWidget):
    def __init__(self, operation_tab, parent=None):
        super().__init__(parent)
        self.operation_tab = operation_tab
        self.operation_tab.destroyed.connect(self.on_operation_tab_destroyed)
        self.setup_ui()
        self.operation_tab.params_updated.connect(self.full_calculation)

    def setup_ui(self):
        self.figure = Figure(figsize=(30, 30))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.axis('off')
        self.full_calculation()
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
        self.full_calculation()
        super().showEvent(event)

    def on_operation_tab_destroyed(self):
        self.operation_tab = None  # Clear reference

    def closeEvent(self, event):
        plt.close(self.figure)
        self.canvas = None
        super().closeEvent(event)

    def full_calculation(self, draw = True, current_depth = None):
        if not self.operation_tab:  # Check if OperationTab is alive
            return

        try:
            self.ax.clear()
            self.ax.axis('off')
            if not hasattr(self.operation_tab, 'params') or not self.operation_tab.params:
                return
            if not self.operation_tab.params or not self.operation_tab.trajectory_data:
                self.ax.text(0.5, 0.5, "No data available", ha='center')
                self.canvas.draw()
                return

            params = self.operation_tab.params
            use_metric = self.operation_tab.use_metric
            if current_depth is None:
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
            friction_coeff = params['friction_coeff']

            # Fluid Drag
            Cd = 0.82
            A_tool = np.pi * (tool_diameter_ft / 2) ** 2

            laminar_fd = 3 * np.pi * dyn_viscosity * tool_diameter_ft * speed_fts
            turbulent_fd = 0.5 * Cd * density_ppcf * A_tool * speed_fts**2


            # toprint = 'wire_weight'
            # print(toprint)
            # print(params[toprint])
            # Depth
            if use_metric:
                L = current_depth
                wire_weight_per_length = params['wire_weight']
            else:
                L = current_depth * 3.28084
                wire_weight_per_length = params['wire_weight']

            # Wire and Tool Weight
            tool_weight = params['tool_weight']
            wire_weight = wire_weight_per_length * L
            total_weight = tool_weight + wire_weight

            # Submerged Weight
            fluid_level = params['fluid_level']
            if use_metric:
                fluid_level *= 3.28084

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

            if draw:

                # Parameter conversions
                tool_diameter_in = params['tool_avg_diameter']
                tool_diameter = tool_diameter_in
                tool_diameter_unit = "in"

                wire_diameter = params['wire_diameter']
                wire_diameter_unit = "in"

                fluid_density = params['fluid_density'] * 119.826 if use_metric else params['fluid_density']
                fluid_density_unit = "kg/m³" if use_metric else "ppg"

                stuffing_box = params['stuffing_box']
                stuffing_box_unit = "lbf"

                tool_length = params['tool_length'] * 0.3048 if use_metric else params['tool_length']
                tool_length_unit = "m" if use_metric else "ft"

                tool_weight = params['tool_weight']
                tool_weight_unit = "lbf"

                fluid_level = params['fluid_level']
                fluid_level_unit = "m" if use_metric else "ft"

                pressure = params['pressure']
                pressure_unit = "psi"

                current_depth_unit = "m" if use_metric else "ft"
                speed = self.operation_tab.speed * 0.3048 if use_metric else self.operation_tab.speed
                speed_unit = "m/min" if use_metric else "ft/min"

                parameters = [
                    (r"Tool Diameter", r"D_{tool}", f"{tool_diameter:.3f}", tool_diameter_unit),
                    (r"Wire Diameter", r"D_{wire}", f"{wire_diameter:.3f}", wire_diameter_unit),
                    (r"Fluid Density", r"\rho_{\text{fluid}}", f"{fluid_density:.2f}", fluid_density_unit),
                    (r"Friction Coeff.", r"\mu", f"{params['friction_coeff']:.2f}", ""),
                    (r"Stuffing Box", r"F_{stuff}", f"{stuffing_box:.2f}", stuffing_box_unit),
                    (r"Tool Length", r"L_{tool}", f"{tool_length:.1f}", tool_length_unit),
                    (r"Tool Weight", r"W_{tool}", f"{tool_weight:.2f}", tool_weight_unit),
                    (r"Fluid Level", r"L_{fluid}", f"{fluid_level:.2f}", fluid_level_unit),
                    (r"Pressure", r"P", f"{pressure:.2f}", pressure_unit),
                    (r"Current Depth", r"L_{depth}", f"{current_depth:.2f}", current_depth_unit),
                    (r"Running Speed", r"v", f"{speed:.2f}", speed_unit),
                ]

                # Draw parameters in left column
                y_param = 1
                param_spacing = 0.06

                # Add section titles and separator line
                self.ax.text(-0.1, 1.1, r"$\mathbf{Parameters}$", fontsize=12, va='top', ha='left')
                self.ax.text(0.25, 1.1, r"$\mathbf{Calculations}$", fontsize=12, va='top', ha='center')

                # Draw parameters
                for name, symbol, value, unit in parameters:
                    text = fr"$\mathbf{{{name}}}$: ${symbol} = {value}\, \text{{{unit}}}$" if unit else fr"$\mathbf{{{name}}}$: ${symbol} = {value}$"
                    self.ax.text(-0.1, y_param, text, fontsize=9, va='top')
                    y_param -= param_spacing

                # Add converted parameters if use_metric is True
                if use_metric:
                    # Calculate converted values

                    tool_length /= 0.3048
                    fluid_level /= 0.3048
                    current_depth *= 3.28084
                    speed /= 0.3048
                    fluid_density /= 119.826

                    converted_parameters = [
                        (r"Tool Length", r"L_{tool,ft}", f"{tool_length:.1f}", "ft"),
                        (r"Fluid Level", r"L_{fluid,ft}", f"{fluid_level:.1f}", "ft"),
                        (r"Current Depth", r"L_{depth,ft}", f"{current_depth:.1f}", "ft"),
                        (r"Running Speed", r"v_{ft/min}", f"{speed:.2f}", "ft/min"),
                        (r"Fluid Density", r"\rho_{\text{fluid},ppg}", f"{fluid_density:.2f}", "ppg"),
                    ]

                    # Add converted parameters section title
                    y_param -= param_spacing * 0.5  # Space before the section title
                    self.ax.text(-0.1, y_param, "Converted Values", fontsize=10, va='top', ha='left')
                    y_param -= param_spacing

                    # Draw converted parameters
                    for name, symbol, value, unit in converted_parameters:
                        text = fr"$\mathbf{{{name}}}$: ${symbol} = {value}\, \text{{{unit}}}$"
                        self.ax.text(-0.1, y_param, text, fontsize=9, va='top', color='dimgray')
                        y_param -= param_spacing

                # Adjust separator line height based on use_metric
                separator_ymax = 3
                self.ax.axvline(x=0.175, ymin=0, ymax=separator_ymax, color='gray', linestyle='-', linewidth=0.5)

                equations = [

                    (r"\mathbf{Projected Area of Tool String:}",
                     r"A_{\text{tool face}} = \pi \left( \frac{D}{2} \right)^2",
                     fr"A_{{tool face}} = \pi \left( \frac{{{tool_diameter_ft:.3f}}}{{2}} \right)^2 = \mathbf{{{A_tool:.5f}}} \, \text{{ft}}^2"),

                    (r"\mathbf{Fluid Drag Force:}",
                     r"F_d = \frac{1}{2} C_d \rho_{\text{fluid}} A v^2",
                     fr"F_d = \frac{{1}}{{2}} \times {Cd} \times {density_slug:.3f} \times {A_tool:.5f} \times {speed_fts:.2f}^2 = \mathbf{{{turbulent_fd:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Tool String + Wire Weight (in air):}",
                     r"W_{\text{air}} = W_{\text{air}} + w_{\text{wire}} \cdot L_{\text{wire}}",
                     fr"W_{{\text{{air}}}} = {tool_weight:.1f} + {wire_weight_per_length:.3f} \cdot {L:.1f} = \mathbf{{{total_weight:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Tool String Volume:}",
                     r"V_{\text{tool string}} = A_{\text{tool face}} \times L_{\text{tool}}",
                     fr"V_{{tool string}} = {A_tool:.3f} \times {tool_length_ft} \times {7.48052} \left( \frac{{gal}}{{ft^3}} \right) = \mathbf{{{tool_volume_gal:.3f}}} \, \text{{gal}}"),

                    (r"\mathbf{Submerged Wire Length:}",
                     r"L_{\text{wire,sub}} = L_{\text{wire,sub}} - Fluid Level",
                     fr"L_{{wire,sub}} = {L:.1f} - {fluid_level:.1f} = \mathbf{{{submerged_length:.1f}}} \, \text{{ft}}"),

                    (r"\mathbf{Submerged Wire Volume:}",
                     r"V_{wire,sub} = \pi \left( \frac{D}{2} \right)^2 \times A_{wire}",
                     fr"V_{{wire,sub}} = {submerged_length:.1f} \times {A_wire_ft2:.5f} \times {7.48052} = \mathbf{{{wire_volume_submerged_gal:.3f}}} \, \text{{gal}}"),

                    (r"\mathbf{Buoyancy Force:}",
                     r"F_b = (V_{\text{tool string}} + V_{wire,sub}) \cdot \rho_{\text{fluid}}",
                     fr"F_b = ({tool_volume_gal:.3f} + {wire_volume_submerged_gal:.3f}) \cdot {density_ppg:.3f} = \mathbf{{{Wb:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Submerged Weight:}",
                     r"W_{\text{sub}} = W_{\text{air}} - F_{\text{b}}",
                     fr"W_{{sub}} = {total_weight:.2f} - {Wb:.2f} = \mathbf{{{submerged_weight:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Effective Weight:}",
                     r"W_{\text{eff}} = W_{\text{sub}} \cdot \cos(\theta)",
                     fr"W_{{\text{{eff}}}} = {submerged_weight:.2f} \cdot \cos({theta}^\circ) = \mathbf{{{Weff:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Normal Force:}",
                     r"N = W_{\text{sub}} \cdot \sin(\theta)",
                     fr"N = {submerged_weight:.2f} \cdot \sin({theta:.1f}^\circ) = \mathbf{{{N:.2f}}} \, \text{{N}}"),

                    (r"\mathbf{Friction Force on Tool String:}",
                     r"F_{f,tool string} = \mu \cdot N",
                     fr"F_{{f,tool string}} = {friction_coeff} \cdot {N:.2f} = \mathbf{{{Ff:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Friction Force Along Wire:}",
                     r"F_{f,wire} = \Sigma (Wire Weight \cdot \delta l \cdot \sin(\theta))",
                     fr"F_{{f,wire}} = {cumulative_friction:.2f} \, \text{{lbf (computer calculated along trajectory)}}"),

                    (r"\mathbf{Total Friction:}",
                     r"\Sigma F_f = F_{f,wire} + F_{f,tool string} + F_{f,stuffing box}",
                     fr"\Sigma F_f = {Ff:.2f} + {cumulative_friction:.2f} + {stuffing_box:.2f} = \mathbf{{{total_friction:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Pressure Force:}",
                     r"F_p = -P \cdot A_{\text{wire}}",
                     fr"F_p = -{P} \cdot {A_wire_in2:.5f} = \mathbf{{{Fp:.2f}}} \, \text{{lbf}}"),

                    (r"\mathbf{Tension (POOH):}",
                     r"T = \max\left(W_{\text{eff}} - F_p + \Sigma F_f + F_d, 0\right)",
                     fr"T = \max({Weff:.2f} - {Fp:.2f} + {Ff:.2f} + {turbulent_fd:.5f}, 0) = \mathbf{{{T_pooh:.2f}}} \, \mathbf{{lbf}}"),

                    (r"\mathbf{Tension (RIH):}",
                     r"T = \max\left(W_{\text{eff}} - F_p - \Sigma F_f - F_d, 0\right)",
                     fr"T = \max({Weff:.2f} - {Fp:.2f} - {total_friction:.2f} - {turbulent_fd:.5f}, 0) = \mathbf{{{T_rih:.2f}}} \, \mathbf{{lbf}}"),
                ]

                # Split equations into columns and draw
                split_index = (len(equations) + 1) // 2
                equations_left = equations[:split_index]
                equations_right = equations[split_index:]

                # Draw equations in middle and right columns
                spacing = 0.07
                mini_spacing = 0.06
                for i, (title, general, substituted) in enumerate(equations_left):
                    y = 1 - i * 2 * spacing
                    self.ax.text(0.2, y, fr"${title} \quad {general}$", fontsize=9, va='top')
                    self.ax.text(0.25, y - mini_spacing, fr"${substituted}$", fontsize=8, va='top', color='gray')

                for j, (title, general, substituted) in enumerate(equations_right):
                    y = 1 - j * 2 * spacing
                    self.ax.text(0.65, y, fr"${title} \quad {general}$", fontsize=9, va='top')
                    self.ax.text(0.7, y - mini_spacing, fr"${substituted}$", fontsize=8, va='top', color='gray')

                self.canvas.setMinimumHeight(100 + max(len(parameters), len(equations)) * 10)
                self.canvas.draw()

            else:
                return T_rih, T_pooh

        except Exception as e:
            print(f"Error drawing equations: {e}")