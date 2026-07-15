import os
import json
from datetime import datetime

class SettingsLoader:
    FILE_PATH = "config.json"
    
    DEFAULT_SETTINGS = {
        'camera_index': 0,
        'grid_size': 3,
        'rotation_mode': False,
        'hand_tracking': False,
        'filter_mode': 'Normal',
        'sound_enabled': True,
        'theme_name': 'Dark Mode'
    }
    
    @classmethod
    def load(cls):
        if not os.path.exists(cls.FILE_PATH):
            cls.save(cls.DEFAULT_SETTINGS)
            return cls.DEFAULT_SETTINGS
        try:
            with open(cls.FILE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return cls.DEFAULT_SETTINGS

    @classmethod
    def save(cls, settings_dict):
        try:
            with open(cls.FILE_PATH, 'w') as f:
                json.dump(settings_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

class LeaderboardManager:
    FILE_PATH = "leaderboard.json"
    
    @classmethod
    def load_scores(cls):
        if not os.path.exists(cls.FILE_PATH):
            return []
        try:
            with open(cls.FILE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def save_score(cls, score, difficulty, moves, seconds):
        scores = cls.load_scores()
        
        # New record entry
        difficulty_text = {3: "Easy", 4: "Medium", 5: "Hard", 6: "Expert"}.get(difficulty, "Custom")
        mins = seconds // 60
        secs = seconds % 60
        time_str = f"{mins:02d}:{secs:02d}"
        
        entry = {
            'score': score,
            'difficulty': difficulty_text,
            'moves': moves,
            'time': time_str,
            'seconds': seconds,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        scores.append(entry)
        # Sort by score descending, then by seconds ascending
        scores = sorted(scores, key=lambda x: (-x['score'], x['seconds']))
        
        # Keep top 20
        scores = scores[:20]
        
        try:
            with open(cls.FILE_PATH, 'w') as f:
                json.dump(scores, f, indent=4)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
            
        return scores

    @classmethod
    def get_best_time(cls, difficulty):
        scores = cls.load_scores()
        diff_text = {3: "Easy", 4: "Medium", 5: "Hard", 6: "Expert"}.get(difficulty, "Custom")
        filtered = [s for s in scores if s['difficulty'] == diff_text]
        if filtered:
            # Sort by time seconds ascending
            filtered = sorted(filtered, key=lambda x: x['seconds'])
            return filtered[0]['seconds']
        return None

class StatisticsTracker:
    FILE_PATH = "stats.json"
    
    DEFAULT_STATS = {
        'games_played': 0,
        'games_won': 0,
        'total_time': 0,
        'best_score': 0,
        'fastest_solve': 999999
    }
    
    @classmethod
    def load_stats(cls):
        if not os.path.exists(cls.FILE_PATH):
            cls.save_stats(cls.DEFAULT_STATS)
            return cls.DEFAULT_STATS
        try:
            with open(cls.FILE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return cls.DEFAULT_STATS

    @classmethod
    def save_stats(cls, stats_dict):
        try:
            with open(cls.FILE_PATH, 'w') as f:
                json.dump(stats_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")

    @classmethod
    def record_game_played(cls):
        stats = cls.load_stats()
        stats['games_played'] += 1
        cls.save_stats(stats)

    @classmethod
    def record_victory(cls, seconds, score):
        stats = cls.load_stats()
        stats['games_won'] += 1
        stats['total_time'] += seconds
        
        if score > stats['best_score']:
            stats['best_score'] = score
            
        if seconds < stats['fastest_solve']:
            stats['fastest_solve'] = seconds
            
        cls.save_stats(stats)
