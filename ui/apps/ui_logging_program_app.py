import math
import sys
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFileDialog, QApplication, QSplitter, QLabel, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


class LoggingProgramApp(QWidget):
    def __init__(self):
        super().__init__()
        self.label_font_size = 9
        self.init_ui()
        self.init_fixed_rows()
        self.select_first_row()

    # ==================== UI SETUP ====================
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        sub_splitter = QSplitter(Qt.Orientation.Vertical)

        # ---------- LEFT: TABLE ----------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Target Depth (ft)", "Speed (ft/min)", "Hold Time (min)", "Direction"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        insert_above_btn = QPushButton("Insert Above")
        insert_below_btn = QPushButton("Insert Below")
        remove_btn = QPushButton("Remove Selected")

        insert_above_btn.clicked.connect(lambda: self.insert_row(True))
        insert_below_btn.clicked.connect(lambda: self.insert_row(False))
        remove_btn.clicked.connect(self.remove_selected_row)

        btn_row = QHBoxLayout()
        btn_row.addWidget(insert_above_btn)
        btn_row.addWidget(insert_below_btn)
        btn_row.addWidget(remove_btn)

        left_layout.addLayout(btn_row)
        left_layout.addWidget(self.table)
        main_splitter.addWidget(left_widget)

        # ---------- RIGHT: PLOT ----------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        # ---------- CONTROLS ----------
        self.chk_depth_labels = QCheckBox("Depth")
        self.chk_hold_labels = QCheckBox("Stop Time")
        self.chk_speed_labels = QCheckBox("Speed")
        self.chk_group_labels = QCheckBox("Grouped Stops")
        self.chk_edge_labels = QCheckBox("First / Last")

        for chk in [self.chk_depth_labels, self.chk_hold_labels,
                    self.chk_speed_labels, self.chk_group_labels, self.chk_edge_labels]:
            chk.setChecked(True)
            chk.stateChanged.connect(self.generate_plot)

        self.full_view_btn = QPushButton("Full Depth View")
        self.full_view_btn.setCheckable(True)
        self.full_view_btn.toggled.connect(self.update_view_limits)

        # Sliders
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(6, 16)
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

        # Export Buttons
        plot_btn = QPushButton("Generate Program Plot")
        plot_btn.clicked.connect(self.generate_plot)
        png_btn = QPushButton("Export PNG")
        png_btn.clicked.connect(lambda: self.export_plot("png"))
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(lambda: self.export_plot("pdf"))
        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self.export_csv)

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
        for btn in [plot_btn, png_btn, pdf_btn, csv_btn]:
            action_layout.addWidget(btn)
        action_layout.addWidget(self.full_view_btn)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.addLayout(editor_layout)
        controls_layout.addLayout(action_layout)

        sub_splitter.addWidget(right_widget)
        sub_splitter.addWidget(controls_widget)
        main_splitter.addWidget(sub_splitter)
        main_splitter.setSizes([520, 600])
        main_layout.addWidget(main_splitter)

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
            item.setBackground(QBrush(QColor(240, 240, 240)))
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
        for col in range(4):
            self._set_item(row, col, "")

    def remove_selected_row(self):
        row = self.table.currentRow()
        if row == 0 or row == self.table.rowCount() - 1:
            QMessageBox.warning(self, "Protected Row", "Cannot remove first/last row.")
            return
        self.table.removeRow(row)

    # ==================== PLOT GENERATION ====================
    def generate_plot(self):
        try:
            depths, speeds, holds = [], [], []
            self.label_font_size = self.font_slider.value()
            depth_offset = self.depth_offset_slider.value()
            speed_offset = self.speed_offset_slider.value()

            # ----- READ TABLE -----
            for r in range(self.table.rowCount()):
                depth = float(self.table.item(r, 0).text() or 0)
                speed_text = self.table.item(r, 1).text()
                if r == 0:
                    speed = float(speed_text or 0)
                elif r == self.table.rowCount() - 1 and not speed_text:
                    QMessageBox.warning(self, "Input Required", "Enter speed in last row.")
                    return
                elif not speed_text:
                    QMessageBox.warning(self, "Input Required", f"Enter speed in row {r+1}.")
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
            xs, ys, segment_info = [0], [depths[0]], []

            group_dir, group_speed, group_hold = None, None, None
            group_count, group_stop_depths = 0, []
            group_start_x, group_end_x = None, None

            first_segment, last_segment = None, None
            x = 0

            # ----- MAIN LOOP -----
            for i in range(1, len(depths)):
                delta = depths[i] - depths[i - 1]
                direction = "RIH" if delta > 0 else "POOH"
                self._set_item(i, 3, direction, editable=False, gray=(i==0 or i==self.table.rowCount()-1))

                # Travel segment
                x_prev, y_prev = x, ys[-1]
                x += 1
                xs.append(x)
                ys.append(depths[i])
                mid_x, mid_y = (x_prev + x)/2, (y_prev + depths[i])/2
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

                    # Labels
                    if self.chk_hold_labels.isChecked() or self.chk_depth_labels.isChecked():
                        if direction == "POOH":
                            offset, va = -depth_offset, "bottom"
                        else:
                            offset, va = depth_offset, "top"

                        label_text = ""
                        if self.chk_depth_labels.isChecked():
                            label_text += f"{depths[i]:.0f} ft"
                        if self.chk_hold_labels.isChecked():
                            label_text += f"\n{holds[i]:.0f} min" if label_text else f"{holds[i]:.0f} min"

                        self.ax.text((x_hold_start + x_hold_end)/2, depths[i]+offset,
                                     label_text, fontsize=self.label_font_size, ha="center", va=va, linespacing=1.2)
                else:
                    if group_count >= 2:
                        self._draw_station_stop_group(group_start_x, group_end_x,
                                                      group_dir, group_speed, group_hold, group_stop_depths)
                    group_count, group_stop_depths = 0, []

            if group_count >= 2:
                self._draw_station_stop_group(group_start_x, group_end_x,
                                              group_dir, group_speed, group_hold, group_stop_depths)

            # ----- PLOT -----
            self.ax.plot(xs, ys, linewidth=2)
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
            self.ax.grid(False)

            # ----- SPEED LABELS -----
            if self.chk_speed_labels.isChecked():
                trans = self.ax.transData
                for mid_x, mid_y, speed, x0, y0, x1, y1, _, in_group in segment_info:
                    if in_group: continue
                    p1 = trans.transform((x0, y0))
                    p2 = trans.transform((x1, y1))
                    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
                    angle = math.degrees(math.atan2(dy, dx))
                    if angle < -90 or angle > 90: angle -= 180
                    length = math.hypot(dx, dy)
                    if length == 0: continue
                    perp_dx, perp_dy = -dy/length, dx/length
                    offset_disp = trans.transform((mid_x, mid_y))
                    offset_disp = (offset_disp[0]+perp_dx*speed_offset,
                                   offset_disp[1]+perp_dy*speed_offset)
                    offset_data = trans.inverted().transform(offset_disp)
                    self.ax.text(offset_data[0], offset_data[1], f"{speed:.0f} ft/min",
                                 fontsize=self.label_font_size, ha="center", va="center",
                                 rotation=angle, rotation_mode="anchor")

            # ----- FIRST/LAST LABELS -----
            if self.chk_edge_labels.isChecked() and not self.full_view_btn.isChecked():
                y_text = self.ax.get_ylim()[1] - 60
                for seg in (first_segment, last_segment):
                    mid_x, speed, direction = seg[0], seg[2], seg[7]

                    if direction == "POOH":
                        surface = "to surface"
                    else:
                        surface = "from surface"
                    self.ax.text(mid_x, y_text, f"{direction} {speed:.0f} ft/min\n{surface}",
                                 fontsize=self.label_font_size, ha="center", va="bottom")

            self._last_all_depths = ys
            self._last_ys = ys
            self.canvas.draw()

        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def _draw_station_stop_group(self, x_start, x_end, direction, speed, hold_time, stop_depths):
        shallowest, deepest = min(stop_depths), max(stop_depths)
        brace_y = shallowest - 140
        x_mid = (x_start + x_end) / 2

        if self.chk_group_labels.isChecked():
            self.ax.text(x_mid, brace_y+35,
                         f"{direction} {speed:.0f} ft/min\nwith station stops {hold_time:.0f} mins",
                         fontsize=self.label_font_size, ha="center", va="bottom")
            self.ax.plot([x_start, x_end], [brace_y, brace_y], color="black", lw=1)
            self.ax.plot([x_start, x_start], [brace_y, brace_y+50], color="black", lw=1)
            self.ax.plot([x_end, x_end], [brace_y, brace_y+50], color="black", lw=1)

    # ==================== EXPORT ====================
    def export_plot(self, fmt):
        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", "", f"*.{fmt}")
        if path:
            self.figure.savefig(path, dpi=300, bbox_inches="tight")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "*.csv")
        if not path: return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Depth (ft)", "Speed (ft/min)", "Hold Time (min)", "Direction"])
            for r in range(self.table.rowCount()):
                writer.writerow([self.table.item(r, c).text() for c in range(4)])

    # ==================== VIEW LIMITS ====================
    def update_view_limits(self):
        if not hasattr(self, "_last_all_depths"): return
        all_depths = self._last_all_depths
        if not all_depths: return
        deep = max(all_depths)
        if self.full_view_btn.isChecked():
            pad = deep*0.05
            self.ax.set_ylim(deep+pad, -pad)
        else:
            non_zero = [d for d in all_depths if d > 0]
            if non_zero:
                shallow = min(non_zero)
                annotation_pad = 200
                data_pad = (deep-shallow)*0.1
                self.ax.set_ylim(deep+data_pad, shallow-annotation_pad)
        self.canvas.draw_idle()

        self.generate_plot()


# Uncomment to run standalone
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = LoggingProgramApp()
#     window.setWindowTitle("Logging Program Generator")
#     window.show()
#     sys.exit(app.exec())
