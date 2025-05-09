from PyQt6.QtWidgets import (
    QVBoxLayout, QPushButton, QSizePolicy, QFrame, QMessageBox
)
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve

from ui.windows.ui_messagebox_window import MessageBoxWindow
from ui.windows.ui_version_window import VersionWindow
from utils.path_finder import get_icon_path
from utils.styles import SIDEBAR_STYLE


class SidebarWidget(QFrame):
    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setObjectName("sidebar")

        self.collapsed_width = 40
        self.expanded_width = 160
        icon_size = QSize(20, 20)

        self.setMinimumWidth(self.collapsed_width)
        self.setMaximumWidth(self.expanded_width)
        self.expanded = False
        self.setFixedWidth(self.collapsed_width)

        self.back_path = get_icon_path('back')
        self.menu_path = get_icon_path('menu')

        self.setStyleSheet(SIDEBAR_STYLE)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(3, 10, 3, 10)
        self.layout.setSpacing(12)
        self.setLayout(self.layout)

        # Toggle button (icon only)
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(QIcon(self.menu_path))
        self.toggle_button.setIconSize(icon_size)
        self.toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.toggle_button.setObjectName("toggleButton")
        self.toggle_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(self.toggle_button)

        # Menu items
        self.menu_items = []
        self.upper_layout = QVBoxLayout()
        self.lower_layout = QVBoxLayout()

        items.extend([
            (get_icon_path('version'), "Version History", self.show_version_window, "View version history"),
            (get_icon_path('home'), "Main Menu", self.go_to_main_menu, "Return to the main menu"),
            (get_icon_path('exit'), "Exit", self.exit, "Exit application")
        ])

        for icon, name, slot, tooltip, *shortcut in items:
            btn = QPushButton(f"  {name}")
            btn.setIcon(QIcon(icon))
            btn.setIconSize(icon_size)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("menuItem")
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setToolTip(tooltip)  # ✅ Tooltip

            if shortcut:
                btn.setShortcut(QKeySequence(shortcut[0]))  # ✅ Shortcut, like "Ctrl+E"

            btn.clicked.connect(slot)

            if name not in ["Main Menu", "Exit", "Version History"]:
                self.upper_layout.addWidget(btn)
            else:
                self.lower_layout.addWidget(btn)

            self.menu_items.append(btn)


        self.layout.addLayout(self.upper_layout)
        self.layout.addStretch()  # Pushes everything after upper_layout to the bottom
        self.layout.addLayout(self.lower_layout)
        # self.layout.addStretch()


    def toggle_sidebar(self):

        start_width = self.width()
        end_width = self.expanded_width if not self.expanded else self.collapsed_width

        # Animate fixed width instead of min/max
        animation = QPropertyAnimation(self, b"minimumWidth")
        animation.setDuration(200)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def on_animation_finished():
            self.setFixedWidth(end_width)  # Lock final width
            self.expanded = not self.expanded
            if self.expanded:
                self.toggle_button.setIcon(QIcon(self.back_path))
                for btn in self.menu_items:
                    btn.setVisible(True)
            else:
                self.toggle_button.setIcon(QIcon(self.menu_path))
                # for btn in self.menu_items:
                #     btn.setVisible(False)

        animation.finished.connect(on_animation_finished)
        animation.start()

        # Optional: keep reference so it doesn't get garbage collected
        self._animation = animation

    def show_version_window(self):
        self.version_window = VersionWindow()
        self.version_window.show()

    def go_to_main_menu(self):
        from ui.windows.ui_start_window import StartWindow

        parent_window = self.window()

        start_window = StartWindow()
        start_window.setWindowIcon(parent_window.windowIcon())
        start_window.show()
        parent_window.close()

    def exit(self):

        reply = MessageBoxWindow.message_yes_no(self,
                                                "Confirm Exit",
                                                "Are you sure you want to exit the application?",
                                                QMessageBox.Icon.Warning)

        if reply == QMessageBox.StandardButton.Yes:
            parent_window = self.window()
            parent_window.close()



