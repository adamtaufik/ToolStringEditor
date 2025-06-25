from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QTimer

from ui.apps.ui_calculations_app import WirelineCalculatorApp
from ui.apps.ui_sgs_txt_app import SGSTXTApp

# from ui.apps.original_simulator import WirelineSimulatorApp
from ui.apps.ui_simulator_app import WirelineSimulatorApp


from ui.apps.ui_toolstring_editor_app import ToolStringEditor
from ui.apps.ui_sgs_fgs_app import SGSFGSApp
from utils.path_finder import get_path, get_icon_path
from ui.components.ui_footer import FooterWidget
import os

from utils.styles import MAIN_MENU_BUTTON


class StartWindow(QWidget):
    def __init__(self, app_icon=None):
        super().__init__()
        self.setWindowTitle("Deleum WireHub")
        self.setFixedSize(500, 500)
        if app_icon:
            self.setWindowIcon(app_icon)

        # Background color
        self.setStyleSheet("font-family: 'Segoe UI';")

        # Background image (optional)
        background_path = get_path(os.path.join("assets", "backgrounds", "wave.png"))
        bg_label = QLabel(self)
        pixmap = QPixmap(background_path).scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        bg_label.setPixmap(pixmap)
        bg_label.setGeometry(0, 0, self.width(), self.height())
        bg_label.setStyleSheet("opacity: 0.05;")
        bg_label.lower()

        # Logo
        # logo_path = get_icon_path('logo_full')
        logo_path = get_path(os.path.join("assets", "backgrounds", "title.png"))
        logo_label = QLabel()
        logo_pixmap = QPixmap(logo_path).scaledToHeight(180, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # # Title
        # title = QLabel("Deleum WireHub")
        # title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # title.setStyleSheet("font-size: 24px; font-weight: bold; color: #800020;")

        # 3D Menu Container
        self.buttons = [
            ("Wireline Tool String Editor", self.open_toolstring_editor_app),
            ("SGS/FGS txt processing", self.open_sgstxt_app),
            ("SGS/FGS Data Interpreter", self.open_sgsfgs_app),
            ("Wireline Calculator", self.open_calculations_app),
            ("Wireline Simulator", self.open_simulator_app)
        ]

        # ,
        # ("PCE Stack Up Editor (Coming Soon)", None)

        self.menu_layout = QVBoxLayout()
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_widgets = []
        for text, callback in self.buttons:
            btn = QPushButton(text)
            btn.setFixedSize(250, 40)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet(MAIN_MENU_BUTTON)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if callback:
                btn.clicked.connect(callback)
            self.button_widgets.append(btn)
            self.menu_layout.addWidget(btn)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo_label)
        main_layout.addSpacing(10)
        # main_layout.addWidget(title)

        # main_layout.addSpacing(30)
        main_layout.addLayout(self.menu_layout)

        # Footer
        footer_widget = FooterWidget()
        footer_version_info = footer_widget.get_version_info()  # Access version info here
        footer = QLabel(footer_version_info)
        footer.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer.setStyleSheet("font-size: 10px; color: black; padding: 5px;")

        footer_layout = QVBoxLayout()
        footer_layout.addStretch()
        footer_layout.addWidget(footer)

        main_layout.addStretch()
        main_layout.addLayout(footer_layout)

    def open_toolstring_editor_app(self):
        self.editor_window = ToolStringEditor()
        self.editor_window.show()
        self.close()

    def open_sgstxt_app(self):
        self.sgstxt_app = SGSTXTApp()
        self.sgstxt_app.show()
        self.close()

    def open_sgsfgs_app(self):
        self.sgsfgs_app = SGSFGSApp()
        self.sgsfgs_app.show()
        self.close()

    def open_calculations_app(self):
        self.calculations_app = WirelineCalculatorApp()
        self.calculations_app.show()
        self.close()
        self.close()

    def open_simulator_app(self):
        self.simulator_app = WirelineSimulatorApp()
        self.simulator_app.show()
        self.close()

