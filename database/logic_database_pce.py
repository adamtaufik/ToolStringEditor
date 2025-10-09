import pandas as pd
import os
from utils.path_finder import get_path, get_resource_path  # ✅ Import helper function
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

csv_path = get_resource_path("pce_database.csv")

# Ensure the file exists before reading
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Database file not found: {csv_path}")

tool_data_df = pd.read_csv(csv_path)  # ✅ Read the tool database

class DatabaseWindow(QDialog):
    """A window to display the tool database."""
    def __init__(self, database_path=csv_path):
        super().__init__()
        self.setWindowTitle("Tool Database")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.load_database(get_path(database_path))  # ✅ Ensure correct file path

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
    If tool_name is None -> return list of all tools (unchanged behavior).
    If provided -> return a dict with:
      - brands: [brand...]
      - sizes_by_brand: {brand: [size...]}
      - services_by_brand_size: {brand: {size: [service...]}}
      - records: {(brand, size, service): {OD, Length, Weight, Top Connections, Lower Connections}}
    """
    if tool_name is None:
        return tool_data_df[["Tool Name", "Category"]].drop_duplicates()

    df = tool_data_df[tool_data_df["Tool Name"] == tool_name].copy()
    if df.empty:
        return None

    # Normalize types/strings
    for col in ["Brand", "Service", "Top Connection", "Lower Connection"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    df["Nominal Size"] = df["Nominal Size"].astype(str)

    # Build lists/maps
    brands = sorted({b for b in df.get("Brand", pd.Series(dtype=str)).unique() if b and b.lower() != "nan"})

    sizes_by_brand = {}
    for b in brands:
        sizes = df.loc[df["Brand"] == b, "Nominal Size"].astype(str).unique().tolist()
        sizes_by_brand[b] = sorted([s for s in sizes if s and s.lower() != "nan"])

    services_by_brand_size = {}
    for b in brands:
        services_by_brand_size[b] = {}
        for s in sizes_by_brand[b]:
            sub = df[(df["Brand"] == b) & (df["Nominal Size"].astype(str) == s)]
            svcs = sub.get("Service", pd.Series(dtype=str)).astype(str).unique().tolist()
            services_by_brand_size[b][s] = sorted([x for x in svcs if x and x.lower() != "nan"])

    # Detailed records
    records = {}
    for _, row in df.iterrows():
        b = row.get("Brand", "")
        s = str(row.get("Nominal Size", ""))
        svc = row.get("Service", "")

        records[(b, s, svc)] = {
            "ID": row.get("Bore ID", 0),
            "OD": row.get("OD (Inches)", 0),
            "Length": row.get("Length (ft)", 0),
            "Weight": row.get("Weight (kg)", 0),
            "Working Pressure": row.get("Working Pressure", 0),
            "Top Connections": str(row.get("Top Connection", "")).split(","),
            "Lower Connections": str(row.get("Lower Connection", "")).split(","),
        }

    return {
        "brands": brands,
        "sizes_by_brand": sizes_by_brand,
        "services_by_brand_size": services_by_brand_size,
        "records": records,
    }


def get_full_tool_database():
    """Returns the full tool database."""
    return tool_data_df  # ✅ Just return the global dataframe

def isNaN(value):
    return value != value
