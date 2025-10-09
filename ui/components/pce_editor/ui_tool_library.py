from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QComboBox, QLabel, QGraphicsOpacityEffect, QPushButton
from ui.components.pce_editor.ui_draggable_button import DraggableButton
from database.logic_database_pce import get_tool_data, get_full_tool_database
from utils.styles import DARK_STYLE


class ToolLibrary(QWidget):
    """Sidebar for listing available PCE tools."""
    def __init__(self, parent=None, drop_zone=None):
        super().__init__(parent)

        self.setStyleSheet(DARK_STYLE)
        self.drop_zone = drop_zone

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # **Search Bar**
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search PCE...")
        self.layout.addWidget(self.search_bar)

        # --- Clear Button (❌) inside QLineEdit ---
        self.clear_button = QPushButton("✕", self.search_bar)
        self.clear_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #aaaaaa;
                font-size: 13px;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        self.clear_button.setVisible(False)
        self.clear_button.clicked.connect(lambda: self.search_bar.clear())

        self.search_bar.setTextMargins(0, 0, 20, 0)  # room for ❌
        self.clear_button.setFixedSize(20, 20)

        def reposition_clear_button():
            """Keep ❌ aligned to right edge of QLineEdit."""
            frame_width = self.search_bar.style().pixelMetric(self.search_bar.style().PixelMetric.PM_DefaultFrameWidth)
            x = self.search_bar.rect().right() - self.clear_button.width() - frame_width - 2
            y = (self.search_bar.height() - self.clear_button.height()) // 2
            self.clear_button.move(x, y)

        def resize_event(event):
            QLineEdit.resizeEvent(self.search_bar, event)
            reposition_clear_button()

        self.search_bar.resizeEvent = resize_event

        self.search_bar.textChanged.connect(lambda text: (
            self.clear_button.setVisible(bool(text.strip())),
            reposition_clear_button(),
            self.update_tool_list()
        ))

        # **Filter Dropdown**
        self.filter_combo = QComboBox()
        self.filter_combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        tool_data = get_tool_data()
        self.filter_combo.addItems(["All PCE"] + tool_data["Category"].unique().tolist())
        self.filter_combo.currentTextChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.filter_combo)

        # **Tool List (Scroll Area)**
        self.tool_list_scroll = QScrollArea()
        self.tool_list_scroll.setWidgetResizable(True)
        self.tool_list_widget = QWidget()
        self.tool_list_widget.setStyleSheet("background-color: white;")
        self.tool_list_layout = QVBoxLayout(self.tool_list_widget)
        self.tool_list_scroll.setWidget(self.tool_list_widget)
        self.tool_list_scroll.setStyleSheet("color: black;")
        self.layout.addWidget(self.tool_list_scroll)

        # **Tool Count Label**
        self.tool_count_label = QLabel("Showing 0 PCE")
        self.tool_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tool_count_label.setStyleSheet("font-size: 10px; font-style: italic;")
        self.layout.addWidget(self.tool_count_label)

        # Run initial load with fade animation after short delay
        QTimer.singleShot(200, self.update_tool_list)

    def update_tool_list(self):
        """Updates the tool list based on search input and selected category."""
        selected_category = self.filter_combo.currentText()
        search_text = self.search_bar.text().strip().lower()

        full_df = get_full_tool_database().copy()

        if selected_category != "All PCE":
            full_df = full_df[full_df["Category"] == selected_category]

        if search_text:
            full_df = full_df[full_df["Tool Name"].str.contains(search_text, case=False, na=False)]

        # Clear old widgets
        while self.tool_list_layout.count():
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build new list
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
                description = "TBC"

            # Create button
            btn = DraggableButton(tool_name, dropzone=self.drop_zone, description=description)
            btn.setGraphicsEffect(QGraphicsOpacityEffect(btn))
            btn.graphicsEffect().setOpacity(0)  # Start invisible

            self.tool_list_layout.addWidget(btn)
            new_buttons.append(btn)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tool_count_label.setText(f"Showing {tool_count} PCE")

        # Animate waterfall fade-in
        self.animate_buttons_fade_in(new_buttons)

    def animate_buttons_fade_in(self, buttons):
        """Creates a staggered waterfall fade-in animation for new tool buttons."""
        delay_interval = 80  # ms between each button fade start
        duration = 300  # fade duration per button

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
            QTimer.singleShot(i * delay_interval, anim.start)
