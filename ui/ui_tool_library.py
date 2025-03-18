from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QScrollArea, QComboBox
from ui.ui_draggable_button import DraggableButton
from database.logic_database import get_tool_data

class ToolLibrary(QWidget):
    """Sidebar for listing available tools."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # self.layout.setContentsMargins(10, 10, 10, 10)
        # self.layout.setSpacing(10)

        # **Search Bar**
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search tools...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                color: white;
                border: 1px solid white;
                padding: 5px;
                background-color: transparent;
                border-radius: 5px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.7);
            }
        """)
        self.search_bar.textChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.search_bar)

        # **Filter Dropdown**
        self.filter_combo = QComboBox()
        tool_data = get_tool_data()  
        self.filter_combo.addItems(["All Tools"] + tool_data["Category"].unique().tolist())
        self.filter_combo.setStyleSheet("""
            QComboBox {
                color: white;
                background-color: transparent;
                border: 1px solid white;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self.update_tool_list)
        self.layout.addWidget(self.filter_combo)

        # **Tool List (Scroll Area)**
        self.tool_list_scroll = QScrollArea()
        self.tool_list_scroll.setWidgetResizable(True)
        self.tool_list_widget = QWidget()
        self.tool_list_layout = QVBoxLayout(self.tool_list_widget)
        self.tool_list_scroll.setWidget(self.tool_list_widget)
        self.layout.addWidget(self.tool_list_scroll)

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

        for tool_name in tool_data["Tool Name"].unique():
            tool_button = DraggableButton(tool_name)
            self.tool_list_layout.addWidget(tool_button)

    def populate_tool_list(self, category):
        """Clears and repopulates the tool list based on category."""
        while self.tool_list_layout.count() > 0:
            item = self.tool_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tools = get_tool_data()
        if category != "All Tools":
            tools = tools[tools["Category"] == category]

        for tool_name in tools["Tool Name"].unique():
            tool_button = DraggableButton(tool_name)
            self.tool_list_layout.addWidget(tool_button)


