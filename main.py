import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFontDatabase, QFont

print("[DEBUG] Step 1: imports succeeded", flush=True)

# Change current working directory to script directory to ensure all relative asset paths resolve correctly
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add project root to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.camera import CameraThread
from core.ui import ThemeManager, Theme
from screens.home import HomeScreen
from screens.game import GameScreen
from screens.victory import VictoryScreen
from screens.settings import SettingsScreen
from screens.leaderboard import LeaderboardScreen
from screens.guide import GuideScreen
from utils.helpers import SettingsLoader, LeaderboardManager, StatisticsTracker
from utils.generate_sounds import generate_all_sounds

print("[DEBUG] Step 2: Custom imports succeeded", flush=True)

class MainWindow(QMainWindow):
    def __init__(self):
        print("[DEBUG] Step 4: MainWindow.__init__ starts", flush=True)
        super().__init__()
        
        # Load user configurations
        self.config = SettingsLoader.load()
        print("[DEBUG] Step 5: Config loaded", flush=True)
        
        # Apply theme
        theme_map = {
            'Dark Mode': Theme.DARK,
            'Cyber Neon': Theme.NEON,
            'Frost Glass': Theme.GLASS,
            '8-Bit Retro': Theme.RETRO
        }
        selected_theme = theme_map.get(self.config.get('theme_name', 'Dark Mode'), Theme.DARK)
        ThemeManager.set_theme(selected_theme)
        ThemeManager.sound_enabled = self.config.get('sound_enabled', True)
        print("[DEBUG] Step 6: Theme applied", flush=True)
        
        self.setWindowTitle("AI Webcam Puzzle Challenge")
        self.setMinimumSize(1024, 768)
        
        # Initialize background Camera processing thread
        print("[DEBUG] Step 7: CameraThread starting...", flush=True)
        self.camera_thread = CameraThread(camera_index=self.config.get('camera_index', 0))
        self.camera_thread.set_filter(self.config.get('filter_mode', 'Normal'))
        self.camera_thread.set_face_detection(False) # Center face on puzzle capture
        self.camera_thread.set_hand_tracking(self.config.get('hand_tracking', False))
        self.camera_thread.start()
        print("[DEBUG] Step 8: CameraThread active", flush=True)
        
        # Central Stacked Widget
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        
        # Create all Screens
        print("[DEBUG] Step 9: Creating screens...", flush=True)
        self.home_screen = HomeScreen(self.camera_thread, self)
        print("[DEBUG] HomeScreen created", flush=True)
        self.game_screen = GameScreen(self)
        print("[DEBUG] GameScreen created", flush=True)
        self.victory_screen = VictoryScreen(self)
        print("[DEBUG] VictoryScreen created", flush=True)
        self.settings_screen = SettingsScreen(self)
        print("[DEBUG] SettingsScreen created", flush=True)
        self.leaderboard_screen = LeaderboardScreen(is_stats_only=False, parent=self)
        print("[DEBUG] LeaderboardScreen created", flush=True)
        self.stats_screen = LeaderboardScreen(is_stats_only=True, parent=self)
        print("[DEBUG] StatsScreen created", flush=True)
        
        self.guide_screen = GuideScreen(self)
        print("[DEBUG] GuideScreen created", flush=True)
        
        # Load saved data into settings screen
        self.settings_screen.load_settings_data(self.config)
        
        # Add to stack
        self.stack.addWidget(self.home_screen)          # Index 0
        self.stack.addWidget(self.game_screen)          # Index 1
        self.stack.addWidget(self.victory_screen)       # Index 2
        self.stack.addWidget(self.settings_screen)      # Index 3
        self.stack.addWidget(self.leaderboard_screen)   # Index 4
        self.stack.addWidget(self.stats_screen)         # Index 5
        self.stack.addWidget(self.guide_screen)         # Index 6
        
        # Connect signals
        self.setup_connections()
        
        # Switch to menu
        self.stack.setCurrentIndex(0)
        print("[DEBUG] Step 10: MainWindow.__init__ finished successfully", flush=True)

    def setup_connections(self):
        # Home Screen Connections
        self.home_screen.start_game.connect(self.on_start_game)
        self.home_screen.show_settings.connect(lambda: self.stack.setCurrentIndex(3))
        self.home_screen.show_leaderboard.connect(self.on_show_leaderboard)
        self.home_screen.show_stats.connect(self.on_show_stats)
        self.home_screen.show_guide.connect(lambda: self.stack.setCurrentIndex(6))
        self.home_screen.btn_exit.clicked.connect(self.close)
        
        # Game Screen Connections
        self.game_screen.victory.connect(self.on_victory)
        self.game_screen.exit_to_menu.connect(self.on_exit_to_menu)
        
        # Connect Hand-tracking parameters to board
        self.camera_thread.hand_position.connect(self.game_screen.board_widget.update_hand_position)
        
        # Settings Connections
        self.settings_screen.back_to_menu.connect(self.on_save_settings_back)
        self.settings_screen.settings_changed.connect(self.on_settings_changed)
        
        # Victory Connections
        self.victory_screen.play_again.connect(self.on_play_again)
        self.victory_screen.new_photo.connect(lambda: self.stack.setCurrentIndex(0))
        self.victory_screen.main_menu.connect(lambda: self.stack.setCurrentIndex(0))
        
        # Leaderboard/Stats Connections
        self.leaderboard_screen.back_to_menu.connect(lambda: self.stack.setCurrentIndex(0))
        self.stats_screen.back_to_menu.connect(lambda: self.stack.setCurrentIndex(0))
        self.guide_screen.back_to_menu.connect(lambda: self.stack.setCurrentIndex(0))

    def on_start_game(self, frame_np):
        # Record game start in statistics
        StatisticsTracker.record_game_played()
        
        grid_size = self.config.get('grid_size', 3)
        rot_mode = self.config.get('rotation_mode', False)
        
        # Switch to game screen first, then start game to avoid dimension issues
        self.stack.setCurrentIndex(1)
        self.game_screen.start_new_game(frame_np, grid_size, rot_mode)

    def on_victory(self, seconds, moves, score, difficulty):
        # Save score
        LeaderboardManager.save_score(score, difficulty, moves, seconds)
        # Save stats
        StatisticsTracker.record_victory(seconds, score)
        
        # Fetch best time
        best_time = LeaderboardManager.get_best_time(difficulty)
        
        # Display victory
        self.victory_screen.show_victory(seconds, moves, score, difficulty, best_time)
        self.stack.setCurrentIndex(2)

    def on_exit_to_menu(self):
        # Stop timers
        self.game_screen.timer.stop()
        self.game_screen.solve_timer.stop()
        self.stack.setCurrentIndex(0)

    def on_show_leaderboard(self):
        self.leaderboard_screen.refresh()
        self.stack.setCurrentIndex(4)

    def on_show_stats(self):
        self.stats_screen.refresh()
        self.stack.setCurrentIndex(5)

    def on_settings_changed(self, new_settings):
        self.config = new_settings
        
        # Apply theme instantly
        theme_map = {
            'Dark Mode': Theme.DARK,
            'Cyber Neon': Theme.NEON,
            'Frost Glass': Theme.GLASS,
            '8-Bit Retro': Theme.RETRO
        }
        selected_theme = theme_map.get(new_settings.get('theme_name', 'Dark Mode'), Theme.DARK)
        ThemeManager.set_theme(selected_theme)
        
        # Update camera settings
        self.camera_thread.set_filter(new_settings.get('filter_mode', 'Normal'))
        self.camera_thread.set_hand_tracking(new_settings.get('hand_tracking', False))
        
        # Update sound toggle
        ThemeManager.sound_enabled = new_settings.get('sound_enabled', True)

    def on_save_settings_back(self):
        # Save to file
        SettingsLoader.save(self.config)
        self.stack.setCurrentIndex(0)

    def on_play_again(self):
        self.stack.setCurrentIndex(1)
        self.game_screen.restart_game()

    def closeEvent(self, event):
        # Stop background thread before exiting to prevent hang
        self.camera_thread.stop()
        self.camera_thread.wait()
        super().closeEvent(event)

def main():
    print("[DEBUG] main() starts", flush=True)
    # Setup directories
    os.makedirs("assets/sounds", exist_ok=True)
    os.makedirs("assets/icons", exist_ok=True)
    os.makedirs("assets/fonts", exist_ok=True)
    
    # Generate procedural sound files if they do not exist
    sound_files = ["click.wav", "hover.wav", "snap.wav", "wrong.wav", "shutter.wav", "countdown.wav", "countdown_smile.wav", "victory.wav"]
    sounds_missing = any(not os.path.exists(os.path.join("assets/sounds", s)) for s in sound_files)
    if sounds_missing:
        print("Sounds missing. Generating procedural WAV files...", flush=True)
        try:
            generate_all_sounds("assets/sounds")
        except Exception as e:
            print(f"Error generating sounds: {e}", flush=True)
            
    print("[DEBUG] Step 3: QApplication initializing...", flush=True)
    app = QApplication(sys.argv)
    
    # Application styling
    app.setStyle('Fusion')
    
    window = MainWindow()
    print("[DEBUG] Showing window...", flush=True)
    window.show()
    print("[DEBUG] Entering app exec...", flush=True)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
