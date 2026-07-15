from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QLinearGradient, QPainterPath
from core.ui import GlassButton, GlassPanel, ThemeManager, Theme
from core.puzzle import PuzzleManager
from core.animation import PuzzleAnimator
from core.timer import PuzzleTimer
from core.score import ScoreCalculator
import numpy as np

class PuzzleBoardWidget(QWidget):
    def __init__(self, manager, animator, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.animator = animator
        self.setMouseTracking(True)
        
        self.dragged_piece = None
        self.drag_offset = QPointF(0, 0)
        self.show_ghost = False
        
        # Original captured image for ghost preview
        self.raw_image_pixmap = None
        
        # Connect animator repaint loop
        self.animator.updated.connect(self.update)
        
        # Hand tracking cursor coordinates
        self.hand_cursor = QPointF(-100, -100)
        self.hand_clicking = False
        self.last_hand_clicking = False
        self.hand_active = False

    def set_raw_image(self, img_np):
        import cv2
        from PyQt6.QtGui import QImage, QPixmap
        rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        self.raw_image_pixmap = QPixmap.fromImage(qimg).scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.update()

    def update_hand_position(self, norm_x, norm_y, is_clicking):
        self.hand_active = True
        
        # Map normalized coordinates to local widget coords
        wx = norm_x * self.width()
        wy = norm_y * self.height()
        self.hand_cursor = QPointF(wx, wy)
        self.hand_clicking = is_clicking
        
        # Handle hand click logic (mimics mouse press, move, release)
        if self.hand_clicking and not self.last_hand_clicking:
            # Press
            self.handle_press(self.hand_cursor)
        elif not self.hand_clicking and self.last_hand_clicking:
            # Release
            self.handle_release(self.hand_cursor)
        elif self.hand_clicking and self.last_hand_clicking:
            # Move/Drag
            self.handle_move(self.hand_cursor)
            
        self.last_hand_clicking = self.hand_clicking
        self.update()

    def mousePressEvent(self, event):
        self.hand_active = False
        if event.button() == Qt.MouseButton.LeftButton:
            self.handle_press(QPointF(event.position()))
        elif event.button() == Qt.MouseButton.RightButton:
            # Rotate piece on right click
            pos = QPointF(event.position())
            for piece in reversed(self.manager.pieces):
                if not piece.is_locked and piece.contains(pos):
                    piece.rotate()
                    ThemeManager.play_sound("assets/sounds/click.wav")
                    self.update()
                    break
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.hand_active = False
        self.handle_move(QPointF(event.position()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.hand_active = False
        if event.button() == Qt.MouseButton.LeftButton:
            self.handle_release(QPointF(event.position()))
        super().mouseReleaseEvent(event)

    def handle_press(self, pos):
        # Scan from top (reversed list) to pick the topmost piece
        for piece in reversed(self.manager.pieces):
            if not piece.is_locked and piece.contains(pos):
                self.dragged_piece = piece
                piece.is_dragging = True
                piece.target_scale = 1.06
                piece.target_shadow_intensity = 0.25
                self.drag_offset = QPointF(piece.x - pos.x(), piece.y - pos.y())
                # Move to the end of list so it renders on top
                self.manager.pieces.remove(piece)
                self.manager.pieces.append(piece)
                ThemeManager.play_sound("assets/sounds/click.wav")
                break

    def handle_move(self, pos):
        if self.dragged_piece:
            self.dragged_piece.target_x = pos.x() + self.drag_offset.x()
            self.dragged_piece.target_y = pos.y() + self.drag_offset.y()
            # Fast update for smooth dragging
            self.dragged_piece.x = self.dragged_piece.target_x
            self.dragged_piece.y = self.dragged_piece.target_y
            self.update()

    def handle_release(self, pos):
        if self.dragged_piece:
            piece = self.dragged_piece
            self.dragged_piece = None
            piece.is_dragging = False
            
            # Record start pos in case of snapback
            old_tx, old_ty = piece.x, piece.y
            
            # Snap check
            self.manager.check_snap(piece)
            
            if not piece.is_locked:
                # Wrong placement or just dropped floating
                # If dropped inside the grid and not snapped (wrong slot or rotation)
                if self.manager.board_rect.contains(pos):
                    # Play wrong sound and shake
                    ThemeManager.play_sound("assets/sounds/wrong.wav")
                    self.animator.trigger_shake(piece)
                    # Float back to random position outside board (or keep where dropped)
                    # Let's keep it where dropped but lower its shadow
                    piece.target_scale = 1.0
                    piece.target_shadow_intensity = 0.1
                else:
                    # Dropped outside grid - play drop sound
                    ThemeManager.play_sound("assets/sounds/snap.wav")
                    piece.target_scale = 1.0
                    piece.target_shadow_intensity = 0.1
            else:
                # Correct snap
                ThemeManager.play_sound("assets/sounds/snap.wav")
                
            self.animator.start_snap_animation(piece)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_H:
            self.show_ghost = True
            self.update()
        elif event.key() == Qt.Key.Key_R and self.dragged_piece:
            # Rotate currently dragged piece with R
            self.dragged_piece.rotate()
            ThemeManager.play_sound("assets/sounds/click.wav")
            self.update()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_H:
            self.show_ghost = False
            self.update()
        super().keyReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        theme = ThemeManager.theme()
        
        # Draw board background layout
        board = self.manager.board_rect
        
        # Transparent board container
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.setPen(QPen(theme['panel_border'], 2))
        painter.drawRoundedRect(board, 12, 12)
        
        # Draw grid outlines
        grid_size = self.manager.grid_size
        step = board.width() / grid_size
        
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1, Qt.PenStyle.DashLine))
        for i in range(1, grid_size):
            # Verticals
            painter.drawLine(int(board.left() + i * step), int(board.top()), 
                             int(board.left() + i * step), int(board.bottom()))
            # Horizontals
            painter.drawLine(int(board.left()), int(board.top() + i * step), 
                             int(board.right()), int(board.top() + i * step))
            
        # Draw ghost preview if held
        if self.show_ghost and self.raw_image_pixmap:
            painter.setOpacity(0.3)
            painter.drawPixmap(board.toRect(), self.raw_image_pixmap)
            painter.setOpacity(1.0)

        # Draw puzzle pieces (locked first, dragging last so it renders on top)
        # Sort so dragging piece is painted last
        sorted_pieces = sorted(self.manager.pieces, key=lambda p: p.is_dragging)
        
        for piece in sorted_pieces:
            self.draw_piece(painter, piece, theme)
            
        # Draw Hand cursor if hand-tracking is active
        if self.hand_active:
            color = QColor(theme['accent'])
            if self.hand_clicking:
                color = QColor(theme['success'])
            
            # Glow aura
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 60)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(self.hand_cursor, 24, 24)
            
            # Center pointer
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawEllipse(self.hand_cursor, 8, 8)

    def draw_piece(self, painter, piece, theme):
        # 1. Shadow
        shadow_dist = int(piece.size * 0.08 * piece.scale)
        shadow_blur = int(piece.size * 0.12 * piece.scale)
        
        painter.save()
        
        # Calculate visual position (incorporating shake offset)
        vx = piece.x + piece.shake_offset_x
        vy = piece.y + piece.shake_offset_y
        
        # Draw shadow
        painter.translate(vx + shadow_dist, vy + shadow_dist)
        painter.rotate(piece.rotation)
        shadow_rect = QRectF(-piece.size/2, -piece.size/2, piece.size, piece.size)
        painter.setBrush(QBrush(QColor(0, 0, 0, int(255 * piece.shadow_intensity))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(shadow_rect, 10, 10)
        
        painter.restore()
        
        # 2. Main Piece Image
        painter.save()
        
        painter.translate(vx, vy)
        painter.scale(piece.scale, piece.scale)
        painter.rotate(piece.rotation)
        
        piece_rect = QRectF(-piece.size/2, -piece.size/2, piece.size, piece.size)
        
        # Clip image to rounded rect
        clip_path = QPainterPath()
        clip_path.addRoundedRect(piece_rect, 10, 10)
        painter.setClipPath(clip_path)
        
        # Draw actual chunk image
        painter.drawPixmap(piece_rect.toRect(), piece.image)
        
        # Disable clip to draw border on top
        painter.setClipping(False)
        
        # Draw piece borders
        if piece.is_locked:
            # Glow green border
            border_pen = QPen(QColor(theme['success']), 3.0)
        elif piece.is_dragging:
            # Highlight border
            border_pen = QPen(QColor(theme['accent']), 2.5)
        else:
            # Subtle glass border
            border_pen = QPen(theme['panel_border'], 1.5)
            
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(piece_rect, 10, 10)
        
        painter.restore()

class GameScreen(QWidget):
    # Signals
    victory = pyqtSignal(int, int, int, int)  # Emits Time (secs), Moves, Score, Difficulty
    exit_to_menu = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = PuzzleManager()
        self.animator = PuzzleAnimator(self.manager.pieces, self)
        
        # UI Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(15)
        
        # HUD Panel (Top)
        self.hud_panel = GlassPanel(self)
        self.hud_layout = QHBoxLayout(self.hud_panel)
        self.hud_layout.setContentsMargins(20, 10, 20, 10)
        
        self.hud_timer = QLabel("Time: 00:00", self)
        self.hud_moves = QLabel("Moves: 0", self)
        self.hud_difficulty = QLabel("Difficulty: Easy", self)
        
        # HUD styling
        for label in [self.hud_timer, self.hud_moves, self.hud_difficulty]:
            label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
            
        self.btn_pause = GlassButton("Pause", self)
        self.btn_pause.setMinimumHeight(36)
        self.btn_pause.clicked.connect(self.toggle_pause)
        
        self.btn_restart = GlassButton("Restart", self)
        self.btn_restart.setMinimumHeight(36)
        self.btn_restart.clicked.connect(self.restart_game)
        
        self.hud_layout.addWidget(self.hud_timer)
        self.hud_layout.addStretch()
        self.hud_layout.addWidget(self.hud_moves)
        self.hud_layout.addStretch()
        self.hud_layout.addWidget(self.hud_difficulty)
        self.hud_layout.addSpacing(40)
        self.hud_layout.addWidget(self.btn_pause)
        self.hud_layout.addWidget(self.btn_restart)
        
        # Main puzzle canvas
        self.board_widget = PuzzleBoardWidget(self.manager, self.animator, self)
        self.board_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Bottom Progress Panel
        self.progress_panel = GlassPanel(self)
        self.progress_layout = QHBoxLayout(self.progress_panel)
        self.progress_layout.setContentsMargins(20, 10, 20, 10)
        
        self.progress_label = QLabel("Solved: 0 / 9", self)
        self.progress_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background-color: #34D399;
                border-radius: 6px;
            }
        """)
        
        self.btn_hint = GlassButton("Hint", self)
        self.btn_hint.setMinimumHeight(36)
        self.btn_hint.clicked.connect(self.trigger_hint)
        
        self.btn_solve = GlassButton("Auto Solve", self)
        self.btn_solve.setMinimumHeight(36)
        self.btn_solve.clicked.connect(self.trigger_auto_solve)
        
        self.btn_exit = GlassButton("Quit", self)
        self.btn_exit.setMinimumHeight(36)
        self.btn_exit.clicked.connect(self.exit_to_menu.emit)
        
        self.progress_layout.addWidget(self.progress_label)
        self.progress_layout.addWidget(self.progress_bar, 1)
        self.progress_layout.addSpacing(20)
        self.progress_layout.addWidget(self.btn_hint)
        self.progress_layout.addWidget(self.btn_solve)
        self.progress_layout.addWidget(self.btn_exit)
        
        self.layout.addWidget(self.hud_panel)
        self.layout.addWidget(self.board_widget, 1)
        self.layout.addWidget(self.progress_panel)
        
        # Connect Manager signals
        self.manager.piece_placed.connect(self.on_piece_placed)
        self.manager.puzzle_solved.connect(self.on_solved)
        
        # Game states
        self.timer = PuzzleTimer(self)
        self.timer.updated.connect(self.update_timer_display)
        self.moves_count = 0
        self.difficulty_grid_size = 3
        self.game_paused = False
        
        # Auto-solve timer
        self.solve_timer = QTimer(self)
        self.solve_timer.timeout.connect(self.tick_auto_solve)
        
        # Store capture for restart
        self.captured_frame_np = None
        self.rotation_mode = False

    def start_new_game(self, image_np, grid_size, rotation_mode=False):
        self.captured_frame_np = image_np
        self.difficulty_grid_size = grid_size
        self.rotation_mode = rotation_mode
        self.moves_count = 0
        self.game_paused = False
        self.btn_pause.setText("Pause")
        
        # Set title texts
        diff_text = {3: "Easy (3x3)", 4: "Medium (4x4)", 5: "Hard (5x5)", 6: "Expert (6x6)"}.get(grid_size, "Custom")
        if rotation_mode:
            diff_text += " + Rotate"
        self.hud_difficulty.setText(f"Difficulty: {diff_text}")
        self.hud_moves.setText("Moves: 0")
        
        # Setup slices
        # Size based on board size
        self.manager.setup_puzzle(image_np, grid_size, 1024, 768, rotation_mode)
        self.board_widget.set_raw_image(image_np)
        
        # Update animator piece list
        self.animator.pieces = self.manager.pieces
        
        # Perform Shuffle Flying Animation
        self.manager.shuffle_pieces(self.board_widget.width(), self.board_widget.height())
        self.animator.start_shuffle_animation(2.0, "bounce")
        
        # Update progress widgets
        self.update_progress()
        
        # Start Timer after shuffle finishes
        self.animator.animation_finished.disconnect() if hasattr(self.animator, 'animation_finished_connected') else None
        self.animator.animation_finished.connect(self.timer.start)
        self.animator.animation_finished_connected = True

    def restart_game(self):
        if self.captured_frame_np is not None:
            self.solve_timer.stop()
            self.start_new_game(self.captured_frame_np, self.difficulty_grid_size, self.rotation_mode)

    def toggle_pause(self):
        self.game_paused = not self.game_paused
        if self.game_paused:
            self.timer.pause()
            self.btn_pause.setText("Resume")
            self.board_widget.setEnabled(False)
        else:
            self.timer.resume()
            self.btn_pause.setText("Pause")
            self.board_widget.setEnabled(True)

    def trigger_hint(self):
        if self.game_paused: return
        piece = self.manager.get_hint()
        if piece:
            # Play snap sound as highlight trigger
            ThemeManager.play_sound("assets/sounds/click.wav")
            # Apply time penalty
            self.timer.add_penalty(10)
            
            # Animate the hint piece briefly towards target and back, or just flash it
            # Let's flash it by scaling it up and shaking
            piece.target_scale = 1.15
            piece.target_shadow_intensity = 0.3
            self.animator.trigger_shake(piece, 0.6)
            
            # Revert scale after 600ms
            QTimer.singleShot(600, lambda: self.reset_piece_scale(piece))

    def reset_piece_scale(self, piece):
        piece.target_scale = 1.0
        piece.target_shadow_intensity = 0.1
        self.board_widget.update()

    def trigger_auto_solve(self):
        if self.game_paused: return
        self.btn_solve.setEnabled(False)
        self.solve_timer.start(500)  # Move one piece every 500ms

    def tick_auto_solve(self):
        piece = self.manager.auto_solve_step()
        if piece:
            ThemeManager.play_sound("assets/sounds/snap.wav")
            self.animator.start_snap_animation(piece)
            self.update_progress()
        else:
            self.solve_timer.stop()
            self.btn_solve.setEnabled(True)

    def on_piece_placed(self, is_correct):
        if not is_correct:
            # Increments move count
            self.moves_count += 1
            self.hud_moves.setText(f"Moves: {self.moves_count}")
        else:
            # Increments correct move
            self.moves_count += 1
            self.hud_moves.setText(f"Moves: {self.moves_count}")
            self.update_progress()

    def update_progress(self):
        total = len(self.manager.pieces)
        solved = sum(1 for p in self.manager.pieces if p.is_locked)
        self.progress_label.setText(f"Solved: {solved} / {total}")
        
        percentage = int((solved / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)

    def update_timer_display(self, time_str):
        self.hud_timer.setText(f"Time: {time_str}")

    def on_solved(self):
        self.timer.stop()
        self.solve_timer.stop()
        
        # Calculate final details
        elapsed = self.timer.elapsed_seconds
        score = ScoreCalculator.calculate_score(self.difficulty_grid_size, self.moves_count, elapsed)
        
        # Emit victory signal
        self.victory.emit(elapsed, self.moves_count, score, self.difficulty_grid_size)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-center puzzle manager board dimensions
        standard_size = 600
        board_x = (self.width() - standard_size) / 2
        board_y = (self.board_widget.height() - standard_size) / 2
        # Adjust vertical alignment inside board_widget
        self.manager.board_rect = QRectF(board_x, max(10, board_y), standard_size, standard_size)
        self.board_widget.update()

    def paintEvent(self, event):
        # Custom background gradient based on theme
        painter = QPainter(self)
        theme = ThemeManager.theme()
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, theme['bg_gradient_start'])
        gradient.setColorAt(1, theme['bg_gradient_end'])
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # HUD Panel Text styling
        font_family = theme['font_family']
        self.hud_timer.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 16px; font-weight: bold;")
        self.hud_moves.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 16px; font-weight: bold;")
        self.hud_difficulty.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 16px; font-weight: bold;")
        self.progress_label.setStyleSheet(f"color: #FFFFFF; font-family: {font_family}; font-size: 14px; font-weight: bold;")
