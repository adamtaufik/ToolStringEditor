import os
import sys
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from database.logic_database import get_tool_data
from utils.get_resource_path import get_resource_path  # ✅ Import helper function

class ToolWidget(QWidget):
    """Widget representing a tool inside the DropZone."""
    BACKGROUND_WIDTH = 100  # Expanded background width for uniformity
    
    def __init__(self, tool_name, drop_zone):
        super().__init__(drop_zone)
        self.tool_name = tool_name
        self.drop_zone = drop_zone
        
        

        # **Retrieve tool data**
        self.tool_data = get_tool_data(tool_name)
        if not self.tool_data:
            print(f"⚠️ WARNING: No data found for tool '{tool_name}'!")
            return

        # **Main Layout**
        self.layout = QHBoxLayout(self)
        # self.layout.setContentsMargins(5, 0, 5, 0)
        self.layout.setSpacing(11)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # **Tool Image (Original Size, Expanded Background)**
        self.image_label = QLabel()

        image_file = f"{tool_name}.png".replace('"','').replace("'","")
        image_path = get_resource_path(os.path.join("assets", "images", image_file))
        print(image_path)
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            pixmap = QPixmap("images/Dummy Image.png")  # Fallback

        # Store original image size
        self.original_width = pixmap.width()
        self.original_height = pixmap.height()

        # **Create Transparent Background**
        self.image_label.setPixmap(pixmap)
        # self.image_label.setFixedSize(self.BACKGROUND_WIDTH, self.original_height)  # Expand background width only
        self.image_label.setFixedSize(self.original_width, self.original_height)  # Expand background width only
        self.image_label.setStyleSheet("background-color: transparent; border: none;")
        
        self.layout.addWidget(self.image_label)

        # **Tool Name**
        self.label = QLabel(tool_name)
        self.label.setFixedSize(120, 40)
        self.label.setWordWrap(True)       
        self.label.setStyleSheet("border: 2px solid black; background-color: lightgray; text-align: center; color: black;")
        self.layout.addWidget(self.label)
        
        # **Nominal Size Selector**
        self.nominal_size_selector = QComboBox()
        self.nominal_size_selector.setFixedWidth(60)
        self.nominal_size_selector.addItems(self.tool_data["Nominal Sizes"])  # Get sizes dynamically
        self.nominal_size_selector.setStyleSheet("color: black")
        self.nominal_size_selector.currentTextChanged.connect(self.update_tool_info)
        self.nominal_size_selector.currentTextChanged.connect(self.drop_zone.update_summary)
        self.layout.addWidget(self.nominal_size_selector)

        # **OD Label**
        self.od_label = QLabel("N/A")
        self.od_label.setFixedWidth(70)
        self.od_label.setStyleSheet("border: none; color: black;")
        self.od_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.od_label)

        # **Length Label**
        self.length_label = QLabel("N/A")
        self.length_label.setFixedWidth(70)
        self.length_label.setStyleSheet("border: none; color: black;")
        self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.length_label)

        # **Weight Label**
        self.weight_label = QLabel("N/A")
        self.weight_label.setFixedWidth(80)
        self.weight_label.setStyleSheet("border: none; color: black;")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.weight_label)

        # **Lower Connection Selector**
        self.connection_label = QComboBox()
        self.connection_label.setFixedWidth(100)
        self.connection_label.setStyleSheet("color: black")
        self.layout.addWidget(self.connection_label)

        # **Move Up Button**
        self.up_button = QPushButton("↑")
        self.up_button.setFixedSize(30, 30)
        self.up_button.setStyleSheet("color: black")
        self.up_button.clicked.connect(self.move_up)
        self.layout.addWidget(self.up_button)

        # **Move Down Button**
        self.down_button = QPushButton("↓")
        self.down_button.setFixedSize(30, 30)
        self.down_button.setStyleSheet("color: black")
        self.down_button.clicked.connect(self.move_down)
        self.layout.addWidget(self.down_button)

        # **Remove Button**
        self.remove_button = QPushButton("X")
        self.remove_button.setFixedSize(30, 30)
        self.remove_button.setStyleSheet("font-weight: bold; background-color: red; color: white;")
        self.remove_button.clicked.connect(self.remove_tool)
        self.layout.addWidget(self.remove_button)

        # **Apply layout and update details**
        self.setLayout(self.layout)
        self.update_tool_info()

    # def get_tool_image_path(self, tool_name):
    #     """Returns the correct image path for a tool."""
    #     image_path = f"images/{tool_name}.png"
    #     image_path = image_path.replace('"','')
    #
    #     """ Get the absolute path to a resource, working for development and PyInstaller. """
    #     if getattr(sys, 'frozen', False):
    #     # If running as a bundled executable
    #             base_path = sys._MEIPASS
    #     else:
    #             # If running in a normal Python environment
    #             base_path = os.path.abspath(".")
    #
    #     image_path = os.path.join(base_path, image_path)
    #
    #
    #     return image_path if os.path.exists(image_path) else "images/Dummy Image.png"


    def update_tool_info(self):
        """Updates OD, Length, Weight, and Lower Connection dynamically."""
        selected_size = self.nominal_size_selector.currentText()
        size_data = self.tool_data["Sizes"].get(selected_size, {})

        # Update labels
        self.od_label.setText(f"{size_data.get('OD', 'N/A')} in")
        self.length_label.setText(f"{size_data.get('Length', 'N/A')} ft")
        self.weight_label.setText(f"{size_data.get('Weight', 'N/A')} lbs")

        # Update connection dropdown
        self.connection_label.clear()
        self.connection_label.addItems(size_data.get("Connections", []))

    def move_up(self):
        """Moves the tool up in the DropZone."""
        index = self.drop_zone.layout.indexOf(self)
        if index > 1:
            self.drop_zone.layout.insertWidget(index - 1, self)
        self.drop_zone.update_summary()  # ✅ Update summary after movement

    def move_down(self):
        """Moves the tool down in the DropZone."""
        index = self.drop_zone.layout.indexOf(self)
        if index < self.drop_zone.layout.count() - 1:
            self.drop_zone.layout.insertWidget(index + 1, self)
        self.drop_zone.update_summary()  # ✅ Update summary after movement

    def remove_tool(self):
        """Removes the tool from the DropZone."""
        if self in self.drop_zone.tool_widgets:
            self.drop_zone.tool_widgets.remove(self)
        self.setParent(None)
        self.deleteLater()
        self.drop_zone.update_placeholder()  # ✅ Ensure placeholder updates
        self.drop_zone.update_summary()  # ✅ Ensure summary updates

    def get_data(self):
        """Returns tool data for saving."""
        return {
            "tool_name": self.tool_name,
            "nominal_size": self.nominal_size_selector.currentText(),
            "od": self.od_label.text(),
            "length": self.length_label.text(),
            "weight": self.weight_label.text(),
            "connection": self.connection_label.currentText()
        }
