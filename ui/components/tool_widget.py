from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor, QColor
from database.logic_database import get_tool_data
from editor.logic_image_processing import expand_and_center_images
from utils.path_finder import get_image_path  # ✅ Import helper function
from utils.styles import COMBO_STYLE


class ToolWidget(QWidget):
    """Widget representing a tool inside the DropZone."""
    BACKGROUND_WIDTH = 80  # Expanded background width for uniformity
    
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
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.setContentsMargins(7, 0, 0, 0)

        # **Tool Image (Original Size, Expanded Background)**
        self.image_label = QLabel()

        image_path = get_image_path(tool_name)
        pixmap = QPixmap(image_path)

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
        self.label.setFixedSize(118, 35)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Ensures text is centered
        self.label.setStyleSheet("border: 0px solid black; border-bottom: 1px solid #A9A9A9; background-color: lightgray; color: black;")
        self.layout.addWidget(self.label)

        self.label.setGraphicsEffect(shadow[0])

        # **Nominal Size Selector**
        self.nominal_size_selector = QComboBox()
        self.nominal_size_selector.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.nominal_size_selector.setFixedWidth(90)

        nominal_sizes = []
        for size in self.tool_data.get("Nominal Sizes", []):
            nominal_sizes.append(str(size))
        self.nominal_size_selector.addItems(nominal_sizes)
        self.nominal_size_selector.setStyleSheet(COMBO_STYLE)
        # self.nominal_size_selector.setStyleSheet("border: 1px solid gray; border-radius: 4px; color: black")
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
        self.length_label.setFixedWidth(65)
        self.length_label.setStyleSheet("border: none; color: black;")
        self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.length_label)

        # **Weight Label**
        self.weight_label = QLabel("N/A")
        self.weight_label.setFixedWidth(72)
        self.weight_label.setStyleSheet("border: none; color: black;")
        self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.weight_label)

        # **Top Connection Selector**
        self.top_connection_label = QLabel("N/A")
        self.top_connection_label.setFixedWidth(90)
        self.top_connection_label.setStyleSheet("border: none; color: black;")
        self.top_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.top_connection_label)

        # **Lower Connection Selector**
        self.lower_connection_label = QComboBox()
        self.lower_connection_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lower_connection_label.setFixedWidth(130)
        self.lower_connection_label.setStyleSheet(COMBO_STYLE)
        # self.lower_connection_label.setStyleSheet("border: 1px solid gray; border-radius: 4px; color: black")
        self.layout.addWidget(self.lower_connection_label)

        self.layout.addSpacing(7)

        # **Move Up Button**
        self.up_button = QPushButton("↑")
        self.up_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.up_button.setFixedSize(28, 30)
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
        self.down_button.setFixedSize(28, 30)
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

        self.layout.addSpacing(7)

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

        lower_connections = size_data.get("Lower Connections", [])
        top_connections = size_data.get("Top Connections", [])

        if lower_connections == ['nan']:
            lower_connections[0] = "N/A"

        # if lower_connections and lower_connections != ['nan']:
        if lower_connections:
            modified_lower_connections = []

            for conn in lower_connections:
                if conn.endswith("SR"):
                    modified_lower_connections.append(conn + " Box")  # SR type → Lower gets Box
                elif conn in ["Sondex", "GO 'A'"]:
                    modified_lower_connections.append(conn + " Pin")  # Sondex & GO 'A' → Lower gets Pin
                else:
                    modified_lower_connections.append(conn)  # Keep as is

            self.lower_connection_label.addItems(modified_lower_connections)

            # If lower and top connections are the same, link updates
            if lower_connections == top_connections:
                self.lower_connection_label.currentTextChanged.connect(self.sync_top_connection)

                selected_lower = self.lower_connection_label.currentText()

                if selected_lower.endswith(" Box"):
                    self.top_connection_label.setText(selected_lower.replace(" Box", " Pin"))
                elif selected_lower.endswith(" Pin"):
                    self.top_connection_label.setText(selected_lower.replace(" Pin", " Box"))
                else:
                    self.top_connection_label.setText(selected_lower)
            else:

                modified_top_connections = []

                for conn in top_connections:
                    if conn.endswith("SR"):
                        modified_top_connections.append(conn + " Pin")  # SR type → Lower gets Box
                    elif conn in ["Sondex", "GO 'A'"]:
                        modified_top_connections.append(conn + " Box")  # Sondex & GO 'A' → Lower gets Pin
                    else:
                        modified_top_connections.append(conn)  # Keep as is

                top_connections = modified_top_connections

                if top_connections == ['nan']:
                    self.top_connection_label.setText("N/A")
                else:
                    self.top_connection_label.setText(top_connections[0])
        else:
            self.lower_connection_label.addItems(['-'])
            self.top_connection_label.setText("-")

    def sync_top_connection(self):
        """Synchronizes top connection label with selected lower connection when they are equal."""
        self.top_connection_label.setText(self.lower_connection_label.currentText())

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
        expand_and_center_images(self.drop_zone.tool_widgets,
                                 self.drop_zone.diagram_width)
        self.drop_zone.update_placeholder()  # ✅ Ensure placeholder updates
        self.drop_zone.update_summary()  # ✅ Ensure summary updates
