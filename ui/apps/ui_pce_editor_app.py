# PyQt6 core modules
from PyQt6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, QTimer, QRect, QRectF
from PyQt6.QtGui import QCursor, QPixmap, QGuiApplication, QRegion, QPainterPath
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QLabel, QComboBox, QMessageBox, QFrame, QDateEdit, QSizePolicy, QGraphicsOpacityEffect
)

# Database & Editor logic
from database.file_io_pce import save_configuration, load_configuration
from features.pce_editor.export_manager import export_configuration

# UI Components
from ui.components.pce_editor.inputs import LimitedTextEdit
from ui.components.ui_footer import FooterWidget
from ui.components.pce_editor.ui_dropzone import DropZone
from ui.components.ui_sidebar_widget import SidebarWidget
from ui.components.pce_editor.ui_summary import SummaryWidget
from ui.components.ui_titlebar import CustomTitleBar
from ui.components.pce_editor.ui_tool_library import ToolLibrary

# Windows
from ui.windows.ui_database_window_pce import DatabaseWindow
from ui.windows.ui_help_window import HelpWindow
from ui.windows.ui_messagebox_window import MessageBoxWindow

# Utils
from utils.path_finder import get_icon_path
from utils.screen_info import get_height
from utils.theme_manager import toggle_theme, apply_theme


