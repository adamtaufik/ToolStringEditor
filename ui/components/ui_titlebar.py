from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QGraphicsBlurEffect
from PyQt6.QtCore import Qt, QPoint, QRect, QPropertyAnimation
from PyQt6.QtGui import QPixmap

from utils.path_finder import get_icon_path
from utils.session_manager import SessionManager


class CustomTitleBar(QWidget):
    def __init__(self, parent, menu_callback=None, title="", user_info=""):
        super().__init__(parent)
        self.parent = parent
        self.menu_callback = menu_callback
        self.setFixedHeight(40)
        session = SessionManager()
        user_info = session.get_user()

        # Background blur
        self.background = QWidget(self)
        self.background.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(15)
        self.background.setGraphicsEffect(blur)

        # Foreground content
        self.content = QWidget(self)
        self.content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QHBoxLayout(self.content)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(8)

        # Logo
        self.logo = QLabel()
        pixmap = QPixmap(get_icon_path("logo"))
        self.logo.setPixmap(pixmap.scaledToHeight(24, Qt.TransformationMode.SmoothTransformation))
        self.logo.setFixedWidth(50)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.logo)

        # Title
        self.title = QLabel(title)
        self.layout.addWidget(self.title)
        self.layout.addStretch()

        # Fetch user info
        display_name, email = user_info

        # User info label
        self.user_label = QLabel(f"{display_name}  |  {email}")
        self.user_label.setStyleSheet("""
            font-size: 10pt;
            color: rgba(255, 255, 255, 0.8);
        """)
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.user_label)

        # Control buttons
        self.minimize_btn = QPushButton("–")
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(self.animate_minimize)

        self.maximize_btn = QPushButton("❐")
        self.maximize_btn.setToolTip("Maximize / Restore")
        self.maximize_btn.clicked.connect(self.toggle_max_restore)

        self.close_btn = QPushButton("×")
        self.close_btn.setToolTip("Close")
        self.close_btn.setObjectName("close")
        self.close_btn.clicked.connect(self.parent.close)

        for btn in [self.minimize_btn, self.maximize_btn, self.close_btn]:
            self.layout.addWidget(btn)

        self.setStyleSheet("""
            QWidget {
                color: white;
            }
            QLabel {
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 12pt;
                padding: 4px;
                min-width: 24px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#close:hover {
                background-color: #e81123;
            }
        """)

        self.start_pos = None
        self.maximized = parent.isMaximized()
        if self.maximized:
            self.maximize_btn.setText("🗗")

    def add_menu_button(self, button: QPushButton):
        self.menu_button = button
        self.layout.insertWidget(0, button)

    def set_user_info(self, text: str):
        """Allow dynamic update of user info from any app."""
        self.user_label.setText(text)

    def toggle_max_restore(self):
        if self.maximized:
            self.parent.showNormal()
            self.maximized = False
            self.maximize_btn.setText("❐")
        else:
            self.parent.showMaximized()
            self.maximized = True
            self.maximize_btn.setText("🗗")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.start_pos:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent.move(self.parent.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def animate_minimize(self):
        geom = self.parent.geometry()
        target_geom = QRect(geom.x() + geom.width() // 2,
                            geom.y() + geom.height() // 2,
                            0, 0)

        animation = QPropertyAnimation(self.parent, b"geometry")
        animation.setDuration(50)
        animation.setStartValue(geom)
        animation.setEndValue(target_geom)
        animation.finished.connect(self.parent.showMinimized)
        animation.start()
        self._minimize_animation = animation

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background.setGeometry(self.rect())
        self.content.setGeometry(self.rect())
