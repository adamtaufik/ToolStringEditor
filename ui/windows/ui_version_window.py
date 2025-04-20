import os
import pandas as pd
from utils.get_resource_path import get_resource_path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractScrollArea, QHeaderView
)
from PyQt6.QtCore import Qt

# Load version history
version_history_path = get_resource_path("assets/resources/version_history.xlsx")
if not os.path.exists(version_history_path):
    raise FileNotFoundError(f"Version history file not found: {version_history_path}")

version_history = pd.read_excel(version_history_path)

# Format date column
if 'Date' in version_history.columns:
    version_history['Date'] = pd.to_datetime(version_history['Date']).dt.strftime('%d/%m/%Y')

class VersionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Version History")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setRowCount(len(version_history))
        self.table.setColumnCount(len(version_history.columns))
        self.table.setHorizontalHeaderLabels(version_history.columns)

        for row_idx, row in enumerate(version_history.itertuples(index=False)):
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                col_name = version_history.columns[col_idx].lower()

                if col_name in ['updates', 'contributors']:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    item.setToolTip(str(value))

                self.table.setItem(row_idx, col_idx, item)

        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)

        # Adjust column behavior
        for col_idx, col_name in enumerate(version_history.columns):
            name = col_name.lower()
            if name in ['version', 'date']:
                self.table.resizeColumnToContents(col_idx)
            elif name == 'updates':
                self.table.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Stretch)
            elif name == 'contributors':
                self.table.setColumnWidth(col_idx, 180)  # slightly wider
                self.table.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.ResizeMode.Interactive)

        layout.addWidget(self.table)
        self.setLayout(layout)
