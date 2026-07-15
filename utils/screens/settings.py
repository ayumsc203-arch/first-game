from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QGroupBox, QButtonGroup, QRadioButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor, QLinearGradient, QFont
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme

class SettingsScreen(QWidget):
    # Signals
    back_to_menu = pyqtSignal()
    settings_changed = pyqtSignal(dict)  # Emits dictionary of updated settings
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Default Settings Values
        self.settings_data = {
            'camera_index': 0,
            'grid_size': 3,
            'rotation_mode': False,
            'hand_tracking': False,
            'filter_mode': 'Normal',
            'sound_enabled': True,
            'theme_name': 'Dark Mode'
        }
        
        # Layouts
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(50, 40, 50, 40)
        self.layout.setSpacing(20)
        
        # Header
        self.header_panel = GlassPanel(self)
        self.header_layout = QHBoxLayout(self.header_panel)
        self.header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.title_label = QLabel("SETTINGS & PREFERENCES", self)
        self.header_layout.addWidget(self.title_label)
        self.layout.addWidget(self.header_panel)
        
        # Central Scroll/Options Grid Box
        self.options_panel = GlassPanel(self)
        self.options_layout = QVBoxLayout(self.options_panel)
        self.options_layout.setContentsMargins(40, 30, 40, 30)
        self.options_layout.setSpacing(25)
        
        # Category: Gameplay & Difficulty
        self.gameplay_group = QHBoxLayout()
        
        # Difficulty Select
        self.diff_label = QLabel("Puzzle Size:", self)
        self.combo_diff = QComboBox(self)
        self.combo_diff.addItems(["Easy (3 x 3)", "Medium (4 x 4)", "Hard (5 x 5)", "Expert (6 x 6)"])
        self.combo_diff.currentIndexChanged.connect(self.save_settings)
        
        # Rotation mode Check
        self.check_rotation = QCheckBox("Rotate Pieces (Hard)", self)
        self.check_rotation.stateChanged.connect(self.save_settings)
        
        # Hand-tracking Mode
        self.check_hand = QCheckBox("MediaPipe Hands Tracking", self)
        self.check_hand.stateChanged.connect(self.save_settings)
        
        self.gameplay_group.addWidget(self.diff_label)
        self.gameplay_group.addWidget(self.combo_diff)
        self.gameplay_group.addSpacing(30)
        self.gameplay_group.addWidget(self.check_rotation)
        self.gameplay_group.addSpacing(30)
        self.gameplay_group.addWidget(self.check_hand)
        
        self.options_layout.addLayout(self.gameplay_group)
        
        # Divider Line
        self.options_layout.addSpacing(5)
        
        # Category: Video & Audio
        self.media_group = QHBoxLayout()
        
        # Camera Index Select
        self.cam_label = QLabel("Camera Input:", self)
        self.combo_cam = QComboBox(self)
        self.combo_cam.addItems(["Default Camera (0)", "Alternative Cam (1)", "Alternative Cam (2)"])
        self.combo_cam.currentIndexChanged.connect(self.save_settings)
        
        # Filter select
        self.filter_label = QLabel("Live Stream Filter:", self)
        self.combo_filter = QComboBox(self)
        self.combo_filter.addItems(["Normal", "Black & White", "Sepia", "Sketch", "Cartoon", "Pixel Art", "Comic", "Neon"])
        self.combo_filter.currentIndexChanged.connect(self.save_settings)
        
        # Audio check
        self.check_sound = QCheckBox("Enable Sound FX", self)
        self.check_sound.setChecked(True)
        self.check_sound.stateChanged.connect(self.save_settings)
        
        self.media_group.addWidget(self.cam_label)
        self.media_group.addWidget(self.combo_cam)
        self.media_group.addSpacing(30)
        self.media_group.addWidget(self.filter_label)
        self.media_group.addWidget(self.combo_filter)
        self.media_group.addSpacing(30)
        self.media_group.addWidget(self.check_sound)
        
        self.options_layout.addLayout(self.media_group)
        
        # Divider Line
        self.options_layout.addSpacing(5)
        
        # Category: UI Theme Selection
        self.theme_vbox = QVBoxLayout()
        self.theme_label = QLabel("App UI Theme Styling:", self)
        self.theme_vbox.addWidget(self.theme_label)
        
        self.theme_hbox = QHBoxLayout()
        self.theme_hbox.setSpacing(15)
        
        self.btn_theme_dark = GlassButton("Dark Ice Mode", self)
        self.btn_theme_neon = GlassButton("Cyberpunk Neon", self)
        self.btn_theme_glass = GlassButton("Frost Glass", self)
        self.btn_theme_retro = GlassButton("8-Bit Retro", self)
        
        self.btn_theme_dark.clicked.connect(lambda: self.apply_theme_choice(Theme.DARK, "Dark Mode"))
        self.btn_theme_neon.clicked.connect(lambda: self.apply_theme_choice(Theme.NEON, "Cyber Neon"))
        self.btn_theme_glass.clicked.connect(lambda: self.apply_theme_choice(Theme.GLASS, "Frost Glass"))
        self.btn_theme_retro.clicked.connect(lambda: self.apply_theme_choice(Theme.RETRO, "8-Bit Retro"))
        
        self.theme_hbox.addWidget(self.btn_theme_dark)
        self.theme_hbox.addWidget(self.btn_theme_neon)
        self.theme_hbox.addWidget(self.btn_theme_glass)
        self.theme_hbox.addWidget(self.btn_theme_retro)
        
        self.theme_vbox.addLayout(self.theme_hbox)
        self.options_layout.addLayout(self.theme_vbox)
        
        self.layout.addWidget(self.options_panel, 1)
        
        # Back Button (Bottom)
        self.btn_back = GlassButton("Save & Back to Menu", self)
        self.btn_back.clicked.connect(self.back_to_menu.emit)
        self.layout.addWidget(self.btn_back)
        
        # Apply style sheets for standard elements like combo box and checkboxes
        self.combo_diff.setStyleSheet("QComboBox { background-color: #1E293B; color: white; border: 1px solid #475569; border-radius: 4px; padding: 5px; } QComboBox QAbstractItemView { background-color: #1E293B; color: white; selection-background-color: #60A5FA; }")
        self.combo_cam.setStyleSheet("QComboBox { background-color: #1E293B; color: white; border: 1px solid #475569; border-radius: 4px; padding: 5px; } QComboBox QAbstractItemView { background-color: #1E293B; color: white; selection-background-color: #60A5FA; }")
        self.combo_filter.setStyleSheet("QComboBox { background-color: #1E293B; color: white; border: 1px solid #475569; border-radius: 4px; padding: 5px; } QComboBox QAbstractItemView { background-color: #1E293B; color: white; selection-background-color: #60A5FA; }")
        
        self.check_rotation.setStyleSheet("QCheckBox { color: white; font-size: 14px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        self.check_hand.setStyleSheet("QCheckBox { color: white; font-size: 14px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        self.check_sound.setStyleSheet("QCheckBox { color: white; font-size: 14px; } QCheckBox::indicator { width: 18px; height: 18px; }")

    def apply_theme_choice(self, theme_dict, theme_name):
        ThemeManager.set_theme(theme_dict)
        self.settings_data['theme_name'] = theme_name
        
        # Apply theme instantly
        self.save_settings()
        self.update()

    def save_settings(self):
        # Update settings data dict
        grid_sizes = [3, 4, 5, 6]
        self.settings_data['grid_size'] = grid_sizes[self.combo_diff.currentIndex()]
        self.settings_data['rotation_mode'] = self.check_rotation.isChecked()
        self.settings_data['hand_tracking'] = self.check_hand.isChecked()
        self.settings_data['camera_index'] = self.combo_cam.currentIndex()
        self.settings_data['filter_mode'] = self.combo_filter.currentText()
        
        sound_on = self.check_sound.isChecked()
        self.settings_data['sound_enabled'] = sound_on
        ThemeManager.sound_enabled = sound_on
        
        # Emit signal to parent/main setup
        self.settings_changed.emit(self.settings_data)

    def load_settings_data(self, data):
        self.settings_data = data
        
        # Sync widgets
        grid_map = {3: 0, 4: 1, 5: 2, 6: 3}
        self.combo_diff.setCurrentIndex(grid_map.get(data.get('grid_size', 3), 0))
        self.check_rotation.setChecked(data.get('rotation_mode', False))
        self.check_hand.setChecked(data.get('hand_tracking', False))
        self.combo_cam.setCurrentIndex(data.get('camera_index', 0))
        self.combo_filter.setCurrentText(data.get('filter_mode', 'Normal'))
        self.check_sound.setChecked(data.get('sound_enabled', True))

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
        
        # Sync widget style updates
        font_family = theme['font_family']
        self.title_label.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 24px; font-weight: 800;")
        
        self.diff_label.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 14px; font-weight: bold;")
        self.cam_label.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 14px; font-weight: bold;")
        self.filter_label.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 14px; font-weight: bold;")
        self.theme_label.setStyleSheet(f"color: {theme['text']}; font-family: {font_family}; font-size: 16px; font-weight: bold; margin-bottom: 5px;")
