import os
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QLabel, QWidget

from utils.get_resource_path import get_resource_path

class FooterWidget(QWidget):
    def __init__(self, parent=None, theme_callback=None, footer_height=30):
        super().__init__(parent)
        self.theme_callback = theme_callback
        self.footer_height = footer_height
        self.setLayout(self._create_footer())

    def _create_footer(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(3, 0, 3, 3)

        # Theme Toggle Button (Left)
        self.theme_button = QPushButton("Theme: Deleum")
        self.theme_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.theme_button.setFixedHeight(self.footer_height)

        if self.theme_callback:
            self.theme_button.clicked.connect(self.theme_callback)

        layout.addWidget(self.theme_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()

        # Footer Text (Right) with version info
        version_text = self._get_version_info()
        footer_label = QLabel(version_text)
        footer_label.setStyleSheet("font-size: 10pt; color: white; padding: 5px;")
        footer_label.setFixedHeight(self.footer_height)
        layout.addWidget(footer_label, alignment=Qt.AlignmentFlag.AlignRight)

        return layout

    def _get_version_info(self):
        try:
            version_history_path = get_resource_path(os.path.join("assets", "resources", "version_history.xlsx"))
            version_history = pd.read_excel(version_history_path)
            version = version_history.iloc[0]["Version"]
            date = pd.to_datetime(version_history.iloc[0]["Date"]).strftime("%d/%m/%Y")
            return f"Created by Adam Mohd Taufik - Operations Engineer  |  Version {version} ({date})"
        except Exception as e:
            return "Created by Adam Mohd Taufik - Operations Engineer"
