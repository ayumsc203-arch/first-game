from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QImage, QColor, QFont, QPainter, QLinearGradient, QBrush
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme
import numpy as np

class HomeScreen(QWidget):
    # Signals to change screen
    start_game = pyqtSignal(np.ndarray)  # Emits captured photo frame
    show_settings = pyqtSignal()
    show_leaderboard = pyqtSignal()
    show_stats = pyqtSignal()
    show_guide = pyqtSignal()
    
    def __init__(self, camera_thread, parent=None):
        super().__init__(parent)
        self.camera_thread = camera_thread
        
        # Main Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(30)
        
        # Left Panel (Menu Options)
        self.menu_panel = GlassPanel(self)
        self.menu_layout = QVBoxLayout(self.menu_panel)
        self.menu_layout.setContentsMargins(30, 40, 30, 40)
        self.menu_layout.setSpacing(20)
        
        # Title Label
        self.title_label = QLabel("PUZZLE\nCAM", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.menu_layout.addWidget(self.title_label)
        self.menu_layout.addSpacing(20)
        
        # Buttons
        self.btn_play = GlassButton("Start Game", self)
        self.btn_play.clicked.connect(self.start_countdown)
        self.menu_layout.addWidget(self.btn_play)
        
        self.btn_settings = GlassButton("Settings & Filters", self)
        self.btn_settings.clicked.connect(self.show_settings.emit)
        self.menu_layout.addWidget(self.btn_settings)
        
        self.btn_leaderboard = GlassButton("Leaderboard", self)
        self.btn_leaderboard.clicked.connect(self.show_leaderboard.emit)
        self.menu_layout.addWidget(self.btn_leaderboard)
        
        self.btn_stats = GlassButton("Statistics", self)
        self.btn_stats.clicked.connect(self.show_stats.emit)
        self.menu_layout.addWidget(self.btn_stats)
        
        self.btn_guide = GlassButton("How to Play", self)
        self.btn_guide.clicked.connect(self.show_guide.emit)
        self.menu_layout.addWidget(self.btn_guide)
        
        self.btn_exit = GlassButton("Exit Game", self)
        self.btn_exit.clicked.connect(lambda: Qt.WindowState.WindowNoState) # Exit handled in main
        self.menu_layout.addWidget(self.btn_exit)
        
        self.menu_layout.addStretch()
        
        # Right Panel (Webcam Live Preview Box)
        self.preview_panel = GlassPanel(self)
        self.preview_layout = QVBoxLayout(self.preview_panel)
        self.preview_layout.setContentsMargins(15, 15, 15, 15)
        
        self.webcam_label = QLabel("Camera Offline", self)
        self.webcam_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.webcam_label.setStyleSheet("border-radius: 12px; background-color: rgba(0, 0, 0, 80); color: #94A3B8;")
        self.preview_layout.addWidget(self.webcam_label)
        
        # Set panel sizing stretches
        self.layout.addWidget(self.menu_panel, 1)
        self.layout.addWidget(self.preview_panel, 2)
        
        # Setup Countdown overlays
        self.countdown_label = QLabel("", self)
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setVisible(False)
        
        # Flash overlay
        self.flash_overlay = QWidget(self)
        self.flash_overlay.setStyleSheet("background-color: white;")
        self.flash_overlay.setVisible(False)
        
        # Background Particles/Gradients (handled in paintEvent)
        self.camera_thread.frame_ready.connect(self.update_camera_frame)
        
        # Countdown timing variables
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.tick_countdown)
        self.countdown_value = 3
        self.latest_frame_np = None

    def start_countdown(self):
        # Disable buttons during countdown
        self.btn_play.setEnabled(False)
        self.btn_settings.setEnabled(False)
        
        # Reset and display countdown
        self.countdown_value = 3
        self.countdown_label.setText(str(self.countdown_value))
        
        # Center the countdown label relative to the preview panel
        p_geom = self.preview_panel.geometry()
        px = p_geom.x() + (p_geom.width() - 400) // 2
        py = p_geom.y() + (p_geom.height() - 250) // 2
        self.countdown_label.setGeometry(px, py, 400, 250)
        self.countdown_label.setVisible(True)
        
        # Style
        self.update_countdown_style()
        
        # Animate countdown scale
        self.animate_countdown()
        
        # Play sound
        ThemeManager.play_sound("assets/sounds/countdown.wav")
        
        # Start timer
        self.countdown_timer.start(1000)

    def update_countdown_style(self):
        theme = ThemeManager.theme()
        color = theme['accent']
        font_family = theme['font_family']
        
        if self.countdown_value == "SMILE 😊":
            self.countdown_label.setStyleSheet(
                f"color: {theme['success']}; font-family: {font_family}; font-size: 72px; font-weight: bold;"
            )
        else:
            self.countdown_label.setStyleSheet(
                f"color: {color}; font-family: {font_family}; font-size: 130px; font-weight: bold;"
            )

    def animate_countdown(self):
        # Simple pop animation for countdown
        font = self.countdown_label.font()
        # Custom property animation on label geometry
        geom = self.countdown_label.geometry()
        cx, cy = geom.x() + geom.width()//2, geom.y() + geom.height()//2
        
        self.anim = QPropertyAnimation(self.countdown_label, b"geometry")
        self.anim.setDuration(400)
        self.anim.setStartValue(QRect(cx - 10, cy - 10, 20, 20))
        self.anim.setEndValue(geom)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

    def tick_countdown(self):
        if isinstance(self.countdown_value, str):
            # Time to capture
            self.countdown_timer.stop()
            self.countdown_label.setVisible(False)
            self.capture_photo()
            return
            
        self.countdown_value -= 1
        
        if self.countdown_value > 0:
            self.countdown_label.setText(str(self.countdown_value))
            self.update_countdown_style()
            self.animate_countdown()
            ThemeManager.play_sound("assets/sounds/countdown.wav")
            
        elif self.countdown_value == 0:
            self.countdown_value = "SMILE 😊"
            self.countdown_label.setText(self.countdown_value)
            self.update_countdown_style()
            self.animate_countdown()
            ThemeManager.play_sound("assets/sounds/countdown_smile.wav")

    def capture_photo(self):
        # Screen flash animation
        self.flash_overlay.setGeometry(self.rect())
        self.flash_overlay.setVisible(True)
        
        # Flash sound
        ThemeManager.play_sound("assets/sounds/shutter.wav")
        
        # Fade out flash
        self.flash_anim = QPropertyAnimation(self.flash_overlay, b"windowOpacity")
        # We can simulate white fadeout using a timer that turns it off after 150ms
        QTimer.singleShot(150, self.hide_flash)

    def hide_flash(self):
        self.flash_overlay.setVisible(False)
        self.btn_play.setEnabled(True)
        self.btn_settings.setEnabled(True)
        
        # Emit latest frame to start game
        if self.latest_frame_np is not None:
            # Let's crop to square first
            h, w = self.latest_frame_np.shape[:2]
            size = min(h, w)
            cx, cy = w // 2, h // 2
            cropped = self.latest_frame_np[cy - size//2 : cy + size//2, cx - size//2 : cx + size//2]
            
            # Switch screen
            self.start_game.emit(cropped)

    def update_camera_frame(self, qimage, frame_np):
        self.latest_frame_np = frame_np
        
        # Scale to fit label aspect ratio
        scaled_img = qimage.scaled(
            self.webcam_label.width(), 
            self.webcam_label.height(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.webcam_label.setPixmap(QPixmap.fromImage(scaled_img))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-center overlay widgets
        if self.countdown_label.isVisible():
            p_geom = self.preview_panel.geometry()
            px = p_geom.x() + (p_geom.width() - 400) // 2
            py = p_geom.y() + (p_geom.height() - 250) // 2
            self.countdown_label.setGeometry(px, py, 400, 250)

    def paintEvent(self, event):
        # Custom background gradient based on theme
        painter = QPainter(self)
        theme = ThemeManager.theme()
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, theme['bg_gradient_start'])
        gradient.setColorAt(1, theme['bg_gradient_end'])
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Dynamically set title styles based on theme
        accent_color = theme['accent']
        font_family = theme['font_family']
        self.title_label.setStyleSheet(
            f"color: #FFFFFF; font-family: {font_family}; font-size: 38px; font-weight: 900; line-height: 1.2;"
        )
