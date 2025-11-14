from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QTimer

from features.editors.logic_image_processing import expand_and_center_images
from ui.components.pce_editor.tool_widget import ToolWidget
from utils.screen_info import get_height
from utils.styles import DROPZONE_STYLE, DROPZONE_HEADERS


class DropZone(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.total_dropzone_height = get_height() - 55
        self.diagram_width = 140

        self.main_window = parent
        self.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.setStyleSheet(DROPZONE_STYLE)
        self.setAcceptDrops(True)

        self.tool_widgets = []  # List to store tool widgets

        # ✅ Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # **Header Row**
        header_layout = QHBoxLayout()
        headers = [
            ("Diagram", 144), ("Item", 115), ("Brand", 87), ("Size", 65), ("ID", 45), ("Service", 65),
            ("WP (psi)", 65), ("Length", 55), ("Weight", 70),
            ("Top Conn.", 72), ("Bottom Conn", 72), ("Move", 80), ("Del", 33)
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

        # **Stretch placeholder (initially empty, later added/removed)**
        self.top_spacer = QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.top_spacer)  # Initially added

        # **Placeholder Label**
        self.placeholder_label = QLabel("Drag PCE here")
        self.placeholder_label.setStyleSheet("color: lightgray; font-size: 50px; background-color: transparent; border: none;")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.placeholder_label)  # Initially shown

        # **Bottom spacer (re-added when empty)**
        self.bottom_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.main_layout.addItem(self.bottom_spacer)  # Initially added

        # **Tools Layout**
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.layout)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(0)

        self.setFixedSize(self.size())  # freezes the entire window size

    # ---------------- ANIMATION ON STARTUP ---------------- #
    def showEvent(self, event):
        """Animate the DropZone expanding into view on startup."""
        super().showEvent(event)

        if getattr(self, "_startup_animated", False):
            return
        self._startup_animated = True  # prevent replay

        # # --- Step 1: Fade-in effect ---
        # opacity_effect = QGraphicsOpacityEffect(self)
        # self.setGraphicsEffect(opacity_effect)
        # opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
        # opacity_anim.setDuration(600)
        # opacity_anim.setStartValue(0)
        # opacity_anim.setEndValue(1)
        # opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # --- Step 2: Height expansion ---
        start_height = 0
        end_height = self.total_dropzone_height
        height_anim = QPropertyAnimation(self, b"maximumHeight")
        height_anim.setDuration(700)
        height_anim.setStartValue(start_height)
        height_anim.setEndValue(end_height)
        height_anim.setEasingCurve(QEasingCurve.Type.OutBack)  # smooth overshoot

        # --- Step 3: Chain animations cleanly ---
        height_anim.start()
        # QTimer.singleShot(150, opacity_anim.start)

        # Keep references to prevent garbage collection
        # self._animations = [height_anim, opacity_anim]
        self._animations = [height_anim]

    def dragEnterEvent(self, event):
        """Allow drag if MIME data has text."""
        if event.mimeData().hasText():
            self.setStyleSheet("background-color: #363737; border: 2px dashed white; border-radius: 5px;")
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(DROPZONE_STYLE)

    def dragMoveEvent(self, event):
        """Allow drag move if valid."""
        event.acceptProposedAction()

    def add_tool(self, tool_name):
        new_tool = ToolWidget(tool_name, self, self.main_window.summary_widget)
        if new_tool.tool_data:
            self.tool_widgets.append(new_tool)
            self.setStyleSheet(DROPZONE_STYLE)
            self.layout.addWidget(new_tool)
            self.update_placeholder()
            self.refresh_dynamic_names()  # ← NEW
            self.main_window.summary_widget.update_summary()
            expand_and_center_images(self.tool_widgets, self.diagram_width)
        else:
            print(f"⚠️ ERROR: Tool '{tool_name}' not found in database!")

    def clear_tools(self):
        for tool in self.tool_widgets:
            tool.setParent(None)
            tool.deleteLater()
        self.tool_widgets.clear()
        self.main_window.summary_widget.update_summary()
        self.update_placeholder()
        self.refresh_dynamic_names()  # ← NEW

    def dropEvent(self, event):
        """Handles dropping tools into DropZone."""
        tool_name = event.mimeData().text()
        self.add_tool(tool_name)

        event.acceptProposedAction()

    def update_placeholder(self):
        """Show or hide the placeholder text and adjust spacing."""
        if self.tool_widgets:
            # **Remove placeholders and spacers**
            self.placeholder_label.hide()
            self.main_layout.removeItem(self.top_spacer)
            self.main_layout.removeItem(self.bottom_spacer)
        elif self.placeholder_label.isHidden():
            # **Show placeholders and re-add spacers**
            self.placeholder_label.show()
            self.main_layout.insertItem(1, self.top_spacer)  # Push it down
            self.main_layout.insertWidget(2, self.placeholder_label)  # Keep it centered
            self.main_layout.insertItem(3, self.bottom_spacer)  # Push it up

    # inside DropZone class

    def _current_tools_in_visual_order(self):
        tools = []
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, ToolWidget):
                tools.append(w)
        return tools

    @staticmethod
    def _replace_token_case_preserving(text: str, old_token: str, new_token: str) -> str:
        """Replace first occurrence of old_token, preserving original token’s case style."""
        lo = text.lower()
        old_lo = old_token.lower()
        idx = lo.find(old_lo)
        if idx == -1:
            return text
        token = text[idx:idx + len(old_token)]
        # preserve case style
        if token.isupper():
            repl = new_token.upper()
        elif token[0].isupper():
            repl = new_token.capitalize()
        else:
            repl = new_token.lower()
        return text[:idx] + repl + text[idx + len(old_token):]

    def refresh_dynamic_names(self):
        """
        Rule:
          - If a 'lubricator' is BELOW any BOP -> display as 'riser'
          - If a 'riser' is ABOVE the HIGHEST BOP -> display as 'lubricator'
        Only affects labels; DB lookups remain on base_name.
        """
        tools = self._current_tools_in_visual_order()
        if not tools:
            return

        bop_indices = [i for i, w in enumerate(tools) if "bop" in w.base_name.lower()]
        if not bop_indices:
            # No BOP present: revert everyone to their base name
            for w in tools:
                w.set_display_name(w.base_name)
            return

        highest_bop = min(bop_indices)

        for i, w in enumerate(tools):
            base = w.base_name
            name = base

            lower_base = base.lower()
            # below any BOP == there exists a BOP above this tool
            is_below_any_bop = any(bi < i for bi in bop_indices)
            is_above_highest_bop = i < highest_bop

            if "lubricator" in lower_base and is_below_any_bop:
                name = self._replace_token_case_preserving(base, "lubricator", "riser")
            elif "riser" in lower_base and is_above_highest_bop:
                name = self._replace_token_case_preserving(base, "riser", "lubricator")
            else:
                name = base  # unchanged

            w.set_display_name(name)

