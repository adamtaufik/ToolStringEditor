import json
import os
from PyQt6.QtWidgets import QFileDialog
from features.editors.logic_image_processing import expand_and_center_images
from ui.components.pce_editor.tool_widget import ToolWidget
from ui.windows.ui_messagebox_window import MessageBoxWindow


def save_configuration(main_window):
    """Save full configuration from PCE Editor including all tool info."""

    file_name, _ = QFileDialog.getSaveFileName(
        main_window,
        "Save Configuration",
        main_window.current_file_name or "",
        "PCE Configuration Files (*.pce)"
    )

    if file_name:
        # Ensure file extension is .pce
        if not file_name.lower().endswith(".pce"):
            file_name += ".pce"

        main_window.current_file_name = file_name

        drop_zone = main_window.drop_zone
        config = {
            "client_name": main_window.client_name.text(),
            "location": main_window.location.text(),
            "well_no": main_window.well_no.text(),
            "well_type": main_window.well_type.currentText(),
            "operation_details": main_window.operation_details.text(),
            "comments": main_window.comments.toPlainText(),
            "tools": []
        }

        for tool in drop_zone.tool_widgets:
            tool_info = {
                "name": tool.tool_name,
                "display_name": tool.get_display_name(),
                "brand": tool.brand_label.currentText(),
                "nominal_size": tool.nominal_size_selector.currentText(),
                "service": tool.service_label.currentText(),
                "id": tool.id_label.text(),
                "working_pressure": tool.wp_label.text(),
                "length": tool.length_label.text(),
                "weight": tool.weight_label.text(),
                "top_connection": tool.top_connection_label.text(),
                "lower_connection": tool.lower_connection_label.text()
            }
            config["tools"].append(tool_info)

        with open(file_name, 'w') as f:
            json.dump(config, f, indent=4)

        main_window.setWindowTitle(f"Deleum PCE Editor - {os.path.basename(file_name)}")
        MessageBoxWindow.message_simple(main_window, "Save Successful", "PCE configuration saved successfully!", "save_black")


def load_configuration(main_window):
    """Load full configuration into PCE Editor."""

    file_name, _ = QFileDialog.getOpenFileName(
        main_window,
        "Load Configuration",
        "",
        "PCE (*.pce)"
    )

    if file_name:
        main_window.current_file_name = file_name

        drop_zone = main_window.drop_zone
        summary_widget = main_window.summary_widget

        with open(file_name, 'r') as f:
            config = json.load(f)

        # Restore form fields
        main_window.client_name.setText(config.get("client_name", ""))
        main_window.location.setText(config.get("location", ""))
        main_window.well_no.setText(config.get("well_no", ""))
        main_window.well_type.setCurrentText(config.get("well_type", "Oil Producer"))
        main_window.operation_details.setText(config.get("operation_details", ""))
        main_window.comments.setPlainText(config.get("comments", ""))

        # Clear existing tools
        drop_zone.clear_tools()

        for tool_data in config.get("tools", []):
            new_tool = ToolWidget(tool_data["name"], drop_zone, summary_widget)

            # Safely set dropdowns and labels
            if "brand" in tool_data:
                new_tool.brand_label.setCurrentText(tool_data["brand"])
            if "nominal_size" in tool_data:
                new_tool.nominal_size_selector.setCurrentText(tool_data["nominal_size"])
            if "service" in tool_data:
                new_tool.service_label.setCurrentText(tool_data["service"])

            new_tool.id_label.setText(tool_data.get("id", "N/A"))
            new_tool.wp_label.setText(tool_data.get("working_pressure", "N/A"))
            new_tool.length_label.setText(tool_data.get("length", "N/A"))
            new_tool.weight_label.setText(tool_data.get("weight", "N/A"))
            new_tool.top_connection_label.setText(tool_data.get("top_connection", "N/A"))
            new_tool.lower_connection_label.setText(tool_data.get("lower_connection", "N/A"))

            # Restore display name if custom
            if tool_data.get("display_name"):
                new_tool.set_display_name(tool_data["display_name"])

            # Add to layout
            drop_zone.tool_widgets.append(new_tool)
            drop_zone.layout.addWidget(new_tool)

        # Recalculate visuals
        expand_and_center_images(drop_zone.tool_widgets, drop_zone.diagram_width)
        drop_zone.update()
        drop_zone.repaint()
        drop_zone.update_placeholder()
        summary_widget.update_summary()

        main_window.setWindowTitle(f"Deleum PCE Editor - {os.path.basename(file_name)}")
        MessageBoxWindow.message_simple(main_window, "Load Successful", "PCE configuration loaded successfully!", "open_black")
