# ui/components/toolstring_editor/dropzone.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QWidget
from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap

from features.editors.logic_image_processing import expand_and_center_images
from utils.screen_info import get_height
from utils.styles import DROPZONE_STYLE, DROPZONE_HEADERS
from utils.path_finder import get_icon_path


class DropZone(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.total_dropzone_height = get_height() - 55
        self.diagram_width = 130  # Adjust as needed
        self.drag_item = None
        self.drag_start_pos = None
        self.drop_pos_index = -1

        self.main_window = parent
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.setStyleSheet(DROPZONE_STYLE)
        self.setAcceptDrops(True)

        self.tool_widgets = []  # List to store tool widgets

        # ✅ Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Header Row** - Updated for tool string editor columns
        header_layout = QHBoxLayout()
        headers = [
            ("Diagram", 140), ("Item", 120), ("Nominal Size", 90),
            ("OD (in)", 70), ("Length (ft)", 65), ("Weight (lbs)", 72),
            ("Top Conn.", 90), ("Bottom Conn", 130)
        ]

        for header_text, width in headers:
            label = QLabel(header_text)
            label.setStyleSheet(DROPZONE_HEADERS)
            label.setFixedSize(width, 30)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            header_layout.addWidget(label)
            header_layout.setContentsMargins(0, 0, 0, 0)

        container_layout = QVBoxLayout()
        container_layout.addLayout(header_layout)
        container_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.addLayout(container_layout)

        # **Trash Area Container** - Same as PCE editor
        trash_container = QWidget()
        trash_container.setFixedSize(50, self.total_dropzone_height)
        trash_container.setStyleSheet("background-color: rgba(255, 0, 0, 30); border: 2px solid red;")
        trash_container.hide()
        trash_container.setAcceptDrops(False)
        trash_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        trash_layout = QVBoxLayout(trash_container)
        trash_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Trash icon
        trash_icon = QLabel()
        trash_pixmap = QPixmap(get_icon_path('delete'))
        trash_icon.setPixmap(trash_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
        trash_layout.addWidget(trash_icon)

        trash_label = QLabel("Drop here\nto delete")
        trash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        trash_label.setStyleSheet("color: red; font-weight: bold; font-size: 10px;")
        trash_label.setWordWrap(True)
        # trash_layout.addWidget(trash_label)

        self.trash_area = trash_container

        # Main content area with trash area on right
        content_area = QWidget()
        content_area.setStyleSheet("border: none;")
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left side - tools area
        tools_area = QWidget()
        tools_area.setStyleSheet("border: none;")
        tools_layout = QVBoxLayout(tools_area)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(0)
        tools_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Tools Layout** - This is where tools will be added
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tools_layout.addLayout(self.layout)

        # Drop indicator line (hidden by default)
        self.drop_indicator = QFrame()
        self.drop_indicator.setFixedHeight(3)
        self.drop_indicator.setStyleSheet(
            "background-color: #00AEEF; border-radius: 1px;"
        )
        self.drop_indicator.hide()

        # **Top spacer** - To push placeholder to middle when empty
        self.top_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        tools_layout.addItem(self.top_spacer)

        # **Placeholder Label** - Below the tools (initially shown when empty)
        self.placeholder_label = QLabel("Drag tools here")
        self.placeholder_label.setStyleSheet(
            "color: lightgray; font-size: 50px; background-color: transparent; border: none;")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tools_layout.addWidget(self.placeholder_label)

        # **Bottom spacer** - To push placeholder to middle when empty
        self.bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        tools_layout.addItem(self.bottom_spacer)

        content_layout.addWidget(tools_area)
        content_layout.addWidget(self.trash_area)

        self.main_layout.addWidget(content_area)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(0)

    def showEvent(self, event):
        """Animate the DropZone expanding into view on startup."""
        super().showEvent(event)

        if getattr(self, "_startup_animated", False):
            return
        self._startup_animated = True

        start_height = 0
        end_height = self.total_dropzone_height
        height_anim = QPropertyAnimation(self, b"maximumHeight")
        height_anim.setDuration(700)
        height_anim.setStartValue(start_height)
        height_anim.setEndValue(end_height)
        height_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        height_anim.start()
        self._animations = [height_anim]

    def dragEnterEvent(self, event):
        """Allow drag if MIME data has text."""
        if event.mimeData().hasText():
            self.setStyleSheet("background-color: #363737; border: 2px dashed white; border-radius: 5px;")
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(DROPZONE_STYLE)
        self.trash_area.hide()
        if hasattr(self, 'drop_indicator'):
            self.layout.removeWidget(self.drop_indicator)
            self.drop_indicator.hide()

    def dragMoveEvent(self, event):
        """Handle drag move for reordering and deletion."""
        if event.mimeData().hasText() and event.mimeData().text().startswith("internal_move:"):
            # Internal drag for reordering
            pos = event.position().toPoint()

            # Always show trash area during internal drag
            if not self.trash_area.isVisible():
                self.trash_area.show()

            # Convert position to trash area coordinates
            pos_in_trash = self.trash_area.mapFromParent(pos)

            # Check if dragging over trash area
            if self.trash_area.rect().contains(pos_in_trash):
                self.trash_area.setStyleSheet("background-color: rgba(255, 0, 0, 80); border: 2px solid red;")
                event.setDropAction(Qt.DropAction.MoveAction)
                event.accept()
            else:
                self.trash_area.setStyleSheet("background-color: rgba(255, 0, 0, 30); border: 2px solid red;")
                # Calculate drop position for reordering
                self._show_drop_indicator(pos)
                event.setDropAction(Qt.DropAction.MoveAction)

            event.accept()
        elif event.mimeData().hasText():
            # External drag from library
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handles dropping tools into DropZone."""
        mime_data = event.mimeData()
        text = mime_data.text()

        # Remove drop indicator
        if hasattr(self, 'drop_indicator'):
            self.layout.removeWidget(self.drop_indicator)
            self.drop_indicator.hide()

        if text.startswith("internal_move:"):
            # Handle reordering or deletion
            tool_index = int(text.split(":")[1])

            # Get the drop position
            drop_pos = event.position().toPoint()
            pos_in_trash = self.trash_area.mapFromParent(drop_pos)

            # Check if dropped inside trash area
            if self.trash_area.isVisible() and self.trash_area.rect().contains(pos_in_trash):
                print("Dropped in trash area")
                # Delete the tool
                if 0 <= tool_index < len(self.tool_widgets):
                    tool = self.tool_widgets[tool_index]
                    print(f"Deleting tool: {tool.tool_name}")
                    self.tool_widgets.remove(tool)
                    self.layout.removeWidget(tool)
                    tool.setParent(None)
                    tool.deleteLater()
                    expand_and_center_images(self.tool_widgets, self.diagram_width)
                    self.update_placeholder()
                    if self.main_window.summary_widget:
                        self.main_window.summary_widget.update_summary()
                self.trash_area.hide()
                event.accept()
                self.setStyleSheet(DROPZONE_STYLE)
                return

            # If not in trash area, reorder the tool
            self._handle_reorder(tool_index, drop_pos)
            self.trash_area.hide()
        else:
            # Handle new tool from library
            tool_name = text
            self.add_tool(tool_name)

        event.acceptProposedAction()
        self.setStyleSheet(DROPZONE_STYLE)

    def _handle_reorder(self, source_index, drop_pos):
        """Reorder tools based on drop position."""
        if source_index < 0 or source_index >= len(self.tool_widgets):
            return

        source_tool = self.tool_widgets[source_index]

        # Find target position (where to insert)
        target_index = self._find_drop_index(drop_pos)
        if target_index == -1 or target_index == source_index:
            return

        # Adjust for removal before insertion
        if target_index > source_index:
            # When moving down, the target index decreases by 1 after removal
            target_index -= 1

        # Remove from old position
        self.tool_widgets.remove(source_tool)
        self.layout.removeWidget(source_tool)

        # Insert at new position (clamp to valid range)
        if target_index < 0:
            target_index = 0
        elif target_index > len(self.tool_widgets):
            target_index = len(self.tool_widgets)

        self.tool_widgets.insert(target_index, source_tool)
        self.layout.insertWidget(target_index, source_tool)

        expand_and_center_images(self.tool_widgets, self.diagram_width)
        if self.main_window.summary_widget:
            self.main_window.summary_widget.update_summary()

    def _find_drop_index(self, pos):
        """Find the index where tool should be dropped (0 = top)."""
        # Find which tool widget the drop position is over
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'tool_name'):  # Check if it's a ToolWidget
                    widget_rect = widget.geometry()
                    # Check if drop position is in the top half of the widget
                    if pos.y() < widget_rect.top() + widget_rect.height() / 2:
                        return i
        # If not found, drop at the end
        return self.layout.count()

    def _show_drop_indicator(self, pos: QPoint):
        """Show a horizontal line indicating where the tool will be dropped."""
        layout = self.layout

        # Remove indicator if already present
        layout.removeWidget(self.drop_indicator)

        insert_index = self._find_drop_index(pos)

        # Clamp index
        insert_index = max(0, min(insert_index, layout.count()))

        layout.insertWidget(insert_index, self.drop_indicator)
        self.drop_indicator.show()

    def add_tool(self, tool_name):
        """Add a new tool to the drop zone at the BOTTOM (end of list)."""
        # Import here to avoid circular imports
        from ui.components.toolstring_editor.tool_widget import ToolWidget

        new_tool = ToolWidget(tool_name, self, self.main_window.summary_widget)
        if new_tool.tool_data:
            # Append to the END (bottom) instead of the top
            self.tool_widgets.append(new_tool)
            self.layout.addWidget(new_tool)
            self.setStyleSheet(DROPZONE_STYLE)
            self.update_placeholder()
            if self.main_window.summary_widget:
                self.main_window.summary_widget.update_summary()
            expand_and_center_images(self.tool_widgets, self.diagram_width, False, 0.5)
        else:
            print(f"⚠️ ERROR: Tool '{tool_name}' not found in database!")

    def clear_tools(self):
        """Clear all tools from the drop zone."""
        for tool in self.tool_widgets:
            self.layout.removeWidget(tool)
            tool.setParent(None)
            tool.deleteLater()
        self.tool_widgets.clear()
        if self.main_window.summary_widget:
            self.main_window.summary_widget.update_summary()
        self.update_placeholder()

    def update_placeholder(self):
        """Show or hide the placeholder text and keep it vertically centered when empty."""
        if not hasattr(self, 'placeholder_label'):
            return

        tools_layout = self.placeholder_label.parentWidget().layout()

        if self.tool_widgets:
            # Hide placeholder and spacers
            self.placeholder_label.hide()

            # Remove spacers if they exist
            if hasattr(self, 'top_spacer'):
                tools_layout.removeItem(self.top_spacer)
            if hasattr(self, 'bottom_spacer'):
                tools_layout.removeItem(self.bottom_spacer)

        else:
            # Show placeholder and spacers
            self.placeholder_label.show()

            # Ensure spacers are added in correct order
            if hasattr(self, 'top_spacer') and tools_layout.indexOf(self.top_spacer) == -1:
                tools_layout.insertItem(1, self.top_spacer)

            if tools_layout.indexOf(self.placeholder_label) == -1:
                tools_layout.insertWidget(2, self.placeholder_label)

            if hasattr(self, 'bottom_spacer') and tools_layout.indexOf(self.bottom_spacer) == -1:
                tools_layout.insertItem(3, self.bottom_spacer)

    def start_drag(self, tool_widget):
        """Initiate drag for a tool widget."""
        index = self.tool_widgets.index(tool_widget) if tool_widget in self.tool_widgets else -1
        if index == -1:
            return

        # Show trash area
        self.trash_area.show()

        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"internal_move:{index}")
        drag.setMimeData(mime_data)

        # Create drag pixmap (thumbnail of the tool)
        pixmap = tool_widget.image_label.pixmap()
        if pixmap:
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

        # Execute drag
        drag.exec(Qt.DropAction.MoveAction)
        self.trash_area.hide()