class PCEEditor(QMainWindow):
    """Main application window."""

    TOOLBAR_HEIGHT = 30  # ✅ Fixed toolbar height
    FOOTER_HEIGHT = 30  # ✅ Fixed footer height
    icon_size = 264
    RESIZE_MARGIN = 8  # size (in px) around edges for resizing
    resizing = False
    resize_dir = None


    def __init__(self):
        super().__init__()

        self.current_file_name = None  # Track last saved or loaded filename
        # self.setMinimumHeight(get_height() - 10)  # ✅ Set minimum resizable height
        # self.setMinimumWidth(1366)

        # ✅ Set initial theme
        self.current_theme = "Deleum"
        apply_theme(self, self.current_theme)

        # **Create Main Widget**
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Replace QVBoxLayout in ts_editor with full vertical layout
        main_container = QVBoxLayout(central_widget)
        main_container.setContentsMargins(0, 0, 0, 0)
        main_container.setSpacing(0)

        self.drop_zone = DropZone(self)

        items = [
            # (get_icon_path('save'), "Save", lambda: save_configuration(self), "Save the current file (Ctrl+S)", "Ctrl+S"),
            # (get_icon_path('load'), "Load", lambda: load_configuration(self), "Open a file (Ctrl+O)", "Ctrl+O"),
            (get_icon_path('copy'), "Copy as Image", self.copy_dropzone_to_clipboard, "Copy current tool config as PNG (Ctrl+C)", "Ctrl+C"),
            (get_icon_path('clear'), "Clear", self.drop_zone.clear_tools, "Clear all tools"),
            (get_icon_path('export'), "Export", lambda: export_configuration(self), "Export to Excel and PDF"),
            (get_icon_path('help'), "Help", self.show_help_window, "Open help documentation"),
            (get_icon_path('database'), "PCE Database", self.show_database_window, "Open PCE database")
        ]


        self.sidebar = SidebarWidget(self, items)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = CustomTitleBar(self, lambda: self.sidebar.toggle_visibility(),"PCE Editor")

        main_container.addWidget(self.title_bar)

        # Below title bar: Main layout (Sidebar + Content)
        main_body = QHBoxLayout()
        main_body.setContentsMargins(0, 0, 0, 0)

        main_body.addWidget(self.sidebar)

        editor_layout = QVBoxLayout()
        editor_layout.setContentsMargins(0, 5, 0, 0)

        # ✅ **Set up UI Components**
        self.setup_ui(editor_layout)

        main_body.addLayout(editor_layout)

        main_container.addLayout(main_body)
        QTimer.singleShot(400, lambda: self.fade_right_sidebar(True))

        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)
        self.enable_mouse_tracking(self)

    def setup_ui(self, editor_layout):
        """Sets up the main UI layout."""

        content_layout = QHBoxLayout()

        # **Sidebar Container (Tool Library)**
        sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(sidebar_container)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(10)

        # **Tool Library**
        self.tool_library_label = QLabel("PCE Library")
        self.tool_library_label.setStyleSheet("font-weight: bold; color: white; font-size: 16px;")
        self.sidebar_layout.addWidget(self.tool_library_label)

        self.tool_library = ToolLibrary(self, drop_zone=self.drop_zone)  # ✅ Initialize Tool Library
        self.sidebar_layout.addWidget(self.tool_library)

        sidebar_container.setLayout(self.sidebar_layout)
        content_layout.addWidget(sidebar_container)

        # **Drop Zone**
        content_layout.addWidget(self.drop_zone)
        self.drop_zone.setFixedWidth(1020)

        content_layout.addSpacing(5)

        # -- Right Sidebar (Well Details & Summary)
        self.right_panel = self.setup_right_sidebar()
        content_layout.addWidget(self.right_panel)

        editor_layout.addLayout(content_layout)

        # ✅ **Footer**
        footer = FooterWidget(self, theme_callback=self.toggle_theme)
        self.theme_button = footer.theme_button  # ✅ now this won't crash
        editor_layout.addWidget(footer)
        self.right_panel.setGraphicsEffect(QGraphicsOpacityEffect(self.right_panel))
        self.right_panel.graphicsEffect().setOpacity(0.0)

        # ✅ **Populate Tools**
        self.tool_library.update_tool_list()

    def copy_dropzone_to_clipboard(self):
        """Capture the drop zone as an image and copy it to the clipboard."""
        try:
            # Grab the drop zone's visible area as a pixmap
            pixmap = self.drop_zone.grab()

            # Convert QPixmap to QImage
            image = pixmap.toImage()

            # Copy to clipboard
            QGuiApplication.clipboard().setImage(image)

            # Optional confirmation (you can use your styled QMessageBox)
            MessageBoxWindow.message_simple(self,
                                            "Copied",
                                            "📋 Tool String configuration copied to clipboard as image!",
                                            'copy_black')

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy drop zone:\n{str(e)}")

    def setup_right_sidebar(self):
        """Creates the right sidebar for well details & summary as a fixed-width panel."""
        right_panel = QWidget()
        right_panel.setObjectName("rightSidebar")
        right_panel.setFixedWidth(150)
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
        input_layout.addLayout(little_layout)

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

        self.summary_widget = SummaryWidget(self.drop_zone)
        input_layout.addWidget(self.summary_widget)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        line2.setStyleSheet("background-color: white; height: 1px;")
        input_layout.addWidget(line2)

        self.comments = LimitedTextEdit(max_lines=5)
        input_layout.addWidget(self.comments, alignment=Qt.AlignmentFlag.AlignTop)

        input_layout.setContentsMargins(3, 10, 8, 0)

        return right_panel

    def toggle_theme(self):
        self.current_theme = toggle_theme(
            widget=self,
            current_theme=self.current_theme,
            theme_button=self.theme_button,
            summary_widget=self.summary_widget
        )

    def show_database_window(self):
        self.database_window = DatabaseWindow()
        self.database_window.show()

    def show_help_window(self):
        self.help_window = HelpWindow()
        self.help_window.show()

    def update_date_display(self):
        """Update the display format of the job date to include day name."""
        date = self.job_date.date()
        formatted_date = date.toString("d/M/yyyy")  # Example: 21/4/2025 (Monday)
        self.job_date.setDisplayFormat("d/M/yyyy")
        self.job_date.setToolTip(formatted_date)  # Optional: tooltip shows full date

    def fade_right_sidebar(self, visible: bool):
        """Fade the right sidebar in or out smoothly."""
        if not hasattr(self, "right_panel") or self.right_panel is None:
            return

        # Create opacity effect if not yet applied
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

            def hide_after():
                self.right_panel.hide()

            anim.finished.connect(hide_after)

        anim.start()
        self._fade_anim = anim  # Keep a reference so GC doesn’t kill it

    def enable_mouse_tracking(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_rounded_corners()

    def mousePressEvent(self, event):
        """Detect when resizing starts."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_pos = event.globalPosition().toPoint()
            self._geo = self.geometry()

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

            if self.resize_dir:
                self.resizing = True
                event.accept()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle cursor feedback and perform resizing."""
        pos = event.position().toPoint()
        margin = self.RESIZE_MARGIN
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()

        if not self.resizing:
            # Change cursor shape when hovering near edges
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
            return

        # Perform resizing
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

    def mouseReleaseEvent(self, event):
        """Stop resizing."""
        self.resizing = False
        self.resize_dir = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)

    def set_rounded_corners(self, radius=12):
        rect = QRectF(0, 0, float(self.width()), float(self.height()))
        path = QPainterPath()
        path.addRoundedRect(rect, float(radius), float(radius))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
