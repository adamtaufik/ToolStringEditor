from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect, QStackedLayout
from PyQt6.QtGui import QPixmap, QFont, QTransform
from PyQt6.QtCore import Qt, QTimer
from ui.ui_mainwindow import MainWindow
from ui.ui_hydrostatic_app import HydrostaticPressureApp
from utils.get_resource_path import get_resource_path
import os
import math

class StartWindow(QWidget):
    def __init__(self, app_icon=None):
        super().__init__()
        self.setWindowTitle("Deleum Software Suite")
        self.setFixedSize(500, 400)
        if app_icon:
            self.setWindowIcon(app_icon)

        # Background color
        self.setStyleSheet("font-family: 'Segoe UI';")

        # Background image (optional)
        background_path = get_resource_path(os.path.join("assets", "images", "wave.png"))
        bg_label = QLabel(self)
        pixmap = QPixmap(background_path).scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
        bg_label.setPixmap(pixmap)
        bg_label.setGeometry(0, 0, self.width(), self.height())
        bg_label.setStyleSheet("opacity: 0.05;")
        bg_label.lower()

        # Logo
        logo_path = get_resource_path(os.path.join("assets", "images", "logo_full.png"))
        logo_label = QLabel()
        logo_pixmap = QPixmap(logo_path).scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Deleum Software Suite")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #800020;")


        # 3D Menu Container
        self.buttons = [
            ("Wireline Tool String Editor", self.launch_editor),
            ("Hydrostatic Pressure Calculator", self.open_hydrostatic_app),
            ("SGS/FGS (Coming Soon)", None)
        ]

        self.angle = 0
        self.menu_layout = QVBoxLayout()
        self.menu_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.button_widgets = []
        for text, callback in self.buttons:
            btn = QPushButton(text)
            btn.setFixedSize(250, 40)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f1f1;
                    color: #800020;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0e0e6;
                }
            """)
            if callback:
                btn.clicked.connect(callback)
            self.button_widgets.append(btn)
            self.menu_layout.addWidget(btn)

        self.revolve_timer = QTimer()
        self.revolve_timer.timeout.connect(self.animate_revolve)
        self.revolve_timer.start(50)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo_label)
        main_layout.addSpacing(10)
        main_layout.addWidget(title)

        main_layout.addSpacing(30)
        main_layout.addLayout(self.menu_layout)

    def animate_revolve(self):
        self.angle += 1
        radius = 30
        for i, btn in enumerate(self.button_widgets):
            offset = math.sin(math.radians(self.angle + i * 120)) * radius
            scale = 1 + math.cos(math.radians(self.angle + i * 120)) * 0.2
            btn.setStyleSheet(btn.styleSheet() + f"""
                QPushButton {{
                    transform: translateY({offset}px) scale({scale});
                }}
            """)

    def launch_editor(self):
        self.editor_window = MainWindow()
        self.editor_window.show()
        self.close()

    def open_hydrostatic_app(self):
        self.hydro_window = HydrostaticPressureApp()
        self.hydro_window.show()
        self.close()
