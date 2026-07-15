from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QLinearGradient, QFont
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme
from utils.helpers import LeaderboardManager, StatisticsTracker

class LeaderboardScreen(QWidget):
    back_to_menu = pyqtSignal()
    
    def __init__(self, is_stats_only=False, parent=None):
        super().__init__(parent)
        self.is_stats_only = is_stats_only
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 40, 50, 40)
        self.layout.setSpacing(20)
        
        # Header Box
        self.header_panel = GlassPanel(self)
        self.header_layout = QHBoxLayout(self.header_panel)
        self.header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.title_label = QLabel(self)
        self.header_layout.addWidget(self.title_label)
        self.layout.addWidget(self.header_panel)
        
        # Content Panel
        self.content_panel = GlassPanel(self)
        self.content_layout = QVBoxLayout(self.content_panel)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        
        # Scroll Area for high scores
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar:vertical { background: transparent; width: 8px; } QScrollBar::handle:vertical { background: rgba(255,255,255,40); border-radius: 4px; }")
        
        self.scroll_content = QWidget(self)
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(0, 0, 10, 0)
        
        self.scroll.setWidget(self.scroll_content)
        self.content_layout.addWidget(self.scroll)
        
        self.layout.addWidget(self.content_panel, 1)
        
        # Back button
        self.btn_back = GlassButton("Back to Menu", self)
        self.btn_back.clicked.connect(self.back_to_menu.emit)
        self.layout.addWidget(self.btn_back)

    def refresh(self):
        # Clear previous scroll contents
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        theme = ThemeManager.theme()
        font_family = theme['font_family']
        
        if self.is_stats_only:
            self.title_label.setText("PLAYER STATISTICS")
            stats = StatisticsTracker.load_stats()
            
            # Display stats cards
            stats_list = [
                ("Games Played", str(stats.get('games_played', 0))),
                ("Games Won", str(stats.get('games_won', 0))),
                ("Best Score", f"{stats.get('best_score', 0)} pts"),
            ]
            
            # Formats average solve time
            won = stats.get('games_won', 0)
            tot_time = stats.get('total_time', 0)
            avg = int(tot_time / won) if won > 0 else 0
            amins, asecs = avg // 60, avg % 60
            stats_list.append(("Average Solve Time", f"{amins:02d}:{asecs:02d}"))
            
            # Formats fastest solve
            fastest = stats.get('fastest_solve', 999999)
            if fastest == 999999:
                stats_list.append(("Fastest Solve", "--:--"))
            else:
                fmins, fsecs = fastest // 60, fastest % 60
                stats_list.append(("Fastest Solve", f"{fmins:02d}:{fsecs:02d}"))
                
            for label_text, val_text in stats_list:
                row = GlassPanel(self.scroll_content)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(20, 15, 20, 15)
                
                lbl_name = QLabel(label_text, row)
                lbl_name.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 16px; font-weight: bold;")
                
                lbl_val = QLabel(val_text, row)
                lbl_val.setStyleSheet(f"color: {theme['accent']}; font-family: {font_family}; font-size: 18px; font-weight: 900;")
                
                row_layout.addWidget(lbl_name)
                row_layout.addStretch()
                row_layout.addWidget(lbl_val)
                self.scroll_layout.addWidget(row)
                
        else:
            self.title_label.setText("LOCAL LEADERBOARD (TOP 20)")
            scores = LeaderboardManager.load_scores()
            
            if not scores:
                empty_lbl = QLabel("No high scores recorded yet. Complete a puzzle!", self.scroll_content)
                empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_lbl.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 16px; font-weight: italic;")
                self.scroll_layout.addWidget(empty_lbl)
            else:
                # Table header
                header_row = QFrame(self.scroll_content)
                h_layout = QHBoxLayout(header_row)
                h_layout.setContentsMargins(15, 5, 15, 5)
                for txt, stretch in [("Rank", 1), ("Date", 2), ("Size", 2), ("Moves", 1), ("Time", 1), ("Score", 2)]:
                    lbl = QLabel(txt, header_row)
                    lbl.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 13px; font-weight: bold; opacity: 0.8;")
                    if txt in ["Moves", "Time", "Score"]:
                        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    h_layout.addWidget(lbl, stretch)
                self.scroll_layout.addWidget(header_row)
                
                # Render records
                for i, score in enumerate(scores):
                    row = GlassPanel(self.scroll_content)
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(15, 10, 15, 10)
                    
                    lbl_rank = QLabel(f"#{i+1}", row)
                    lbl_rank.setStyleSheet(f"color: {theme['accent']}; font-family: {font_family}; font-size: 15px; font-weight: 900;")
                    
                    lbl_date = QLabel(score.get('date', ''), row)
                    lbl_date.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 14px;")
                    
                    lbl_diff = QLabel(score.get('difficulty', ''), row)
                    lbl_diff.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 14px;")
                    
                    lbl_moves = QLabel(str(score.get('moves', 0)), row)
                    lbl_moves.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 14px;")
                    lbl_moves.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    lbl_time = QLabel(score.get('time', ''), row)
                    lbl_time.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 14px;")
                    lbl_time.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    lbl_score = QLabel(f"{score.get('score', 0)} pts", row)
                    lbl_score.setStyleSheet(f"color: {theme['success']}; font-family: {font_family}; font-size: 15px; font-weight: bold;")
                    lbl_score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    row_layout.addWidget(lbl_rank, 1)
                    row_layout.addWidget(lbl_date, 2)
                    row_layout.addWidget(lbl_diff, 2)
                    row_layout.addWidget(lbl_moves, 1)
                    row_layout.addWidget(lbl_time, 1)
                    row_layout.addWidget(lbl_score, 2)
                    
                    self.scroll_layout.addWidget(row)
                    
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
        
        # Style header label
        font_family = theme['font_family']
        self.title_label.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 24px; font-weight: 800;")
