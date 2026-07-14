import math
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

def ease_in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 2) / 2

def elastic_ease_out(t):
    if t == 0: return 0.0
    if t == 1: return 1.0
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1.0

def bounce_ease_out(t):
    n1 = 7.5625
    d1 = 2.75
    
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375

class PuzzleAnimator(QObject):
    updated = pyqtSignal()
    animation_finished = pyqtSignal()
    
    def __init__(self, pieces, parent=None):
        super().__init__(parent)
        self.pieces = pieces
        
        # 60 FPS Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_animations)
        
        # Animation properties
        self.duration = 1.0  # Duration in seconds
        self.elapsed = 0.0
        self.is_active = False
        
        # Store starting positions for interpolation
        self.start_positions = {}  # piece_id -> (start_x, start_y, start_scale, start_shadow)
        self.easing_func = bounce_ease_out
        
        # Shake properties
        self.shake_pieces = []  # List of (piece, start_t, duration)
        
    def start_shuffle_animation(self, duration=2.0, easing_type="bounce"):
        self.duration = duration
        self.elapsed = 0.0
        self.is_active = True
        
        if easing_type == "bounce":
            self.easing_func = bounce_ease_out
        elif easing_type == "elastic":
            self.easing_func = elastic_ease_out
        else:
            self.easing_func = ease_in_out_quad
            
        self.start_positions.clear()
        for piece in self.pieces:
            self.start_positions[piece.id] = (piece.x, piece.y, piece.scale, piece.shadow_intensity)
            # Make sure target scale is normal
            piece.target_scale = 1.0
            piece.target_shadow_intensity = 0.1
            
        self.timer.start(16)  # ~60 FPS

    def start_snap_animation(self, piece, duration=0.25):
        # Specific snap-to-grid animation for a single piece
        # If the timer is already running, we just update target_x, target_y.
        # But we can also run a general interpolation loop every frame for all active movement!
        # Let's run a continuous 60fps physics/animation loop whenever any piece is not at its target!
        piece.target_scale = 1.0
        piece.target_shadow_intensity = 0.05
        if not self.timer.isActive():
            self.timer.start(16)

    def trigger_shake(self, piece, duration=0.4):
        # Register piece for a shake animation
        # Store initial shake details
        self.shake_pieces.append({
            'piece': piece,
            'elapsed': 0.0,
            'duration': duration,
            'amplitude': 15.0  # Pixels of shake
        })
        if not self.timer.isActive():
            self.timer.start(16)

    def _update_animations(self):
        fps_step = 0.016  # Approx 16ms
        any_movement = False
        
        # 1. Update general interpolation for positions, scale, shadows
        if self.is_active:
            self.elapsed += fps_step
            progress = min(1.0, self.elapsed / self.duration)
            eased_val = self.easing_func(progress)
            
            for piece in self.pieces:
                if piece.id in self.start_positions:
                    start_x, start_y, start_scale, start_shadow = self.start_positions[piece.id]
                    
                    # Interpolate position
                    piece.x = start_x + (piece.target_x - start_x) * eased_val
                    piece.y = start_y + (piece.target_y - start_y) * eased_val
                    
                    # Interpolate scale & shadow
                    piece.scale = start_scale + (piece.target_scale - start_scale) * eased_val
                    piece.shadow_intensity = start_shadow + (piece.target_shadow_intensity - start_shadow) * eased_val
                    
            if progress >= 1.0:
                self.is_active = False
                self.start_positions.clear()
                self.animation_finished.emit()
            else:
                any_movement = True
                
        # 2. Continuous smooth easing/physics loop for individual drag snaps
        # For pieces that are NOT part of global shuffle, we can smoothly slide them to their target_x/y
        # using a simple lerp: x = x + (target_x - x) * 0.25 (springy and beautiful)
        if not self.is_active:
            for piece in self.pieces:
                if not piece.is_dragging:
                    dx = piece.target_x - piece.x
                    dy = piece.target_y - piece.y
                    ds = piece.target_scale - piece.scale
                    dsh = piece.target_shadow_intensity - piece.shadow_intensity
                    
                    # If offset is non-trivial, interpolate
                    if abs(dx) > 0.1 or abs(dy) > 0.1 or abs(ds) > 0.01 or abs(dsh) > 0.01:
                        piece.x += dx * 0.25
                        piece.y += dy * 0.25
                        piece.scale += ds * 0.2
                        piece.shadow_intensity += dsh * 0.2
                        any_movement = True
                    else:
                        piece.x = piece.target_x
                        piece.y = piece.target_y
                        piece.scale = piece.target_scale
                        piece.shadow_intensity = piece.target_shadow_intensity
                else:
                    # Piece is dragging, it should scale to 1.05 and shadow intensity to 0.25
                    ds = 1.05 - piece.scale
                    dsh = 0.25 - piece.shadow_intensity
                    if abs(ds) > 0.01 or abs(dsh) > 0.01:
                        piece.scale += ds * 0.2
                        piece.shadow_intensity += dsh * 0.2
                        any_movement = True

        # 3. Update shaking pieces (error visual feedback)
        still_shaking = []
        for shake in self.shake_pieces:
            piece = shake['piece']
            shake['elapsed'] += fps_step
            progress = shake['elapsed'] / shake['duration']
            
            if progress < 1.0:
                # Shake sine wave: decays over time
                decay = 1.0 - progress
                freq = 40.0  # speed of vibration
                offset = math.sin(progress * freq) * shake['amplitude'] * decay
                piece.shake_offset_x = offset
                still_shaking.append(shake)
                any_movement = True
            else:
                piece.shake_offset_x = 0.0
                piece.shake_offset_y = 0.0
                
        self.shake_pieces = still_shaking
        
        # 4. Notify widget to repaint
        self.updated.emit()
        
        # Stop timer if nothing is animating anymore
        if not any_movement and len(self.shake_pieces) == 0 and not self.is_active:
            self.timer.stop()
