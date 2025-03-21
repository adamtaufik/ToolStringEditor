import os
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor, QColor
from database.logic_database import get_tool_data
from utils.get_resource_path import get_resource_path  # ✅ Import helper function

class ToolWidget(QWidget):
    """Widget representing a tool inside the DropZone."""
    BACKGROUND_WIDTH = 100  # Expanded background width for uniformity
    
    def __init__(self, tool_name, drop_zone):
        super().__init__(drop_zone)
        self.tool_name = tool_name
        self.drop_zone = drop_zone

        shadow = []
        for i in range(4):
            # **Soft Shadow Effect**
            shadow.append(QGraphicsDropShadowEffect())
            shadow[i].setBlurRadius(10)  # Softness of the shadow
            shadow[i].setXOffset(2)  # Horizontal shadow offset
            shadow[i].setYOffset(2)  # Vertical shadow offset
            shadow[i].setColor(QColor(50, 50, 50, 100))  # Shadow color with transparency

        # **Retrieve tool data**
        self.tool_data = get_tool_data(tool_name)
        if not self.tool_data:
            print(f"⚠️ WARNING: No data found for tool '{tool_name}'!")
            return

        # **Main Layout**
        self.layout = QHBoxLayout(self)
        # self.layout.setContentsMargins(5, 0, 5, 0)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.setContentsMargins(7, 0, 0, 0)

        # **Tool Image (Original Size, Expanded Background)**
        self.image_label = QLabel()

        if "X-Over" in tool_name:
            tool_name = "X-Over"
        image_file = f"{tool_name}.png".replace('"','').replace("'","")
        image_path = get_resource_path(os.path.join("assets", "images", image_file))
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
        else:
            dummy_path = get_resource_path(os.path.join("assets", "images", "Dummy Image.png"))
            pixmap = QPixmap(dummy_path)  # Fallback

        # Store original image size
        self.original_width = pixmap.width()
        self.original_height = pixmap.height()

        # **Create Transparent Background**
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(self.original_width, self.original_height)  # Expand background width only
        self.image_label.setStyleSheet("background-color: transparent; border: none;")

        self.layout.addWidget(self.image_label)

        # **Tool Name**
        self.label = QLabel(tool_name)
        self.label.setFixedSize(120, 35)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Ensures text is centered
        self.label.setStyleSheet("border: 0px solid black; border-bottom: 1px solid #A9A9A9; background-color: lightgray; color: black;")
        self.layout.addWidget(self.label)

        self.label.setGraphicsEffect(shadow[0])

        # **Nominal Size Selector**
        self.nominal_size_selector = QComboBox()
        self.nominal_size_selector.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nominal_size_selector.setFixedWidth(80)

        nominal_sizes = []
        for size in self.tool_data.get("Nominal Sizes", []):
            nominal_sizes.append(str(size))
        print(nominal_sizes)
        self.nominal_size_selector.addItems(nominal_sizes)
        self.nominal_size_selector.setStyleSheet("border: 1px solid gray; border-radius: 4px; color: black")
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
        self.weight_label.setFixedWidth(70)
        self.weight_label.setStyleSheet("border: none; color: black;")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.weight_label)

        # **Top Connection Selector**
        self.top_connection_label = QLabel("N/A")
        self.top_connection_label.setFixedWidth(100)
        self.top_connection_label.setStyleSheet("border: none; color: black;")
        self.top_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.top_connection_label)

        # **Lower Connection Selector**
        self.lower_connection_label = QComboBox()
        self.lower_connection_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lower_connection_label.setFixedWidth(100)
        self.lower_connection_label.setStyleSheet("border: 1px solid gray; border-radius: 4px; color: black")
        self.layout.addWidget(self.lower_connection_label)

        # **Move Up Button**
        self.up_button = QPushButton("↑")
        self.up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.up_button.setFixedSize(30, 30)
        self.up_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                border: none;
            }
            QPushButton:hover {
                background-color: #87CEEB;  /* Slightly darker blue */
            }
        """)
        self.up_button.clicked.connect(self.move_up)
        self.layout.addWidget(self.up_button)
        self.up_button.setGraphicsEffect(shadow[1])

        # **Move Down Button**
        self.down_button = QPushButton("↓")
        self.down_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.down_button.setFixedSize(30, 30)
        self.down_button.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: black;
                border: none;
            }
            QPushButton:hover {
                background-color: #87CEEB;  /* Slightly darker blue */
            }
        """)
        self.down_button.clicked.connect(self.move_down)
        self.layout.addWidget(self.down_button)
        self.down_button.setGraphicsEffect(shadow[2])

        # **Remove Button**
        self.remove_button = QPushButton("X")
        self.remove_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.remove_button.setFixedSize(30, 30)
        self.remove_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: red;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #CC0000;  /* Darker red */
            }
        """)
        self.remove_button.clicked.connect(self.remove_tool)
        self.layout.addWidget(self.remove_button)
        self.remove_button.setGraphicsEffect(shadow[3])

        # **Apply layout and update details**
        self.setLayout(self.layout)
        self.update_tool_info()

    def update_tool_info(self):
        """Updates OD, Length, Weight, and Lower Connection dynamically."""
        selected_size = self.nominal_size_selector.currentText()
        size_data = self.tool_data["Sizes"].get(selected_size, {})

        # Update labels
        self.od_label.setText(f"{size_data.get('OD', 'N/A'):.3f} in")
        self.length_label.setText(f"{size_data.get('Length', 'N/A'):.1f} ft")
        self.weight_label.setText(f"{size_data.get('Weight', 'N/A'):.1f} lbs")

        # Update connection dropdown
        self.lower_connection_label.clear()
        if size_data.get("Connections", []) != ['nan']:
            self.lower_connection_label.addItems(size_data.get("Connections", []))
            self.top_connection_label.setText("Upcoming")
        else:
            self.lower_connection_label.addItems(['-'])
            self.top_connection_label.setText("-")

    def move_up(self):
        """Moves the tool up in the DropZone."""
        index = self.drop_zone.layout.indexOf(self)
        if index > 0:
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
            "connection": self.lower_connection_label.currentText()
        }
