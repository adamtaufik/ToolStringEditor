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
    tvd_list = []
    pressure_list = []
    temperature_list = []

    for row in range(table.rowCount()):
        tvd_item = table.item(row, 0)
        pressure_item = table.item(row, 1)
        temp_item = table.item(row, 2)

        if not tvd_item or not pressure_item or not temp_item:
            raise ValueError(f"Missing data at row {row+1}.")

        try:
            tvd = float(tvd_item.text())
            pressure = float(pressure_item.text())
            temperature = float(temp_item.text())
        except ValueError:
            raise ValueError(f"Invalid numeric data at row {row+1}.")

        tvd_list.append(tvd)
        pressure_list.append(pressure)
        temperature_list.append(temperature)

    return tvd_list, pressure_list, temperature_list
