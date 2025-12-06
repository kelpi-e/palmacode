"""
Модуль трекинга взгляда с калибровкой
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
from threading import Thread, Event
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QPoint
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QBrush, QPen
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget, QApplication


@dataclass
class GazeData:
    """Данные о направлении взгляда"""
    gaze_x: float  # Сырые координаты (0-1)
    gaze_y: float
    screen_x: float  # Калиброванные координаты экрана (0-1)
    screen_y: float
    horizontal_direction: str
    vertical_direction: str
    left_eye_open: bool
    right_eye_open: bool
    face_x: float
    face_y: float
    confidence: float


@dataclass 
class CalibrationPoint:
    """Точка калибровки"""
    screen_x: float  # Позиция на экране (0-1)
    screen_y: float
    gaze_samples: List[Tuple[float, float]]  # Собранные значения взгляда


class CalibrationWidget(QWidget):
    """Виджет для отображения точки калибровки"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.point_x = 0.5
        self.point_y = 0.5
        self.point_size = 30
        self.pulse_size = 0
        self.is_active = False
        self.progress = 0
        
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._pulse)
        self.pulse_timer.start(50)
    
    def set_point(self, x: float, y: float):
        self.point_x = x
        self.point_y = y
        self.progress = 0
        self.is_active = True
        self.update()
    
    def set_progress(self, progress: float):
        self.progress = progress
        self.update()
    
    def _pulse(self):
        if self.is_active:
            self.pulse_size = (self.pulse_size + 2) % 20
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Фон
        painter.fillRect(self.rect(), QColor("#0d1117"))
        
        # Инструкция
        painter.setPen(QColor("#8b949e"))
        painter.setFont(QFont("Segoe UI", 16))
        painter.drawText(self.rect().adjusted(0, 50, 0, 0), Qt.AlignmentFlag.AlignHCenter, 
                        "Смотрите на точку")
        
        # Прогресс текст
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(self.rect().adjusted(0, 80, 0, 0), Qt.AlignmentFlag.AlignHCenter,
                        f"Прогресс: {int(self.progress * 100)}%")
        
        # Позиция точки
        cx = int(self.point_x * self.width())
        cy = int(self.point_y * self.height())
        
        # Внешний пульсирующий круг
        if self.is_active:
            pulse_color = QColor("#58a6ff")
            pulse_color.setAlpha(100 - self.pulse_size * 5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pulse_color))
            painter.drawEllipse(cx - self.point_size - self.pulse_size, 
                               cy - self.point_size - self.pulse_size,
                               (self.point_size + self.pulse_size) * 2,
                               (self.point_size + self.pulse_size) * 2)
        
        # Прогресс-кольцо
        if self.progress > 0:
            painter.setPen(QPen(QColor("#3fb950"), 4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int(self.progress * 360 * 16)
            painter.drawArc(cx - self.point_size - 5, cy - self.point_size - 5,
                           (self.point_size + 5) * 2, (self.point_size + 5) * 2,
                           90 * 16, -span)
        
        # Основная точка
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#58a6ff")))
        painter.drawEllipse(cx - self.point_size // 2, cy - self.point_size // 2,
                           self.point_size, self.point_size)
        
        # Центр точки
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)


class CalibrationDialog(QDialog):
    """Диалог калибровки взгляда"""
    
    calibration_complete = pyqtSignal(object)  # Отправляет данные калибровки
    
    # Точки калибровки: углы + центр + середины сторон
    CALIBRATION_POINTS = [
        (0.5, 0.5),   # Центр
        (0.1, 0.1),   # Верхний левый
        (0.9, 0.1),   # Верхний правый
        (0.9, 0.9),   # Нижний правый
        (0.1, 0.9),   # Нижний левый
        (0.5, 0.1),   # Верх центр
        (0.5, 0.9),   # Низ центр
        (0.1, 0.5),   # Лево центр
        (0.9, 0.5),   # Право центр
    ]
    
    def __init__(self, eye_tracker, parent=None):
        super().__init__(parent)
        self.eye_tracker = eye_tracker
        self.setWindowTitle("Калибровка взгляда")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        
        self.current_point_idx = 0
        self.samples_per_point = 30
        self.current_samples = []
        self.calibration_data = []
        
        self.setup_ui()
        
        # Таймер для сбора данных
        self.sample_timer = QTimer()
        self.sample_timer.timeout.connect(self._collect_sample)
        
        # Подключаем сигнал взгляда
        self.eye_tracker.gaze_updated.connect(self._on_gaze)
        self._last_gaze = None
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.calib_widget = CalibrationWidget()
        layout.addWidget(self.calib_widget)
        
        # Показываем на весь экран
        self.showFullScreen()
    
    def start_calibration(self):
        """Начать калибровку"""
        self.current_point_idx = 0
        self.calibration_data = []
        self._start_point()
    
    def _start_point(self):
        """Начать сбор для текущей точки"""
        if self.current_point_idx >= len(self.CALIBRATION_POINTS):
            self._finish_calibration()
            return
        
        px, py = self.CALIBRATION_POINTS[self.current_point_idx]
        self.calib_widget.set_point(px, py)
        self.current_samples = []
        
        # Даём время на переместить взгляд
        QTimer.singleShot(1000, self._begin_sampling)
    
    def _begin_sampling(self):
        """Начать сбор сэмплов"""
        self.sample_timer.start(50)  # 20 Hz
    
    def _on_gaze(self, gaze):
        """Получение данных взгляда"""
        self._last_gaze = gaze
    
    def _collect_sample(self):
        """Собрать один сэмпл"""
        if self._last_gaze:
            self.current_samples.append((self._last_gaze.gaze_x, self._last_gaze.gaze_y))
        
        progress = len(self.current_samples) / self.samples_per_point
        self.calib_widget.set_progress(progress)
        
        if len(self.current_samples) >= self.samples_per_point:
            self.sample_timer.stop()
            self._finish_point()
    
    def _finish_point(self):
        """Завершить сбор для точки"""
        px, py = self.CALIBRATION_POINTS[self.current_point_idx]
        
        # Усредняем сэмплы
        if self.current_samples:
            avg_x = np.mean([s[0] for s in self.current_samples])
            avg_y = np.mean([s[1] for s in self.current_samples])
            self.calibration_data.append({
                'screen': (px, py),
                'gaze': (avg_x, avg_y)
            })
        
        self.current_point_idx += 1
        
        # Небольшая пауза перед следующей точкой
        QTimer.singleShot(500, self._start_point)
    
    def _finish_calibration(self):
        """Завершить калибровку"""
        self.sample_timer.stop()
        
        try:
            self.eye_tracker.gaze_updated.disconnect(self._on_gaze)
        except:
            pass
        
        # Вычисляем матрицу трансформации
        calibration = self._compute_calibration()
        self.calibration_complete.emit(calibration)
        self.accept()
    
    def _compute_calibration(self):
        """Вычислить параметры калибровки"""
        if len(self.calibration_data) < 4:
            return None
        
        # Собираем точки
        src_points = np.array([d['gaze'] for d in self.calibration_data], dtype=np.float32)
        dst_points = np.array([d['screen'] for d in self.calibration_data], dtype=np.float32)
        
        # Вычисляем аффинное преобразование (или перспективное если достаточно точек)
        if len(self.calibration_data) >= 4:
            # Используем гомографию для лучшей точности
            matrix, _ = cv2.findHomography(src_points, dst_points, cv2.RANSAC)
            return {'type': 'homography', 'matrix': matrix}
        else:
            # Простое линейное преобразование
            matrix = cv2.getAffineTransform(src_points[:3], dst_points[:3])
            return {'type': 'affine', 'matrix': matrix}
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.sample_timer.stop()
            try:
                self.eye_tracker.gaze_updated.disconnect(self._on_gaze)
            except:
                pass
            self.reject()


class EyeTracker(QObject):
    """Трекер взгляда с поддержкой калибровки"""
    
    gaze_updated = pyqtSignal(object)
    frame_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._stop_event = Event()
        self._thread = None
        self._is_running = False
        self._calibration = None
        
        cv2_data = cv2.data.haarcascades
        self._face_cascade_path = cv2_data + 'haarcascade_frontalface_default.xml'
        self._eye_cascade_path = cv2_data + 'haarcascade_eye.xml'
        
        self._smooth_x = 0.5
        self._smooth_y = 0.5
        self._smooth_factor = 0.3
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    @property
    def is_calibrated(self) -> bool:
        return self._calibration is not None
    
    def set_calibration(self, calibration):
        """Установить данные калибровки"""
        self._calibration = calibration
    
    def clear_calibration(self):
        """Сбросить калибровку"""
        self._calibration = None
    
    def _apply_calibration(self, gaze_x: float, gaze_y: float) -> Tuple[float, float]:
        """Применить калибровку к координатам взгляда"""
        if self._calibration is None:
            return gaze_x, gaze_y
        
        try:
            point = np.array([[[gaze_x, gaze_y]]], dtype=np.float32)
            
            if self._calibration['type'] == 'homography':
                transformed = cv2.perspectiveTransform(point, self._calibration['matrix'])
            else:
                transformed = cv2.transform(point, self._calibration['matrix'])
            
            sx = float(np.clip(transformed[0][0][0], 0, 1))
            sy = float(np.clip(transformed[0][0][1], 0, 1))
            return sx, sy
        except:
            return gaze_x, gaze_y
    
    def start(self, camera_index: int = 0):
        if self._is_running:
            return
        
        self._stop_event.clear()
        self._is_running = True
        self._thread = Thread(target=self._run_loop, args=(camera_index,), daemon=True)
        self._thread.start()
    
    def stop(self):
        if not self._is_running:
            return
        
        self._stop_event.set()
        self._is_running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
    
    def _run_loop(self, camera_index: int):
        capture = None
        face_cascade = None
        eye_cascade = None
        
        try:
            face_cascade = cv2.CascadeClassifier(self._face_cascade_path)
            eye_cascade = cv2.CascadeClassifier(self._eye_cascade_path)
            
            if face_cascade.empty() or eye_cascade.empty():
                self.error_occurred.emit("Не удалось загрузить каскады")
                self._is_running = False
                self.tracking_stopped.emit()
                return
            
            capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not capture.isOpened():
                capture = cv2.VideoCapture(camera_index)
            
            if not capture.isOpened():
                self.error_occurred.emit("Камера недоступна")
                self._is_running = False
                self.tracking_stopped.emit()
                return
            
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            capture.set(cv2.CAP_PROP_FPS, 30)
            
            self.tracking_started.emit()
            
            while not self._stop_event.is_set():
                ret, frame = capture.read()
                if not ret:
                    continue
                
                frame = cv2.flip(frame, 1)
                gaze_data, annotated = self._process(frame, face_cascade, eye_cascade)
                
                if gaze_data and not self._stop_event.is_set():
                    self.gaze_updated.emit(gaze_data)
                
                if not self._stop_event.is_set():
                    rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    bytes_data = rgb.tobytes()
                    img = QImage(bytes_data, w, h, ch * w, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(img.copy())
        
        except Exception as e:
            if not self._stop_event.is_set():
                self.error_occurred.emit(str(e))
        
        finally:
            if capture is not None:
                capture.release()
            self._is_running = False
            self.tracking_stopped.emit()
    
    def _process(self, frame, face_cascade, eye_cascade) -> Tuple[Optional[GazeData], np.ndarray]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]
        
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        
        gaze_data = None
        
        if len(faces) > 0:
            face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = face
            
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2)
            
            roi_gray = gray[fy:fy + int(fh * 0.6), fx:fx + fw]
            roi_color = frame[fy:fy + int(fh * 0.6), fx:fx + fw]
            
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 5, minSize=(20, 20))
            
            left_eye = None
            right_eye = None
            gaze_x, gaze_y = 0.5, 0.5
            
            if len(eyes) >= 2:
                eyes_sorted = sorted(eyes, key=lambda e: e[0])
                right_eye = eyes_sorted[0]
                left_eye = eyes_sorted[1]
            elif len(eyes) == 1:
                e = eyes[0]
                if e[0] < fw // 2:
                    right_eye = e
                else:
                    left_eye = e
            
            for eye in [left_eye, right_eye]:
                if eye is not None:
                    ex, ey, ew, eh = eye
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (255, 0, 255), 2)
                    
                    eye_roi = gray[fy + ey:fy + ey + eh, fx + ex:fx + ex + ew]
                    if eye_roi.size > 0:
                        pupil = self._find_pupil(eye_roi)
                        if pupil:
                            px, py = pupil
                            cv2.circle(roi_color, (ex + px, ey + py), 3, (0, 255, 255), -1)
                            gaze_x = px / ew
                            gaze_y = py / eh
            
            self._smooth_x += (gaze_x - self._smooth_x) * self._smooth_factor
            self._smooth_y += (gaze_y - self._smooth_y) * self._smooth_factor
            
            # Применяем калибровку
            screen_x, screen_y = self._apply_calibration(self._smooth_x, self._smooth_y)
            
            # Направление на основе калиброванных координат
            if screen_x < 0.35:
                h_dir = "left"
            elif screen_x > 0.65:
                h_dir = "right"
            else:
                h_dir = "center"
            
            if screen_y < 0.35:
                v_dir = "up"
            elif screen_y > 0.65:
                v_dir = "down"
            else:
                v_dir = "center"
            
            gaze_data = GazeData(
                gaze_x=self._smooth_x,
                gaze_y=self._smooth_y,
                screen_x=screen_x,
                screen_y=screen_y,
                horizontal_direction=h_dir,
                vertical_direction=v_dir,
                left_eye_open=left_eye is not None,
                right_eye_open=right_eye is not None,
                face_x=(fx + fw / 2) / w,
                face_y=(fy + fh / 2) / h,
                confidence=1.0 if len(eyes) >= 2 else 0.5
            )
            
            self._draw_indicator(frame, gaze_data)
        else:
            cv2.putText(frame, "Face not detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return gaze_data, frame
    
    def _find_pupil(self, eye_roi) -> Optional[Tuple[int, int]]:
        if eye_roi.size == 0:
            return None
        
        blurred = cv2.GaussianBlur(eye_roi, (7, 7), 0)
        min_val, _, min_loc, _ = cv2.minMaxLoc(blurred)
        
        if min_val < 100:
            return min_loc
        
        h, w = eye_roi.shape[:2]
        return (w // 2, h // 2)
    
    def _draw_indicator(self, frame, gaze: GazeData):
        # Индикатор сырых данных
        cv2.rectangle(frame, (10, 10), (110, 70), (40, 40, 40), -1)
        cv2.rectangle(frame, (10, 10), (110, 70), (100, 100, 100), 1)
        
        ix = int(10 + gaze.gaze_x * 100)
        iy = int(10 + gaze.gaze_y * 60)
        cv2.circle(frame, (ix, iy), 4, (100, 100, 255), -1)
        
        # Калиброванная позиция (если есть)
        if self._calibration:
            sx = int(10 + gaze.screen_x * 100)
            sy = int(10 + gaze.screen_y * 60)
            cv2.circle(frame, (sx, sy), 6, (0, 255, 255), -1)
            cv2.putText(frame, "CAL", (115, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        txt = f"{gaze.horizontal_direction}/{gaze.vertical_direction}"
        cv2.putText(frame, txt, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        eyes = f"L:{'O' if gaze.left_eye_open else 'C'} R:{'O' if gaze.right_eye_open else 'C'}"
        cv2.putText(frame, eyes, (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)


# Глобальный экземпляр
eye_tracker = EyeTracker()
