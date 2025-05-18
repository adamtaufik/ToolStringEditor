from PyQt6.QtWidgets import (QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np

from features.simulator.plot import plot_trajectory, plot_tool_view, plot_lubricator
from utils.styles import GROUPBOX_STYLE

class OperationTab(QWidget):
    operationChanged = pyqtSignal(str)  # "RIH", "POOH", or "STOP"
    speedChanged = pyqtSignal(int)  # Current speed in ft/min
    params_updated = pyqtSignal()  # New signal
    WELL_WIDTH = 25
    TUBING_WIDTH = WELL_WIDTH - 10
    CENTER_X = WELL_WIDTH / 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_depth = 0
        self.max_depth = 100
        self.speed = 60
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

    def depth_counter(self):
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
        self.trajectory_data = trajectory_data
        self.trajectory_ax = plot_trajectory(
            trajectory_data=trajectory_data,
            current_depth=self.current_depth,
            use_metric=self.use_metric,
            canvas=self.trajectory_canvas
        )

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
        self.speed = value
        self.speedChanged.emit(value)

    def update_visualizations(self, current_depth, trajectory_data, params, operation):
        self.current_depth = current_depth
        self.trajectory_data = trajectory_data
        self.params = params
        self.operation = operation

        # Update trajectory
        self.trajectory_ax = plot_trajectory(
            trajectory_data=trajectory_data,
            current_depth=self.current_depth,
            use_metric=self.use_metric,
            canvas=self.trajectory_canvas
        )

        # Update lubricator
        plot_lubricator(
            operation=self.operation,
            speed=self.speed,
            current_depth=self.current_depth,
            params=self.params,
            canvas=self.lubricator_canvas
        )

        # Update tool view and get tension value
        tension = plot_tool_view(
            params=self.params,
            trajectory_data=self.trajectory_data,
            current_depth=self.current_depth,
            operation=self.operation,
            speed=self.speed,
            use_metric=self.use_metric,
            canvas=self.tool_canvas
        )

        # Update tension label with the new value
        if tension is not None:
            self.tension_label.setText(f"{tension:.1f} lbs")
        else:
            self.tension_label.setText("N/A")

        self.depth_counter()
        self.params_updated.emit()  # Emit signal when params update