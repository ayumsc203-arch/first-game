import random
import math
from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPixmap, QImage

class PuzzlePiece:
    def __init__(self, id_val, correct_row, correct_col, image, size):
        self.id = id_val
        self.correct_row = correct_row
        self.correct_col = correct_col
        self.image = image  # QPixmap or QImage
        self.size = size
        
        # Positions
        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0
        
        # Interaction state
        self.is_dragging = False
        self.is_locked = False
        
        # Rotation (0, 90, 180, 270 in degrees)
        self.rotation = 0
        
        # Animation properties
        self.scale = 1.0
        self.target_scale = 1.0
        self.shadow_intensity = 0.1  # Normal shadow
        self.target_shadow_intensity = 0.1
        
        # Shake animation offset
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

    def contains(self, point: QPointF):
        # Checks if point is inside current piece bounds (rotated bounds simplified as box for click ease)
        # Piece is drawn centered at (self.x, self.y) or top-left. Let's draw centered for easy rotation.
        half = self.size / 2.0
        return (self.x - half <= point.x() <= self.x + half and 
                self.y - half <= point.y() <= self.y + half)

    def rotate(self):
        if not self.is_locked:
            self.rotation = (self.rotation + 90) % 360

class PuzzleManager(QObject):
    puzzle_solved = pyqtSignal()
    piece_placed = pyqtSignal(bool)  # Emits True if correct, False if wrong
    
    def __init__(self):
        super().__init__()
        self.pieces = []
        self.grid_size = 3  # Default Easy 3x3
        self.board_rect = QRectF(0, 0, 600, 600)  # Central grid rect
        self.rotation_mode = False
        
    def setup_puzzle(self, image_np, grid_size, screen_width, screen_height, rotation_mode=False):
        """Slices the image and creates the puzzle pieces."""
        self.grid_size = grid_size
        self.rotation_mode = rotation_mode
        self.pieces = []
        
        # Convert OpenCV BGR to RGB, then to QImage
        import cv2
        rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        h, w, c = rgb_image.shape
        
        # Ensure square crop
        crop_size = min(w, h)
        cx, cy = w // 2, h // 2
        cropped = rgb_image[cy - crop_size//2 : cy + crop_size//2, cx - crop_size//2 : cx + crop_size//2]
        
        # Resize to standard size (e.g. 600x600 for high resolution pieces)
        standard_size = 600
        resized = cv2.resize(cropped, (standard_size, standard_size))
        
        # Create QImage
        qimage = QImage(resized.data, standard_size, standard_size, standard_size * 3, QImage.Format.Format_RGB888)
        
        piece_pixel_size = standard_size // grid_size
        piece_id = 0
        
        # Define board layout in center of screen
        board_x = (screen_width - standard_size) / 2
        board_y = (screen_height - standard_size) / 2
        self.board_rect = QRectF(board_x, board_y, standard_size, standard_size)
        
        for r in range(grid_size):
            for c in range(grid_size):
                # Crop QImage piece
                px = c * piece_pixel_size
                py = r * piece_pixel_size
                cropped_piece_img = qimage.copy(px, py, piece_pixel_size, piece_pixel_size)
                
                # Convert to Pixmap for rendering efficiency
                pixmap = QPixmap.fromImage(cropped_piece_img)
                
                piece = PuzzlePiece(piece_id, r, c, pixmap, piece_pixel_size)
                
                # Initial position is its solved position
                solved_x = board_x + (c + 0.5) * piece_pixel_size
                solved_y = board_y + (r + 0.5) * piece_pixel_size
                piece.x = solved_x
                piece.y = solved_y
                piece.target_x = solved_x
                piece.target_y = solved_y
                
                self.pieces.append(piece)
                piece_id += 1

    def shuffle_pieces(self, screen_width, screen_height):
        """Scrambles pieces randomly outside or around the board."""
        piece_size = 600 // self.grid_size
        
        # We can scatter pieces around the board edges or on the sides
        # Create safe spawn regions
        left_region = (50, self.board_rect.left() - piece_size)
        right_region = (self.board_rect.right() + piece_size, screen_width - 50)
        top_region = (50, self.board_rect.top() - piece_size)
        bottom_region = (self.board_rect.bottom() + piece_size, screen_height - 50)
        
        regions = []
        if left_region[0] < left_region[1]:
            regions.append(('left', left_region))
        if right_region[0] < right_region[1]:
            regions.append(('right', right_region))
        if top_region[0] < top_region[1]:
            regions.append(('top', top_region))
        if bottom_region[0] < bottom_region[1]:
            regions.append(('bottom', bottom_region))
            
        if not regions:
            # Fallback if window is too small
            regions = [('all', (50, screen_width - 50))]
            
        for piece in self.pieces:
            piece.is_locked = False
            
            # Select random region
            reg_type, bounds = random.choice(regions)
            if reg_type == 'left' or reg_type == 'right':
                rx = random.uniform(bounds[0], bounds[1])
                ry = random.uniform(50, screen_height - 50)
            elif reg_type == 'top' or reg_type == 'bottom':
                rx = random.uniform(50, screen_width - 50)
                ry = random.uniform(bounds[0], bounds[1])
            else:
                rx = random.uniform(50, screen_width - 50)
                ry = random.uniform(50, screen_height - 50)
                
            piece.target_x = rx
            piece.target_y = ry
            
            # Random rotation if mode enabled
            if self.rotation_mode:
                piece.rotation = random.choice([0, 90, 180, 270])
            else:
                piece.rotation = 0

    def check_snap(self, piece):
        """Checks if a piece is dropped close to its correct target grid slot."""
        if piece.is_locked:
            return
            
        piece_size = 600 // self.grid_size
        
        # Solved position coordinates
        solved_x = self.board_rect.left() + (piece.correct_col + 0.5) * piece_size
        solved_y = self.board_rect.top() + (piece.correct_row + 0.5) * piece_size
        
        distance = math.hypot(piece.x - solved_x, piece.y - solved_y)
        
        # Dynamic snap distance: half of piece size
        snap_threshold = piece_size * 0.5
        
        if distance < snap_threshold and (not self.rotation_mode or piece.rotation == 0):
            # Snap to grid!
            piece.target_x = solved_x
            piece.target_y = solved_y
            piece.is_locked = True
            piece.rotation = 0  # Just in case
            piece.target_scale = 1.0
            piece.target_shadow_intensity = 0.05
            self.piece_placed.emit(True)
            
            # Check if game is completely solved
            if all(p.is_locked for p in self.pieces):
                self.puzzle_solved.emit()
        else:
            # Shake and return to drag start, handled by the UI controller or snaps back
            self.piece_placed.emit(False)

    def get_hint(self):
        """Finds one misplaced/unsolved piece and briefly moves it towards the target or flashes it."""
        unsolved = [p for p in self.pieces if not p.is_locked]
        if unsolved:
            # Select random unsolved piece
            piece = random.choice(unsolved)
            return piece
        return None

    def auto_solve_step(self):
        """Moves one unsolved piece directly to its correct slot (for auto-solve mode)."""
        unsolved = [p for p in self.pieces if not p.is_locked]
        if unsolved:
            piece = unsolved[0]
            piece_size = 600 // self.grid_size
            solved_x = self.board_rect.left() + (piece.correct_col + 0.5) * piece_size
            solved_y = self.board_rect.top() + (piece.correct_row + 0.5) * piece_size
            
            piece.target_x = solved_x
            piece.target_y = solved_y
            piece.rotation = 0
            piece.is_locked = True
            
            if all(p.is_locked for p in self.pieces):
                self.puzzle_solved.emit()
            return piece
        return None
