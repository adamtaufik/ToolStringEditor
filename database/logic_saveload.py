import json
from ui.ui_toolwidget import ToolWidget
from ui.ui_dropzone import expand_and_center_images_dropzone  # ✅ Import image processing function

def save_configuration(file_name, client_name, location, well_no, max_angle, well_type, operation_details, comments, drop_zone):
    """Saves configuration including client info and all tools."""
    config_data = {
        "client_name": client_name,
        "location": location,
        "well_no": well_no,
        "max_angle": max_angle,
        "well_type": well_type,
        "operation_details": operation_details,
        "comments": comments,  # ✅ Include comments
        "tools": []
    }

    for tool in drop_zone.tool_widgets:
        tool_data = {
            "name": tool.tool_name,
            "nominal_size": tool.nominal_size_selector.currentText(),
            "od": tool.od_label.text(),
            "length": tool.length_label.text(),
            "weight": tool.weight_label.text(),
            "top_connection": tool.top_connection_label.text(),
            "lower_connection": tool.lower_connection_label.currentText()
        }
        config_data["tools"].append(tool_data)

    with open(file_name, 'w') as f:
        json.dump(config_data, f, indent=4)


def load_configuration(file_name, client_name_input, location_input, well_no_input, max_angle_input, well_type_input, operation_details_input, comments_widget, drop_zone):
    """Loads configuration and restores tools in DropZone."""
    with open(file_name, 'r') as f:
        config_data = json.load(f)

    # ✅ Restore all client information
    client_name_input.setText(config_data.get("client_name", ""))
    location_input.setText(config_data.get("location", ""))
    well_no_input.setText(config_data.get("well_no", ""))
    max_angle_input.setText(config_data.get("max_angle", ""))
    well_type_input.setCurrentText(config_data.get("well_type", "Oil Producer"))
    operation_details_input.setText(config_data.get("operation_details", ""))
    comments_widget.setPlainText(config_data.get("comments", ""))

    # ✅ Clear existing tools before loading new ones
    drop_zone.clear_tools()

    # ✅ Restore tools from JSON
    for tool_data in config_data["tools"]:
        new_tool = ToolWidget(tool_data["name"], drop_zone)
        new_tool.nominal_size_selector.setCurrentText(tool_data["nominal_size"])
        new_tool.od_label.setText(tool_data["od"])
        new_tool.length_label.setText(tool_data["length"])
        new_tool.weight_label.setText(tool_data["weight"])
        new_tool.top_connection_label.setText(tool_data["top_connection"])
        new_tool.lower_connection_label.setCurrentText(tool_data["lower_connection"])

        drop_zone.tool_widgets.append(new_tool)
        drop_zone.layout.addWidget(new_tool)

    # ✅ Ensure images are expanded & centered immediately
    expand_and_center_images_dropzone(drop_zone.tool_widgets)

    # ✅ Force the UI to refresh
    drop_zone.update()
    drop_zone.repaint()
    drop_zone.update_placeholder()

    # ✅ **NEW: Update summary immediately after loading**
    drop_zone.update_summary()

