from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QCursor, QIcon, QAction
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QComboBox, QLabel, QGraphicsOpacityEffect
from ui.components.toolstring_editor.ui_draggable_button import DraggableButton
from database.logic_database import get_tool_data, get_full_tool_database
from utils.styles import DARK_STYLE
import os

class ToolLibrary(QWidget):
    """Sidebar for listing available tools."""
    def __init__(self, parent=None, drop_zone=None):
        super().__init__(parent)

        self.setStyleSheet(DARK_STYLE)
        self.drop_zone = drop_zone

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # **Search Bar**
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tools...")
        self.search_bar.textChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.search_bar)

        from PyQt6.QtWidgets import QPushButton

        # --- Clear (❌) button setup ---
        self.clear_button = QPushButton("✕", self.search_bar)
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.setVisible(False)
        self.clear_button.setStyleSheet("""
            QPushButton {
                color: white;
                font-size: 14px;
                background-color: transparent;
                border: none;
                padding: 0 6px;
            }
            QPushButton:hover {
                color: #dddddd;
            }
            QPushButton:pressed {
                color: #aaaaaa;
            }
        """)

        # Connect behavior
        self.clear_button.clicked.connect(self.clear_search_bar)

        # --- Position it inside QLineEdit ---
        self.search_bar.setTextMargins(0, 0, 20, 0)  # make room for the button
        self.clear_button.setFixedSize(20, 20)

        def reposition_clear_button():
            """Keep the ❌ button aligned at the right edge of QLineEdit."""
            frame_width = self.search_bar.style().pixelMetric(self.search_bar.style().PixelMetric.PM_DefaultFrameWidth)
            x = self.search_bar.rect().right() - self.clear_button.width() - frame_width - 2
            y = (self.search_bar.height() - self.clear_button.height()) // 2
            self.clear_button.move(x, y)

        self.search_bar.textChanged.connect(lambda text: (
            self.clear_button.setVisible(bool(text.strip())),
            reposition_clear_button()
        ))

        # ✅ safer resize event binding (no tuple return)
        def resize_event(event):
            QLineEdit.resizeEvent(self.search_bar, event)
            reposition_clear_button()

        self.search_bar.resizeEvent = resize_event

        # **Filter Dropdown**
        self.filter_combo = QComboBox()
        self.filter_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        tool_data = get_tool_data()
        self.filter_combo.addItems(["All Tools"] + tool_data["Category"].unique().tolist())

        self.filter_combo.currentTextChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.filter_combo)

        # **Tool List (Scroll Area)**
        self.tool_list_scroll = QScrollArea()
        self.tool_list_scroll.setWidgetResizable(True)
        self.tool_list_widget = QWidget()
        self.tool_list_widget.setStyleSheet("background-color: white; ")
        self.tool_list_layout = QVBoxLayout(self.tool_list_widget)
        self.tool_list_scroll.setWidget(self.tool_list_widget)
        self.tool_list_scroll.setStyleSheet("color: black; ")
        self.layout.addWidget(self.tool_list_scroll)

        # **Tool Count Label**
        self.tool_count_label = QLabel("Showing 0 tools")
        self.tool_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tool_count_label.setStyleSheet("font-size: 10px; font-style: italic;")
        self.layout.addWidget(self.tool_count_label)

        # # Run initial load with a slight delay to ensure sidebar is visible
        # QTimer.singleShot(200, self.update_tool_list)

    # ✅ New helper: toggles ❌ visibility
    def toggle_clear_button(self, text):
        self.clear_action.setVisible(bool(text.strip()))

    # ✅ New helper: clears text when ❌ clicked
    def clear_search_bar(self):
        self.search_bar.clear()
        self.search_bar.setFocus()

    def update_tool_list(self):
        """Updates the tool list based on search input and selected category."""
        selected_category = self.filter_combo.currentText()
        search_text = self.search_bar.text().strip().lower()

        full_df = get_full_tool_database().copy()

        if selected_category != "All Tools":
            full_df = full_df[full_df["Category"] == selected_category]

        if search_text:
            full_df = full_df[full_df["Tool Name"].str.contains(search_text, case=False, na=False)]

        # Clear list
        while self.tool_list_layout.count():
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build unique list with description lookup
        tool_count = 0
        seen = set()
        new_buttons = []
        for _, row in full_df.iterrows():
            tool_name = str(row["Tool Name"])
            if tool_name in seen:
                continue
            seen.add(tool_name)

            description = None
            if "Description" in full_df.columns:
                desc_series = full_df.loc[full_df["Tool Name"] == tool_name, "Description"].dropna()
                if not desc_series.empty:
                    description = str(desc_series.iloc[0]).strip()

            if not description:
                description = self._fallback_description(tool_name, str(row.get("Category", "")))

            btn = DraggableButton(tool_name, dropzone=self.drop_zone, description=description)
            btn.setGraphicsEffect(QGraphicsOpacityEffect(btn))
            btn.graphicsEffect().setOpacity(0)  # Start invisible

            self.tool_list_layout.addWidget(btn)
            new_buttons.append(btn)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tool_count_label.setText(f"Showing {tool_count} tools")

        # Trigger waterfall fade-in
        self.animate_buttons_fade_in(new_buttons)

    def animate_buttons_fade_in(self, buttons):
        """Creates a staggered waterfall fade-in animation for new tool buttons."""
        delay_interval = 80  # milliseconds between each button fade start
        duration = 300  # fade duration per button

        # Keep reference to prevent garbage collection
        if not hasattr(self, "_fade_animations"):
            self._fade_animations = []

        for i, btn in enumerate(buttons):
            effect = btn.graphicsEffect()
            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(duration)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            self._fade_animations.append(anim)

            # Start animation after staggered delay
            QTimer.singleShot(i * delay_interval, anim.start)


