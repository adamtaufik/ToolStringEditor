"""
Core simulation engine with timer-based updates
"""
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from .calculations import SimulationParameters, calculate_tension
from .data_models import WellTrajectory


class WirelineSimulator(QObject):
    simulation_updated = pyqtSignal(float, float, dict)  # depth, tension, breakdown
    simulation_stopped = pyqtSignal()
    trajectory_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.trajectory: Optional[WellTrajectory] = None
        self.params = SimulationParameters(
            wire_diameter=0.108,
            wire_weight=0.021,
            tool_weight=150,
            fluid_density=8.5,
            fluid_level=300,
            well_pressure=500,
            friction_coeff=0.3
        )
        self.current_depth = 0.0
        self.operation = None
        self.last_operation = None
        self.speed = 60  # ft/min
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)

    def set_trajectory(self, trajectory: WellTrajectory):
        self.trajectory = trajectory
        self.trajectory_changed.emit()
        self.current_depth = 0.0

    def set_parameters(self, params: SimulationParameters):
        self.params = params

    def start_operation(self, operation: str):
        if self.operation == operation:
            return

        self.operation = operation
        interval = int(60000 / (self.speed * 10))  # ms per 0.1 ft
        self.timer.start(interval)

    def stop_operation(self):
        self.timer.stop()
        self.last_operation = self.operation
        self.operation = None
        self.simulation_stopped.emit()

    def update_simulation(self):
        if not self.trajectory or not self.operation:
            return

        # Calculate depth increment
        step = 0.1 * (-1 if self.operation == "POOH" else 1)
        new_depth = self.current_depth + step

        # Clamp depth values
        if new_depth < 0:
            new_depth = 0
            self.stop_operation()
        elif new_depth > self.trajectory.max_depth:
            new_depth = self.trajectory.max_depth
            self.stop_operation()

        self.current_depth = new_depth

        # Get current survey data
        survey_point = self.trajectory.get_point_at_depth(self.current_depth)

        # Calculate tension
        tension, breakdown = calculate_tension(
            depth=self.current_depth,
            params=self.params,
            inclination=survey_point.incl,
            operation=self.operation,
            last_operation=self.last_operation
        )

        self.simulation_updated.emit(self.current_depth, tension, breakdown)

    def set_simulation_speed(self, speed: int):
        """Set speed in ft/min"""
        self.speed = speed
        if self.timer.isActive():
            interval = int(60000 / (speed * 10))  # ms per 0.1 ft
            self.timer.setInterval(interval)