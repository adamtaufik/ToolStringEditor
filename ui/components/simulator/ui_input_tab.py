from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                            QDoubleSpinBox, QComboBox, QTableWidget, QCheckBox,
                            QPushButton, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QClipboard, QGuiApplication
import numpy as np

from ui.windows.ui_messagebox_window import MessageBoxWindow
from utils.styles import GROUPBOX_STYLE, CHECKBOX_STYLE


class InputTab(QWidget):
    trajectory_updated = pyqtSignal(dict)  # Signal when new trajectory is generated
    units_toggled = pyqtSignal(bool)  # New signal for unit changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = "Deleum"
        self.use_metric = False
        self.trajectory_data = None
        self.init_ui()

        self.wire_weight = 0.03111  # Will be updated when combo box changes
        self.breaking_strength = 2550
        self.wire_diameter = 0.108

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left side controls
        left_side = QWidget()
        left_layout = QVBoxLayout(left_side)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Tool Configuration
        tool_group = self.create_tool_group()
        fluid_group = self.create_fluid_group()
        well_group = self.create_well_group()
        checkbox_group = self.create_checkbox_group()
        unit_btn = QPushButton("Toggle Units (ft ↔ m)")
        unit_btn.clicked.connect(self.toggle_units)

        left_layout.addWidget(tool_group)
        left_layout.addWidget(fluid_group)
        left_layout.addWidget(well_group)
        left_layout.addWidget(checkbox_group)
        left_layout.addWidget(unit_btn)
        left_layout.addStretch()

        # Right side survey tables
        survey_group = self.create_survey_group()

        main_layout.addWidget(left_side)
        main_layout.addWidget(survey_group)

    def generate_trajectory_from_tables(self):
        try:
            md_data = self.get_table_values(self.md_table['table'])
            tvd_data = self.get_table_values(self.tvd_table['table']) if self.tvd_checkbox.isChecked() else md_data.copy()
            incl_data = self.get_table_values(self.incl_table['table']) if self.incl_checkbox.isChecked() else self.calculate_inclinations(md_data, tvd_data)
            azim_data = self.get_table_values(self.azim_table['table']) if self.azim_checkbox.isChecked() else [45.0]*len(md_data)

            if not md_data:
                raise ValueError("Please enter MD values")

            self.trajectory_data = {
                'mds': md_data,
                'tvd': tvd_data,
                'inclinations': incl_data,
                'azimuths': azim_data,
                'north': [0.0]*len(md_data),
                'east': [0.0]*len(md_data)
            }
            self.calculate_north_east()
            try:
                self.trajectory_updated.emit(self.trajectory_data)
            except Exception as e:
                print('Error when emitting:', e)
            MessageBoxWindow.message_simple(self,
                                            "Success",
                                            "Well trajectory generated",
                                            "check")

        except Exception as e:
            print('Error to generate trajectory:',e)
            QMessageBox.warning(self, "Error", str(e))
            # MessageBoxWindow.message_simple(self,
            #                                 "Error",
            #                                 str(e),
            #                                 )

    def create_tool_group(self):
        group = QGroupBox("Tool String Configuration")
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()

        # Wire size selection
        wire_size_layout = QHBoxLayout()
        wire_size_layout.addWidget(QLabel("Wire Size:"))
        self.wire_size_combo = QComboBox()
        self.wire_size_combo.addItems(["0.092", "0.108", "0.125", "0.140", "0.160"])
        self.wire_size_combo.setCurrentText("0.108")
        self.wire_size_combo.currentTextChanged.connect(self.update_wire_properties)
        wire_size_layout.addWidget(self.wire_size_combo)
        layout.addLayout(wire_size_layout)

        # Breaking strength display
        breaking_strength_layout = QHBoxLayout()
        breaking_strength_layout.addWidget(QLabel("Breaking Strength:"))
        self.breaking_strength_label = QLabel("2550 lbs")
        breaking_strength_layout.addWidget(self.breaking_strength_label)
        layout.addLayout(breaking_strength_layout)

        # Wire weight display
        wire_weight_layout = QHBoxLayout()
        wire_weight_layout.addWidget(QLabel("Wire Weight:"))
        self.wire_weight_label = QLabel("0.021 lbs/ft")
        wire_weight_layout.addWidget(self.wire_weight_label)
        layout.addLayout(wire_weight_layout)

        # Safe Operating Load input
        safe_operating_load_layout = QHBoxLayout()
        safe_operating_load_layout.addWidget(QLabel("Safe Operating Load:"))
        self.safe_operating_load_input = QDoubleSpinBox()
        self.safe_operating_load_input.setRange(0, 100)
        self.safe_operating_load_input.setValue(50)
        self.safe_operating_load_input.setSuffix(" %")
        safe_operating_load_layout.addWidget(self.safe_operating_load_input)
        layout.addLayout(safe_operating_load_layout)

        # Tool weight input
        tool_weight_layout = QHBoxLayout()
        tool_weight_layout.addWidget(QLabel("Tool String Weight:"))
        self.tool_weight_input = QDoubleSpinBox()
        self.tool_weight_input.setRange(0, 1000)
        self.tool_weight_input.setValue(80)
        self.tool_weight_input.setSuffix(" lbs")
        tool_weight_layout.addWidget(self.tool_weight_input)
        layout.addLayout(tool_weight_layout)

        # Tool Avg Diameter input
        tool_avg_diameter_layout = QHBoxLayout()
        tool_avg_diameter_layout.addWidget(QLabel("Average Tool String Diameter:"))
        self.tool_avg_diameter_input = QDoubleSpinBox()
        self.tool_avg_diameter_input.setRange(1.000, 5.000)
        self.tool_avg_diameter_input.setDecimals(3)
        self.tool_avg_diameter_input.setSingleStep(0.125)
        self.tool_avg_diameter_input.setValue(1.875)
        self.tool_avg_diameter_input.setSuffix(" \"")
        tool_avg_diameter_layout.addWidget(self.tool_avg_diameter_input)
        layout.addLayout(tool_avg_diameter_layout)

        # Tool String Length input
        tool_length_layout = QHBoxLayout()
        tool_length_layout.addWidget(QLabel("Tool String Length:"))
        self.tool_length_input = QDoubleSpinBox()
        self.tool_length_input.setRange(1, 50)
        self.tool_length_input.setDecimals(1)
        self.tool_length_input.setSingleStep(0.5)
        self.tool_length_input.setValue(10)
        self.tool_length_input.setSuffix(" ft")
        tool_length_layout.addWidget(self.tool_length_input)
        layout.addLayout(tool_length_layout)

        # Stuffing box friction input
        stuffing_box_layout = QHBoxLayout()
        stuffing_box_layout.addWidget(QLabel("Stuffing Box Friction:"))
        self.stuffing_box_input = QDoubleSpinBox()
        self.stuffing_box_input.setRange(0, 200)
        self.stuffing_box_input.setValue(50)
        self.stuffing_box_input.setSuffix(" lbs")
        stuffing_box_layout.addWidget(self.stuffing_box_input)
        layout.addLayout(stuffing_box_layout)

        group.setLayout(layout)
        return group

    def create_fluid_group(self):
        group = QGroupBox("Fluid Properties")
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()

        fluid_density_layout = QHBoxLayout()
        fluid_density_layout.addWidget(QLabel("Fluid Density:"))
        self.fluid_density_input = QDoubleSpinBox()
        self.fluid_density_input.setRange(0, 20)
        self.fluid_density_input.setValue(8.33)
        self.fluid_density_input.setSuffix(" ppg")
        fluid_density_layout.addWidget(self.fluid_density_input)
        layout.addLayout(fluid_density_layout)

        fluid_level_layout = QHBoxLayout()
        fluid_level_layout.addWidget(QLabel("Fluid Level:"))
        self.fluid_level_input = QDoubleSpinBox()
        self.fluid_level_input.setRange(0, 10000)
        self.fluid_level_input.setValue(300)
        self.fluid_level_input.setSuffix(" ft")
        fluid_level_layout.addWidget(self.fluid_level_input)
        layout.addLayout(fluid_level_layout)

        group.setLayout(layout)
        return group

    def create_well_group(self):
        group = QGroupBox("Well Conditions")
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()

        pressure_layout = QHBoxLayout()
        pressure_layout.addWidget(QLabel("Well Pressure:"))
        self.pressure_input = QDoubleSpinBox()
        self.pressure_input.setRange(0, 10000)
        self.pressure_input.setValue(500)
        self.pressure_input.setSuffix(" psi")
        pressure_layout.addWidget(self.pressure_input)
        layout.addLayout(pressure_layout)

        friction_layout = QHBoxLayout()
        friction_layout.addWidget(QLabel("Friction Coefficient:"))
        self.friction_input = QDoubleSpinBox()
        self.friction_input.setRange(0, 1)
        self.friction_input.setValue(0.3)
        self.friction_input.setSingleStep(0.05)
        friction_layout.addWidget(self.friction_input)
        layout.addLayout(friction_layout)

        group.setLayout(layout)
        return group

    def create_checkbox_group(self):
        group = QGroupBox("Survey Options")
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()

        checkboxes = QHBoxLayout()
        self.tvd_checkbox = QCheckBox("Use Custom TVD")
        self.incl_checkbox = QCheckBox("Use Custom Inclination")
        self.azim_checkbox = QCheckBox("Use Custom Azimuth")

        self.tvd_checkbox.setStyleSheet(CHECKBOX_STYLE)
        self.incl_checkbox.setStyleSheet(CHECKBOX_STYLE)
        self.azim_checkbox.setStyleSheet(CHECKBOX_STYLE)

        checkboxes.addWidget(self.tvd_checkbox)
        checkboxes.addWidget(self.incl_checkbox)
        checkboxes.addWidget(self.azim_checkbox)
        layout.addLayout(checkboxes)

        group.setLayout(layout)
        return group

    def create_survey_group(self):
        group = QGroupBox("Deviation Survey")
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()

        tables_layout = QHBoxLayout()
        self.md_table = self.create_table("MD (ft)", "Paste MD Data")
        self.tvd_table = self.create_table("TVD (ft)", "Paste TVD Data", enabled=False)
        self.incl_table = self.create_table("Inclination (deg)", "Paste Inclination Data", enabled=False)
        self.azim_table = self.create_table("Azimuth (deg)", "Paste Azimuth Data", enabled=False)

        tables_layout.addWidget(self.md_table['group'])
        tables_layout.addWidget(self.tvd_table['group'])
        tables_layout.addWidget(self.incl_table['group'])
        tables_layout.addWidget(self.azim_table['group'])
        
        layout.addLayout(tables_layout)

        generate_btn = QPushButton("Generate Well Trajectory")
        generate_btn.clicked.connect(self.generate_trajectory_from_tables)
        layout.addWidget(generate_btn)

        # Connect checkbox states
        self.tvd_checkbox.stateChanged.connect(
            lambda: self.tvd_table['table'].setEnabled(self.tvd_checkbox.isChecked()))
        self.incl_checkbox.stateChanged.connect(
            lambda: self.incl_table['table'].setEnabled(self.incl_checkbox.isChecked()))
        self.azim_checkbox.stateChanged.connect(
            lambda: self.azim_table['table'].setEnabled(self.azim_checkbox.isChecked()))

        group.setLayout(layout)
        return group

    def create_table(self, title, btn_text, enabled=True):
        container = QWidget()
        layout = QVBoxLayout(container)
        
        group = QGroupBox(title.split()[0])
        group.setStyleSheet(GROUPBOX_STYLE)
        group_layout = QVBoxLayout()
        
        paste_btn = QPushButton(btn_text)
        table = QTableWidget()
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels([title])
        table.setRowCount(20)
        table.setEnabled(enabled)
        
        paste_btn.clicked.connect(lambda: self.paste_table_data(table))
        
        group_layout.addWidget(paste_btn)
        group_layout.addWidget(table)
        group.setLayout(group_layout)
        
        layout.addWidget(group)
        return {'container': container, 'group': group, 'table': table}

    def paste_table_data(self, table):
        clipboard = QGuiApplication.clipboard()
        data = clipboard.text().strip()
        if not data:
            return

        rows = [row.split('\t') for row in data.split('\n')]
        current_row = table.currentRow() if table.currentRow() >= 0 else 0
        
        for i, row in enumerate(rows):
            if current_row + i >= table.rowCount():
                table.insertRow(table.rowCount())
            for j, cell in enumerate(row):
                if j >= table.columnCount():
                    continue
                cleaned = cell.replace(',', '').strip()
                try:
                    value = float(cleaned)
                    item = QTableWidgetItem(f"{value:.2f}")
                except ValueError:
                    item = QTableWidgetItem(cleaned)
                table.setItem(current_row + i, j, item)

    def get_table_values(self, table):
        values = []
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.text():
                try:
                    values.append(float(item.text()))
                except ValueError:
                    raise ValueError(f"Invalid number in row {row+1}")
        return values

    def calculate_inclinations(self, mds, tvds):
        incl = [0.0]
        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i-1]
            delta_tvd = tvds[i] - tvds[i-1]
            incl.append(np.degrees(np.arccos(delta_tvd/delta_md)) if delta_md > 0 else 0.0)
        return incl

    def calculate_north_east(self):
        mds = self.trajectory_data['mds']
        incl = np.radians(self.trajectory_data['inclinations'])
        azim = np.radians(self.trajectory_data['azimuths'])

        north, east = [0.0], [0.0]
        for i in range(1, len(mds)):
            delta_md = mds[i] - mds[i-1]
            north.append(north[i-1] + np.sin(incl[i])*np.cos(azim[i])*delta_md)
            east.append(east[i-1] + np.sin(incl[i])*np.sin(azim[i])*delta_md)
        
        self.trajectory_data.update({'north': north, 'east': east})

    def toggle_units(self):
        self.use_metric = not self.use_metric
        factor = 0.3048 if self.use_metric else 1/0.3048
        suffix = "m" if self.use_metric else "ft"

        # Convert spinbox values
        self.fluid_level_input.setSuffix(f" {suffix}")
        self.fluid_level_input.setValue(self.fluid_level_input.value() * factor)

        # Update tables and wire properties
        for table in [self.md_table, self.tvd_table]:
            table['table'].setHorizontalHeaderLabels([f"{table['group'].title().split()[0]} ({suffix})"])
            for row in range(table['table'].rowCount()):
                item = table['table'].item(row, 0)
                if item and item.text():
                    try:
                        value = float(item.text()) * factor
                        item.setText(f"{value:.2f}")
                    except ValueError:
                        pass

        self.update_wire_properties()
        self.units_toggled.emit(self.use_metric)  # Emit signal

    def update_wire_properties(self):
        od = float(self.wire_size_combo.currentText())
        self.wire_weight = (od ** 2) * (8 / 3)
        self.wire_diameter = od

        if self.use_metric:
            self.wire_weight_label.setText(f"{(self.wire_weight * 3.28084):.3f} lbs/m")
        else:
            self.wire_weight_label.setText(f"{self.wire_weight:.3f} lbs/ft")

        breaking_strengths = {
            0.092 : 1750,
            0.108 : 2550,
            0.125 : 3325,
            0.140 : 4100,
            0.160 : 5150
        }

        self.breaking_strength = breaking_strengths[self.wire_diameter]
        self.breaking_strength_label.setText(f"{self.breaking_strength} lbs")
