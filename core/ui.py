import os
from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect, QFrame, QLabel
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QPointF, QSize, Qt, pyqtSignal, QEvent, QUrl
from PyQt6.QtGui import QColor, QFont, QPainter, QLinearGradient, QBrush, QPen
from PyQt6.QtMultimedia import QSoundEffect

class Theme:
    DARK = {
        'name': 'Dark Mode',
        'bg_gradient_start': QColor(20, 24, 33),
        'bg_gradient_end': QColor(10, 12, 16),
        'panel_bg': QColor(30, 36, 48, 180),
        'panel_border': QColor(255, 255, 255, 30),
        'text': '#E2E8F0',
        'accent': '#60A5FA',      # Soft Blue
        'accent_hover': '#93C5FD',
        'success': '#34D399',     # Soft Green
        'shadow': QColor(0, 0, 0, 80),
        'font_family': 'Outfit, Inter, Segoe UI'
    }
    
    NEON = {
        'name': 'Cyber Neon',
        'bg_gradient_start': QColor(13, 10, 25),
        'bg_gradient_end': QColor(3, 2, 8),
        'panel_bg': QColor(25, 15, 45, 160),
        'panel_border': QColor(236, 72, 153, 100), # Neon Pink border
        'text': '#F8FAFC',
        'accent': '#EC4899',      # Neon Pink
        'accent_hover': '#06B6D4', # Neon Cyan
        'success': '#10B981',
        'shadow': QColor(236, 72, 153, 40),
        'font_family': 'Outfit, Inter, Segoe UI'
    }
    
    GLASS = {
        'name': 'Frost Glass',
        'bg_gradient_start': QColor(135, 80, 156),
        'bg_gradient_end': QColor(241, 196, 15),
        'panel_bg': QColor(255, 255, 255, 40),
        'panel_border': QColor(255, 255, 255, 120),
        'text': '#1E293B',
        'accent': '#7C3AED',      # Deep Violet
        'accent_hover': '#6D28D9',
        'success': '#059669',
        'shadow': QColor(0, 0, 0, 30),
        'font_family': 'Outfit, Inter, Segoe UI'
    }
    
    RETRO = {
        'name': '8-Bit Retro',
        'bg_gradient_start': QColor(44, 62, 80),
        'bg_gradient_end': QColor(44, 62, 80),
        'panel_bg': QColor(236, 240, 241),
        'panel_border': QColor(44, 62, 80),
        'text': '#2C3E50',
        'accent': '#E67E22',      # Carrot orange
        'accent_hover': '#D35400',
        'success': '#27AE60',
        'shadow': QColor(0, 0, 0, 100),
        'font_family': 'Courier New, Consolas, monospace'
    }

class ThemeManager:
    _current_theme = Theme.DARK
    sound_enabled = True
    _sound_cache = {}

    @classmethod
    def set_theme(cls, theme_dict):
        cls._current_theme = theme_dict

    @classmethod
    def theme(cls):
        return cls._current_theme
        
    @classmethod
    def play_sound(cls, sound_file):
        if not cls.sound_enabled:
            return
        try:
            if sound_file not in cls._sound_cache:
                effect = QSoundEffect()
                abs_path = os.path.abspath(sound_file)
                effect.setSource(QUrl.fromLocalFile(abs_path))
                effect.setVolume(1.0)
                cls._sound_cache[sound_file] = effect
            
            # Play
            cls._sound_cache[sound_file].play()
        except Exception as e:
            # Sound play warning suppressed for production stability
            pass

class GlassButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMouseTracking(True)
        self._hover = False
        self._pressed = False
        
        # Scale factor
        self.scale_factor = 1.0
        
        # Set up a property animation for the scale factor
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(120)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Font settings
        font = QFont(ThemeManager.theme()['font_family'], 12, QFont.Weight.Bold)
        self.setFont(font)
        
        # Apply drop shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(ThemeManager.theme()['shadow'])
        self.setGraphicsEffect(self.shadow)
        
        self.setMinimumHeight(48)

    def enterEvent(self, event):
        self._hover = True
        self.scale_factor = 1.08
        ThemeManager.play_sound("assets/sounds/hover.wav")
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.scale_factor = 1.0
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            ThemeManager.play_sound("assets/sounds/click.wav")
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = ThemeManager.theme()
        
        # Draw background
        rect = self.rect()
        
        # Adjust rect for slight hover scale (visual expansion)
        if self._hover:
            dw = int(rect.width() * 0.04)
            dh = int(rect.height() * 0.04)
            rect = rect.adjusted(-dw, -dh, dw, dh)
            
        if self._pressed:
            rect = rect.adjusted(1, 1, -1, -1)

        # Border color & Background color depending on theme
        bg_color = QColor(theme['accent'])
        if self._hover:
            bg_color = QColor(theme['accent_hover'])
            
        if theme == Theme.RETRO:
            # Retro style button (solid pixel art look)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(QColor(theme['panel_border']), 3))
            painter.drawRect(rect)
            painter.setPen(QPen(QColor(theme['text'])))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        else:
            # Glass/Neon style button (smooth gradient, glows, rounded corners)
            gradient = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
            if self._hover:
                gradient.setColorAt(0, QColor(theme['accent_hover']))
                gradient.setColorAt(1, QColor(theme['accent']))
            else:
                gradient.setColorAt(0, QColor(theme['accent']))
                gradient.setColorAt(1, QColor(theme['accent']).darker(115))
                
            painter.setBrush(QBrush(gradient))
            
            # Subtle glow border
            border_pen = QPen(theme['panel_border'], 1.5)
            painter.setPen(border_pen)
            
            # Rounded corners
            painter.drawRoundedRect(rect, 12, 12)
            
            # Draw Text
            painter.setPen(QPen(QColor("#FFFFFF" if theme != Theme.GLASS else theme['text'])))
            font = QFont(theme['font_family'], 11, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

class GlassPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        
        # Default shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(25)
        self.shadow.setOffset(0, 8)
        self.shadow.setColor(ThemeManager.theme()['shadow'])
        self.setGraphicsEffect(self.shadow)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        theme = ThemeManager.theme()
        
        # Transparent panel
        rect = self.rect()
        
        if theme == Theme.RETRO:
            painter.setBrush(QBrush(theme['panel_bg']))
            painter.setPen(QPen(theme['panel_border'], 3))
            painter.drawRect(rect)
        else:
            # Frosted glass look
            painter.setBrush(QBrush(theme['panel_bg']))
            painter.setPen(QPen(theme['panel_border'], 1.5))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 16, 16)
