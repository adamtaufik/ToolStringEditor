import json
import os

from PyQt6.QtWidgets import QFileDialog

from features.ts_editor.logic_image_processing import expand_and_center_images
from ui.components.toolstring_editor.tool_widget import ToolWidget
from ui.windows.ui_messagebox_window import MessageBoxWindow


def save_configuration(main_window):
    """Save configuration from ToolStringEditor."""

    file_name, _ = QFileDialog.getSaveFileName(main_window, "Save Configuration", main_window.current_file_name or "",
                                               "JSON Files (*.json)")
    if file_name:
        main_window.current_file_name = file_name

        drop_zone = main_window.drop_zone
        config = {
            "client_name": main_window.client_name.text(),
            "location": main_window.location.text(),
            "well_no": main_window.well_no.text(),
            "max_angle": main_window.max_angle.text(),
            "well_type": main_window.well_type.currentText(),
            "operation_details": main_window.operation_details.text(),
            "comments": main_window.comments.toPlainText(),
            "tools": []
        }

        for tool in drop_zone.tool_widgets:
            config["tools"].append({
                "name": tool.tool_name,
                "nominal_size": tool.nominal_size_selector.currentText(),
                "od": tool.od_label.text(),
                "length": tool.length_label.text(),
                "weight": tool.weight_label.text(),
                "top_connection": tool.top_connection_label.text(),
                "lower_connection": tool.lower_connection_label.currentText()
            })

        with open(file_name, 'w') as f:
            json.dump(config, f, indent=4)

        main_window.setWindowTitle(f"Deleum Tool String Editor - {os.path.basename(file_name)}")
        MessageBoxWindow.message_simple(main_window, "Save Successful", "Tool string saved successfully!", "save_black")


def load_configuration(main_window):
    """Load configuration into ToolStringEditor."""

    file_name, _ = QFileDialog.getOpenFileName(main_window, "Load Configuration", "", "JSON Files (*.json)")
    if file_name:
        main_window.current_file_name = file_name

        drop_zone = main_window.drop_zone
        summary_widget = main_window.summary_widget

        with open(file_name, 'r') as f:
            config = json.load(f)

        # Restore fields
        main_window.client_name.setText(config.get("client_name", ""))
        main_window.location.setText(config.get("location", ""))
        main_window.well_no.setText(config.get("well_no", ""))
        main_window.max_angle.setText(config.get("max_angle", ""))
        main_window.well_type.setCurrentText(config.get("well_type", "Oil Producer"))
        main_window.operation_details.setText(config.get("operation_details", ""))
        main_window.comments.setPlainText(config.get("comments", ""))

        drop_zone.clear_tools()

        for tool_data in config["tools"]:
            new_tool = ToolWidget(tool_data["name"], drop_zone, summary_widget)
            new_tool.nominal_size_selector.setCurrentText(tool_data["nominal_size"])
            new_tool.od_label.setText(tool_data["od"])
            new_tool.length_label.setText(tool_data["length"])
            new_tool.weight_label.setText(tool_data["weight"])
            new_tool.top_connection_label.setText(tool_data["top_connection"])
            new_tool.lower_connection_label.setCurrentText(tool_data["lower_connection"])

            drop_zone.tool_widgets.append(new_tool)
            drop_zone.layout.addWidget(new_tool)

        expand_and_center_images(drop_zone.tool_widgets, drop_zone.diagram_width)
        drop_zone.update()
        drop_zone.repaint()
        drop_zone.update_placeholder()
        summary_widget.update_summary()

        main_window.setWindowTitle(f"Deleum Tool String Editor - {os.path.basename(file_name)}")
