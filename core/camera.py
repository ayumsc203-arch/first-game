import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QImage

HAND_TRACKING_AVAILABLE = False
try:
    import mediapipe as mp
    HAND_TRACKING_AVAILABLE = True
except ImportError:
    pass

class CameraThread(QThread):
    frame_ready = pyqtSignal(QImage, np.ndarray)  # Emits QImage for preview, and raw numpy array for puzzle slicing
    hand_position = pyqtSignal(float, float, bool)  # Emits normalized X, Y, and is_clicking (e.g., pinch gesture)
    
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._running = False
        self._mutex = QMutex()
        self.filter_mode = "Normal"
        self.face_detection_enabled = False
        self.hand_tracking_enabled = False
        
        # Load Face Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Synthetic generator variables
        self.is_synthetic_mode = False
        self.synthetic_t = 0.0
        
        # Initialize MediaPipe Hands if available
        self.mp_hands = None
        self.hands = None
        if HAND_TRACKING_AVAILABLE:
            try:
                self.mp_hands = mp.solutions.hands
                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            except Exception:
                self.hand_tracking_enabled = False

    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
            
    def set_filter(self, mode):
        with QMutexLocker(self._mutex):
            self.filter_mode = mode
            
    def set_face_detection(self, enabled):
        with QMutexLocker(self._mutex):
            self.face_detection_enabled = enabled
            
    def set_hand_tracking(self, enabled):
        with QMutexLocker(self._mutex):
            self.hand_tracking_enabled = enabled and HAND_TRACKING_AVAILABLE

    def run(self):
        # Flag to indicate if real camera is opened
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if cv2.os.name == 'nt' else cv2.CAP_ANY)
        if not cap.isOpened():
            # Fallback to default index if DSHOW failed
            cap.open(self.camera_index)
            
        if not cap.isOpened():
            print("Warning: Physical camera could not be opened. Starting Synthetic Camera Simulation Mode...")
            self.is_synthetic_mode = True
        else:
            self.is_synthetic_mode = False
            # Try to set 60fps and 720p
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 60)

        self._running = True
        while True:
            with QMutexLocker(self._mutex):
                if not self._running:
                    break
                current_filter = self.filter_mode
                detect_faces = self.face_detection_enabled
                track_hands = self.hand_tracking_enabled
            
            if self.is_synthetic_mode:
                # Generate synthetic animated frame
                self.synthetic_t += 0.08
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                
                # Make a gorgeous plasma background using numpy wave equations
                y_coords, x_coords = np.mgrid[0:480, 0:640]
                
                # BGR channels
                # Blue: Sine wave based on width
                b_val = (np.sin(x_coords / 60.0 + self.synthetic_t) * 60 + 90).astype(np.uint8)
                # Green: Cosine wave based on height + diagonal
                g_val = (np.cos((y_coords + x_coords) / 100.0 - self.synthetic_t) * 40 + 50).astype(np.uint8)
                # Red: Cosine wave based on diagonal sweep
                r_val = (np.cos(y_coords / 80.0 + self.synthetic_t * 0.7) * 70 + 110).astype(np.uint8)
                
                frame[:, :, 0] = b_val
                frame[:, :, 1] = g_val
                frame[:, :, 2] = r_val
                
                # Overlay bouncing grid lines (neon look)
                grid_pos = int((self.synthetic_t * 20) % 40)
                frame[grid_pos::40, :, :] = (frame[grid_pos::40, :, :] * 0.6).astype(np.uint8)
                frame[:, grid_pos::40, :] = (frame[:, grid_pos::40, :] * 0.6).astype(np.uint8)
                
                # Generate a moving "head" to simulate face tracking
                face_x = int(320 + 150 * np.sin(self.synthetic_t * 0.4))
                face_y = int(240 + 100 * np.cos(self.synthetic_t * 0.6))
                face_w, face_h = 90, 90
                
                # Bouncing neon bubble
                cv2.circle(frame, (face_x, face_y), 45, (236, 72, 153), -1)  # Neon Pink
                cv2.circle(frame, (face_x, face_y), 35, (6, 182, 212), -1)   # Neon Cyan
                cv2.circle(frame, (face_x, face_y), 15, (255, 255, 255), -1) # Glowing core
                
                # Text labels on preview
                cv2.putText(frame, "Webcam: Simulation Active", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, "Press 'Start Game' to slice this frame into a puzzle", (20, 450), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (226, 232, 240), 1)
                
                # Face detection box simulator
                if detect_faces:
                    # Draw virtual detector bounding box
                    cv2.rectangle(frame, (face_x - face_w, face_y - face_h), 
                                  (face_x + face_w, face_y + face_h), (52, 211, 153), 2)  # Success Green
                    cv2.putText(frame, "FACE TRACKING [MOCK]", (face_x - face_w, face_y - face_h - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (52, 211, 153), 1)
                    
                    # Crop and scale to mock face centering
                    x1 = max(0, face_x - int(face_w * 1.8))
                    y1 = max(0, face_y - int(face_h * 1.8))
                    size = int(max(face_w, face_h) * 3.6)
                    if x1 + size > 640: x1 = 640 - size
                    if y1 + size > 480: y1 = 480 - size
                    
                    if size > 50 and x1 >= 0 and y1 >= 0:
                        cropped = frame[y1:y1+size, x1:x1+size]
                        frame = cv2.resize(cropped, (600, 600))
                        
                # Hand tracking mock simulator
                if track_hands:
                    # Mock hand moves in circle around the head
                    hand_x = face_x + int(120 * np.cos(self.synthetic_t * 1.2))
                    hand_y = face_y + int(120 * np.sin(self.synthetic_t * 1.2))
                    # Convert to normalized
                    norm_hx = hand_x / 640.0
                    norm_hy = hand_y / 480.0
                    is_pinch = (int(self.synthetic_t) % 4 == 0) # Periodic pinch clicks
                    self.hand_position.emit(norm_hx, norm_hy, is_pinch)
                    
                    # Draw fake hand marker in simulation stream
                    color = (52, 211, 153) if is_pinch else (236, 72, 153)
                    cv2.circle(frame, (hand_x, hand_y), 10, color, -1)
                    cv2.putText(frame, "HAND TRACKING [MOCK]", (hand_x + 12, hand_y + 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            else:
                # Real camera frame reading
                ret, frame = cap.read()
                if not ret:
                    QThread.msleep(10)
                    continue
                    
                # Mirroring
                frame = cv2.flip(frame, 1)
                h, w, c = frame.shape
                
                # Face detection crop
                if detect_faces:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces) > 0:
                        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
                        fx, fy, fw, fh = faces[0]
                        cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), (52, 211, 153), 2)
                        
                        cx, cy = fx + fw // 2, fy + fh // 2
                        size = min(w, h, int(max(fw, fh) * 2.2))
                        
                        x1 = max(0, cx - size // 2)
                        y1 = max(0, cy - size // 2)
                        if x1 + size > w: x1 = w - size
                        if y1 + size > h: y1 = h - size
                        
                        if size > 50 and x1 >= 0 and y1 >= 0:
                            cropped = frame[y1:y1+size, x1:x1+size]
                            frame = cv2.resize(cropped, (600, 600))
                
                # Hand tracking (MediaPipe)
                if track_hands and self.hands:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = self.hands.process(rgb_frame)
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            index_tip = hand_landmarks.landmark[8]
                            thumb_tip = hand_landmarks.landmark[4]
                            
                            dist = np.sqrt(
                                (index_tip.x - thumb_tip.x)**2 + 
                                (index_tip.y - thumb_tip.y)**2 + 
                                (index_tip.z - thumb_tip.z)**2
                            )
                            is_clicking = dist < 0.05
                            
                            self.hand_position.emit(index_tip.x, index_tip.y, is_clicking)
                            
                            ix, iy = int(index_tip.x * frame.shape[1]), int(index_tip.y * frame.shape[0])
                            tx, ty = int(thumb_tip.x * frame.shape[1]), int(thumb_tip.y * frame.shape[0])
                            color = (52, 211, 153) if is_clicking else (236, 72, 153)
                            cv2.circle(frame, (ix, iy), 8, color, -1)
                            cv2.circle(frame, (tx, ty), 6, (6, 182, 212), -1)
                            cv2.line(frame, (ix, iy), (tx, ty), color, 2)

            # Apply camera style filter
            processed_frame = self.apply_filter(frame, current_filter)
            
            # Convert to QImage
            rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            qh, qw, qc = rgb_image.shape
            bytes_per_line = qc * qw
            qimg = QImage(rgb_image.data, qw, qh, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.frame_ready.emit(qimg.copy(), processed_frame.copy())
            QThread.msleep(16)
            
        if not self.is_synthetic_mode:
            cap.release()
        if self.hands:
            self.hands.close()

    def apply_filter(self, img, filter_name):
        if filter_name == "Normal":
            return img
        
        elif filter_name == "Black & White":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            
        elif filter_name == "Sepia":
            kernel = np.array([
                [0.272, 0.534, 0.131],
                [0.349, 0.686, 0.168],
                [0.393, 0.769, 0.189]
            ])
            sepia = cv2.transform(img, kernel)
            return np.clip(sepia, 0, 255).astype(np.uint8)
            
        elif filter_name == "Sketch":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            inverted = cv2.bitwise_not(gray)
            blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
            inverted_blurred = cv2.bitwise_not(blurred)
            sketch = cv2.divide(gray, inverted_blurred, scale=256.0)
            return cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
            
        elif filter_name == "Cartoon":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.medianBlur(gray, 5)
            edges = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9
            )
            color = cv2.bilateralFilter(img, 9, 300, 300)
            cartoon = cv2.bitwise_and(color, color, mask=edges)
            return cartoon
            
        elif filter_name == "Pixel Art":
            h, w = img.shape[:2]
            temp = cv2.resize(img, (80, 80), interpolation=cv2.INTER_LINEAR)
            pixel = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)
            return pixel
            
        elif filter_name == "Comic":
            n = 4
            indices = np.arange(0, 256)
            divider = np.linspace(0, 255, n + 1)
            quantiles = np.clip(np.digitize(indices, divider) - 1, 0, n - 1)
            values = np.linspace(0, 255, n).astype(np.uint8)
            lut = values[quantiles]
            posterized = cv2.LUT(img, lut)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edges = cv2.dilate(edges, np.ones((2,2), np.uint8))
            edges_inv = cv2.bitwise_not(edges)
            
            comic = cv2.bitwise_and(posterized, posterized, mask=edges_inv)
            return comic
            
        elif filter_name == "Neon":
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edges_dilated = cv2.dilate(edges, np.ones((3,3), np.uint8))
            
            neon_img = np.zeros_like(img)
            for y in range(img.shape[0]):
                color = [
                    int(127 + 127 * np.sin(y * 0.01 + 0)),
                    int(127 + 127 * np.sin(y * 0.01 + 2)),
                    int(127 + 127 * np.sin(y * 0.01 + 4))
                ]
                neon_img[y, edges_dilated[y] > 0] = color
                
            glow = cv2.GaussianBlur(neon_img, (15, 15), 0)
            combined = cv2.addWeighted(img, 0.3, glow, 0.7, 0)
            return combined
            
        return img
