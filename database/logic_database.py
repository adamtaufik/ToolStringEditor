import pandas as pd
import os

from utils.path_finder import get_path, get_resource_path  # ✅ Import helper function
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

csv_files = {"Tool": "tool_database.csv",
             "PCE": "pce_database.csv"}
data_df = {}

for data_type in ["Tool", "PCE"]:
    csv_path = get_resource_path(csv_files[data_type])
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Database file not found: {csv_path}")
    data_df[data_type] = pd.read_csv(csv_path)


def get_tool_data(tool_name=None):
    """
    Fetches tool data from the database.
    
    - If `tool_name` is **None**, returns a list of all available tools.
    - If `tool_name` is **provided**, returns detailed info for that specific tool.
    """
    if tool_name is None:
        return data_df["Tool"][["Tool Name", "Category"]].drop_duplicates()  # ✅ Returns all tools

    filtered_tools = data_df["Tool"][data_df["Tool"]["Tool Name"] == tool_name]

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
    return data_df["Tool"]  # ✅ Just return the global dataframe

def isNaN(value):
    return value != value


def get_pce_data(tool_name=None):
    """
    If tool_name is None -> return list of all tools (unchanged behavior).
    If provided -> return a dict with:
      - brands: [brand...]
      - sizes_by_brand: {brand: [size...]}
      - services_by_brand_size: {brand: {size: [service...]}}
      - records: {(brand, size, service): {OD, Length, Weight, Top Connections, Lower Connections}}
    """
    if tool_name is None:
        return data_df["PCE"][["Tool Name", "Category"]].drop_duplicates()

    df = data_df["PCE"][data_df["PCE"]["Tool Name"] == tool_name].copy()
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


def get_full_pce_database():
    """Returns the full tool database."""
    return data_df["PCE"]  # ✅ Just return the global dataframe
