from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt

from editor.logic_image_processing import expand_and_center_images
from ui.components.tool_widget import ToolWidget
from utils.screen_info import get_height
from utils.styles import DROPZONE_STYLE


class DropZone(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.total_dropzone_height = get_height() - 55
        self.diagram_width = 70

        self.main_window = parent
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.setStyleSheet(DROPZONE_STYLE)
        self.setAcceptDrops(True)

        self.tool_widgets = []  # List to store tool widgets

        # ✅ Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Header Row**
        header_layout = QHBoxLayout()
        headers = [
            ("Diagram", 74), ("Tool", 120), ("Nom. Size", 90),
            ("OD (in.)", 70), ("Length (ft)", 65), ("Weight (lbs)", 80),
            ("Top Connection", 92), ("Bottom Connection", 130), ("Move", 80), ("Del", 33)
        ]

        for header_text, width in headers:
            label = QLabel(header_text)
            label.setStyleSheet("""
            font-weight: bold; 
            font-size: 8pt;
            background-color: #f0f0f0; 
            border: 0px white;
            border-bottom: 2px solid #A9A9A9; 
            color: black;
            border-radius: 5px;
            """)
            label.setFixedSize(width, 30)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            header_layout.addWidget(label)
            header_layout.setContentsMargins(0, 0, 0, 0)

        container_layout = QVBoxLayout()
        container_layout.addLayout(header_layout)
        container_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.addLayout(container_layout)

        # **Stretch placeholder (initially empty, later added/removed)**
        self.top_spacer = QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.top_spacer)  # Initially added

        # **Placeholder Label**
        self.placeholder_label = QLabel("Drag tools here")
        self.placeholder_label.setStyleSheet("color: lightgray; font-size: 50px; background-color: transparent; border: none;")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.placeholder_label)  # Initially shown

        # **Bottom spacer (re-added when empty)**
        self.bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.bottom_spacer)  # Initially added

        # **Tools Layout**
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)  
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.layout)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(0)

    def clear_tools(self):
        """Removes all tools from the DropZone."""
        for tool in self.tool_widgets:
            tool.setParent(None)
            tool.deleteLater()
        self.tool_widgets.clear()

        self.update_summary()
        self.update_placeholder()

    def dragEnterEvent(self, event):
        """Allow drag if MIME data has text."""
        if event.mimeData().hasText():
            self.setStyleSheet("background-color: #363737; border: 2px dashed white; border-radius: 5px;")
            event.acceptProposedAction()
        
    def dragLeaveEvent(self, event):
        self.setStyleSheet(DROPZONE_STYLE)
    
    def dragMoveEvent(self, event):
        """Allow drag move if valid."""
        event.acceptProposedAction()

    def drop_event_with_tool(self, tool_name):
        """Handle adding the tool when right-clicked from DraggableButton."""
        new_tool = ToolWidget(tool_name, self)
        if new_tool.tool_data:  # ✅ Check if tool data exists
            self.tool_widgets.append(new_tool)
            self.setStyleSheet(DROPZONE_STYLE)
            self.layout.addWidget(new_tool)
            self.update_placeholder()  # ✅ Ensure placeholder updates
            self.update_summary()  # ✅ Update summary when tools are added
            expand_and_center_images(self.tool_widgets, self.diagram_width)  # ✅ Resize images
        else:
            print(f"⚠️ ERROR: Tool '{tool_name}' not found in database!")

    def dropEvent(self, event):
        """Handles dropping tools into DropZone."""
        tool_name = event.mimeData().text()
        new_tool = ToolWidget(tool_name, self)
        if new_tool.tool_data:  # ✅ Check if tool data exists
            self.tool_widgets.append(new_tool)
            self.setStyleSheet(DROPZONE_STYLE)
            self.layout.addWidget(new_tool)
            self.update_placeholder()  # ✅ Ensure placeholder updates
            self.update_summary()  # ✅ Update summary when tools are added
            expand_and_center_images(self.tool_widgets, self.diagram_width)  # ✅ Resize images
        else:
            print(f"⚠️ ERROR: Tool '{tool_name}' not found in database!")

        event.acceptProposedAction()

    def update_placeholder(self):
        """Show or hide the placeholder text and adjust spacing."""
        if self.tool_widgets:
            # **Remove placeholders and spacers**
            self.placeholder_label.hide()
            self.main_layout.removeItem(self.top_spacer)
            # self.main_layout.removeItem(self.placeholder_label)
            self.main_layout.removeItem(self.bottom_spacer)
        elif self.placeholder_label.isHidden():
            # **Show placeholders and re-add spacers**
            self.placeholder_label.show()
            self.main_layout.insertItem(1, self.top_spacer)  # Push it down
            self.main_layout.insertWidget(2, self.placeholder_label)  # Keep it centered
            self.main_layout.insertItem(3, self.bottom_spacer)  # Push it up

    def update_summary(self):
        """Updates max OD, total length, and total weight."""
        max_od = 0.0
        total_length = 0.0
        total_weight = 0.0

        for tool in self.tool_widgets:
            try:
                od = float(tool.od_label.text().split()[0]) if tool.od_label.text() != "N/A" else 0.0
                length = float(tool.length_label.text().split()[0]) if tool.length_label.text() != "N/A" else 0.0
                weight = float(tool.weight_label.text().split()[0]) if tool.weight_label.text() != "N/A" else 0.0
            except ValueError:
                continue  # Ignore errors

            max_od = max(max_od, od)
            total_length += length
            total_weight += weight

        print(f"Updating summary: Max OD={max_od}, Length={total_length}, Weight={total_weight}")

        if hasattr(self.main_window, "summary_widget"):
            self.main_window.summary_widget.update_summary(max_od, total_length, total_weight)