def _fallback_description(self, tool_name:str, category:str) -> str:
    name = (tool_name or "").lower()
    cat = (category or "").strip()

    # Very light heuristics so you always get something readable
    if "rope socket" in name:
        return "Connects slickline to the toolstring and transmits tensile load; quick re-heading at surface."
    if "knuckle" in name and "joint" in name:
        return "Articulated joint providing flexibility through deviations and reducing side-loading."
    if "swivel" in name:
        return "Allows the toolstring to rotate and relieve torque; reduces cable twist."
    if "stem" in name or "sinker" in name or "weight bar" in name:
        return "Adds mass to deliver jarring impact energy and stabilise the BHA."
    if "jar" in name and "hydraulic" in name:
        return "Hydraulic time-delay jar for controlled, powerful up/down impacts."
    if "jar" in name:
        return "Mechanical jar delivering impact to free stuck tools or actuate mechanisms."
    if "accelerator" in name or "shock" in name:
        return "Energy-storing shock absorber that boosts jar impact and reduces recoil."
    if "gauge cutter" in name or "drift" in name:
        return "Verifies internal diameter and clears light debris/scale before larger tools."
    if "lead impression" in name or "lib" in name:
        return "Captures an impression of a fish top to identify profile and plan fishing."
    if "wire grab" in name or "wire finder" in name or "scratcher" in name:
        return "Locates and retrieves parted wireline from the wellbore."
    if "spear" in name:
        return "Internal engagement tool (expandable slips) to latch and retrieve a fish."
    if "pulling tool" in name:
        return "Shear-release latch to retrieve devices with internal fishing necks."
    if "running tool" in name:
        return "Latch used to run/set subsurface devices; releases by jarring per tool spec."
    if "x-over" in name or "crossover" in name:
        return "Adapter converting between different connection types/sizes in the string."
    if "kickover" in name or "okot" in name or "ok-6" in name or "merla" in name:
        return "Side-pocket mandrel positioning tool to install/retrieve gas-lift valves."
    if "mit" in name or "multi-finger" in name:
        return "Multi-finger imaging caliper to measure internal tubular geometry and metal loss."
    if "pgr" in name or "gamma ray" in name:
        return "Production gamma-ray tool for lithology/depth correlation and scale detection."
    if "pps" in name and "gauge" in name:
        return "Quartz memory pressure/temperature gauge for slickline-deployed well tests."

    # Generic fallback
    base = "Slickline tool used in {} operations; see procedure/OEM datasheet for specifics."
    return base.format(cat if cat else "wireline")
