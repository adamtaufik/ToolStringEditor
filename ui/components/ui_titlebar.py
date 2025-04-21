from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QGraphicsBlurEffect
from PyQt6.QtCore import Qt, QPoint, QRect, QPropertyAnimation
from PyQt6.QtGui import QCursor, QPixmap

from utils.path_finder import get_path, get_icon_path

class CustomTitleBar(QWidget):
    def __init__(self, parent, menu_callback=None, title=""):
        super().__init__(parent)
        self.parent = parent
        self.menu_callback = menu_callback
        self.setFixedHeight(40)

        # Background blur widget
        self.background = QWidget(self)
        self.background.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(15)
        self.background.setGraphicsEffect(blur)

        # Foreground content
        self.content = QWidget(self)
        self.content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QHBoxLayout(self.content)
        self.layout.setContentsMargins(0, 0, 10, 0)  # <-- Adjust spacing here
        self.layout.setSpacing(5)

        # Logo
        self.logo = QLabel()
        pixmap = QPixmap(get_icon_path('logo'))
        self.logo.setPixmap(pixmap.scaledToHeight(24, Qt.TransformationMode.SmoothTransformation))
        self.logo.setFixedWidth(50)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.logo)

        # Title
        self.title = QLabel(title)
        self.layout.addWidget(self.title)
        self.layout.addStretch()  # <-- Push everything else to the right

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
        self.maximized = False


    def add_menu_button(self, button: QPushButton):
        """Externally add a menu button (e.g., hamburger) to the title bar."""
        self.menu_button = button
        self.layout.insertWidget(0, button)

    def toggle_max_restore(self):
        if self.maximized:
            self.parent.showNormal()
            self.maximized = False
            self.maximize_btn.setText("❐")
        else:
            self.parent.showMaximized()
            self.maximized = True
            self.maximize_btn.setText("🗗")  # Restore icon

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
        """Simulate shrink animation before minimizing."""
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

        # Store animation to prevent garbage collection
        self._minimize_animation = animation

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background.setGeometry(self.rect())
        self.content.setGeometry(self.rect())
