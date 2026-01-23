# ui/components/pce_editor/tool_widget.py
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSignalBlocker, QPoint, QMimeData
from PyQt6.QtGui import QPixmap, QCursor, QColor, QMouseEvent, QDrag
from pandas import factorize

from database.logic_database import get_pce_data
from features.editors.logic_image_processing import expand_and_center_images
from utils.path_finder import get_pce_image_path
from utils.styles import COMBO_STYLE, COMBO_STYLE_BLACK


class ToolWidget(QWidget):
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
            self.tool_data = get_pce_data(tool_name)
            if not self.tool_data:
                print(f"⚠️ No data for '{tool_name}'")
                return

            # --- build UI ---
            self.layout = QHBoxLayout(self)
            self.layout.setSpacing(5)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.setContentsMargins(7, 0, 0, 0)

            # image (make draggable)
            self.image_label = QLabel()
            self.image_label.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            pixmap = QPixmap(get_pce_image_path(tool_name))
            self.image_label.setPixmap(pixmap)
            factor = 1
            width = int(round(pixmap.width() * factor))
            height = int(round(pixmap.height() * factor))
            self.image_label.setFixedSize(width, height)
            self.image_label.setStyleSheet("background: transparent; border: none;")
            self.image_label.mousePressEvent = self._image_mouse_press
            self.image_label.mouseMoveEvent = self._image_mouse_move
            self.layout.addWidget(self.image_label)

            # tool name
            self.label = QLabel(tool_name)
            self.label.setFixedSize(113, 35)
            self.label.setWordWrap(True)
            self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.label.setStyleSheet(
                "border: 0; border-bottom: 1px solid #A9A9A9; background: lightgray; color: black;"
            )
            self.layout.addWidget(self.label)

            # --- combos ---
            self.brand_label = QComboBox()
            self.brand_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.brand_label.setFixedWidth(85)
            self.brand_label.setStyleSheet(COMBO_STYLE_BLACK)
            self.layout.addWidget(self.brand_label)

            self.nominal_size_selector = QComboBox()
            self.nominal_size_selector.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.nominal_size_selector.setFixedWidth(64)
            self.nominal_size_selector.setStyleSheet(COMBO_STYLE_BLACK)
            self.layout.addWidget(self.nominal_size_selector)

            self.id_label = QLabel("N/A");
            self.id_label.setFixedWidth(44)
            self.id_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
            self.id_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.id_label)

            self.service_label = QComboBox()
            self.service_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.service_label.setFixedWidth(60)
            self.service_label.setStyleSheet(COMBO_STYLE_BLACK)
            self.layout.addWidget(self.service_label)

            # Working Pressure
            self.wp_label = QLabel("N/A");
            self.wp_label.setFixedWidth(65)
            self.wp_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
            self.wp_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.wp_label)

            # metrics
            self.length_label = QLabel("N/A");
            self.length_label.setFixedWidth(55)
            self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
            self.length_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.length_label)

            self.weight_label = QLabel("N/A");
            self.weight_label.setFixedWidth(65)
            self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter);
            self.weight_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.weight_label)

            # connections
            self.top_connection_label = QLabel("N/A")
            self.top_connection_label.setFixedWidth(70)
            self.top_connection_label.setWordWrap(True)
            self.top_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_connection_label.setStyleSheet("border:none; color:black;")
            font = self.top_connection_label.font()
            font.setPointSize(8)
            self.top_connection_label.setFont(font)
            self.layout.addWidget(self.top_connection_label)

            self.lower_connection_label = QLabel("N/A")
            self.lower_connection_label.setFixedWidth(70)
            self.lower_connection_label.setWordWrap(True)
            self.lower_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lower_connection_label.setStyleSheet("border:none; color:black;")
            font = self.lower_connection_label.font()
            font.setPointSize(8)
            self.lower_connection_label.setFont(font)
            self.layout.addWidget(self.lower_connection_label)

            # Remove move up/down and delete buttons entirely

            # Apply layout and update details
            self.setLayout(self.layout)
            self.init_brand_size_service_combos()

            # Connect signals
            self.brand_label.currentTextChanged.connect(self.on_brand_changed)
            self.nominal_size_selector.currentTextChanged.connect(self.on_size_changed)
            self.service_label.currentTextChanged.connect(self.on_service_changed)

            # Update tool info
            self.update_tool_info()
        except Exception as e:
            print(e)

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

    def _modify_connection(self, conn, side="lower"):
        """Modifies the connection name based on position and standard rules."""
        try:
            if "MCEvoy" in self.tool_name:
                return f"{conn} {'Pin' if side == 'lower' else 'Box'}"
            else:
                return f"{conn} {'Pin & Collar' if side == 'lower' else 'Box'}"
        except Exception as e:
            print(e)

    # REMOVED: move_up, move_down, and remove_tool methods

    def init_brand_size_service_combos(self):
        brands = self.tool_data.get("brands", [])

        with QSignalBlocker(self.brand_label):
            self.brand_label.clear()
            self.brand_label.addItems(brands)

            # --- Priority selection logic ---
            preferred_brand = None
            if "NOV" in brands:
                preferred_brand = "NOV"
            elif "RMZ" in brands:
                preferred_brand = "RMZ"
            elif brands:
                preferred_brand = brands[0]

            if preferred_brand:
                self.brand_label.setCurrentText(preferred_brand)

        # --- Populate size & service combos based on selected brand ---
        brand = self.brand_label.currentText() if brands else ""
        self._rebuild_sizes_for_brand(brand)
        size = self.nominal_size_selector.currentText()
        self._rebuild_services_for(brand, size)

    def _rebuild_sizes_for_brand(self, brand):
        sizes = self.tool_data.get("sizes_by_brand", {}).get(brand, [])
        with QSignalBlocker(self.nominal_size_selector):
            current = self.nominal_size_selector.currentText()
            self.nominal_size_selector.clear()
            self.nominal_size_selector.addItems(sizes)
            if current not in sizes and sizes:
                self.nominal_size_selector.setCurrentText(sizes[0])

    def _rebuild_services_for(self, brand, size):
        services_map = self.tool_data.get("services_by_brand_size", {})
        services = services_map.get(brand, {}).get(size, [])
        with QSignalBlocker(self.service_label):
            current = self.service_label.currentText()
            self.service_label.clear()
            self.service_label.addItems(services)
            if services and current not in services:
                self.service_label.setCurrentText(services[0])

    # -------- signal handlers --------
    def on_brand_changed(self, brand):
        self._rebuild_sizes_for_brand(brand)
        size = self.nominal_size_selector.currentText()
        self._rebuild_services_for(brand, size)
        self.update_tool_info()
        if self.summary_widget: self.summary_widget.update_summary()

    def on_size_changed(self, size):
        brand = self.brand_label.currentText()
        self._rebuild_services_for(brand, size)
        self.update_tool_info()
        if self.summary_widget: self.summary_widget.update_summary()

    def on_service_changed(self, _):
        self.update_tool_info()
        if self.summary_widget: self.summary_widget.update_summary()

    # -------- record lookup & UI refresh --------
    def _lookup_record(self, brand, size, service):
        recs = self.tool_data.get("records", {})
        if (brand, size, service) in recs:
            return recs[(brand, size, service)]
        # fallback to any record for (brand,size)
        for (b, s, _svc), rec in recs.items():
            if b == brand and s == size:
                return rec
        return None

    def update_tool_info(self):
        brand = self.brand_label.currentText()
        size = self.nominal_size_selector.currentText()
        service = self.service_label.currentText()

        rec = self._lookup_record(brand, size, service)
        if not rec:
            self.length_label.setText("N/A")
            self.weight_label.setText("N/A")
            self.top_connection_label.setText("N/A")
            self.lower_connection_label.setText("-")
            return

        self.id_label.setText(f"{float(rec.get('ID', 0)):.3f}\"")
        self.length_label.setText(f"{float(rec.get('Length', 0)):.1f} ft")
        self.weight_label.setText(f"{float(rec.get('Weight', 0)):.1f} kg")
        self.wp_label.setText(rec.get('Working Pressure', 0))

        lowers = [x.strip() for x in rec.get("Lower Connections", []) if x and x.lower() != "nan"]
        tops = [x.strip() for x in rec.get("Top Connections", []) if x and x.lower() != "nan"]

        lower_text = self._modify_connection(lowers[0], "lower") if lowers else "-"
        if lowers and tops and set(lowers) == set(tops):
            top_text = self._modify_connection(lowers[0], "top")
        else:
            top_text = self._modify_connection(tops[0], "top") if tops else "-"

        self.lower_connection_label.setText(lower_text)
        self.top_connection_label.setText(top_text)

    # Helper methods for display name
    def set_display_name(self, name: str):
        """Set what's shown on the label (does not affect DB lookups)."""
        self.display_name = name
        self.label.setText(name)

    def get_display_name(self) -> str:
        return self.display_name