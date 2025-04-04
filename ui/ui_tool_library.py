from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QComboBox, QLabel
from ui.ui_draggable_button import DraggableButton
from database.logic_database import get_tool_data
from utils.styles import GLASSMORPHISM_STYLE

class ToolLibrary(QWidget):
    """Sidebar for listing available tools."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setStyleSheet(GLASSMORPHISM_STYLE)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # **Search Bar**
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tools...")
        self.search_bar.textChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.search_bar)

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

        self.update_tool_list()

    def update_tool_list(self):
        """Updates the tool list based on search input and selected category."""
        selected_category = self.filter_combo.currentText()
        search_text = self.search_bar.text().strip().lower()

        tool_data = get_tool_data()
        if selected_category != "All Tools":
            tool_data = tool_data[tool_data["Category"] == selected_category]  

        # **Apply search filter**
        if search_text:
            tool_data = tool_data[tool_data["Tool Name"].str.contains(search_text, case=False, na=False)]

        # **Clear and Repopulate Tool List**
        while self.tool_list_layout.count():
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tool_count = 0
        for tool_name in tool_data["Tool Name"].unique():
            tool_button = DraggableButton(tool_name)
            self.tool_list_layout.addWidget(tool_button)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ✅ Update tool count label
        self.tool_count_label.setText(f"Showing {tool_count} tools")

    def populate_tool_list(self, category):


        """Clears and repopulates the tool list based on category."""
        while self.tool_list_layout.count() > 0:
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tools = get_tool_data()
        if category != "All Tools":
            tools = tools[tools["Category"] == category]

        tool_count = 0
        for tool_name in tools["Tool Name"].unique():
            tool_button = DraggableButton(tool_name)
            self.tool_list_layout.addWidget(tool_button)
            tool_count += 1

        self.tool_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # ✅ Update tool count label
        self.tool_count_label.setText(f"Showing {tool_count} tools")


