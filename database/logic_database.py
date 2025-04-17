import pandas as pd
import os
from utils.get_resource_path import get_resource_path  # ✅ Import helper function
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

csv_path = get_resource_path(os.path.join("assets","resources", "tool_database.csv"))

# Ensure the file exists before reading
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Database file not found: {csv_path}")

tool_data_df = pd.read_csv(csv_path)  # ✅ Read the tool database

class DatabaseWindow(QDialog):
    """A window to display the tool database."""
    def __init__(self, database_path="resources/tool_database.csv"):
        super().__init__()
        self.setWindowTitle("Tool Database")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.load_database(get_resource_path(database_path))  # ✅ Ensure correct file path

    def load_database(self, file_path):
        """Loads the CSV tool database into the table."""
        df = pd.read_csv(file_path)

        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                self.table.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))

def get_tool_data(tool_name=None):
    """
    Fetches tool data from the database.
    
    - If `tool_name` is **None**, returns a list of all available tools.
    - If `tool_name` is **provided**, returns detailed info for that specific tool.
    """
    if tool_name is None:
        return tool_data_df[["Tool Name", "Category"]].drop_duplicates()  # ✅ Returns all tools

    filtered_tools = tool_data_df[tool_data_df["Tool Name"] == tool_name]

    if filtered_tools.empty:
        return None  # No data found

    tool_info = {
        "Nominal Sizes": filtered_tools["Nominal Size"].unique().tolist(),
        "Sizes": {}
    }

    for _, row in filtered_tools.iterrows():

        size = row["Nominal Size"]

        tool_info["Sizes"][size] = {
            "OD": row["OD (Inches)"],
            "Length": row["Length (ft)"],
            "Weight": row["Weight (lbs)"],
            "Top Connections": str(row["Top Connection"]).split(","),
            "Lower Connections": str(row["Lower Connection"]).split(",")
        }

    return tool_info

def get_full_tool_database():
    """Returns the full tool database."""
    return tool_data_df  # ✅ Just return the global dataframe

def isNaN(value):
    return value != value
