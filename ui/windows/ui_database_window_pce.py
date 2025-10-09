import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from database.logic_database_pce import get_full_tool_database


class DatabaseWindow(QWidget):
    """Displays the full tool database in a scrollable window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCE Database")
        self.setGeometry(200, 200, 800, 400)

        layout = QVBoxLayout(self)

        # ✅ Table Widget
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # ✅ Load Data
        self.load_data()

    def load_data(self):
        """Loads the tool database into the table."""
        df = get_full_tool_database()  # Ensure function returns full dataframe
        if df.empty:
            return

        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)

        for i, row in df.iterrows():
            for j, value in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
