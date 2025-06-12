# ui_operatioon_tab.py
import bisect
import os

import psutil
from PyQt6.QtWidgets import (QWidget, QSplitter, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QPushButton, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from matplotlib import pyplot as plt
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
        self.is_closed = False
        self.last_idx = None
        self.current_depth = 0
        self.max_depth = 100
        self.speed = 60
        self.trajectory_data = None
        self.current_theme = "Deleum"
        self.operation = None
        self.use_metric = False
        self.init_ui()
        self.params = None
        self.connect_signals()
        self.trajectory_ax = None  # Added to store 3D axis reference
        self.tool_line = None
        self.wire_line = None
        self.trajectory_ax = None
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
        main_splitter.setSizes([500, 500])

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

    def force_redraw(self):
        if self.trajectory_canvas:
            self.trajectory_canvas.draw_idle()
            # pass

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

    def update_trajectory_view(self, trajectory_data, fluid_level=None):


        # Convert lists to numpy arrays once and store
        self.trajectory_data = {
            'mds': np.array(trajectory_data['mds'], dtype=np.float32),
            'tvd': np.array(trajectory_data['tvd'], dtype=np.float32),
            'north': np.array(trajectory_data['north'], dtype=np.float32),
            'east': np.array(trajectory_data['east'], dtype=np.float32),
            'inclinations': np.array(trajectory_data['inclinations'], dtype=np.float32),
            'azimuths': np.array(trajectory_data['azimuths'], dtype=np.float32)
        }
        self.last_idx = None

        # Clear previous plot and redraw
        self.trajectory_canvas.figure.clf()

        try:
            # Plot trajectory and get references
            self.trajectory_ax, self.tool_line, self.wire_line = plot_trajectory(
                trajectory_data=self.trajectory_data,
                current_depth=self.current_depth,
                use_metric=self.use_metric,
                canvas=self.trajectory_canvas,
                fluid_level=fluid_level
            )
        except Exception as e:
            print('Update Trajectory Error:',e)
        self.trajectory_canvas.draw_idle()

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

    def closeEvent(self, event):
        self.is_closed = True
        # Disconnect external signals
        try:
            self.parent().input_tab.trajectory_updated.disconnect(self.update_trajectory_view)
            self.parent().input_tab.units_toggled.disconnect(self.handle_units_toggle)
        except AttributeError:
            pass

        # Flag to block further updates
        self.is_closed = True

        # Close matplotlib figures
        if self.trajectory_canvas:
            plt.close(self.trajectory_canvas.figure)
            self.trajectory_canvas = None
        if self.lubricator_canvas:
            plt.close(self.lubricator_canvas.figure)
            self.lubricator_canvas = None
        if self.tool_canvas:
            plt.close(self.tool_canvas.figure)
            self.tool_canvas = None

        # Clear references to prevent access
        self.trajectory_ax = None
        self.tool_line = None
        self.wire_line = None

        super().closeEvent(event)

    def update_visualizations(self, current_depth, params, operation):
        if self.is_closed:  # Block updates if closed
            return

        self.current_depth = current_depth
        self.params = params
        self.operation = operation

        # Safer tool position update
        if (self.tool_line is not None and
                self.trajectory_data is not None and
                len(self.trajectory_data['mds']) > 0):

            # idx = np.argmin(np.abs(self.trajectory_data['mds'] - self.current_depth))

            mds = self.trajectory_data['mds']
            idx = bisect.bisect_left(mds, self.current_depth)
            # Handle edge cases and find nearest index
            if idx == len(mds):
                idx -= 1
            elif idx > 0 and (mds[idx] - self.current_depth) > (self.current_depth - mds[idx - 1]):
                idx -= 1

            if idx != self.last_idx:
                try:
                    new_north = self.trajectory_data['north'][idx]
                    new_east = self.trajectory_data['east'][idx]
                    new_tvd = self.trajectory_data['tvd'][idx]

                    self.tool_line.set_data([new_north], [new_east])
                    self.tool_line.set_3d_properties([new_tvd])

                    if self.wire_line is not None:
                        self.wire_line.set_data(self.trajectory_data['north'][:idx + 1],
                                                self.trajectory_data['east'][:idx + 1])
                        self.wire_line.set_3d_properties(self.trajectory_data['tvd'][:idx + 1])

                    self.trajectory_canvas.draw_idle()  # Redraw only on movement
                    self.last_idx = idx

                    # self.trajectory_canvas.draw_idle()
                except IndexError:
                    pass  # Handle case where index is out of bounds

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
        self.params_updated.emit()

        # process = psutil.Process(os.getpid())
        # print(f"Memory used: {process.memory_info().rss / 1024 ** 2:.2f} MB")