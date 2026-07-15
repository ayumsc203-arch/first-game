import random
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QLinearGradient
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme
from core.score import ScoreCalculator

class ConfettiParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(8, 15)
        self.color = QColor(
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )
        self.speed_x = random.uniform(-3, 3)
        self.speed_y = random.uniform(4, 10)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self, gravity=0.15):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += gravity
        self.rotation += self.rot_speed

class VictoryScreen(QWidget):
    # Signals
    play_again = pyqtSignal()
    new_photo = pyqtSignal()
    main_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 50, 50, 50)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(25)
        
        # Central Glass Card
        self.card = GlassPanel(self)
        self.card.setFixedSize(500, 550)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(40, 40, 40, 40)
        self.card_layout.setSpacing(15)
        
        # Title
        self.title_lbl = QLabel("🎉 PUZZLE COMPLETE!", self.card)
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addWidget(self.title_lbl)
        
        # Stars Display
        self.stars_lbl = QLabel("⭐⭐⭐", self.card)
        self.stars_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stars_lbl.setStyleSheet("font-size: 40px; margin: 10px 0;")
        self.card_layout.addWidget(self.stars_lbl)
        
        # Stat Labels Container
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(8)
        
        self.lbl_time = QLabel("Time: 00:00", self.card)
        self.lbl_moves = QLabel("Moves: 0", self.card)
        self.lbl_score = QLabel("Score: 0", self.card)
        self.lbl_accuracy = QLabel("Accuracy: 100%", self.card)
        self.lbl_best = QLabel("Personal Best: --:--", self.card)
        
        for lbl in [self.lbl_time, self.lbl_moves, self.lbl_score, self.lbl_accuracy, self.lbl_best]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stats_layout.addWidget(lbl)
            
        self.card_layout.addLayout(self.stats_layout)
        self.card_layout.addSpacing(15)
        
        # Buttons layout
        self.btn_layout = QVBoxLayout()
        self.btn_layout.setSpacing(10)
        
        self.btn_again = GlassButton("Play Again", self.card)
        self.btn_again.clicked.connect(self.play_again.emit)
        
        self.btn_photo = GlassButton("New Photo Capture", self.card)
        self.btn_photo.clicked.connect(self.new_photo.emit)
        
        self.btn_menu = GlassButton("Back to Menu", self.card)
        self.btn_menu.clicked.connect(self.main_menu.emit)
        
        self.btn_layout.addWidget(self.btn_again)
        self.btn_layout.addWidget(self.btn_photo)
        self.btn_layout.addWidget(self.btn_menu)
        
        self.card_layout.addLayout(self.btn_layout)
        self.layout.addWidget(self.card)
        
        # Confetti details
        self.particles = []
        self.confetti_timer = QTimer(self)
        self.confetti_timer.timeout.connect(self.update_confetti)
        
        # Play sounds
        self.sound_played = False

    def show_victory(self, seconds, moves, score, difficulty, best_time_seconds=None):
        self.sound_played = False
        
        # Setup display texts
        mins = seconds // 60
        secs = seconds % 60
        self.lbl_time.setText(f"Time Taken: {mins:02d}:{secs:02d}")
        self.lbl_moves.setText(f"Total Moves: {moves}")
        self.lbl_score.setText(f"Final Score: {score}")
        
        # Calculate Accuracy
        # Let's say target pieces = difficulty^2
        pieces_count = difficulty * difficulty
        # Accuracy = pieces_count / moves (with upper bound 100%)
        acc = int((pieces_count / moves) * 100) if moves > 0 else 100
        acc = min(100, acc)
        self.lbl_accuracy.setText(f"Accuracy: {acc}%")
        
        # Best time text
        if best_time_seconds:
            bmins = best_time_seconds // 60
            bsecs = best_time_seconds % 60
            self.lbl_best.setText(f"Personal Best: {bmins:02d}:{bsecs:02d}")
        else:
            self.lbl_best.setText("Personal Best: New Record!")
            
        # Stars
        stars_count = ScoreCalculator.calculate_stars(difficulty, score)
        self.stars_lbl.setText("⭐" * stars_count + "☆" * (3 - stars_count))
        
        # Generate Confetti
        self.particles = []
        for _ in range(120):
            # Spawn in upper half
            self.particles.append(ConfettiParticle(
                random.uniform(0, 1024),
                random.uniform(-100, 0)
            ))
            
        # Start confetti repaint loop
        self.confetti_timer.start(16)
        
        # Play Victory sound
        if not self.sound_played:
            ThemeManager.play_sound("assets/sounds/victory.wav")
            self.sound_played = True

    def update_confetti(self):
        # Update particles
        for p in self.particles:
            p.update()
            
        # Remove off-screen particles
        self.particles = [p for p in self.particles if p.y < self.height() + 50]
        
        # If all particles finished, we can stop the loop
        if not self.particles:
            self.confetti_timer.stop()
            
        self.update()

    def paintEvent(self, event):
        # Background gradient
        painter = QPainter(self)
        theme = ThemeManager.theme()
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, theme['bg_gradient_start'])
        gradient.setColorAt(1, theme['bg_gradient_end'])
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Draw Confetti
        for p in self.particles:
            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.rotation)
            painter.setBrush(QBrush(p.color))
            # Slightly translucent border
            border = QColor(255, 255, 255, 100)
            painter.setPen(QPen(border, 1))
            
            # Draw particle as rectangle or diamond
            painter.drawRect(QRectF(-p.size/2, -p.size/2, p.size, p.size))
            painter.restore()
            
        # Theme specific labels updating
        font_family = theme['font_family']
        self.title_lbl.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 26px; font-weight: 900;")
        
        for lbl in [self.lbl_time, self.lbl_moves, self.lbl_score, self.lbl_accuracy, self.lbl_best]:
            lbl.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 16px; font-weight: 500;")
