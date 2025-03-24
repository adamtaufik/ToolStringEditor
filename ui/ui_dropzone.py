from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem
from PyQt6.QtCore import Qt, QSize
from PIL import Image as PILImage
from PIL.ImageQt import ImageQt
from PyQt6.QtGui import QPixmap
from ui.ui_toolwidget import ToolWidget

total_dropzone_height = 650  
diagram_width = 70


class DropZone(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dropzone_style_main = "background-color: white; border: 0px solid gray; border-radius: 10px;"

        self.main_window = parent
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.setStyleSheet(self.dropzone_style_main)
        # self.setFixedSize(800, total_dropzone_height)  # Adjust DropZone size if needed
        self.setAcceptDrops(True)

        self.tool_widgets = []  # List to store tool widgets

        # ✅ Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Header Row**
        header_layout = QHBoxLayout()
        headers = [
            ("Diagram", 74), ("Tool", 124), ("Nom. Size", 80),
            ("OD (in.)", 70), ("Length (ft)", 70), ("Weight (lbs)", 80),
            ("Top Connection", 90), ("Bottom Connection", 120), ("Move", 78), ("Del", 33)
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
        # self.main_layout.addLayout(header_layout)


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

    # def sizeHint(self):
    #     """Returns the suggested height for DropZone based on available space."""
    #     if self.main_window:
    #         # return self.main_window.height() - (self.main_window.TOOLBAR_HEIGHT + self.main_window.FOOTER_HEIGHT)
    #         return self.main_window.height() - 60
    #     return 400  # Fallback default height

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
        self.setStyleSheet(self.dropzone_style_main)
    
    def dragMoveEvent(self, event):
        """Allow drag move if valid."""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Handles dropping tools into DropZone."""
        tool_name = event.mimeData().text()    
        new_tool = ToolWidget(tool_name, self)
        if new_tool.tool_data:  # ✅ Check if tool data exists
            self.tool_widgets.append(new_tool)
            self.setStyleSheet(self.dropzone_style_main)
            self.layout.addWidget(new_tool)
            self.update_placeholder()  # ✅ Ensure placeholder updates
            self.update_summary()  # ✅ Update summary when tools are added
            expand_and_center_images_dropzone(self.tool_widgets)  # ✅ Resize images
        else:
            print(f"⚠️ ERROR: Tool '{tool_name}' not found in database!")
    
        event.acceptProposedAction()

    def add_tool(self, tool_name):
        """Add a tool to the DropZone."""
        tool_widget = ToolWidget(tool_name, self)
        self.tool_widgets.append(tool_widget)
        self.layout.addWidget(tool_widget)
        
        # ✅ Resize all images when a new tool is added
        expand_and_center_images_dropzone(self.tool_widgets)
        self.update_placeholder()
        self.update_summary()

    def remove_tool(self, tool_widget):
        """Remove a tool from the DropZone."""
        if tool_widget in self.tool_widgets:
            self.tool_widgets.remove(tool_widget)
            tool_widget.setParent(None)
            tool_widget.deleteLater()
        
        # ✅ Resize remaining images
        expand_and_center_images_dropzone(self.tool_widgets)
        self.update_placeholder()
        self.update_summary()


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

    def get_tools_data(self):
        """Returns all tool data for saving."""
        return [tool.get_data() for tool in self.tool_widgets]

    def load_tools(self, tools_data):
        """Loads tools from saved data and ensures images are properly displayed."""
        
        self.clear_tools()  # Clear existing tools before loading
    
        for tool_data in tools_data:
            tool_widget = ToolWidget(tool_data["name"], self)
    
            # ✅ Restore tool properties
            tool_widget.nominal_size_selector.setCurrentText(tool_data["nominal_size"])
            tool_widget.od_label.setText(tool_data["od"])
            tool_widget.length_label.setText(tool_data["length"])
            tool_widget.weight_label.setText(tool_data["weight"])
            tool_widget.connection_label.setCurrentText(tool_data["connection"])
    
            self.tool_widgets.append(tool_widget)
            self.layout.addWidget(tool_widget)
    
        # ✅ Ensure images are expanded & centered immediately
        expand_and_center_images_dropzone(self.tool_widgets)
    
        # ✅ Force the UI to refresh
        self.update()
        self.repaint()
        self.update_placeholder()

def expand_and_center_images_dropzone(tool_widgets):
    """Expands background width first, then resizes all tool images only if needed."""
    
    if not tool_widgets:
        return

    dropzone_height = total_dropzone_height - 40  # Adjusted for padding
    max_width = diagram_width  # ✅ Set a fixed width for all images

    min_image_height = max(tool.label.height() for tool in tool_widgets)  # Prevents images from being too small

    # ✅ Step 1: Expand background width while keeping images at original size
    for tool in tool_widgets:
        if tool.image_label.pixmap():
            original_pixmap = tool.image_label.pixmap()
            # **Expand background to max_width without changing image size**
            new_width = max_width  # Fixed background width
            new_height = original_pixmap.height()  # Keep original height initially

            # **Convert to PIL and expand background**
            qimage = original_pixmap.toImage()
            pil_img = PILImage.fromqimage(qimage).convert("RGBA")

            expanded_img = PILImage.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
            x_offset = (new_width - pil_img.width) // 2
            expanded_img.paste(pil_img, (x_offset, 0), pil_img)

            # **Convert back to QPixmap**
            qimage_expanded = ImageQt(expanded_img)
            pixmap_expanded = QPixmap.fromImage(qimage_expanded)

            # **Apply expanded background**
            tool.image_label.setPixmap(pixmap_expanded)
            tool.image_label.setFixedSize(QSize(new_width, new_height))

    # ✅ Step 2: Check if resizing is needed (Only resize if the total height exceeds DropZone height)
    original_total_height = sum(tool.image_label.height() for tool in tool_widgets)

    if original_total_height > dropzone_height:
        scale_factor = dropzone_height / original_total_height  # Compute scaling factor
    else:
        scale_factor = 1.0  # No scaling needed

    # ✅ Step 3: Resize all tool images if necessary
    if scale_factor < 1.0:
        for tool in tool_widgets:
            if tool.image_label.pixmap():
                original_pixmap = tool.image_label.pixmap()

                # Apply uniform scaling
                new_height = max(int(original_pixmap.height() * scale_factor), min_image_height)  # Ensure min height          
                new_width = max_width  # Keep width fixed

                resized_pixmap = original_pixmap.scaled(
                    new_width, new_height,  
                    Qt.AspectRatioMode.IgnoreAspectRatio,  # ✅ No aspect ratio preservation
                    Qt.TransformationMode.SmoothTransformation
                )

                # **Convert to PIL for background adjustment**
                qimage = resized_pixmap.toImage()
                pil_img = PILImage.fromqimage(qimage).convert("RGBA")

                # **Create new expanded background**
                resized_img = PILImage.new("RGBA", (max_width, new_height), (255, 255, 255, 0))
                x_offset = (max_width - pil_img.width) // 2
                resized_img.paste(pil_img, (x_offset, 0), pil_img)

                # **Convert back to QPixmap**
                qimage_resized = ImageQt(resized_img)
                pixmap_resized = QPixmap.fromImage(qimage_resized)

                # **Apply resized image**
                tool.image_label.setPixmap(pixmap_resized)
                tool.image_label.setFixedSize(QSize(max_width, new_height))  # Ensure QLabel matches new size
