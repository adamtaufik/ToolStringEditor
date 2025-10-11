from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor, QColor
from database.logic_database import get_tool_data
from features.editors.logic_image_processing import expand_and_center_images
from utils.path_finder import get_tool_image_path  # ✅ Import helper function
from utils.styles import COMBO_STYLE, COMBO_STYLE_BLACK


class ToolWidget(QWidget):
    """Widget representing a tool inside the DropZone."""
    BACKGROUND_WIDTH = 80  # Expanded background width for uniformity
    
    def __init__(self, tool_name, drop_zone, summary_widget=None):
        super().__init__(drop_zone)
        self.tool_name = tool_name
        self.drop_zone = drop_zone
        self.summary_widget = summary_widget

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

        image_path = get_tool_image_path(tool_name)
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
        self.nominal_size_selector.setStyleSheet(COMBO_STYLE_BLACK)
        self.nominal_size_selector.currentTextChanged.connect(self.update_tool_info)
        self.nominal_size_selector.currentTextChanged.connect(self.summary_widget.update_summary)
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
        self.lower_connection_label.setStyleSheet(COMBO_STYLE_BLACK)
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
        """Updates OD, Length, Weight, and Lower/Top Connections dynamically."""
        selected_size = self.nominal_size_selector.currentText()
        size_data = self.tool_data.get("Sizes", {}).get(selected_size, {})

        # Update dimension labels
        self.od_label.setText(f"{size_data.get('OD', 0):.3f} in")
        self.length_label.setText(f"{size_data.get('Length', 0):.1f} ft")
        self.weight_label.setText(f"{size_data.get('Weight', 0):.1f} lbs")

        # Extract connections
        lower_conns = size_data.get("Lower Connections", [])
        top_conns = size_data.get("Top Connections", [])

        # Handle NaNs or blanks
        lower_conns = [] if lower_conns == ['nan'] else lower_conns
        top_conns = [] if top_conns == ['nan'] else top_conns

        # Update lower connection dropdown
        self.lower_connection_label.clear()

        if lower_conns:
            mod_lower_conns = [self._modify_connection(conn, side="lower") for conn in lower_conns]
            self.lower_connection_label.addItems(mod_lower_conns)

            if lower_conns == top_conns:
                self.lower_connection_label.currentTextChanged.connect(self.sync_top_connection)
                self.sync_top_connection()  # Initial sync
            else:
                mod_top_conns = [self._modify_connection(conn, side="top") for conn in top_conns]
                self.top_connection_label.setText(mod_top_conns[0] if mod_top_conns else "N/A")
        else:
            self.lower_connection_label.addItem("-")
            mod_top_conns = [self._modify_connection(conn, side="top") for conn in top_conns]
            self.top_connection_label.setText(mod_top_conns[0] if mod_top_conns else "-"
                                                                                     "")
            # self.top_connection_label.setText("-")

    def sync_top_connection(self):
        """Synchronizes top connection label with the selected lower connection."""
        raw_conn = self.lower_connection_label.currentText().replace(" Pin", "").replace(" Box", "")
        self.top_connection_label.setText(self._modify_connection(raw_conn, side="top"))

    def _modify_connection(self, conn, side="lower"):
        """Modifies the connection name based on position and standard rules."""
        if conn.endswith("SR"):
            return f"{conn} {'Box' if side == 'lower' else 'Pin'}"
        elif conn in ["Sondex", "GO 'A'"]:
            return f"{conn} {'Pin' if side == 'lower' else 'Box'}"
        return conn

    def move_up(self):
        """Moves the tool up in the DropZone."""
        index = self.drop_zone.layout.indexOf(self)
        if index > 0:
            self.drop_zone.layout.insertWidget(index - 1, self)
        self.summary_widget.update_summary()  # ✅ Update summary after movement

    def move_down(self):
        """Moves the tool down in the DropZone."""
        index = self.drop_zone.layout.indexOf(self)
        if index < self.drop_zone.layout.count() - 1:
            self.drop_zone.layout.insertWidget(index + 1, self)
        self.summary_widget.update_summary()  # ✅ Update summary after movement

    def remove_tool(self):
        """Removes the tool from the DropZone."""
        if self in self.drop_zone.tool_widgets:
            self.drop_zone.tool_widgets.remove(self)
        self.setParent(None)
        self.deleteLater()
        expand_and_center_images(self.drop_zone.tool_widgets,
                                 self.drop_zone.diagram_width)
        self.drop_zone.update_placeholder()  # ✅ Ensure placeholder updates
        self.summary_widget.update_summary()  # ✅ Ensure summary updates
