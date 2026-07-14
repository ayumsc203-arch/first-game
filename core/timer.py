from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class PuzzleTimer(QObject):
    updated = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        self.elapsed_seconds = 0
        
    def start(self):
        self.elapsed_seconds = 0
        self.timer.start(1000)  # Trigger every 1s
        self.updated.emit(self.get_formatted_time())
        
    def pause(self):
        self.timer.stop()
        
    def resume(self):
        self.timer.start(1000)
        
    def stop(self):
        self.timer.stop()
        
    def add_penalty(self, seconds=10):
        self.elapsed_seconds += seconds
        self.updated.emit(self.get_formatted_time())
        
    def get_formatted_time(self):
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
        
    def _on_timeout(self):
        self.elapsed_seconds += 1
        self.updated.emit(self.get_formatted_time())
