# ui_simulator_app.py
import math

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QTimer

from features.simulator.calculations import calculate_wire_friction
from ui.components.simulator.ui_equation_tab import EquationTab
from ui.components.simulator.ui_operation_tab import OperationTab
from ui.components.simulator.ui_input_tab import InputTab
from ui.components.simulator.ui_results_tab import PlotsTab
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.theme_manager import toggle_theme, apply_theme


class WirelineSimulatorApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.visualization_params = None
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
        self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(), "Wireline Operations Simulator")
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
        self.create_input_tab()
        self.create_main_operation_tab()
        self.create_plots_tab()
        self.create_equation_tab()
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
        self.max_depth = 100

        # Default values for wire and tool
        self.tool_weight = 150

        # Fluid properties
        self.fluid_density = 8.5  # ppg
        self.buoyancy_factor = 1 - (self.fluid_density / 65.4)
        self.pressure = 500  # psi
        self.FRICTION_COEFF = 0.3

        # Initialize trajectory data with default vertical well
        self.initial_trajectory()


    def create_input_tab(self):
        """Create input tab using the new component"""
        self.input_tab = InputTab()
        try:
            # self.input_tab.units_toggled.connect(self.handle_new_trajectory)
            self.input_tab.trajectory_updated.connect(self.handle_new_trajectory)
        except Exception as e:
            print('Create input error:',e)
        self.tabs.addTab(self.input_tab, "Input Panel")

    def create_main_operation_tab(self):
        """Create the main operation tab using the new component"""
        self.operation_tab = OperationTab(self)
        self.operation_tab.operationChanged.connect(self.handle_operation_change)
        self.operation_tab.speedChanged.connect(self.handle_speed_change)
        self.tabs.addTab(self.operation_tab, "Operation View")

    def create_plots_tab(self):
        self.plots_tab = PlotsTab(self)
        self.plots_tab.updateRequested.connect(self.handle_plots_update)
        self.tabs.addTab(self.plots_tab, "Results")

    def create_equation_tab(self):
        try:
            self.equation_tab = EquationTab(self.operation_tab)
        except Exception as e:
            print(e)
        self.tabs.addTab(self.equation_tab, "Calculations")

    def initial_trajectory(self):

        mds = list(range(0, 4000, 20))  # 0-1000 ft in 100 ft increments
        tvd = []
        north = []
        east = []
        inclinations = []
        dls_list = []
        azimuths = []

        # Trajectory parameters
        ko_point = 800  # Kickoff at 5000 ft
        build_rate = 0.5  # 2°/100 ft
        target_inc = 30  # Final inclination
        azimuth = 45.0  # Constant azimuth

        # Initialize tracking variables WITH VERTICAL SECTION VALUES
        current_tvd = 0.0
        current_north = 0.0
        current_east = 0.0
        current_inc = 0.0
        current_dls = 0.0

        for md in mds:
            if current_inc < target_inc and md > ko_point:
                current_inc = min(current_inc + build_rate, target_inc)

            # Convert angles to radians
            inc_rad = math.radians(current_inc)
            az_rad = math.radians(azimuth)

            # Calculate true vertical depth component
            delta_tvd = 20 * math.cos(inc_rad)
            current_tvd += delta_tvd

            # Calculate horizontal displacement
            delta_horizontal = 20 * math.sin(inc_rad)
            delta_north = delta_horizontal * math.cos(az_rad)
            delta_east = delta_horizontal * math.sin(az_rad)
            current_north += delta_north
            current_east += delta_east

            # Store values
            tvd.append(round(current_tvd, 2))
            north.append(round(current_north, 2))
            east.append(round(current_east, 2))
            inclinations.append(current_inc)
            dls_list.append(current_dls)

            azimuths.append(azimuth)

        self.trajectory_data = {
            'mds': mds,
            'tvd': [round(x, 2) for x in tvd],  # Rounded for readability
            'inclinations': inclinations,
            'dls_list': dls_list,
            'azimuths': azimuths,
            'north': [round(x, 2) for x in north],
            'east': [round(x, 2) for x in east]
        }

        self.operation_tab.update_trajectory_view(self.trajectory_data, self.input_tab.fluid_level_input.value())
        self.operation_tab.update_visualizations(
            current_depth=self.current_depth,
            params=self.visualization_params,
            operation=self.operation
        )

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )

    def handle_new_trajectory(self, trajectory_data):
        self.trajectory_data = trajectory_data

    def handle_operation_change(self, operation):
        if operation == "RIH":
            self.start_rih()
        elif operation == "POOH":
            self.start_pooh()
        else:
            self.stop_movement()

    def handle_speed_change(self, speed):
        self.sim_speed = speed / 60  # Convert ft/min to ft/sec

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

    def update_simulation(self):
        """Update the simulation state with all safety checks and visualization updates"""
        try:
            # Check for valid trajectory data
            if not hasattr(self, 'trajectory_data') or not self.trajectory_data['mds']:
                return

            if not hasattr(self, '_update_counter'):
                self._update_counter = 0

            # Get current operation parameters
            max_depth = self.trajectory_data['mds'][-1]
            speed = self.operation_tab.speed_slider.value() * self.sim_speed  # ft/min * speed multiplier

            # Update depth based on operation
            if self.operation == "RIH":
                self.current_depth += speed / 600  # Convert ft/min to ft per 100ms
                self.current_depth = min(self.current_depth, max_depth)
            elif self.operation == "POOH":
                self.current_depth -= speed / 600
                self.current_depth = max(0, self.current_depth)

            # Prepare parameters for visualization
            self.visualization_params = {
                'fluid_density': self.input_tab.fluid_density_input.value(),
                'pressure': self.input_tab.pressure_input.value(),
                'tool_weight': self.input_tab.tool_weight_input.value(),
                'tool_avg_diameter': self.input_tab.tool_avg_diameter_input.value(),
                'tool_length': self.input_tab.tool_length_input.value(),
                'stuffing_box': self.input_tab.stuffing_box_input.value(),
                'friction_coeff': self.input_tab.friction_input.value(),
                'wire_diameter': self.input_tab.wire_diameter,
                'wire_weight': self.input_tab.wire_weight,
                'fluid_level': self.input_tab.fluid_level_input.value(),
                'buoyancy_factor': 1 - (self.input_tab.fluid_density_input.value() / 65.4)
            }

            # Update all visualizations through the operation tab
            self.operation_tab.update_visualizations(
                current_depth=self.current_depth,
                params=self.visualization_params,
                operation=self.operation
            )

            # Only update plots tab every 5 frames
            if self._update_counter % 5 == 0:
                self.handle_plots_update()

            self._update_counter += 1

        except Exception as e:
            print(f"Simulation Error: {str(e)}")
            self.sim_timer.stop()
            QMessageBox.critical(self, "Simulation Error",
                                 f"An error occurred:\n{str(e)}")

    # Add handler for plot updates
    def handle_plots_update(self):
        params = {
            'speed': self.sim_speed * 60,
            'tool_weight': self.input_tab.tool_weight_input.value(),
            'tool_avg_diameter': self.input_tab.tool_avg_diameter_input.value(),
            'tool_length': self.input_tab.tool_length_input.value(),
            'stuffing_box': self.input_tab.stuffing_box_input.value(),
            'wire_weight': self.input_tab.wire_weight,
            'breaking_strength': self.input_tab.breaking_strength,
            'wire_diameter': self.input_tab.wire_diameter,
            'safe_operating_load': self.input_tab.safe_operating_load_input.value(),
            'fluid_density': self.input_tab.fluid_density_input.value(),
            'fluid_level': self.input_tab.fluid_level_input.value(),
            'pressure': self.input_tab.pressure_input.value(),
            'friction_coeff': self.input_tab.friction_input.value(),
            'current_depth': self.current_depth
        }
        self.plots_tab.update_plots(self.trajectory_data, params)
