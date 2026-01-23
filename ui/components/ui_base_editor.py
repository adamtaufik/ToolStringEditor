# ui/components/base_editor.py
from PyQt6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, QTimer, QRect, QRectF
from PyQt6.QtGui import QCursor, QPixmap, QGuiApplication, QRegion, QPainterPath
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QComboBox, QMessageBox, QFrame, QDateEdit, QSizePolicy, QGraphicsOpacityEffect
)

from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.ui_titlebar import CustomTitleBar
from ui.windows.ui_help_window import HelpWindow
from ui.windows.ui_messagebox_window import MessageBoxWindow
from utils.path_finder import get_icon_path
from utils.theme_manager import toggle_theme, apply_theme


class BaseEditor(QMainWindow):
    """Base class for editor windows with common functionality."""

    TOOLBAR_HEIGHT = 30
    FOOTER_HEIGHT = 30
    icon_size = 264
    RESIZE_MARGIN = 8

    def __init__(self, window_title, sidebar_items, drop_zone_class, tool_library_class, summary_widget_class):

        super().__init__()

        self.current_file_name = None
        self.resizing = False
        self.resize_dir = None
        self.is_maximized_by_drag = False
        self.drag_start_pos = None
        self.normal_geometry = None

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # Store classes for specific implementations
        self.drop_zone_class = drop_zone_class
        self.tool_library_class = tool_library_class
        self.summary_widget_class = summary_widget_class

        # Store sidebar items for later use
        self.sidebar_items = sidebar_items
        self.window_title = window_title

        # Initialize UI
        self.setup_base_ui()

    def setup_base_ui(self):
        """Sets up the base UI structure common to all editors."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_container = QVBoxLayout(central_widget)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        # Create drop zone - but don't reference it until after super().__init__() is complete
        self.drop_zone = None

        self.sidebar = SidebarWidget(self, self.sidebar_items)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.title_bar = CustomTitleBar(
            self,
            lambda: self.sidebar.toggle_visibility(),
            self.window_title
        )

        main_container.addWidget(self.title_bar)

        # Main body layout
        main_body = QHBoxLayout()
        main_body.setContentsMargins(0, 0, 0, 0)
        main_body.addWidget(self.sidebar)

        self.editor_layout = QVBoxLayout()
        self.editor_layout.setContentsMargins(0, 5, 0, 0)

        # Setup editor-specific UI - this will be called by subclasses
        self.setup_editor_ui()

        main_body.addLayout(self.editor_layout)
        main_container.addLayout(main_body)

        # Enable mouse tracking for resizing
        self.setMouseTracking(True)
        if self.centralWidget():
            self.centralWidget().setMouseTracking(True)
        self.enable_mouse_tracking(self)

    def center_on_screen(self):
        """Center the window on the primary screen."""
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)

    def setup_editor_ui(self):
        """To be implemented by subclasses for editor-specific UI setup."""
        raise NotImplementedError("Subclasses must implement setup_editor_ui")

    def create_drop_zone(self):
        """Create the drop zone after super().__init__() is complete."""
        self.drop_zone = self.drop_zone_class(self)
        return self.drop_zone

    def setup_common_sidebar(self, library_label, drop_zone_width=870):
        """Sets up the common sidebar structure."""
        content_layout = QHBoxLayout()

        # Sidebar Container (Tool Library)
        sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(sidebar_container)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        # Tool Library
        self.tool_library_label = QLabel(library_label)
        self.tool_library_label.setStyleSheet("font-weight: bold; color: white; font-size: 16px;")
        self.sidebar_layout.addWidget(self.tool_library_label)

        self.tool_library = self.tool_library_class(self, drop_zone=self.drop_zone)
        self.sidebar_layout.addWidget(self.tool_library)

        sidebar_container.setLayout(self.sidebar_layout)
        content_layout.addWidget(sidebar_container)

        # Drop Zone
        content_layout.addWidget(self.drop_zone)
        self.drop_zone.setFixedWidth(drop_zone_width)
        content_layout.addSpacing(5)

        return content_layout

    def setup_common_right_sidebar(self, fixed_width=100):
        """Creates the common right sidebar for well details & summary."""
        right_panel = QWidget()
        right_panel.setObjectName("rightSidebar")
        if fixed_width:
            right_panel.setFixedWidth(fixed_width)
            right_panel.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        input_layout = QVBoxLayout(right_panel)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        input_layout.setContentsMargins(10, 0, 10, 0)
        input_layout.setSpacing(10)

        self.well_details_label = QLabel("Well Details")
        self.well_details_label.setStyleSheet("font: bold; font-size: 12pt;")
        input_layout.addWidget(self.well_details_label)

        self.client_name = QLineEdit(placeholderText="Client Name")
        self.location = QLineEdit(placeholderText="Location")
        self.well_no = QLineEdit(placeholderText="Well No.")
        self.operation_details = QLineEdit(placeholderText="Operation Details")

        # Date Picker
        self.job_date = QDateEdit()
        self.job_date.setFixedHeight(30)
        self.job_date.setCalendarPopup(True)
        self.job_date.setDate(QDate.currentDate())
        self.job_date.setDisplayFormat("dd MMM yyyy")
        self.job_date.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.job_date.dateChanged.connect(self.update_date_display)

        self.well_type = QComboBox()
        self.well_type.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.well_type.addItems([
            "Oil Producer", "Gas Producer", "Water Injection", "Gas Injection",
            "Development Well", "Exploration Well", "CCUS Well"
        ])
        self.well_type.setStyleSheet("""
            QComboBox { color: white; background-color: transparent; padding: 5px; border-radius: 5px; }
            QComboBox QAbstractItemView { background-color: white; color: black; }
        """)

        input_layout.addWidget(self.client_name)
        input_layout.addWidget(self.location)

        little_layout = QHBoxLayout()
        little_layout.setContentsMargins(0, 0, 0, 0)
        little_layout.setSpacing(5)
        little_layout.addWidget(self.well_no)

        # # Add angle input for ToolStringEditor
        # if hasattr(self, 'max_angle'):
        #     little_layout.addWidget(self.max_angle)

        input_layout.addLayout(little_layout)
        if hasattr(self, 'max_angle'):
            input_layout.addWidget(self.max_angle)
        input_layout.addWidget(self.well_type)

        date_layout = QHBoxLayout()
        calendar_icon = get_icon_path('calendar')
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(calendar_icon).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        icon_label.setFixedWidth(24)
        date_layout.addWidget(icon_label)
        date_layout.addWidget(self.job_date)
        input_layout.addLayout(date_layout)
        self.update_date_display()

        input_layout.addWidget(self.operation_details)

        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setStyleSheet("background-color: white; height: 1px;")
        input_layout.addWidget(line1)

        self.summary_label = QLabel("Summary")
        self.summary_label.setStyleSheet("font: bold; font-size: 12pt;")
        input_layout.addWidget(self.summary_label)

        self.summary_widget = self.summary_widget_class(self.drop_zone)
        input_layout.addWidget(self.summary_widget)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setStyleSheet("background-color: white; height: 1px;")
        input_layout.addWidget(line2)

        from ui.components.inputs import LimitedTextEdit
        self.comments = LimitedTextEdit(max_lines=4)
        input_layout.addWidget(self.comments, alignment=Qt.AlignmentFlag.AlignTop)

        input_layout.setContentsMargins(3, 10, 8, 0)

        return right_panel

    # Common methods
    def copy_dropzone_to_clipboard(self):
        """Capture the drop zone as an image and copy it to the clipboard."""
        try:
            pixmap = self.drop_zone.grab()
            image = pixmap.toImage()
            QGuiApplication.clipboard().setImage(image)
            MessageBoxWindow.message_simple(
                self, "Copied",
                "📋 Tool String configuration copied to clipboard as image!",
                'copy_black'
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy drop zone:\n{str(e)}")

    def toggle_theme(self):
        if hasattr(self, 'theme_button') and hasattr(self, 'summary_widget'):
            self.current_theme = toggle_theme(
                widget=self,
                current_theme=self.current_theme,
                theme_button=self.theme_button,
                summary_widget=self.summary_widget
            )

    def show_help_window(self):
        self.help_window = HelpWindow()
        self.help_window.show()

    def update_date_display(self):
        """Update the display format of the job date."""
        if hasattr(self, 'job_date'):
            date = self.job_date.date()
            if hasattr(self, 'max_angle'):  # ToolStringEditor
                formatted_date = date.toString("d/M/yyyy (dddd)")
                self.job_date.setDisplayFormat("d/M/yyyy (dddd)")
            else:  # PCEEditor
                formatted_date = date.toString("d/M/yyyy")
                self.job_date.setDisplayFormat("d/M/yyyy")
            self.job_date.setToolTip(formatted_date)

    def fade_right_sidebar(self, visible: bool, delay=300):
        """Fade the right sidebar in or out smoothly."""
        if not hasattr(self, "right_panel") or self.right_panel is None:
            return

        QTimer.singleShot(delay, lambda: self._perform_fade(visible))

    def _perform_fade(self, visible: bool):
        """Perform the actual fade animation."""
        if not hasattr(self.right_panel, "opacity_effect"):
            self.right_panel.opacity_effect = QGraphicsOpacityEffect(self.right_panel)
            self.right_panel.setGraphicsEffect(self.right_panel.opacity_effect)

        anim = QPropertyAnimation(self.right_panel.opacity_effect, b"opacity")
        anim.setDuration(250)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        if visible:
            self.right_panel.show()
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
        else:
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.finished.connect(lambda: self.right_panel.hide())

        anim.start()
        self._fade_anim = anim

    # Window management methods
    def set_rounded_corners(self, radius=12):
        rect = QRectF(0, 0, float(self.width()), float(self.height()))
        path = QPainterPath()
        path.addRoundedRect(rect, float(radius), float(radius))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Remove rounded corners when maximized, restore otherwise
        if self.isMaximized():
            self.clearMask()  # Remove mask to make edges square
        else:
            self.set_rounded_corners()

    def mousePressEvent(self, event):
        """Detect when resizing or dragging starts."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_pos = event.globalPosition().toPoint()
            self._geo = self.geometry()
            self.drag_start_pos = event.globalPosition().toPoint()

            margin = self.RESIZE_MARGIN
            x, y = event.position().x(), event.position().y()
            w, h = self.width(), self.height()

            # Determine resize direction
            if x <= margin and y <= margin:
                self.resize_dir = "topleft"
            elif x >= w - margin and y <= margin:
                self.resize_dir = "topright"
            elif x <= margin and y >= h - margin:
                self.resize_dir = "bottomleft"
            elif x >= w - margin and y >= h - margin:
                self.resize_dir = "bottomright"
            elif x <= margin:
                self.resize_dir = "left"
            elif x >= w - margin:
                self.resize_dir = "right"
            elif y <= margin:
                self.resize_dir = "top"
            elif y >= h - margin:
                self.resize_dir = "bottom"
            else:
                self.resize_dir = None

            # Detect if it's a move drag (not resize)
            if not self.resize_dir:
                self.dragging = True
                self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            if self.resize_dir:
                self.resizing = True
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle cursor feedback, resizing, and window snapping."""
        pos = event.position().toPoint()
        margin = self.RESIZE_MARGIN
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()

        # print(w,'\t',h)

        # Cursor feedback
        if not self.resizing:
            if x <= margin and y <= margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif x >= w - margin and y <= margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif x <= margin and y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif x >= w - margin and y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif x <= margin or x >= w - margin:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif y <= margin or y >= h - margin:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        # Resizing
        if self.resizing:
            delta = event.globalPosition().toPoint() - self._mouse_pos
            geom = QRect(self._geo)
            if "left" in self.resize_dir:
                geom.setLeft(geom.left() + delta.x())
            if "right" in self.resize_dir:
                geom.setRight(geom.right() + delta.x())
            if "top" in self.resize_dir:
                geom.setTop(geom.top() + delta.y())
            if "bottom" in self.resize_dir:
                geom.setBottom(geom.bottom() + delta.y())

            min_width, min_height = self.minimumWidth(), self.minimumHeight()
            if geom.width() >= min_width and geom.height() >= min_height:
                self.setGeometry(geom)
                self.set_rounded_corners()
            return

        # Moving (dragging)
        if hasattr(self, "dragging") and self.dragging:
            global_pos = event.globalPosition().toPoint()
            new_pos = global_pos - self.drag_offset
            self.move(new_pos)

            # Window snapping logic
            screen_geo = QGuiApplication.primaryScreen().availableGeometry()
            if global_pos.y() <= 5 and not self.is_maximized_by_drag:
                self.normal_geometry = self.geometry()
                self.showMaximized()
                self.is_maximized_by_drag = True
            elif self.is_maximized_by_drag and global_pos.y() > 50:
                self.showNormal()
                if self.normal_geometry:
                    self.setGeometry(self.normal_geometry)
                self.is_maximized_by_drag = False

    def mouseReleaseEvent(self, event):
        """Stop resizing or dragging."""
        self.resizing = False
        self.resize_dir = None
        self.dragging = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def enable_mouse_tracking(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)