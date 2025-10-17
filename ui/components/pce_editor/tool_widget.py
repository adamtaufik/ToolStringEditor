from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QComboBox, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSignalBlocker
from PyQt6.QtGui import QPixmap, QCursor, QColor
from pandas import factorize

from database.logic_database import get_pce_data
from features.editors.logic_image_processing import expand_and_center_images
from utils.path_finder import get_pce_image_path  # ✅ Import helper function
from utils.styles import COMBO_STYLE, COMBO_STYLE_BLACK


class ToolWidget(QWidget):
    def __init__(self, tool_name, drop_zone, summary_widget=None):
        super().__init__(drop_zone)

        try:
            self.tool_name = tool_name

            self.base_name = tool_name  # immutable source name for logic
            self.display_name = tool_name  # what the user sees

            self.drop_zone = drop_zone
            self.summary_widget = summary_widget

            # --- load DB first ---
            self.tool_data = get_pce_data(tool_name)
            if not self.tool_data:
                print(f"⚠️ No data for '{tool_name}'")
                return

            # --- build UI (all widgets must exist before we fill them) ---
            self.layout = QHBoxLayout(self)
            self.layout.setSpacing(5)
            self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.setContentsMargins(7, 0, 0, 0)

            # image
            self.image_label = QLabel()
            pixmap = QPixmap(get_pce_image_path(tool_name))
            self.image_label.setPixmap(pixmap)
            # factors = {'3.5"':0.8,
            #            '4.5"':0.85,
            #            '5.5"':0.9,
            #            '7"':1}
            # factor = factors[self.nominal_size_selector]
            factor = 1
            width = pixmap.width() * factor
            height = pixmap.height() * factor
            self.image_label.setFixedSize(width, height)
            self.image_label.setStyleSheet("background: transparent; border: none;")
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

            # --- combos (create first, fill later) ---
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

            self.id_label = QLabel("N/A"); self.id_label.setFixedWidth(44)
            self.id_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.id_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.id_label)

            self.service_label = QComboBox()
            self.service_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.service_label.setFixedWidth(60)
            self.service_label.setStyleSheet(COMBO_STYLE_BLACK)
            self.layout.addWidget(self.service_label)

            # Working Pressure
            self.wp_label = QLabel("N/A"); self.wp_label.setFixedWidth(65)
            self.wp_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.wp_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.wp_label)

            # metrics
            self.length_label = QLabel("N/A"); self.length_label.setFixedWidth(55)
            self.length_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.length_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.length_label)

            self.weight_label = QLabel("N/A"); self.weight_label.setFixedWidth(65)
            self.weight_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.weight_label.setStyleSheet("border:none;color:black;")
            self.layout.addWidget(self.weight_label)

            # --- connections (labels now; both wrap) ---
            self.top_connection_label = QLabel("N/A")
            self.top_connection_label.setFixedWidth(70)
            self.top_connection_label.setWordWrap(True)  # ← enable wrapping
            self.top_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_connection_label.setStyleSheet("border:none; color:black;")
            font = self.top_connection_label.font()
            font.setPointSize(8)  # Set the desired font size
            self.top_connection_label.setFont(font)
            self.layout.addWidget(self.top_connection_label)

            self.lower_connection_label = QLabel("N/A")  # ← was QComboBox before
            self.lower_connection_label.setFixedWidth(70)
            self.lower_connection_label.setWordWrap(True)  # ← enable wrapping
            self.lower_connection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lower_connection_label.setStyleSheet("border:none; color:black;")
            font = self.lower_connection_label.font()
            font.setPointSize(8)  # Set the desired font size
            self.lower_connection_label.setFont(font)
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

            def _make_shadow():
                eff = QGraphicsDropShadowEffect(self)
                eff.setBlurRadius(10)
                eff.setXOffset(2)
                eff.setYOffset(2)
                eff.setColor(QColor(50, 50, 50, 100))
                return eff

            self.up_button.setGraphicsEffect(_make_shadow())
            self.down_button.setGraphicsEffect(_make_shadow())
            self.remove_button.setGraphicsEffect(_make_shadow())
            # (optional) self.label.setGraphicsEffect(_make_shadow())

            # **Apply layout and update details**
            self.setLayout(self.layout)
            # --- now that widgets exist, populate them ---
            self.init_brand_size_service_combos()   # fills brand -> size -> service

            # --- connect signals AFTER initial population ---
            self.brand_label.currentTextChanged.connect(self.on_brand_changed)
            self.nominal_size_selector.currentTextChanged.connect(self.on_size_changed)
            self.service_label.currentTextChanged.connect(self.on_service_changed)

            # finish: paint current record
            self.update_tool_info()
        except Exception as e:
            print(e)

    def _modify_connection(self, conn, side="lower"):
        """Modifies the connection name based on position and standard rules."""
        try:
            if "MCEvoy" in self.tool_name:
                return f"{conn} {'Pin' if side == 'lower' else 'Box'}"
            else:
                return f"{conn} {'Pin & Collar' if side == 'lower' else 'Box'}"
        except Exception as e:
            print(e)

    def move_up(self):
        index = self.drop_zone.layout.indexOf(self)
        if index > 0:
            self.drop_zone.layout.insertWidget(index - 1, self)
        self.drop_zone.refresh_dynamic_names()  # ← NEW
        if self.summary_widget:
            self.summary_widget.update_summary()

    def move_down(self):
        index = self.drop_zone.layout.indexOf(self)
        if index < self.drop_zone.layout.count() - 1:
            self.drop_zone.layout.insertWidget(index + 1, self)
        self.drop_zone.refresh_dynamic_names()  # ← NEW
        if self.summary_widget:
            self.summary_widget.update_summary()

    def remove_tool(self):
        if self in self.drop_zone.tool_widgets:
            self.drop_zone.tool_widgets.remove(self)
        self.setParent(None)
        self.deleteLater()
        expand_and_center_images(self.drop_zone.tool_widgets, self.drop_zone.diagram_width)
        self.drop_zone.update_placeholder()
        self.drop_zone.refresh_dynamic_names()  # ← NEW
        if self.summary_widget:
            self.summary_widget.update_summary()

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
        # Optional: hide service combo if empty
        # self.service_label.setVisible(bool(services))

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
            self.lower_connection_label.setText("-")  # label now
            return

        self.id_label.setText(f"{float(rec.get('ID', 0)):.3f}\"")
        self.length_label.setText(f"{float(rec.get('Length', 0)):.1f} ft")
        self.weight_label.setText(f"{float(rec.get('Weight', 0)):.1f} kg")
        self.wp_label.setText(rec.get('Working Pressure', 0))

        lowers = [x.strip() for x in rec.get("Lower Connections", []) if x and x.lower() != "nan"]
        tops = [x.strip() for x in rec.get("Top Connections", []) if x and x.lower() != "nan"]

        # choose what to display in labels
        # (current behavior: show the first available option; wrapping handles long names)
        lower_text = self._modify_connection(lowers[0], "lower") if lowers else "-"
        if lowers and tops and set(lowers) == set(tops):
            # if sets are the same, mirror the lower (no selection now, so we mirror the first)
            top_text = self._modify_connection(lowers[0], "top")
        else:
            top_text = self._modify_connection(tops[0], "top") if tops else "-"

        # if you prefer to show ALL options, switch to:
        # lower_text = "\n".join(self._modify_connection(c, "lower") for c in lowers) if lowers else "-"
        # top_text   = "\n".join(self._modify_connection(c, "top")   for c in (lowers if set(lowers)==set(tops) else tops)) if (lowers or tops) else "-"

        self.lower_connection_label.setText(lower_text)
        self.top_connection_label.setText(top_text)

    # add these helper methods to ToolWidget:
    def set_display_name(self, name: str):
        """Set what’s shown on the label (does not affect DB lookups)."""
        self.display_name = name
        self.label.setText(name)

    def get_display_name(self) -> str:
        return self.display_name