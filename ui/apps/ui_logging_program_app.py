import math
import sys
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFileDialog, QApplication, QSplitter, QLabel,
    QSlider, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QPixmap, QImage
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import io

# Import your existing styling components
from ui.components.ui_footer import FooterWidget
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from utils.path_finder import get_icon_path
from utils.screen_info import get_height
from utils.theme_manager import apply_theme, toggle_theme

from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit


class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # Returning None prevents an editor from being created
        return None

class NoFrameItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        # Remove the "rounded box" look:
        editor.setFrame(False)
        editor.setStyleSheet("""
            QLineEdit {
                border: 0;
                border-radius: 0;
                background: transparent;
                padding: 0;
                color: white;
            }
        """)
        return editor

class LoggingProgramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logging Program")
        self.setMinimumWidth(1280)
        self.setMinimumHeight(get_height() - 10)

        # Top-level vertical layout (entire window)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # ✅ Custom Frameless Title Bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            "Logging Program"
        )
        root_layout.addWidget(self.title_bar)

        # Initialize the main logging widget
        self.label_font_size = 9
        self.logging_widget = self._create_logging_widget()

        # ✅ Toolbar-style sidebar (left) for Save/Load
        items = [
            (get_icon_path('save'), "Save", self.export_csv,
             "Save the current program (Ctrl+S)"),
            (get_icon_path('load'), "Load", self.load_csv,
             "Load a program file (Ctrl+O)"),
            (get_icon_path('export'), "Export Plot", lambda: self.export_plot("png"),
             "Export plot as PNG"),
            (get_icon_path('export_pdf'), "Export PDF", lambda: self.export_plot("pdf"),
             "Export plot as PDF"),
        ]
        self.sidebar = SidebarWidget(self, items)

        # Wrap main content
        content_wrapper_layout = QVBoxLayout()
        content_wrapper_layout.addWidget(self.logging_widget)

        # ✅ Footer
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button
        content_wrapper_layout.addWidget(footer)

        # ✅ Left sidebar + main content wrapper
        full_horizontal_layout = QHBoxLayout()
        full_horizontal_layout.addWidget(self.sidebar)
        full_horizontal_layout.addLayout(content_wrapper_layout)

        root_layout.addLayout(full_horizontal_layout)

        # Initialize fixed rows and selection
        self.init_fixed_rows()
        self._enforce_direction_column_readonly()
        self.select_first_row()

        # Apply initial stylesheet
        self.update_widget_styles()

    def _create_logging_widget(self):
        """Create the main logging program widget with old bottom-right controls layout."""
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Main splitter: left (table) | right (plot + controls)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        sub_splitter = QSplitter(Qt.Orientation.Vertical)

        # ---------- LEFT: TABLE ----------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Table group (optional groupbox removed to match old layout feel; keep if you prefer)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Target Depth (ft)", "Speed (ft/min)", "Hold Time (min)", "Direction"]
        )
        # IMPORTANT: don't recreate self.table again (this used to overwrite settings)
        # Delegates: column-specific read-only for Direction, and no-frame editor by default
        self.table.setItemDelegate(NoFrameItemDelegate(self.table))
        self.table.setItemDelegateForColumn(3, ReadOnlyDelegate(self.table))  # Direction column

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self.update_total_time)

        # Table control buttons
        btn_row = QHBoxLayout()
        insert_above_btn = self._create_styled_button("Insert Above", lambda: self.insert_row(True))
        insert_below_btn = self._create_styled_button("Insert Below", lambda: self.insert_row(False))
        remove_btn = self._create_styled_button("Remove Selected", self.remove_selected_row)
        btn_row.addWidget(insert_above_btn)
        btn_row.addWidget(insert_below_btn)
        btn_row.addWidget(remove_btn)

        left_layout.addLayout(btn_row)
        left_layout.addWidget(self.table)

        self.time_label = QLabel()
        self.time_label.setText("Total duration: 0.0 minutes")
        left_layout.addWidget(self.time_label)

        main_splitter.addWidget(left_widget)

        # ---------- RIGHT: PLOT (top) ----------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        # ---------- BOTTOM-RIGHT: CONTROLS + BUTTONS ----------
        # Checkboxes
        self.chk_depth_labels = QCheckBox("Depth")
        self.chk_hold_labels = QCheckBox("Stop Time")
        self.chk_speed_labels = QCheckBox("Speed")
        self.chk_group_labels = QCheckBox("Grouped Stops")
        self.chk_edge_labels = QCheckBox("First / Last")

        for chk in [self.chk_depth_labels, self.chk_hold_labels,
                    self.chk_speed_labels, self.chk_group_labels, self.chk_edge_labels]:
            chk.setChecked(True)
            chk.stateChanged.connect(self.generate_plot)

        # Full view toggle
        self.full_view_btn = QPushButton("Full Depth View")
        self.full_view_btn.setCheckable(True)
        self.full_view_btn.toggled.connect(self.update_view_limits)

        # Sliders
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(4, 12)
        self.font_slider.setValue(9)
        self.font_slider.valueChanged.connect(self.generate_plot)

        self.depth_offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_offset_slider.setRange(0, 300)
        self.depth_offset_slider.setValue(60)
        self.depth_offset_slider.valueChanged.connect(self.generate_plot)

        self.speed_offset_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_offset_slider.setRange(0, 40)
        self.speed_offset_slider.setValue(10)
        self.speed_offset_slider.valueChanged.connect(self.generate_plot)

        # Left side of bottom-right: checkboxes + sliders
        checkbox_layout = QVBoxLayout()
        for chk in [self.chk_depth_labels, self.chk_hold_labels,
                    self.chk_speed_labels, self.chk_group_labels, self.chk_edge_labels]:
            checkbox_layout.addWidget(chk)

        slider_layout = QVBoxLayout()
        slider_layout.addWidget(QLabel("Label Size"))
        slider_layout.addWidget(self.font_slider)
        slider_layout.addWidget(QLabel("Depth Label Offset"))
        slider_layout.addWidget(self.depth_offset_slider)
        slider_layout.addWidget(QLabel("Speed Label Offset"))
        slider_layout.addWidget(self.speed_offset_slider)

        editor_layout = QHBoxLayout()
        editor_layout.addLayout(checkbox_layout)
        editor_layout.addLayout(slider_layout)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.full_view_btn)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.addLayout(editor_layout)
        controls_layout.addLayout(action_layout)

        # Right side of bottom-right: vertical buttons (exactly like your old version)
        plot_btn = QPushButton("Generate Program Plot")
        plot_btn.clicked.connect(self.generate_plot)

        clipboard_btn = QPushButton("Copy to Clipboard")
        clipboard_btn.clicked.connect(self.copy_to_clipboard)

        png_btn = QPushButton("Export PNG")
        png_btn.clicked.connect(lambda: self.export_plot("png"))

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(lambda: self.export_plot("pdf"))

        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv)

        button_layout = QVBoxLayout()
        for btn in [plot_btn, clipboard_btn, png_btn, pdf_btn, csv_btn]:
            button_layout.addWidget(btn)

        bottom_right_widget = QWidget()
        bottom_right_layout = QHBoxLayout(bottom_right_widget)
        bottom_right_layout.addWidget(controls_widget)
        bottom_right_layout.addLayout(button_layout)

        # Add top-right plot and bottom-right controls to the vertical splitter
        sub_splitter.addWidget(right_widget)
        sub_splitter.addWidget(bottom_right_widget)

        # Assemble main layout
        main_splitter.addWidget(sub_splitter)
        main_splitter.setSizes([520, 600])

        main_layout.addWidget(main_splitter)
        return widget

    def _create_styled_button(self, text, callback):
        """Create a styled button matching the theme"""
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    def _make_direction_cell_readonly_and_grey(self, row: int):
        """Force column 3 (Direction) to be grey and non-editable for a given row."""
        col = 3  # Direction column
        item = self.table.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            self.table.setItem(row, col, item)

        # Make it non-editable
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Style: grey background, white (or light) text
        item.setBackground(QBrush(QColor(80, 80, 80)))
        item.setForeground(QBrush(QColor(230, 230, 230)))

    def _enforce_direction_column_readonly(self):
        for r in range(self.table.rowCount()):
            self._make_direction_cell_readonly_and_grey(r)

    def update_widget_styles(self):
        """Update styles for labels and groupboxes with white text and transparent background"""
        # Set white text color for labels and groupboxes while keeping background transparent
        stylesheet = """
            QGroupBox {
                color: white;
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                color: white;
                background-color: transparent;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }

            QLabel {
                color: white;
                background-color: transparent;
            }

            QCheckBox {
                color: white;
                background-color: transparent;
            }

            QCheckBox::indicator {
                width: 13px;
                height: 13px;
                border: 2px solid white;   /* ✔ White outline box */
                background: transparent;
            }
            
            QCheckBox::indicator:checked {
                background: white;         /* ✔ Keep tick background white */
            }

            QTableWidget {
                background-color: rgba(40, 40, 40, 150);
                alternate-background-color: rgba(50, 50, 50, 150);
                color: white;
                gridline-color: #555555;
            }

            QTableWidget::item {
                padding: 5px;
            }

            QHeaderView::section {
                background-color: rgba(60, 60, 60, 200);
                color: white;
                padding: 5px;
                border: 1px solid #555555;
            }

            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 8px;
                background: rgba(60, 60, 60, 150);
                margin: 2px 0;
            }

            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4a9eff, stop:1 #0078D7);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """

        # Apply stylesheet to the logging widget
        self.logging_widget.setStyleSheet(stylesheet)

        # Also apply to specific child widgets
        for widget in [self.table, self.time_label]:
            if widget:
                widget.setStyleSheet("""
                    color: white;
                    background-color: transparent;
                """)

    # ==================== TABLE MANAGEMENT ====================
    def init_fixed_rows(self):
        self._add_fixed_row(0, ["0", "0", "0", "Start"])
        self._add_fixed_row(1, ["0", "", "0", ""])

    def _add_fixed_row(self, row_idx, values):
        self.table.insertRow(row_idx)
        for col, val in enumerate(values):
            editable = True if (row_idx == 1 and col == 1) else False
            gray = not editable
            self._set_item(row_idx, col, val, editable, gray)

    def _set_item(self, row, col, text, editable=True, gray=False):
        item = QTableWidgetItem(text)
        if not editable:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if gray:
            item.setBackground(QBrush(QColor(80, 80, 80)))
        else:
            item.setForeground(QBrush(QColor(255, 255, 255)))  # White text
        self.table.setItem(row, col, item)

    def select_first_row(self):
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def insert_row(self, above=True):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Selection Required", "Select a row first.")
            return
        if (above and selected == 0) or (not above and selected == self.table.rowCount() - 1):
            QMessageBox.warning(self, "Invalid Operation", "Cannot insert in this position.")
            return

        row = selected if above else selected + 1
        self.table.insertRow(row)

        # 1) Create items first (so we don't overwrite the styling later)
        for col in range(4):
            item = QTableWidgetItem("")
            item.setForeground(QBrush(QColor(255, 255, 255)))  # default white text
            self.table.setItem(row, col, item)

        # 2) Now enforce Direction column grey + read-only
        self._make_direction_cell_readonly_and_grey(row)

        self.update_total_time()

    def remove_selected_row(self):
        row = self.table.currentRow()
        if row == 0 or row == self.table.rowCount() - 1:
            QMessageBox.warning(self, "Protected Row", "Cannot remove first/last row.")
            return
        self.table.removeRow(row)
        self.update_total_time()

    # ==================== TOTAL TIME CALCULATION ====================
    def calculate_total_time(self):
        total_time = 0.0
        try:
            depths = []
            speeds = []
            holds = []

            for r in range(self.table.rowCount()):
                depth = float(self.table.item(r, 0).text() or 0)
                speed_text = self.table.item(r, 1).text()
                hold = float(self.table.item(r, 2).text() or 0)

                if r == 0:
                    speed = float(speed_text or 0)
                elif r == self.table.rowCount() - 1 and not speed_text:
                    return 0.0
                elif not speed_text:
                    return 0.0
                else:
                    speed = float(speed_text)

                depths.append(depth)
                speeds.append(speed)
                holds.append(hold)

            for i in range(1, len(depths)):
                depth_diff = abs(depths[i] - depths[i - 1])
                if speeds[i] > 0:
                    travel_time = depth_diff / speeds[i]
                    total_time += travel_time
                total_time += holds[i]

            return total_time
        except (ValueError, AttributeError):
            return 0.0

    def update_total_time(self, item=None):
        total_time = self.calculate_total_time()
        self.time_label.setText(
            f"Total duration: {total_time:.1f} minutes (eqv. to {total_time / 60:.0f} hrs {total_time % 60:.1f} mins)")

    # ==================== PLOT GENERATION ====================
    def generate_plot(self):
        try:
            depths, speeds, holds = [], [], []
            self.label_font_size = self.font_slider.value()
            depth_offset = self.depth_offset_slider.value()
            speed_offset = self.speed_offset_slider.value()

            # Read table
            for r in range(self.table.rowCount()):
                depth = float(self.table.item(r, 0).text() or 0)
                speed_text = self.table.item(r, 1).text()
                if r == 0:
                    speed = float(speed_text or 0)
                elif r == self.table.rowCount() - 1 and not speed_text:
                    QMessageBox.warning(self, "Input Required", "Enter speed in last row.")
                    return
                elif not speed_text:
                    QMessageBox.warning(self, "Input Required", f"Enter speed in row {r + 1}.")
                    return
                else:
                    speed = float(speed_text)
                hold = float(self.table.item(r, 2).text() or 0)
                depths.append(depth)
                speeds.append(speed)
                holds.append(hold)

            if depths[-1] != 0:
                self.table.item(self.table.rowCount() - 1, 0).setText("0")
                depths[-1] = 0
                QMessageBox.warning(self, "Auto Correction", "Last row depth corrected to 0.")

            self.ax.clear()

            # Set dark theme for matplotlib plot
            if self.current_theme.lower() in ["deleum", "dark"]:
                self.ax.set_facecolor('#1E1E1E')
                self.figure.patch.set_facecolor('#1E1E1E')
                self.ax.tick_params(colors='white')
                self.ax.xaxis.label.set_color('white')
                self.ax.yaxis.label.set_color('white')
                self.ax.title.set_color('white')
                self.ax.spines['bottom'].set_color('white')
                self.ax.spines['top'].set_color('white')
                self.ax.spines['left'].set_color('white')
                self.ax.spines['right'].set_color('white')

            xs, ys, segment_info = [0], [depths[0]], []

            group_dir, group_speed, group_hold = None, None, None
            group_count, group_stop_depths = 0, []
            group_start_x, group_end_x = None, None

            first_segment, last_segment = None, None
            x = 0

            # Main loop
            for i in range(1, len(depths)):
                delta = depths[i] - depths[i - 1]
                direction = "RIH" if delta > 0 else "POOH"
                self._set_item(i, 3, direction, editable=False, gray=True)  # always grey
                self._make_direction_cell_readonly_and_grey(i)  # enforce flags+style

                # Travel segment
                x_prev, y_prev = x, ys[-1]
                x += 1
                xs.append(x)
                ys.append(depths[i])
                mid_x, mid_y = (x_prev + x) / 2, (y_prev + depths[i]) / 2
                seg = [mid_x, mid_y, speeds[i], x_prev, y_prev, x, depths[i], direction, False]
                segment_info.append(seg)
                if first_segment is None: first_segment = seg
                last_segment = seg

                # Hold segment
                if holds[i] > 0:
                    x_hold_start = x
                    x += 1
                    xs.append(x)
                    ys.append(depths[i])
                    x_hold_end = x

                    # Group logic
                    if direction == group_dir and speeds[i] == group_speed and holds[i] == group_hold:
                        group_end_x = x_hold_end
                        group_stop_depths.append(depths[i])
                        group_count += 1
                        segment_info[-1][-1] = True
                    else:
                        if group_count >= 2:
                            self._draw_station_stop_group(group_start_x, group_end_x,
                                                          group_dir, group_speed, group_hold, group_stop_depths)
                        group_dir, group_speed, group_hold = direction, speeds[i], holds[i]
                        group_start_x, group_end_x = x_hold_start, x_hold_end
                        group_count = 1
                        group_stop_depths = [depths[i]]

                    # Draw labels
                    if (self.chk_hold_labels.isChecked() or self.chk_depth_labels.isChecked()):
                        if group_count < 2:
                            if direction == "POOH":
                                offset, va = -depth_offset, "bottom"
                            else:
                                offset, va = depth_offset, "top"

                            label_text = ""
                            if self.chk_depth_labels.isChecked():
                                label_text += f"{depths[i]:.0f} ft"
                            if self.chk_hold_labels.isChecked():
                                label_text += f"\n{holds[i]:.0f} min" if label_text else f"{holds[i]:.0f} min"

                            self.ax.text((x_hold_start + x_hold_end) / 2, depths[i] + offset,
                                         label_text, fontsize=self.label_font_size, ha="center", va=va,
                                         color='white' if self.current_theme.lower() in ["deleum", "dark"] else 'black',
                                         linespacing=1.2)
                        else:
                            if direction == "POOH":
                                offset, va = -depth_offset, "bottom"
                            else:
                                offset, va = depth_offset, "top"

                            label_text = ""
                            if self.chk_depth_labels.isChecked():
                                label_text += f"{depths[i]:.0f} ft"

                            self.ax.text((x_hold_start + x_hold_end) / 2, depths[i] + offset,
                                         label_text, fontsize=self.label_font_size, ha="center", va=va,
                                         color='white' if self.current_theme.lower() in ["deleum", "dark"] else 'black',
                                         linespacing=1.2)
                else:
                    if group_count >= 2:
                        self._draw_station_stop_group(group_start_x, group_end_x,
                                                      group_dir, group_speed, group_hold, group_stop_depths)
                    group_count, group_stop_depths = 0, []

            if group_count >= 2:
                self._draw_station_stop_group(group_start_x, group_end_x,
                                              group_dir, group_speed, group_hold, group_stop_depths)

            # Plot styling
            self.ax.plot(xs, ys, linewidth=2,
                         color='cyan' if self.current_theme.lower() in ["deleum", "dark"] else 'blue')
            self.ax.invert_yaxis()
            deep = max(ys)

            if self.full_view_btn.isChecked():
                pad = deep * 0.05
                self.ax.set_ylim(deep + pad, -pad)
            else:
                non_zero = [d for d in ys if d > 0]
                if non_zero:
                    shallow = min(non_zero)
                    data_pad = (deep - shallow) * 0.1
                    annotation_pad = max(500, shallow / 5)
                    self.ax.set_ylim(deep + data_pad, shallow - annotation_pad)

            self.ax.set_xticks([])
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Depth (ft)")
            self.ax.set_title("Logging Program Diagram")
            self.ax.grid(True, alpha=0.3)

            # Speed labels
            if self.chk_speed_labels.isChecked():
                trans = self.ax.transData
                for mid_x, mid_y, speed, x0, y0, x1, y1, _, in_group in segment_info:
                    if in_group: continue
                    p1 = trans.transform((x0, y0))
                    p2 = trans.transform((x1, y1))
                    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                    angle = math.degrees(math.atan2(dy, dx))
                    if angle < -90 or angle > 90: angle -= 180
                    length = math.hypot(dx, dy)
                    if length == 0: continue
                    perp_dx, perp_dy = -dy / length, dx / length
                    offset_disp = trans.transform((mid_x, mid_y))
                    offset_disp = (offset_disp[0] + perp_dx * speed_offset,
                                   offset_disp[1] + perp_dy * speed_offset)
                    offset_data = trans.inverted().transform(offset_disp)
                    self.ax.text(offset_data[0], offset_data[1], f"{speed:.0f} ft/min",
                                 fontsize=self.label_font_size, ha="center", va="center",
                                 color='white' if self.current_theme.lower() in ["deleum", "dark"] else 'black',
                                 rotation=angle, rotation_mode="anchor")

            # First/Last labels
            if self.chk_edge_labels.isChecked() and not self.full_view_btn.isChecked():
                y_text = self.ax.get_ylim()[1] - 60
                for seg in (first_segment, last_segment):
                    mid_x, speed, direction = seg[0], seg[2], seg[7]
                    if direction == "POOH":
                        surface = "to surface"
                    else:
                        surface = "from surface"
                    self.ax.text(mid_x, y_text, f"{direction} {speed:.0f} ft/min\n{surface}",
                                 fontsize=self.label_font_size, ha="center", va="bottom",
                                 color='white' if self.current_theme.lower() in ["deleum", "dark"] else 'black')

            self._last_all_depths = ys
            self._last_ys = ys
            self.canvas.draw()
            self.update_total_time()

        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def _draw_station_stop_group(self, x_start, x_end, direction, speed, hold_time, stop_depths):
        shallowest, deepest = min(stop_depths), max(stop_depths)
        brace_y = shallowest - 140
        x_mid = (x_start + x_end) / 2

        if self.chk_group_labels.isChecked():
            self.ax.text(x_mid, brace_y + 35,
                         f"{direction} {speed:.0f} ft/min\nwith station stops {hold_time:.0f} mins",
                         fontsize=self.label_font_size, ha="center", va="bottom",
                         color='white' if self.current_theme.lower() in ["deleum", "dark"] else 'black')
            self.ax.plot([x_start, x_end], [brace_y, brace_y],
                         color="white" if self.current_theme.lower() in ["deleum", "dark"] else "black", lw=1)
            self.ax.plot([x_start, x_start], [brace_y, brace_y + 50],
                         color="white" if self.current_theme.lower() in ["deleum", "dark"] else "black", lw=1)
            self.ax.plot([x_end, x_end], [brace_y, brace_y + 50],
                         color="white" if self.current_theme.lower() in ["deleum", "dark"] else "black", lw=1)

    # ==================== CLIPBOARD FUNCTION ====================
    def copy_to_clipboard(self):
        try:
            buf = io.BytesIO()
            self.figure.savefig(buf, format='png', dpi=300, bbox_inches='tight',
                                facecolor=self.figure.get_facecolor())
            buf.seek(0)

            image = QImage()
            image.loadFromData(buf.getvalue())
            pixmap = QPixmap.fromImage(image)

            clipboard = QApplication.clipboard()
            clipboard.setPixmap(pixmap)

            QMessageBox.information(self, "Success", "Plot copied to clipboard!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to copy to clipboard:\n{str(e)}")

    # ==================== EXPORT ====================
    def export_plot(self, fmt):
        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", "", f"*.{fmt}")
        if path:
            self.figure.savefig(path, dpi=300, bbox_inches="tight",
                                facecolor=self.figure.get_facecolor())
            QMessageBox.information(self, "Success", f"Plot exported as {fmt.upper()}")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "*.csv")
        if not path: return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Depth (ft)", "Speed (ft/min)", "Hold Time (min)", "Direction"])
            for r in range(self.table.rowCount()):
                writer.writerow([self.table.item(r, c).text() for c in range(4)])
        QMessageBox.information(self, "Success", "CSV exported successfully")

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "*.csv")
        if not path: return
        try:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                self.table.setRowCount(0)
                for row in reader:
                    row_num = self.table.rowCount()
                    self.table.insertRow(row_num)
                    for col, text in enumerate(row):
                        item = QTableWidgetItem(text)
                        item.setForeground(QBrush(QColor(255, 255, 255)))  # White text
                        self.table.setItem(row_num, col, item)
            QMessageBox.information(self, "Success", "CSV loaded successfully")
            self.generate_plot()
            self._enforce_direction_column_readonly()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load CSV:\n{str(e)}")

    # ==================== VIEW LIMITS ====================
    def update_view_limits(self):
        if not hasattr(self, "_last_all_depths"): return
        all_depths = self._last_all_depths
        if not all_depths: return
        deep = max(all_depths)
        if self.full_view_btn.isChecked():
            pad = deep * 0.05
            self.ax.set_ylim(deep + pad, -pad)
        else:
            non_zero = [d for d in all_depths if d > 0]
            if non_zero:
                shallow = min(non_zero)
                annotation_pad = 200
                data_pad = (deep - shallow) * 0.1
                self.ax.set_ylim(deep + data_pad, shallow - annotation_pad)
        self.canvas.draw_idle()
        self.generate_plot()

    # ==================== THEME TOGGLING ====================
    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=None
        )
        # Update widget styles when theme changes
        self.update_widget_styles()
        # Regenerate plot to update colors
        self.generate_plot()