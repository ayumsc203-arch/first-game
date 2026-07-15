from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QLinearGradient, QFont
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme

class GuideScreen(QWidget):
    back_to_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 40, 50, 40)
        self.layout.setSpacing(20)
        
        # Header Box
        self.header_panel = GlassPanel(self)
        self.header_layout = QHBoxLayout(self.header_panel)
        self.header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.title_label = QLabel("HOW TO PLAY GUIDE", self)
        self.header_layout.addWidget(self.title_label)
        self.layout.addWidget(self.header_panel)
        
        # Content Panel
        self.content_panel = GlassPanel(self)
        self.content_layout = QVBoxLayout(self.content_panel)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        
        # Scroll Area for guide content
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; } 
            QScrollBar:vertical { background: transparent; width: 8px; } 
            QScrollBar::handle:vertical { background: rgba(255,255,255,40); border-radius: 4px; }
        """)
        
        self.scroll_content = QWidget(self)
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(25)
        self.scroll_layout.setContentsMargins(0, 0, 10, 0)
        
        self.scroll.setWidget(self.scroll_content)
        self.content_layout.addWidget(self.scroll)
        
        # Populate Guide Content
        self.populate_guide()
        
        # Back button
        self.btn_back = GlassButton("Back to Menu", self)
        self.btn_back.clicked.connect(self.back_to_menu.emit)
        self.layout.addWidget(self.btn_back)

    def populate_guide(self):
        # We will add multiple sections
        sections = [
            ("📸 CAPTURING THE PUZZLE", 
             "1. Click 'Start Game' on the menu.\n"
             "2. A countdown will trigger: 3... 2... 1... SMILE 😊!\n"
             "3. The camera will flash and capture your photo.\n"
             "4. The picture is sliced into pieces according to the difficulty (Easy 3x3 to Expert 6x6) and scrambled!"),
             
            ("🧩 GAMEPLAY MECHANICS", 
             "• Click and hold a piece with the Left Mouse Button to lift it. It scales up and casts a larger shadow.\n"
             "• Drag the piece to the target board and release to drop it.\n"
             "• Snapping: If placed near the correct slot, it snaps into place, locks, and glows green.\n"
             "• Shake Back: If dropped in the wrong cell, it vibrates and snaps back to where you grabbed it."),
             
            ("⌨️ KEYBOARD SHORTCUTS & CONTROLS", 
             "• Hold 'H' key: Toggle Ghost Preview (semi-transparent guide overlay).\n"
             "• Press 'R' key or Right-Click: Rotates the selected piece 90° (only in Rotate Mode).\n"
             "• Click 'Hint': Highlights a misplaced piece (+10 seconds time penalty).\n"
             "• Click 'Auto Solve': Watch the computer solve the puzzle automatically."),
             
            ("🖐️ MEDIAPIPE HAND-TRACKING (AIR CONTROL)", 
             "• Enable Hands Tracking in the Settings panel.\n"
             "• Move your index finger in front of your camera to move the glowing pointer.\n"
             "• Pinch your thumb and index finger together to grab a piece. Keep them pinched to drag, and open your fingers to release and drop the piece!"),
             
            ("🏆 SCORING & STARS FORMULA", 
             "Score = (Difficulty x 1000) - (Moves x 5) - (Seconds x 2)\n\n"
             "• Finish quickly and make fewer mistakes to maximize your score.\n"
             "• Stars are awarded based on efficiency:\n"
             "  - 3 Stars: Score >= 75% of maximum possible.\n"
             "  - 2 Stars: Score >= 45% of maximum.\n"
             "  - 1 Star: Complete the puzzle.")
        ]
        
        theme = ThemeManager.theme()
        font_family = theme['font_family']
        
        for title_text, body_text in sections:
            section_box = QFrame(self.scroll_content)
            section_box.setStyleSheet("background-color: rgba(255, 255, 255, 10); border-radius: 12px; border: 1px solid rgba(255,255,255,15);")
            box_layout = QVBoxLayout(section_box)
            box_layout.setContentsMargins(20, 20, 20, 20)
            box_layout.setSpacing(10)
            
            lbl_title = QLabel(title_text, section_box)
            lbl_title.setStyleSheet(f"color: {theme['accent']}; font-family: {font_family}; font-size: 16px; font-weight: 900; border: none; background: transparent;")
            
            lbl_body = QLabel(body_text, section_box)
            lbl_body.setWordWrap(True)
            lbl_body.setStyleSheet(f"color: #E2E8F0; font-family: {font_family}; font-size: 14px; line-height: 1.5; border: none; background: transparent;")
            
            box_layout.addWidget(lbl_title)
            box_layout.addWidget(lbl_body)
            self.scroll_layout.addWidget(section_box)
            
        self.scroll_layout.addStretch()

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
        
        # Style title
        font_family = theme['font_family']
        self.title_label.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 24px; font-weight: 800;")
