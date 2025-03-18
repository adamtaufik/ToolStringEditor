import os
import pandas as pd
from utils.get_resource_path import get_resource_path  # ✅ Import helper function
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QAbstractScrollArea, QHeaderView

# Ensure the correct file path
version_history_path = get_resource_path("assets/resources/version_history.xlsx")

# Check if the file exists before reading
if not os.path.exists(version_history_path):
    raise FileNotFoundError(f"Version history file not found: {version_history_path}")

# Load version history
version_history = pd.read_excel(version_history_path)  

class VersionWindow(QWidget):
    """Displays version information."""
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
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
                
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
