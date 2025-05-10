from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
                             QLabel, QPushButton, QTextEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QApplication)
from PyQt6.QtCore import Qt
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from utils.path_finder import get_icon_path


class MDtoTVDTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side (Input/Output)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # MD Input Section
        md_input_group = QWidget()
        md_input_layout = QVBoxLayout(md_input_group)
        md_input_layout.addWidget(QLabel("MD Values to Convert:"))

        self.md_input = QTextEdit()
        self.md_input.setPlaceholderText("Paste MD values here (one per line or Excel column)...")
        md_input_layout.addWidget(self.md_input)

        # Deviation Survey Input
        survey_group = QWidget()
        survey_layout = QVBoxLayout(survey_group)
        survey_layout.addWidget(QLabel("Deviation Survey (MD to TVD):"))

        # Add paste from Excel button
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)

        paste_excel_btn = QPushButton("Paste from Excel")
        paste_excel_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #5cb85c;
                        color: white;
                        padding: 5px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #4cae4c;
                    }
                """)
        paste_excel_btn.clicked.connect(self.paste_from_excel)

        button_layout.addWidget(paste_excel_btn)
        survey_layout.addWidget(button_group)

        self.survey_table = QTableWidget()
        self.survey_table.setColumnCount(2)
        self.survey_table.setHorizontalHeaderLabels(["MD", "TVD"])
        self.survey_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        survey_layout.addWidget(self.survey_table)

        # Conversion Controls
        controls_group = QWidget()
        controls_layout = QHBoxLayout(controls_group)

        self.convert_btn = QPushButton("Convert MD to TVD")
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #800020;
                color: white;
                padding: 8px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a00028;
            }
        """)

        self.clear_btn = QPushButton("Clear All")
        self.copy_btn = QPushButton("Copy Results")

        controls_layout.addWidget(self.convert_btn)
        controls_layout.addWidget(self.clear_btn)

        # Results Display
        results_group = QWidget()
        results_layout = QVBoxLayout(results_group)
        results_layout.addWidget(QLabel("Conversion Results:"))

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["MD", "TVD"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)
        results_layout.addWidget(self.copy_btn)

        # Add all to left layout
        left_layout.addWidget(md_input_group)
        left_layout.addWidget(survey_group)
        left_layout.addWidget(controls_group)
        left_layout.addWidget(results_group)
        # Right side (Visualization)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Create and style the title label
        title_label = QLabel("Well Trajectory Visualization")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 20px;
                padding: 5px;
            }
        """)
        right_layout.addWidget(title_label)

        # Replace QChartView with matplotlib FigureCanvas
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        right_layout.addWidget(self.canvas)

        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 400])

        main_layout.addWidget(splitter)

    def paste_from_excel(self):
        """Handle pasting Excel data into the survey table"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text.strip():
            return

        try:
            # Parse the clipboard data (tab/newline separated)
            rows = []
            for line in text.split('\n'):
                if line.strip():
                    # Split on tabs or multiple spaces
                    parts = [p.strip() for p in line.split('\t') if p.strip()]
                    if len(parts) >= 2:
                        try:
                            md = float(parts[0])
                            tvd = float(parts[1])
                            rows.append((md, tvd))
                        except ValueError:
                            continue

            if not rows:
                raise ValueError("No valid MD/TVD pairs found in clipboard")

            # Populate the table
            self.survey_table.setRowCount(len(rows))
            for row, (md, tvd) in enumerate(rows):
                self.survey_table.setItem(row, 0, QTableWidgetItem(str(md)))
                self.survey_table.setItem(row, 1, QTableWidgetItem(str(tvd)))

            self.update_chart()

        except Exception as e:
            self.survey_table.setRowCount(1)
            self.survey_table.setItem(0, 0, QTableWidgetItem("Paste Error"))
            self.survey_table.setItem(0, 1, QTableWidgetItem(str(e)))

    def setup_connections(self):
        self.convert_btn.clicked.connect(self.convert_md_to_tvd)
        self.clear_btn.clicked.connect(self.clear_all)
        self.copy_btn.clicked.connect(self.copy_results)

    def get_survey_data(self):
        survey_data = []
        for row in range(self.survey_table.rowCount()):
            md_item = self.survey_table.item(row, 0)
            tvd_item = self.survey_table.item(row, 1)

            if md_item and tvd_item and md_item.text() and tvd_item.text():
                try:
                    md = float(md_item.text())
                    tvd = float(tvd_item.text())
                    survey_data.append((md, tvd))
                except ValueError:
                    continue

        # Sort by MD if not already sorted
        survey_data.sort(key=lambda x: x[0])
        return survey_data

    def calculate_vertical_section(self, md, tvd):
        """Approximate vertical section from MD and TVD changes"""
        vs = [0.0]  # Start at zero
        for i in range(1, len(md)):
            delta_md = md[i] - md[i - 1]
            delta_tvd = tvd[i] - tvd[i - 1]
            # Calculate horizontal displacement (simplified)
            delta_vs = np.sqrt(delta_md ** 2 - delta_tvd ** 2) if delta_md > delta_tvd else 0
            vs.append(vs[i - 1] + delta_vs)
        return vs

    def update_chart(self):
        """Plot TVD vs Vertical Section with proper wellbore labels"""
        self.figure.clear()

        # Create a main axis with adjusted position
        ax = self.figure.add_axes([0.18, 0.15, 0.80, 0.60])  # [left, bottom, width, height]

        image_path = get_icon_path('slickline_unit')

        # Load slickline unit image
        try:
            slickline_img = plt.imread(image_path)
            if slickline_img.shape[2] == 4:  # If RGBA
                mask = slickline_img[:, :, 3] > 0.1
                slickline_img = np.dstack((slickline_img[:, :, :3], mask))
        except:
            print("Slickline image not found - using placeholder")
            slickline_img = None

        survey_data = self.get_survey_data()
        if not survey_data or len(survey_data) < 3:
            ax.text(0.5, 0.5, 'Insufficient survey data\nNeed at least 3 points',
                    ha='center', va='center')
            self.canvas.draw()
            return

        mds, tvds = zip(*survey_data)
        vs = self.calculate_vertical_section(mds, tvds)

        # Add slickline unit (shifted down with the chart)
        start_x, start_y = vs[0], tvds[0]
        if slickline_img is not None:
            imagebox = OffsetImage(slickline_img, zoom=0.2)
            ab = AnnotationBbox(imagebox, (start_x, start_y),
                                xybox=(start_x, start_y - (max(tvds) * 0.2)),  # Adjusted position
                                xycoords='data',
                                boxcoords="data",
                                pad=0.0,
                                frameon=False,
                                bboxprops=dict(edgecolor='none', facecolor='none'),
                                arrowprops=dict(arrowstyle="->"))
            ax.add_artist(ab)
        else:
            ax.plot(start_x, start_y - (max(tvds) * 0.05), 'k^', markersize=12, label='Slickline Unit')

        # Calculate inclinations
        inclinations = []
        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i - 1]
            delta_tvd = tvds[i] - tvds[i - 1]
            angle = np.degrees(np.arccos(delta_tvd / delta_md)) if delta_md > 0 else 0
            inclinations.append(angle)

        max_inc_idx = np.argmax(inclinations) + 1
        max_inc = inclinations[max_inc_idx - 1]

        # Store survey data for hover
        self.survey_mds = mds
        self.survey_tvds = tvds
        self.survey_vs = vs
        self.survey_inclinations = [0] + inclinations

        # Plot main trajectory
        self.well_path_line, = ax.plot(vs, tvds, 'b-', linewidth=2, label='Well Path')

        # Mark maximum inclination point
        ax.plot(vs[max_inc_idx], tvds[max_inc_idx], 's',
                markersize=8, color='purple', label=f'Max Inc. ({max_inc:.1f}°)')
        ax.annotate(f'MD: {mds[max_inc_idx]:.1f}\nTVD: {tvds[max_inc_idx]:.1f}\nIncl: {max_inc:.1f}°',
                    xy=(vs[max_inc_idx], tvds[max_inc_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round', fc='white', alpha=0.8))

        # Mark key points
        kop_idx, eob_idx, eoh_idx = self.identify_well_sections(mds, tvds)
        if kop_idx is not None:
            ax.plot(vs[kop_idx], tvds[kop_idx], 'ro', markersize=8, label='KOP')
        if eob_idx is not None:
            ax.plot(vs[eob_idx], tvds[eob_idx], 'go', markersize=8, label='EOB')

        # Label sections
        self.label_well_sections(ax, vs, tvds, kop_idx, eob_idx, eoh_idx)

        # Hover annotation
        self.hover_annotation = ax.annotate(
            "", xy=(0, 0),
            xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w", alpha=0.9),
            arrowprops=dict(arrowstyle="->")
        )
        self.hover_annotation.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # Formatting with adjusted margins
        ax.set_xlabel('Vertical Section (ft) →', fontweight='bold')
        ax.set_ylabel('True Vertical Depth (ft) ←', fontweight='bold')
        ax.invert_yaxis()
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='upper right', bbox_to_anchor=(1, 1))  # Adjust legend position

        # Set axis limits with padding
        ax.set_xlim(min(vs) * 0.95, max(vs) * 1.05)
        ax.set_ylim(max(tvds) * 1.1, min(tvds) * 0.9)  # Extra space at top

        self.canvas.draw()

    def identify_well_sections(self, mds, tvds):
        """Identify KOP, EOB, and EOH indices"""
        kop_idx = eob_idx = eoh_idx = None
        inclinations = []

        # Calculate approximate inclinations
        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i - 1]
            delta_tvd = tvds[i] - tvds[i - 1]
            incl = np.degrees(np.arccos(delta_tvd / delta_md)) if delta_md != 0 else 0
            inclinations.append(incl)

        # Find KOP (first significant deviation)
        for i, inc in enumerate(inclinations):
            if inc > 5:  # Threshold for deviation
                kop_idx = i
                break

        # Find EOB (peak inclination)
        if kop_idx is not None:
            max_inc = max(inclinations[kop_idx:])
            eob_idx = kop_idx + inclinations[kop_idx:].index(max_inc)

            # Find EOH (where inclination starts decreasing)
            for i in range(eob_idx, len(inclinations)):
                if inclinations[i] < max_inc - 5:  # Threshold for hold
                    eoh_idx = i
                    break

        return kop_idx, eob_idx, eoh_idx

    def label_well_sections(self, ax, vs, tvds, kop_idx, eob_idx, eoh_idx):
        """Add well section labels with simple side offsets"""
        # Vertical Section
        if kop_idx is not None and kop_idx > 0:
            mid_idx = kop_idx // 2
            # ax.annotate('Vertical',
            #             xy=(vs[mid_idx], tvds[mid_idx]),
            #             xytext=(-10, 5),  # Small offset to left and up
            #             textcoords='offset points',
            #             ha='right', va='bottom',
            #             bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8))

        # Build Section
        if kop_idx is not None and eob_idx is not None:
            build_mid = kop_idx + (eob_idx - kop_idx) // 2
            ax.annotate('Build',
                        xy=(vs[build_mid], tvds[build_mid]),
                        xytext=(10, 5),  # Small offset to right and up
                        textcoords='offset points',
                        ha='left', va='bottom',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8))

        # Hold Section
        if eob_idx is not None:
            if eoh_idx is not None:  # Has drop section
                hold_mid = eob_idx + (eoh_idx - eob_idx) // 2
                label = 'Hold'
            else:  # Hold to TD
                hold_mid = eob_idx + (len(vs) - eob_idx) // 2
                label = 'Hold to TD'

            ax.annotate(label,
                        xy=(vs[hold_mid], tvds[hold_mid]),
                        xytext=(-10, -10),  # Small offset to left and down
                        textcoords='offset points',
                        ha='right', va='top',
                        bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.8))

        # Drop Section
        if eoh_idx is not None:
            drop_mid = eoh_idx + (len(vs) - eoh_idx) // 2
            ax.annotate('Drop',
                        xy=(vs[drop_mid], tvds[drop_mid]),
                        xytext=(10, -10),  # Small offset to right and down
                        textcoords='offset points',
                        ha='left', va='top',
                        bbox=dict(boxstyle='round,pad=0.5', fc='orange', alpha=0.8))

        # Ensure TVD label isn't cropped
        ax.yaxis.label.set_visible(True)
        self.figure.tight_layout()

    def setup_hover_interaction(self):
        """Set up cursor hover interaction with the well path"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        survey_data = self.get_survey_data()
        if not survey_data or len(survey_data) < 3:
            ax.text(0.5, 0.5, 'Insufficient survey data\nNeed at least 3 points',
                    ha='center', va='center')
            self.canvas.draw()
            return

        mds, tvds = zip(*survey_data)
        vs = self.calculate_vertical_section(mds, tvds)

        # Plot main trajectory
        self.well_path_line, = ax.plot(vs, tvds, 'b-', linewidth=2, label='Well Path')

        # Create annotation for hover
        self.hover_annotation = ax.annotate(
            "", xy=(0, 0),
            xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w", alpha=0.9),
            arrowprops=dict(arrowstyle="->")
        )
        self.hover_annotation.set_visible(False)

        # Connect event handlers
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # Rest of your plotting code...
        self.label_well_sections(ax, vs, tvds, *self.identify_well_sections(mds, tvds))
        ax.set_xlabel('Vertical Section (ft) →', fontweight='bold')
        ax.set_ylabel('True Vertical Depth (ft) ↓', fontweight='bold')
        ax.set_title('Well Trajectory (TVD vs Vertical Section)')
        ax.invert_yaxis()
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

        self.canvas.draw()

    def on_hover(self, event):
        """Handle mouse hover events to show MD/TVD/Inclination values"""
        if not hasattr(self, 'well_path_line') or not self.well_path_line:
            return

        if event.inaxes != self.well_path_line.axes:
            self.hover_annotation.set_visible(False)
            self.canvas.draw_idle()
            return

        if not hasattr(self, 'survey_mds'):
            return

        x, y = event.xdata, event.ydata
        distances = np.sqrt((np.array(self.survey_vs) - x) ** 2 +
                            (np.array(self.survey_tvds) - y) ** 2)
        idx = np.argmin(distances)

        if distances[idx] > 0.05 * max(self.survey_vs):  # 5% threshold
            self.hover_annotation.set_visible(False)
            self.canvas.draw_idle()
            return

        # Get all values for the closest point
        md = self.survey_mds[idx]
        tvd = self.survey_tvds[idx]
        incl = self.survey_inclinations[idx]

        self.hover_annotation.xy = (self.survey_vs[idx], self.survey_tvds[idx])
        self.hover_annotation.set_text(
            f"MD: {md:.1f} ft\nTVD: {tvd:.1f} ft\nIncl: {incl:.1f}°"
        )
        self.hover_annotation.set_visible(True)
        self.canvas.draw_idle()

    def convert_md_to_tvd(self):
        try:
            # Get input MD values
            md_text = self.md_input.toPlainText()
            md_values = []
            for line in md_text.split():
                for part in line.split():
                    try:
                        md_values.append(float(part))
                    except ValueError:
                        continue

            if not md_values:
                raise ValueError("No valid MD values entered")

            # Get survey data
            survey_data = self.get_survey_data()
            if len(survey_data) < 2:
                raise ValueError("At least 2 survey points required")

            # Create interpolation function
            survey_md = [x[0] for x in survey_data]
            survey_tvd = [x[1] for x in survey_data]

            # Interpolate TVD values
            tvd_values = np.interp(md_values, survey_md, survey_tvd)

            # Display results
            self.results_table.setRowCount(len(md_values))
            for row, (md, tvd) in enumerate(zip(md_values, tvd_values)):
                self.results_table.setItem(row, 0, QTableWidgetItem(f"{md:.2f}"))
                self.results_table.setItem(row, 1, QTableWidgetItem(f"{tvd:.2f}"))

            # Update chart with converted points
            self.update_chart()
            self.add_converted_points_to_chart(md_values, tvd_values)

        except Exception as e:
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QTableWidgetItem("Error"))
            self.results_table.setItem(0, 1, QTableWidgetItem(str(e)))


    def add_converted_points_to_chart(self, md_values, tvd_values):
        """Store converted points and update the chart"""
        self.converted_points = list(zip(md_values, tvd_values))
        self.update_chart()

    def clear_all(self):
        """Clear all inputs, results, and reset the chart"""
        self.md_input.clear()
        self.survey_table.setRowCount(0)
        self.results_table.setRowCount(0)

        # Clear the matplotlib figure instead of QtChart
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'No data available',
                ha='center', va='center', fontsize=12)
        self.canvas.draw()

        # Clear any stored converted points
        if hasattr(self, 'converted_points'):
            del self.converted_points

    def copy_results(self):
        clipboard = QApplication.clipboard()
        rows = self.results_table.rowCount()
        cols = self.results_table.columnCount()

        if rows == 0:
            return

        text = "MD\tTVD\n"
        for row in range(rows):
            for col in range(cols):
                item = self.results_table.item(row, col)
                if item:
                    text += item.text() + ("\t" if col < cols - 1 else "")
            text += "\n"

        clipboard.setText(text)