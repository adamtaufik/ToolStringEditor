import os
from PyQt6.QtCore import Qt, QTimer, QSizeF, QRect, QPropertyAnimation, QUrl
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QGraphicsScene, QGraphicsView, QApplication, QFrame, QGraphicsPixmapItem
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem

from utils.path_finder import get_path


class VideoSplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        # ---- Window setup ----
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.SplashScreen |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(700, 400)
        self.center()

        # ---- Graphics Scene & View ----
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setGeometry(self.rect())

        # ---- Background Video ----
        self.video_item = QGraphicsVideoItem()
        self.video_item.setOpacity(0.55)  # semi-transparent video
        self.scene.addItem(self.video_item)

        video_path = get_path(os.path.join("assets", "backgrounds", "Wave Loop.mp4"))
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.0)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_item)
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.play()

        # ---- Logo on top of video ----
        logo_path = get_path(os.path.join("assets", "icons", "WireHub Logo.png"))
        pixmap = QPixmap(logo_path)

        # Scale logo if too big, keeping smooth quality
        max_logo_size = 500
        if pixmap.width() > max_logo_size or pixmap.height() > max_logo_size:
            pixmap = pixmap.scaled(max_logo_size, max_logo_size,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

        self.logo_item = QGraphicsPixmapItem(pixmap)
        self.logo_item.setZValue(1)  # ensure logo is always above the video
        self.scene.addItem(self.logo_item)
        self.update_logo_position()

        # ---- Loading text ----
        self.text_label = QLabel("Loading...", self)
        self.text_label.setFont(QFont("Roboto", 12))
        self.text_label.setStyleSheet("color: white;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setGeometry(0, self.height() - 60, self.width(), 40)
        self.text_label.raise_()  # ensure label is above the view

        # ---- Fade-in ----
        self.setWindowOpacity(0.0)
        self.fade_in()

    def fade_in(self):
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        self.fade_anim = anim  # keep reference

    def update_message(self, text):
        self.text_label.setText(text)

    def center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.view.setGeometry(self.rect())
        self.video_item.setSize(QSizeF(self.size()))
        self.update_logo_position()
        self.text_label.setGeometry(0, self.height() - 60, self.width(), 40)

    def update_logo_position(self):
        """Keep the logo centered in the window."""
        if hasattr(self, "logo_item"):
            logo_width = self.logo_item.pixmap().width()
            logo_height = self.logo_item.pixmap().height()
            self.logo_item.setOffset(
                (self.width() - logo_width) / 2,
                (self.height() - logo_height) / 2
            )
