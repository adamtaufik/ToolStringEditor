# ui/components/toolstring_editor/tool_widget.py
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QComboBox
from PyQt6.QtCore import Qt, QSignalBlocker, QPoint
from PyQt6.QtGui import QPixmap, QCursor, QMouseEvent, QDrag
from database.logic_database import get_tool_data
from utils.path_finder import get_tool_image_path
from utils.styles import COMBO_STYLE_BLACK


class ToolWidget(QWidget):
    """Widget representing a tool inside the DropZone for tool string editor."""

    def __init__(self, tool_name, drop_zone, summary_widget=None):
        super().__init__(drop_zone)

        try:
            self.tool_name = tool_name
            self.base_name = tool_name
            self.display_name = tool_name
            self.drop_zone = drop_zone
            self.summary_widget = summary_widget
            self.drag_start_pos = None

            # --- load DB first ---
            self.tool_data = get_tool_data(tool_name)
            if not self.tool_data:
                print(f"⚠️ No data for '{tool_name}'")
                return

            # --- build UI ---
            self.layout = QHBoxLayout(self)
            self.layout.setSpacing(5)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.setContentsMargins(7, 0, 0, 0)

            # image (make draggable) - copied from PCE editor
            self.image_label = QLabel()
            self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            image_path = get_tool_image_path(tool_name)
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap)

            # Store original image size for centering
            self.original_width = pixmap.width()
            self.original_height = pixmap.height()

            self.image_label.setFixedSize(self.original_width, self.original_height)
            self.image_label.setStyleSheet("background: transparent; border: none;")
            self.image_label.mousePressEvent = self._image_mouse_press
            self.image_label.mouseMoveEvent = self._image_mouse_move
            self.layout.addWidget(self.image_label)

            # tool name
            self.label = QLabel(tool_name)
            self.label.setFixedSize(118, 35)
            self.label.setWordWrap(True)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setStyleSheet(
                "border: 0; border-bottom: 1px solid #A9A9A9; background: lightgray; color: black;"
            )
            self.layout.addWidget(self.label)

            # **Nominal Size Selector**
            self.nominal_size_selector = QComboBox()
            self.nominal_size_selector.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.nominal_size_selector.setFixedWidth(87)

            nominal_sizes = []
            for size in self.tool_data.get("Nominal Sizes", []):
                nominal_sizes.append(str(size))
            self.nominal_size_selector.addItems(nominal_sizes)
            self.nominal_size_selector.setStyleSheet(COMBO_STYLE_BLACK)
            self.nominal_size_selector.currentTextChanged.connect(self.update_tool_info)
            if self.summary_widget:
                self.nominal_size_selector.currentTextChanged.connect(self.summary_widget.update_summary)
            self.layout.addWidget(self.nominal_size_selector)

            # **OD Label**
            self.od_label = QLabel("N/A")
            self.od_label.setFixedWidth(62)
            self.od_label.setStyleSheet("border: none; color: black;")
            self.od_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.od_label)

            # **Length Label**
            self.length_label = QLabel("N/A")
            self.length_label.setFixedWidth(60)
            self.length_label.setStyleSheet("border: none; color: black;")
            self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.length_label)

            # **Weight Label**
            self.weight_label = QLabel("N/A")
            self.weight_label.setFixedWidth(67)
            self.weight_label.setStyleSheet("border: none; color: black;")
            self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.weight_label)

            # **Top Connection Label**
            self.top_connection_label = QLabel("N/A")
            self.top_connection_label.setFixedWidth(82)
            self.top_connection_label.setStyleSheet("border: none; color: black;")
            self.top_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.top_connection_label)

            # **Lower Connection Selector**
            self.lower_connection_label = QComboBox()
            self.lower_connection_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.lower_connection_label.setFixedWidth(127)
            self.lower_connection_label.setStyleSheet(COMBO_STYLE_BLACK)
            self.lower_connection_label.currentTextChanged.connect(self.sync_top_connection)

            if self.summary_widget:
                self.lower_connection_label.currentTextChanged.connect(self.summary_widget.update_summary)
            self.layout.addWidget(self.lower_connection_label)

            # Apply layout and update details
            self.setLayout(self.layout)
            self.update_tool_info()
        except Exception as e:
            print(f"Error creating ToolWidget: {e}")

    # Drag and drop methods - same as PCE editor
    def _image_mouse_press(self, event: QMouseEvent):
        """Handle mouse press on image for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
            self.image_label.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        event.accept()

    def _image_mouse_move(self, event: QMouseEvent):
        """Handle mouse move to initiate drag."""
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.drag_start_pos:
            return

        # Check if mouse has moved enough to start drag
        if (event.pos() - self.drag_start_pos).manhattanLength() < 10:
            return

        # Start drag operation
        self.drop_zone.start_drag(self)
        self.drag_start_pos = None
        self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Reset cursor when mouse is released."""
        self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def update_tool_info(self):
        """Updates OD, Length, Weight, and Connections based on selected nominal size."""
        selected_size = self.nominal_size_selector.currentText()
        size_data = self.tool_data.get("Sizes", {}).get(selected_size)

        # ---- Reset UI if no data ----
        if not size_data:
            self.od_label.setText("N/A")
            self.length_label.setText("N/A")
            self.weight_label.setText("N/A")
            self.top_connection_label.setText("N/A")

            with QSignalBlocker(self.lower_connection_label):
                self.lower_connection_label.clear()
                self.lower_connection_label.addItem("-")
            return

        # ---- Dimensions ----
        self.od_label.setText(f"{float(size_data.get('OD', 0)):.3f} in")
        self.length_label.setText(f"{float(size_data.get('Length', 0)):.1f} ft")
        self.weight_label.setText(f"{float(size_data.get('Weight', 0)):.1f} lbs")

        # ---- Connections ----
        lowers = [x for x in size_data.get("Lower Connections", []) if x and x != "nan"]
        tops = [x for x in size_data.get("Top Connections", []) if x and x != "nan"]

        # ---- Rebuild lower-connection combo safely ----
        with QSignalBlocker(self.lower_connection_label):
            self.lower_connection_label.clear()

            if lowers:
                mod_lowers = [self._modify_connection(c, "lower") for c in lowers]
                self.lower_connection_label.addItems(mod_lowers)
            else:
                self.lower_connection_label.addItem("-")

        # ---- Determine top connection ----
        if lowers and tops and set(lowers) == set(tops):
            # Sync mode
            self._sync_enabled = True
            self.sync_top_connection()
        else:
            self._sync_enabled = False
            if tops:
                self.top_connection_label.setText(
                    self._modify_connection(tops[0], "top")
                )
            else:
                self.top_connection_label.setText("-")

    def sync_top_connection(self):
        """Synchronizes top connection label with the selected lower connection."""
        if not getattr(self, "_sync_enabled", False):
            return

        raw = self.lower_connection_label.currentText()
        raw = raw.replace(" Pin", "").replace(" Box", "")
        self.top_connection_label.setText(
            self._modify_connection(raw, side="top")
        )

    def _modify_connection(self, conn, side="lower"):
        """Modifies the connection name based on position and standard rules."""
        if conn.endswith("SR"):
            return f"{conn} {'Box' if side == 'lower' else 'Pin'}"
        elif conn in ["Sondex", "GO 'A'"]:
            return f"{conn} {'Pin' if side == 'lower' else 'Box'}"
        return conn

    # Helper methods for display name (if you need dynamic naming like in PCE editor)
    def set_display_name(self, name: str):
        """Set what's shown on the label (does not affect DB lookups)."""
        self.display_name = name
        self.label.setText(name)

    def get_display_name(self) -> str:
        return self.display_name