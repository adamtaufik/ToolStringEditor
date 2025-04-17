from PyQt6.QtWidgets import QTableWidgetItem


def calculate_gradients(tvd_list, pressure_list):
    gradients = []
    for i in range(1, len(tvd_list)):
        delta_tvd = tvd_list[i] - tvd_list[i - 1]
        delta_p = pressure_list[i] - pressure_list[i - 1]
        gradient = delta_p / delta_tvd if delta_tvd != 0 else 0
        gradients.append(round(gradient, 4))
    return gradients


def validate_table_data(table):
    tvd_list, pressure_list = [], []
    for row in range(table.rowCount()):
        tvd_item = table.item(row, 0) or QTableWidgetItem("")
        p_item = table.item(row, 1) or QTableWidgetItem("")

        if tvd_item and p_item:
            try:
                tvd = float(tvd_item.text())
                p = float(p_item.text())
                tvd_list.append(tvd)
                pressure_list.append(p)
            except ValueError:
                raise ValueError(f"Non-numeric input at row {row+1}")
    if len(tvd_list) < 2:
        raise ValueError("At least 2 rows of data required.")
    return tvd_list, pressure_list
