from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QComboBox, QLabel
from ui.components.pce_editor.ui_draggable_button import DraggableButton
from database.logic_database_pce import get_tool_data, get_full_tool_database
from utils.styles import DARK_STYLE

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
        self.search_bar.setPlaceholderText("Search PCE...")
        self.search_bar.textChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.search_bar)

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

        self.update_tool_list()

    def update_tool_list(self):
        """Updates the tool list based on search input and selected category."""
        selected_category = self.filter_combo.currentText()
        search_text = self.search_bar.text().strip().lower()

        # Use full DB so we can see 'Description' if it exists
        full_df = get_full_tool_database().copy()

        if selected_category != "All PCE":
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
        for _, row in full_df.iterrows():
            tool_name = str(row["Tool Name"])
            if tool_name in seen:
                continue
            seen.add(tool_name)

            # Prefer row Description; else try a quick heuristic fallback
            description = None
            if "Description" in full_df.columns:
                desc_series = full_df.loc[full_df["Tool Name"] == tool_name, "Description"].dropna()
                if not desc_series.empty:
                    description = str(desc_series.iloc[0]).strip()

            if not description:
                description = "TBC"

            btn = DraggableButton(tool_name, dropzone=self.drop_zone, description=description)
            self.tool_list_layout.addWidget(btn)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tool_count_label.setText(f"Showing {tool_count} tools")

    def populate_tool_list(self, category):
        """Clears and repopulates the tool list based on category."""
        while self.tool_list_layout.count() > 0:
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        full_df = get_full_tool_database().copy()
        if category != "All Tools":
            full_df = full_df[full_df["Category"] == category]

        tool_count = 0
        seen = set()
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

            btn = DraggableButton(tool_name, dropzone=self.drop_zone, description=description)
            self.tool_list_layout.addWidget(btn)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tool_count_label.setText(f"Showing {tool_count} tools")
