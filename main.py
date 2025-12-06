import sys
import os
import json
from datetime import datetime
from collections import deque

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QListWidget, QProgressBar,
    QLineEdit, QGroupBox, QFileDialog, QFrame, QSlider, QSplitter,
    QDialog, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QBrush
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

import pyqtgraph as pg

from brain_bit_controller import (
    brain_bit_controller, BrainBitInfo, ConnectionState, ResistValues,
    MindDataReal, MindDataInst, SpectralData
)
from styles import STYLESHEET
from widgets import MetricCard, ResistCard
from eye_tracker import eye_tracker, GazeData, CalibrationDialog


class FullscreenVideoDialog(QDialog):
    """Диалог для полноэкранного воспроизведения видео"""
    def __init__(self, media_player: QMediaPlayer, parent=None, is_recording: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Видео")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.media_player = media_player
        self.original_output = media_player.videoOutput()
        self.is_recording = is_recording
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = QVideoWidget()
        layout.addWidget(self.video_widget)
        
        # Индикатор записи (если идёт запись)
        if is_recording:
            self.record_indicator = QLabel("REC", self)
            self.record_indicator.setStyleSheet("""
                QLabel {
                    background-color: rgba(218, 54, 51, 0.9);
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 8px 16px;
                    border-radius: 8px;
                }
            """)
            self.record_indicator.move(20, 20)
            self.record_indicator.raise_()
            
            # Мигание индикатора
            self.blink_timer = QTimer(self)
            self.blink_timer.timeout.connect(self._blink_indicator)
            self.blink_timer.start(500)
            self.blink_state = True
        
        # Предупреждение об электродах (изначально скрыто)
        self.electrode_warning = QLabel("Проверьте контакт электродов!", self)
        self.electrode_warning.setStyleSheet("""
            QLabel {
                background-color: rgba(218, 54, 51, 0.95);
                color: white;
                font-weight: bold;
                font-size: 18px;
                padding: 12px 24px;
                border-radius: 8px;
            }
        """)
        self.electrode_warning.adjustSize()
        self.electrode_warning.setVisible(False)
        
        # Подсказка
        self.hint_label = QLabel("Esc — выход  |  Пробел — пауза", self)
        self.hint_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.7);
                color: #8b949e;
                font-size: 12px;
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        self.hint_label.adjustSize()
        
        # Переключаем вывод видео на этот виджет
        self.media_player.setVideoOutput(self.video_widget)
        
        # Показываем в полный экран
        self.showFullScreen()
        
        # Позиционируем элементы
        QTimer.singleShot(100, self._position_elements)
    
    def _position_elements(self):
        # Подсказка внизу по центру
        self.hint_label.move(
            (self.width() - self.hint_label.width()) // 2,
            self.height() - self.hint_label.height() - 20
        )
        # Предупреждение об электродах вверху по центру
        self.electrode_warning.move(
            (self.width() - self.electrode_warning.width()) // 2,
            60
        )
    
    def show_electrode_warning(self, show: bool):
        """Показать/скрыть предупреждение об электродах"""
        self.electrode_warning.setVisible(show)
    
    def _blink_indicator(self):
        if hasattr(self, 'record_indicator'):
            self.blink_state = not self.blink_state
            self.record_indicator.setVisible(self.blink_state)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape or event.key() == Qt.Key.Key_F:
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
    
    def closeEvent(self, event):
        if hasattr(self, 'blink_timer'):
            self.blink_timer.stop()
        # Возвращаем вывод на оригинальный виджет
        self.media_player.setVideoOutput(self.original_output)
        event.accept()


class GazeHeatmapWidget(QWidget):
    """Виджет для отображения тепловой карты взгляда"""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.gaze_points = []  # [(x, y, timestamp), ...]
        self.setStyleSheet("background-color: #0d1117; border-radius: 8px;")
    
    def set_data(self, points):
        """Установить данные точек взгляда"""
        self.gaze_points = points
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Фон
        painter.fillRect(self.rect(), QColor("#0d1117"))
        
        # Рамка области взгляда
        margin = 20
        area_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.setPen(QPen(QColor("#30363d"), 2))
        painter.drawRect(area_rect)
        
        # Сетка
        painter.setPen(QPen(QColor("#21262d"), 1))
        for i in range(1, 4):
            x = area_rect.left() + (area_rect.width() * i // 4)
            painter.drawLine(x, area_rect.top(), x, area_rect.bottom())
            y = area_rect.top() + (area_rect.height() * i // 4)
            painter.drawLine(area_rect.left(), y, area_rect.right(), y)
        
        # Метки
        painter.setPen(QColor("#8b949e"))
        painter.drawText(area_rect.left() - 15, area_rect.top() + 5, "↑")
        painter.drawText(area_rect.left() - 15, area_rect.bottom() - 5, "↓")
        painter.drawText(area_rect.left() + 5, area_rect.bottom() + 15, "←")
        painter.drawText(area_rect.right() - 15, area_rect.bottom() + 15, "→")
        
        if not self.gaze_points:
            painter.setPen(QColor("#8b949e"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return
        
        # Рисуем точки взгляда с градиентом по времени
        total = len(self.gaze_points)
        for i, (x, y, _) in enumerate(self.gaze_points):
            # Позиция в пикселях
            px = area_rect.left() + int(x * area_rect.width())
            py = area_rect.top() + int(y * area_rect.height())
            
            # Цвет от синего (старые) к красному (новые)
            progress = i / total
            r = int(88 + progress * (248 - 88))
            g = int(166 - progress * 166)
            b = int(255 - progress * (255 - 81))
            
            color = QColor(r, g, b, 150)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            
            size = 4 + int(progress * 4)
            painter.drawEllipse(px - size//2, py - size//2, size, size)
        
        # Траектория
        if len(self.gaze_points) > 1:
            painter.setPen(QPen(QColor("#58a6ff"), 1, Qt.PenStyle.DotLine))
            for i in range(1, min(len(self.gaze_points), 200)):
                x1, y1, _ = self.gaze_points[i-1]
                x2, y2, _ = self.gaze_points[i]
                px1 = area_rect.left() + int(x1 * area_rect.width())
                py1 = area_rect.top() + int(y1 * area_rect.height())
                px2 = area_rect.left() + int(x2 * area_rect.width())
                py2 = area_rect.top() + int(y2 * area_rect.height())
                painter.drawLine(px1, py1, px2, py2)


class ResultsTab(QWidget):
    """Вкладка для просмотра результатов записи"""
    def __init__(self):
        super().__init__()
        self.data = None
        self.json_data = None
        self.video_path = None
        self.is_playing = False
        self.times = []
        self.attention = []
        self.alpha = []
        self.beta = []
        self.theta = []
        self.gaze_x = []
        self.gaze_y = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Просмотр результатов")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.load_btn = QPushButton("Загрузить JSON")
        self.load_btn.setMinimumHeight(40)
        self.load_btn.clicked.connect(self.load_json)
        header_layout.addWidget(self.load_btn)
        
        self.load_video_btn = QPushButton("Загрузить видео")
        self.load_video_btn.setMinimumHeight(40)
        self.load_video_btn.setProperty("class", "secondary")
        self.load_video_btn.clicked.connect(self.load_video)
        self.load_video_btn.setEnabled(False)
        header_layout.addWidget(self.load_video_btn)
        layout.addLayout(header_layout)
        
        # File info
        self.file_label = QLabel("Файл не загружен")
        self.file_label.setStyleSheet("color: #8b949e; font-size: 14px;")
        layout.addWidget(self.file_label)
        
        # Main content splitter (vertical)
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top: Video + Gaze heatmap
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Video player
        video_container = QFrame()
        video_container.setStyleSheet("QFrame { background-color: #000; border: 2px solid #30363d; border-radius: 12px; }")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(4, 4, 4, 4)
        video_layout.setSpacing(4)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(500, 280)
        video_layout.addWidget(self.video_widget, stretch=1)
        
        # Controls container to prevent video overlap
        controls_widget = QWidget()
        controls_widget.setFixedHeight(40)
        controls_widget.setStyleSheet("background-color: transparent;")
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        self.play_btn = QPushButton(">")
        self.play_btn.setFixedWidth(50)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        self.video_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_slider.setEnabled(False)
        self.video_slider.sliderMoved.connect(self.seek_video)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.video_slider)
        controls_layout.addWidget(self.time_label)
        video_layout.addWidget(controls_widget, stretch=0)
        
        top_layout.addWidget(video_container, stretch=2)
        
        # Gaze heatmap
        heatmap_container = QFrame()
        heatmap_container.setStyleSheet("QFrame { background-color: #161b22; border: 2px solid #30363d; border-radius: 12px; }")
        heatmap_layout = QVBoxLayout(heatmap_container)
        heatmap_layout.setContentsMargins(8, 8, 8, 8)
        
        heatmap_header = QLabel("Карта взгляда")
        heatmap_header.setStyleSheet("font-size: 14px; font-weight: 600; color: #58a6ff;")
        heatmap_layout.addWidget(heatmap_header)
        
        self.gaze_heatmap = GazeHeatmapWidget()
        self.gaze_heatmap.setMinimumSize(250, 200)
        heatmap_layout.addWidget(self.gaze_heatmap)
        
        top_layout.addWidget(heatmap_container, stretch=1)
        
        main_splitter.addWidget(top_widget)
        
        # Middle: Real-time metric cards
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 8, 0, 8)
        
        self.cur_attention = MetricCard("Внимание", "--", "#58a6ff")
        self.cur_alpha = MetricCard("Альфа", "--", "#3fb950")
        self.cur_beta = MetricCard("Бета", "--", "#f0883e")
        self.cur_theta = MetricCard("Тета", "--", "#d29922")
        self.cur_gaze_x = MetricCard("Взгляд X", "--", "#a371f7")
        self.cur_gaze_y = MetricCard("Взгляд Y", "--", "#f778ba")
        
        cards_layout.addWidget(self.cur_attention)
        cards_layout.addWidget(self.cur_alpha)
        cards_layout.addWidget(self.cur_beta)
        cards_layout.addWidget(self.cur_theta)
        cards_layout.addWidget(self.cur_gaze_x)
        cards_layout.addWidget(self.cur_gaze_y)
        
        main_splitter.addWidget(cards_widget)
        
        # Bottom: Graphs
        graphs_widget = QWidget()
        graphs_layout = QVBoxLayout(graphs_widget)
        graphs_layout.setContentsMargins(0, 0, 0, 0)
        
        pg.setConfigOptions(antialias=True)
        
        # Attention graph
        mental_group = QGroupBox("Внимание")
        mental_layout = QVBoxLayout(mental_group)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('#161b22')
        self.mental_plot.setMinimumHeight(100)
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_plot.setLabel('left', 'Значение', units='%')
        self.mental_plot.setLabel('bottom', 'Время', units='с')
        # Vertical line for current position
        self.mental_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.mental_plot.addItem(self.mental_vline)
        mental_layout.addWidget(self.mental_plot)
        graphs_layout.addWidget(mental_group)
        
        # Spectral graph
        spectral_group = QGroupBox("Спектральные данные (Альфа, Бета, Тета)")
        spectral_layout = QVBoxLayout(spectral_group)
        self.spectral_plot = pg.PlotWidget()
        self.spectral_plot.setBackground('#161b22')
        self.spectral_plot.setMinimumHeight(100)
        self.spectral_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectral_plot.setLabel('left', 'Значение', units='%')
        self.spectral_plot.setLabel('bottom', 'Время', units='с')
        self.spectral_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.spectral_plot.addItem(self.spectral_vline)
        spectral_layout.addWidget(self.spectral_plot)
        graphs_layout.addWidget(spectral_group)
        
        # Gaze position graph
        gaze_group = QGroupBox("Позиция взгляда")
        gaze_layout = QVBoxLayout(gaze_group)
        self.gaze_plot = pg.PlotWidget()
        self.gaze_plot.setBackground('#161b22')
        self.gaze_plot.setMinimumHeight(100)
        self.gaze_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gaze_plot.setLabel('left', 'Позиция (0-1)')
        self.gaze_plot.setLabel('bottom', 'Время', units='с')
        self.gaze_plot.setYRange(0, 1)
        self.gaze_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.gaze_plot.addItem(self.gaze_vline)
        gaze_layout.addWidget(self.gaze_plot)
        graphs_layout.addWidget(gaze_group)
        
        main_splitter.addWidget(graphs_widget)
        main_splitter.setSizes([300, 80, 400])
        
        layout.addWidget(main_splitter)
        
        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        # Update timer for syncing data with video
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_data_with_video)
        self.sync_timer.setInterval(100)
    
    def load_json(self):
        # Открываем папку reports по умолчанию
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        if not os.path.exists(reports_dir):
            reports_dir = ""
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить результаты", reports_dir,
            "JSON файлы (*.json);;Все файлы (*)"
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            
            self.data = self.json_data.get('records', [])
            video_file = self.json_data.get('video_file', '')
            
            info_text = f"Загружено: {os.path.basename(filename)} ({len(self.data)} записей)"
            if video_file:
                info_text += f" | Видео: {video_file}"
            
            self.file_label.setText(info_text)
            self.file_label.setStyleSheet("color: #3fb950; font-size: 14px;")
            
            self.update_graphs()
            self.load_video_btn.setEnabled(True)
            
            # Попробуем автоматически загрузить видео если путь есть
            video_path = self.json_data.get('video_path')
            if video_path and os.path.exists(video_path):
                self.video_path = video_path
                self.media_player.setSource(QUrl.fromLocalFile(video_path))
                self.play_btn.setEnabled(True)
                self.video_slider.setEnabled(True)
            
        except Exception as e:
            self.file_label.setText(f"Ошибка: {str(e)}")
            self.file_label.setStyleSheet("color: #f85149; font-size: 14px;")
    
    def load_video(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить видео", "",
            "Видео (*.mp4 *.avi *.mkv *.mov);;Все файлы (*)"
        )
        if not filename:
            return
        
        self.video_path = filename
        self.media_player.setSource(QUrl.fromLocalFile(filename))
        self.play_btn.setEnabled(True)
        self.video_slider.setEnabled(True)
    
    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.sync_timer.stop()
        else:
            self.media_player.play()
            self.sync_timer.start()
    
    def seek_video(self, pos):
        self.media_player.setPosition(pos)
        self.sync_data_with_video()
    
    def on_position_changed(self, pos):
        self.video_slider.setValue(pos)
        duration = self.media_player.duration()
        self.time_label.setText(f"{self._format_time(pos)} / {self._format_time(duration)}")
    
    def on_duration_changed(self, duration):
        self.video_slider.setRange(0, duration)
    
    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("||")
            self.sync_timer.start()
        else:
            self.play_btn.setText(">")
            self.sync_timer.stop()
    
    def _format_time(self, ms):
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
    
    def sync_data_with_video(self):
        """Синхронизировать отображение данных с текущей позицией видео"""
        if not self.data or not self.times:
            return
        
        video_pos_ms = self.media_player.position()
        
        # Найти ближайшую запись по video_ms
        closest_idx = 0
        min_diff = float('inf')
        for i, record in enumerate(self.data):
            diff = abs(record.get('video_ms', 0) - video_pos_ms)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        if closest_idx < len(self.data):
            record = self.data[closest_idx]
            elapsed = record.get('elapsed_sec', 0)
            
            # Update metric cards
            attention_val = record.get('attention', 0)
            self.cur_attention.set_value(f"{attention_val:.0f}%" if attention_val else "--")
            self.cur_alpha.set_value(f"{record.get('alpha', 0)}%")
            self.cur_beta.set_value(f"{record.get('beta', 0)}%")
            self.cur_theta.set_value(f"{record.get('theta', 0)}%")
            
            gaze_x = record.get('gaze_x', 0)
            gaze_y = record.get('gaze_y', 0)
            self.cur_gaze_x.set_value(f"{gaze_x:.2f}" if gaze_x else "--")
            self.cur_gaze_y.set_value(f"{gaze_y:.2f}" if gaze_y else "--")
            
            # Update vertical lines on graphs
            self.mental_vline.setPos(elapsed)
            self.spectral_vline.setPos(elapsed)
            self.gaze_vline.setPos(elapsed)
    
    def update_graphs(self):
        if not self.data:
            return
        
        # Extract data and store in instance variables for sync
        self.times = []
        self.attention = []
        self.alpha = []
        self.beta = []
        self.theta = []
        self.gaze_x = []
        self.gaze_y = []
        
        for row in self.data:
            try:
                self.times.append(float(row.get('elapsed_sec', 0)))
                self.attention.append(float(row.get('attention', 0)))
                self.alpha.append(float(row.get('alpha', 0)))
                self.beta.append(float(row.get('beta', 0)))
                self.theta.append(float(row.get('theta', 0)))
                gx = row.get('gaze_x', 0)
                gy = row.get('gaze_y', 0)
                self.gaze_x.append(float(gx) if gx else 0)
                self.gaze_y.append(float(gy) if gy else 0)
            except:
                continue
        
        # Mental plot
        self.mental_plot.clear()
        self.mental_plot.addItem(self.mental_vline)
        if self.times:
            self.mental_plot.plot(self.times, self.attention, pen=pg.mkPen('#58a6ff', width=2), name='Внимание')
        
        # Spectral plot
        self.spectral_plot.clear()
        self.spectral_plot.addItem(self.spectral_vline)
        if self.times:
            self.spectral_plot.plot(self.times, self.alpha, pen=pg.mkPen('#3fb950', width=2), name='Альфа')
            self.spectral_plot.plot(self.times, self.beta, pen=pg.mkPen('#f0883e', width=2), name='Бета')
            self.spectral_plot.plot(self.times, self.theta, pen=pg.mkPen('#d29922', width=2), name='Тета')
        
        # Gaze plot
        self.gaze_plot.clear()
        self.gaze_plot.addItem(self.gaze_vline)
        if self.times:
            self.gaze_plot.plot(self.times, self.gaze_x, pen=pg.mkPen('#a371f7', width=2), name='X')
            self.gaze_plot.plot(self.times, self.gaze_y, pen=pg.mkPen('#f778ba', width=2), name='Y')
        
        # Gaze heatmap
        gaze_points = [(self.gaze_x[i], self.gaze_y[i], self.times[i]) for i in range(len(self.times)) if self.gaze_x[i] > 0 or self.gaze_y[i] > 0]
        self.gaze_heatmap.set_data(gaze_points)


class ConnectionTab(QWidget):
    """Вкладка подключения устройства"""
    def __init__(self):
        super().__init__()
        self._founded_sensors = []
        self._current_address = None
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QLabel("Подключение BrainBit")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)
        
        subtitle = QLabel("Найдите и подключите ваше устройство BrainBit")
        subtitle.setStyleSheet("color: #8b949e; font-size: 14px;")
        layout.addWidget(subtitle)
        
        search_layout = QHBoxLayout()
        self.search_btn = QPushButton("Начать поиск")
        self.search_btn.setMinimumHeight(44)
        search_layout.addWidget(self.search_btn)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        devices_group = QGroupBox("Найденные устройства")
        devices_layout = QVBoxLayout(devices_group)
        self.devices_list = QListWidget()
        self.devices_list.setMinimumHeight(120)
        devices_layout.addWidget(self.devices_list)
        layout.addWidget(devices_group)
        
        resist_group = QGroupBox("Проверка контакта электродов")
        resist_layout = QVBoxLayout(resist_group)
        
        buttons_layout = QHBoxLayout()
        self.start_resist_btn = QPushButton("Начать проверку")
        self.start_resist_btn.setEnabled(False)
        self.stop_resist_btn = QPushButton("Остановить")
        self.stop_resist_btn.setProperty("class", "secondary")
        self.stop_resist_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_resist_btn)
        buttons_layout.addWidget(self.stop_resist_btn)
        buttons_layout.addStretch()
        resist_layout.addLayout(buttons_layout)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)
        self.o1_card = ResistCard("O1")
        self.o2_card = ResistCard("O2")
        self.t3_card = ResistCard("T3")
        self.t4_card = ResistCard("T4")
        cards_layout.addWidget(self.o1_card)
        cards_layout.addWidget(self.o2_card)
        cards_layout.addWidget(self.t3_card)
        cards_layout.addWidget(self.t4_card)
        cards_layout.addStretch()
        resist_layout.addLayout(cards_layout)
        layout.addWidget(resist_group)
        
        calib_group = QGroupBox("Калибровка")
        calib_layout = QVBoxLayout(calib_group)
        
        calib_buttons = QHBoxLayout()
        self.start_calc_btn = QPushButton("Начать калибровку")
        self.start_calc_btn.setEnabled(False)
        self.stop_calc_btn = QPushButton("Остановить")
        self.stop_calc_btn.setProperty("class", "secondary")
        self.stop_calc_btn.setEnabled(False)
        calib_buttons.addWidget(self.start_calc_btn)
        calib_buttons.addWidget(self.stop_calc_btn)
        calib_buttons.addStretch()
        calib_layout.addLayout(calib_buttons)
        
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("Прогресс:"))
        self.calib_progress = QProgressBar()
        self.calib_progress.setValue(0)
        progress_layout.addWidget(self.calib_progress)
        calib_layout.addLayout(progress_layout)
        
        artifact_layout = QHBoxLayout()
        artifact_layout.addWidget(QLabel("Артефакты:"))
        self.artifact_label = QLabel("—")
        artifact_layout.addWidget(self.artifact_label)
        artifact_layout.addStretch()
        calib_layout.addLayout(artifact_layout)
        layout.addWidget(calib_group)
        layout.addStretch()
    
    def connect_signals(self):
        self.search_btn.clicked.connect(self.start_search)
        self.devices_list.itemClicked.connect(self.connect_to_device)
        self.start_resist_btn.clicked.connect(self.start_resist)
        self.stop_resist_btn.clicked.connect(self.stop_resist)
        self.start_calc_btn.clicked.connect(self.start_calc)
        self.stop_calc_btn.clicked.connect(self.stop_calc)
    
    def start_search(self):
        self.devices_list.clear()
        self.search_btn.setText("Поиск...")
        self.search_btn.setEnabled(False)
        
        def on_founded(sensors):
            self._founded_sensors = sensors
            self.devices_list.addItems([f"{s.Name} ({s.Address})" for s in sensors])
            self.search_btn.setText("Искать снова")
            self.search_btn.setEnabled(True)
            brain_bit_controller.foundedDevices.disconnect(on_founded)
        
        brain_bit_controller.foundedDevices.connect(on_founded)
        brain_bit_controller.search_with_result(5, [])

    def connect_to_device(self, item):
        idx = self.devices_list.row(item)
        info = self._founded_sensors[idx]
        
        def on_connected(address, state):
            item.setText(f"{info.Name} ({info.Address}): {state.name}")
            if address == info.Address and state == ConnectionState.Connected:
                self.start_resist_btn.setEnabled(True)
            elif address == info.Address and state == ConnectionState.Disconnected:
                self.start_resist_btn.setEnabled(False)
                self.start_calc_btn.setEnabled(False)
        
        brain_bit_controller.connectionStateChanged.connect(on_connected)
        brain_bit_controller.connect_to(info=info, need_reconnect=True)

    def start_resist(self):
        if not brain_bit_controller.connected_devices:
            return
        addr = brain_bit_controller.connected_devices[0]
        
        def on_resist(address, values):
            if address == addr:
                self.o1_card.set_status(values.O1.name == "Normal")
                self.o2_card.set_status(values.O2.name == "Normal")
                self.t3_card.set_status(values.T3.name == "Normal")
                self.t4_card.set_status(values.T4.name == "Normal")
        
        brain_bit_controller.resistValuesUpdated.connect(on_resist)
        brain_bit_controller.start_resist(addr)
        self.start_resist_btn.setEnabled(False)
        self.stop_resist_btn.setEnabled(True)

    def stop_resist(self):
        try:
            brain_bit_controller.resistValuesUpdated.disconnect()
        except:
            pass
        if brain_bit_controller.connected_devices:
            brain_bit_controller.stop_resist(brain_bit_controller.connected_devices[0])
        self.start_resist_btn.setEnabled(True)
        self.stop_resist_btn.setEnabled(False)
        self.start_calc_btn.setEnabled(True)

    def start_calc(self):
        if not brain_bit_controller.connected_devices:
            return
        addr = brain_bit_controller.connected_devices[0]
        
        def on_artifact(address, is_art):
            if address == addr:
                self.artifact_label.setText("Есть" if is_art else "Нет")
                self.artifact_label.setStyleSheet(f"color: {'#f85149' if is_art else '#3fb950'}; font-weight: 600;")
        
        def on_progress(address, progress):
            if address == addr:
                self.calib_progress.setValue(progress)
        
        brain_bit_controller.isArtefacted.connect(on_artifact)
        brain_bit_controller.calibrationProcessChanged.connect(on_progress)
        brain_bit_controller.start_calculations(addr)
        self.start_calc_btn.setEnabled(False)
        self.stop_calc_btn.setEnabled(True)

    def stop_calc(self):
        try:
            brain_bit_controller.isArtefacted.disconnect()
            brain_bit_controller.calibrationProcessChanged.disconnect()
        except:
            pass
        if brain_bit_controller.connected_devices:
            brain_bit_controller.stop_calculations(brain_bit_controller.connected_devices[0])
        self.start_calc_btn.setEnabled(True)
        self.stop_calc_btn.setEnabled(False)


class MonitoringTab(QWidget):
    """Вкладка мониторинга в реальном времени"""
    def __init__(self):
        super().__init__()
        self.data_points = 100
        self.attention_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.alpha_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.beta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.theta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.is_monitoring = False
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header_layout = QHBoxLayout()
        header = QLabel("Мониторинг в реальном времени")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.start_monitor_btn = QPushButton("Начать")
        self.start_monitor_btn.setMinimumHeight(40)
        self.stop_monitor_btn = QPushButton("Стоп")
        self.stop_monitor_btn.setProperty("class", "secondary")
        self.stop_monitor_btn.setEnabled(False)
        header_layout.addWidget(self.start_monitor_btn)
        header_layout.addWidget(self.stop_monitor_btn)
        layout.addLayout(header_layout)
        
        # Предупреждение о контакте электродов
        self.electrode_warning = QLabel("")
        self.electrode_warning.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 8px;
                padding: 12px;
                color: #f85149;
                font-weight: 600;
            }
        """)
        self.electrode_warning.setVisible(False)
        layout.addWidget(self.electrode_warning)
        
        # Статус электродов
        electrode_layout = QHBoxLayout()
        electrode_layout.addWidget(QLabel("Электроды:"))
        self.o1_status = QLabel("O1: —")
        self.o2_status = QLabel("O2: —")
        self.t3_status = QLabel("T3: —")
        self.t4_status = QLabel("T4: —")
        for lbl in [self.o1_status, self.o2_status, self.t3_status, self.t4_status]:
            lbl.setStyleSheet("color: #8b949e; font-size: 12px; margin: 0 8px;")
            electrode_layout.addWidget(lbl)
        electrode_layout.addStretch()
        layout.addLayout(electrode_layout)
        
        cards_layout = QHBoxLayout()
        self.attention_card = MetricCard("Внимание", "0%", "#58a6ff")
        self.alpha_card = MetricCard("Альфа", "0%", "#3fb950")
        self.beta_card = MetricCard("Бета", "0%", "#f0883e")
        self.theta_card = MetricCard("Тета", "0%", "#d29922")
        cards_layout.addWidget(self.attention_card)
        cards_layout.addWidget(self.alpha_card)
        cards_layout.addWidget(self.beta_card)
        cards_layout.addWidget(self.theta_card)
        layout.addLayout(cards_layout)
        
        pg.setConfigOptions(antialias=True)
        
        mental_group = QGroupBox("Внимание")
        mental_layout = QVBoxLayout(mental_group)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('#161b22')
        self.mental_plot.setMinimumHeight(160)
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_plot.setYRange(0, 100)
        self.attention_curve = self.mental_plot.plot(pen=pg.mkPen('#58a6ff', width=2))
        mental_layout.addWidget(self.mental_plot)
        layout.addWidget(mental_group)
        
        spectral_group = QGroupBox("Спектральные данные")
        spectral_layout = QVBoxLayout(spectral_group)
        self.spectral_plot = pg.PlotWidget()
        self.spectral_plot.setBackground('#161b22')
        self.spectral_plot.setMinimumHeight(160)
        self.spectral_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectral_plot.setYRange(0, 100)
        self.alpha_curve = self.spectral_plot.plot(pen=pg.mkPen('#3fb950', width=2))
        self.beta_curve = self.spectral_plot.plot(pen=pg.mkPen('#f0883e', width=2))
        self.theta_curve = self.spectral_plot.plot(pen=pg.mkPen('#d29922', width=2))
        spectral_layout.addWidget(self.spectral_plot)
        layout.addWidget(spectral_group)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
    
    def connect_signals(self):
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
    
    def start_monitoring(self):
        if not brain_bit_controller.connected_devices:
            return
        self.is_monitoring = True
        addr = brain_bit_controller.connected_devices[0]
        
        # Используем данные без калибровки для мгновенного отображения
        def on_inst_mind(address, data):
            if address == addr and self.is_monitoring:
                self.attention_data.append(data.attention)
                self.attention_card.set_value(f"{data.attention:.0f}%")
        
        def on_spec(address, data):
            if address == addr and self.is_monitoring:
                self.alpha_data.append(data.alpha)
                self.beta_data.append(data.beta)
                self.theta_data.append(data.theta)
                self.alpha_card.set_value(f"{data.alpha}%")
                self.beta_card.set_value(f"{data.beta}%")
                self.theta_card.set_value(f"{data.theta}%")
        
        def on_artifact(address, is_art):
            if address == addr and self.is_monitoring:
                if is_art:
                    self.electrode_warning.setText("Обнаружены артефакты! Проверьте контакт электродов.")
                    self.electrode_warning.setVisible(True)
                else:
                    self.electrode_warning.setVisible(False)
        
        brain_bit_controller.mindDataWithoutCalibrationUpdated.connect(on_inst_mind)
        brain_bit_controller.spectralDataUpdated.connect(on_spec)
        brain_bit_controller.isArtefacted.connect(on_artifact)
        brain_bit_controller.start_calculations(addr)
        
        self.update_timer.start(100)
        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
    
    def _update_electrode_status(self, values):
        """Обновить статус электродов"""
        bad_electrodes = []
        
        if values.O1.name == "Normal":
            self.o1_status.setText("O1: OK")
            self.o1_status.setStyleSheet("color: #3fb950; font-size: 12px; margin: 0 8px;")
        else:
            self.o1_status.setText("O1: X")
            self.o1_status.setStyleSheet("color: #f85149; font-size: 12px; margin: 0 8px;")
            bad_electrodes.append("O1")
        
        if values.O2.name == "Normal":
            self.o2_status.setText("O2: OK")
            self.o2_status.setStyleSheet("color: #3fb950; font-size: 12px; margin: 0 8px;")
        else:
            self.o2_status.setText("O2: X")
            self.o2_status.setStyleSheet("color: #f85149; font-size: 12px; margin: 0 8px;")
            bad_electrodes.append("O2")
        
        if values.T3.name == "Normal":
            self.t3_status.setText("T3: OK")
            self.t3_status.setStyleSheet("color: #3fb950; font-size: 12px; margin: 0 8px;")
        else:
            self.t3_status.setText("T3: X")
            self.t3_status.setStyleSheet("color: #f85149; font-size: 12px; margin: 0 8px;")
            bad_electrodes.append("T3")
        
        if values.T4.name == "Normal":
            self.t4_status.setText("T4: OK")
            self.t4_status.setStyleSheet("color: #3fb950; font-size: 12px; margin: 0 8px;")
        else:
            self.t4_status.setText("T4: X")
            self.t4_status.setStyleSheet("color: #f85149; font-size: 12px; margin: 0 8px;")
            bad_electrodes.append("T4")
        
        if bad_electrodes:
            self.electrode_warning.setText(f"Плохой контакт электродов: {', '.join(bad_electrodes)}. Поправьте устройство!")
            self.electrode_warning.setVisible(True)
        else:
            self.electrode_warning.setVisible(False)
    
    def stop_monitoring(self):
        self.is_monitoring = False
        self.update_timer.stop()
        self.electrode_warning.setVisible(False)
        try:
            brain_bit_controller.mindDataWithoutCalibrationUpdated.disconnect()
            brain_bit_controller.spectralDataUpdated.disconnect()
            brain_bit_controller.isArtefacted.disconnect()
        except:
            pass
        if brain_bit_controller.connected_devices:
            brain_bit_controller.stop_calculations(brain_bit_controller.connected_devices[0])
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)
    
    def update_plots(self):
        x = list(range(self.data_points))
        self.attention_curve.setData(x, list(self.attention_data))
        self.alpha_curve.setData(x, list(self.alpha_data))
        self.beta_curve.setData(x, list(self.beta_data))
        self.theta_curve.setData(x, list(self.theta_data))


class VideoRecordingTab(QWidget):
    """Вкладка с видео, трекингом взгляда и записью"""
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recording_start_time = None
        self.record_data = []  # Список записей для JSON
        self.record_count_value = 0
        self.current_brain_data = {}
        self.current_gaze_data = None
        self.video_loaded = False
        self.video_file_path = None  # Путь к видеофайлу для сохранения в JSON
        self.camera_active = False
        self.fullscreen_dialog = None
        self.reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)
        
        header = QLabel("Видео + Трекинг взгляда + Запись")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)
        
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Video player
        video_container = QFrame()
        video_container.setStyleSheet("QFrame { background-color: #000; border: 2px solid #30363d; border-radius: 12px; }")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(4, 4, 4, 4)
        
        video_file_layout = QHBoxLayout()
        self.video_path_label = QLabel("Видео не выбрано")
        self.video_path_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.select_video_btn = QPushButton("MP4")
        self.select_video_btn.setProperty("class", "secondary")
        self.select_video_btn.setFixedWidth(80)
        self.fullscreen_btn = QPushButton("[ ]")
        self.fullscreen_btn.setToolTip("Полный экран (F)")
        self.fullscreen_btn.setFixedWidth(40)
        self.fullscreen_btn.setEnabled(False)
        video_file_layout.addWidget(self.video_path_label, stretch=1)
        video_file_layout.addWidget(self.select_video_btn)
        video_file_layout.addWidget(self.fullscreen_btn)
        video_layout.addLayout(video_file_layout)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 225)
        video_layout.addWidget(self.video_widget)
        
        controls_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedWidth(50)
        self.play_btn.setEnabled(False)
        self.video_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_slider.setEnabled(False)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.video_slider)
        controls_layout.addWidget(self.time_label)
        video_layout.addLayout(controls_layout)
        
        content_splitter.addWidget(video_container)
        
        # Camera
        camera_container = QFrame()
        camera_container.setStyleSheet("QFrame { background-color: #161b22; border: 2px solid #30363d; border-radius: 12px; }")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(8, 8, 8, 8)
        
        cam_header = QLabel("Трекинг взгляда")
        cam_header.setStyleSheet("font-size: 14px; font-weight: 600; color: #58a6ff;")
        camera_layout.addWidget(cam_header)
        
        self.camera_label = QLabel("Камера запустится при записи")
        self.camera_label.setMinimumSize(320, 240)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #0d1117; border-radius: 8px; color: #8b949e;")
        camera_layout.addWidget(self.camera_label)
        
        gaze_info = QHBoxLayout()
        self.gaze_direction_label = QLabel("Направление: —")
        self.gaze_direction_label.setStyleSheet("color: #e6edf3; font-size: 12px;")
        self.eyes_status_label = QLabel("Глаза: —")
        self.eyes_status_label.setStyleSheet("color: #e6edf3; font-size: 12px;")
        gaze_info.addWidget(self.gaze_direction_label)
        gaze_info.addWidget(self.eyes_status_label)
        camera_layout.addLayout(gaze_info)
        
        # Статус калибровки
        self.calibration_status = QLabel("Не откалибровано")
        self.calibration_status.setStyleSheet("color: #8b949e; font-size: 11px;")
        camera_layout.addWidget(self.calibration_status)
        
        cam_controls = QHBoxLayout()
        self.start_camera_btn = QPushButton("Тест камеры")
        self.start_camera_btn.setProperty("class", "secondary")
        self.calibrate_btn = QPushButton("Калибровка")
        self.calibrate_btn.setToolTip("Калибровка взгляда по точкам экрана")
        self.calibrate_btn.setEnabled(False)
        self.stop_camera_btn = QPushButton("Стоп")
        self.stop_camera_btn.setProperty("class", "secondary")
        self.stop_camera_btn.setEnabled(False)
        self.stop_camera_btn.setFixedWidth(60)
        cam_controls.addWidget(self.start_camera_btn)
        cam_controls.addWidget(self.calibrate_btn)
        cam_controls.addWidget(self.stop_camera_btn)
        camera_layout.addLayout(cam_controls)
        
        # Статус калибровки
        self.calibration_status = QLabel("Требуется калибровка")
        self.calibration_status.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f85149;
                font-size: 12px;
            }
        """)
        camera_layout.addWidget(self.calibration_status)
        
        content_splitter.addWidget(camera_container)
        content_splitter.setSizes([550, 400])
        layout.addWidget(content_splitter)
        
        # Предупреждение об электродах
        self.electrode_warning = QLabel("")
        self.electrode_warning.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 8px;
                padding: 10px;
                color: #f85149;
                font-weight: 600;
            }
        """)
        self.electrode_warning.setVisible(False)
        layout.addWidget(self.electrode_warning)
        
        # Recording
        record_group = QGroupBox("Запись")
        record_layout = QVBoxLayout(record_group)
        
        output_layout = QHBoxLayout()
        self.output_path_label = QLabel(f"Отчёты сохраняются в: reports/")
        self.output_path_label.setStyleSheet("color: #8b949e;")
        output_layout.addWidget(self.output_path_label, stretch=1)
        record_layout.addLayout(output_layout)
        
        buttons_layout = QHBoxLayout()
        self.start_record_btn = QPushButton("НАЧАТЬ ЗАПИСЬ")
        self.start_record_btn.setStyleSheet("""
            QPushButton { background-color: #da3633; color: white; font-weight: 700; font-size: 16px; }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        self.start_record_btn.setMinimumHeight(50)
        
        self.stop_record_btn = QPushButton("СТОП")
        self.stop_record_btn.setStyleSheet("""
            QPushButton { background-color: #21262d; border: 2px solid #da3633; color: #da3633; font-weight: 700; }
            QPushButton:disabled { border-color: #484f58; color: #484f58; }
        """)
        self.stop_record_btn.setMinimumHeight(50)
        self.stop_record_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_record_btn)
        buttons_layout.addWidget(self.stop_record_btn)
        record_layout.addLayout(buttons_layout)
        
        status_layout = QHBoxLayout()
        self.record_status = QLabel("Готов")
        self.record_status.setStyleSheet("font-weight: 600;")
        self.record_count = QLabel("Записей: 0")
        self.record_count.setStyleSheet("color: #8b949e;")
        status_layout.addWidget(self.record_status)
        status_layout.addStretch()
        status_layout.addWidget(self.record_count)
        record_layout.addLayout(status_layout)
        
        values_layout = QHBoxLayout()
        self.rec_attention = MetricCard("Внимание", "—", "#58a6ff")
        self.rec_gaze_x = MetricCard("Взгляд X", "—", "#3fb950")
        self.rec_gaze_y = MetricCard("Взгляд Y", "—", "#f0883e")
        values_layout.addWidget(self.rec_attention)
        values_layout.addWidget(self.rec_gaze_x)
        values_layout.addWidget(self.rec_gaze_y)
        record_layout.addLayout(values_layout)
        
        layout.addWidget(record_group)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self._write_record)
    
    def connect_signals(self):
        self.select_video_btn.clicked.connect(self.select_video)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.play_btn.clicked.connect(self.toggle_play)
        self.video_slider.sliderMoved.connect(self.seek_video)
        self.start_record_btn.clicked.connect(self.start_recording)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.start_camera_btn.clicked.connect(self.start_camera)
        self.calibrate_btn.clicked.connect(self.start_calibration)
        self.stop_camera_btn.clicked.connect(self.stop_camera)
        
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.playbackStateChanged.connect(self.update_play_button)
        
        eye_tracker.frame_ready.connect(self.update_camera_frame)
        eye_tracker.gaze_updated.connect(self.update_gaze_data)
        eye_tracker.tracking_started.connect(self.on_tracking_started)
        eye_tracker.tracking_stopped.connect(self.on_tracking_stopped)
        eye_tracker.error_occurred.connect(self.on_tracking_error)
    
    def select_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать видео", "", "Видео (*.mp4 *.avi *.mkv *.mov)")
        if filename:
            self.video_file_path = filename  # Сохраняем путь для JSON
            self.video_path_label.setText(os.path.basename(filename))
            self.video_path_label.setStyleSheet("color: #3fb950; font-size: 12px;")
            self.media_player.setSource(QUrl.fromLocalFile(filename))
            self.video_loaded = True
            self.play_btn.setEnabled(True)
            self.fullscreen_btn.setEnabled(True)
            self.video_slider.setEnabled(True)
            self._check_ready()
    
    def toggle_fullscreen(self):
        if self.video_loaded:
            self.fullscreen_dialog = FullscreenVideoDialog(self.media_player, self, self.is_recording)
    
    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def seek_video(self, pos):
        self.media_player.setPosition(pos)
    
    def update_position(self, pos):
        self.video_slider.setValue(pos)
        self.time_label.setText(f"{self._format_time(pos)} / {self._format_time(self.media_player.duration())}")
    
    def update_duration(self, dur):
        self.video_slider.setRange(0, dur)
    
    def update_play_button(self, state):
        self.play_btn.setText("⏸" if state == QMediaPlayer.PlaybackState.PlayingState else "▶")
    
    def _format_time(self, ms):
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
    
    def start_camera(self):
        if not eye_tracker.is_running:
            self.camera_label.setText("Запуск...")
            self.start_camera_btn.setEnabled(False)
            eye_tracker.start(0)
    
    def stop_camera(self):
        self.stop_camera_btn.setEnabled(False)
        self.camera_active = False
        eye_tracker.stop()
    
    def on_tracking_started(self):
        self.camera_active = True
        self.start_camera_btn.setEnabled(False)
        self.calibrate_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(True)
        self.camera_label.setText("")
        # Обновляем статус калибровки
        if eye_tracker.is_calibrated:
            self.calibration_status.setText("Калибровка выполнена")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #23863622;
                    border: 1px solid #238636;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #3fb950;
                    font-size: 12px;
                }
            """)
        else:
            self.calibration_status.setText("Требуется калибровка")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #da363322;
                    border: 1px solid #da3633;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #f85149;
                    font-size: 12px;
                }
            """)
    
    def on_tracking_stopped(self):
        self.camera_active = False
        self.start_camera_btn.setEnabled(True)
        self.calibrate_btn.setEnabled(False)
        self.stop_camera_btn.setEnabled(False)
        self.camera_label.clear()
        self.camera_label.setText("Камера выключена")
        self.gaze_direction_label.setText("Направление: —")
        self.eyes_status_label.setText("Глаза: —")
    
    def start_calibration(self):
        """Запуск калибровки взгляда"""
        if not eye_tracker.is_running:
            return
        
        # Создаём диалог калибровки
        self.calibration_dialog = CalibrationDialog(eye_tracker, self)
        self.calibration_dialog.calibration_complete.connect(self.on_calibration_complete)
        self.calibration_dialog.start_calibration()
    
    def on_calibration_complete(self, calibration_data):
        """Обработка завершения калибровки"""
        if calibration_data:
            eye_tracker.set_calibration(calibration_data)
            self.calibration_status.setText("Калибровка выполнена")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #23863622;
                    border: 1px solid #238636;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #3fb950;
                    font-size: 12px;
                }
            """)
        else:
            self.calibration_status.setText("Ошибка калибровки")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #da363322;
                    border: 1px solid #da3633;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #f85149;
                    font-size: 12px;
                }
            """)
    
    def on_tracking_error(self, error):
        self.camera_active = False
        self.camera_label.setText(f"Ошибка: {error}")
        self.start_camera_btn.setEnabled(True)
        self.stop_camera_btn.setEnabled(False)
    
    def update_camera_frame(self, image):
        if not self.camera_active:
            return
        try:
            if image and not image.isNull():
                scaled = image.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.camera_label.setPixmap(QPixmap.fromImage(scaled))
        except Exception:
            pass
    
    def update_gaze_data(self, gaze):
        if not self.camera_active:
            return
        try:
            self.current_gaze_data = gaze
            self.gaze_direction_label.setText(f"Направление: {gaze.horizontal_direction}/{gaze.vertical_direction}")
            self.eyes_status_label.setText(f"Глаза: L:{'O' if gaze.left_eye_open else 'C'} R:{'O' if gaze.right_eye_open else 'C'}")
            if self.is_recording:
                # Используем калиброванные координаты экрана
                self.rec_gaze_x.set_value(f"{gaze.screen_x:.2f}")
                self.rec_gaze_y.set_value(f"{gaze.screen_y:.2f}")
        except Exception:
            pass
    
    def _check_ready(self):
        # Кнопка записи всегда доступна (файл сохраняется автоматически)
        self.start_record_btn.setEnabled(True)
    
    def start_recording(self):
        # Проверяем калибровку трекинга взгляда
        if not eye_tracker.is_calibrated:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Требуется калибровка")
            msg.setText("Трекинг взгляда не откалиброван!")
            msg.setInformativeText("Сначала включите камеру и выполните калибровку (кнопка Калибровка).")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet("""
                QMessageBox { background-color: #161b22; }
                QLabel { color: #e6edf3; }
                QPushButton { background-color: #238636; color: white; padding: 8px 16px; border-radius: 6px; }
            """)
            msg.exec()
            return
        
        # Создаём папку reports если её нет
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        # Запускаем камеру если не запущена
        if not eye_tracker.is_running:
            eye_tracker.start(0)
        
        # Запускаем видео с начала
        if self.video_loaded:
            self.media_player.setPosition(0)
            self.media_player.play()
            # Открываем полноэкранный режим с индикатором записи
            self.fullscreen_dialog = FullscreenVideoDialog(self.media_player, self, is_recording=True)
        
        self.is_recording = True
        self.recording_start_time = datetime.now()
        self.record_count_value = 0
        self.record_data = []  # Очищаем данные для новой записи
        
        self.current_brain_data = {'attention': 0, 'alpha': 0, 'beta': 0, 'theta': 0}
        
        if brain_bit_controller.connected_devices:
            addr = brain_bit_controller.connected_devices[0]
            
            # Используем данные без калибровки для мгновенного отображения
            def on_inst_mind(address, data):
                if address == addr and self.is_recording:
                    self.current_brain_data['attention'] = data.attention
                    self.rec_attention.set_value(f"{data.attention:.0f}%")
            
            def on_spec(address, data):
                if address == addr and self.is_recording:
                    self.current_brain_data['alpha'] = data.alpha
                    self.current_brain_data['beta'] = data.beta
                    self.current_brain_data['theta'] = data.theta
            
            def on_artifact(address, is_art):
                if address == addr and self.is_recording:
                    # Показываем предупреждение в полноэкранном режиме
                    if self.fullscreen_dialog and self.fullscreen_dialog.isVisible():
                        self.fullscreen_dialog.show_electrode_warning(is_art)
                    else:
                        # Показываем в основном окне
                        if is_art:
                            self.electrode_warning.setText("Артефакты! Проверьте контакт электродов.")
                            self.electrode_warning.setVisible(True)
                        else:
                            self.electrode_warning.setVisible(False)
            
            brain_bit_controller.mindDataWithoutCalibrationUpdated.connect(on_inst_mind)
            brain_bit_controller.spectralDataUpdated.connect(on_spec)
            brain_bit_controller.isArtefacted.connect(on_artifact)
            brain_bit_controller.start_calculations(addr)
        
        self.record_timer.start(100)
        self.record_status.setText("ЗАПИСЬ")
        self.record_status.setStyleSheet("color: #f85149; font-weight: 600;")
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
    
    def _write_record(self):
        if not self.is_recording:
            return
        now = datetime.now()
        elapsed = (now - self.recording_start_time).total_seconds()
        video_pos = self.media_player.position() if self.video_loaded else 0
        gaze = self.current_gaze_data
        
        record = {
            'timestamp': now.isoformat(),
            'elapsed_sec': round(elapsed, 2),
            'video_ms': video_pos,
            'attention': self.current_brain_data.get('attention', 0),
            'alpha': self.current_brain_data.get('alpha', 0),
            'beta': self.current_brain_data.get('beta', 0),
            'theta': self.current_brain_data.get('theta', 0),
            'gaze_x': round(gaze.screen_x, 3) if gaze else 0,
            'gaze_y': round(gaze.screen_y, 3) if gaze else 0,
            'gaze_h': gaze.horizontal_direction if gaze else '',
            'gaze_v': gaze.vertical_direction if gaze else '',
            'left_eye': gaze.left_eye_open if gaze else False,
            'right_eye': gaze.right_eye_open if gaze else False
        }
        self.record_data.append(record)
        
        self.record_count_value += 1
        self.record_count.setText(f"Записей: {self.record_count_value}")
    
    def stop_recording(self):
        # Сначала останавливаем таймер и флаг
        self.is_recording = False
        self.record_timer.stop()
        
        # Скрываем предупреждение
        self.electrode_warning.setVisible(False)
        
        # Закрываем полноэкранный режим если открыт
        if self.fullscreen_dialog and self.fullscreen_dialog.isVisible():
            self.fullscreen_dialog.close()
            self.fullscreen_dialog = None
        
        # Останавливаем видео
        self.media_player.pause()
        
        # Сбрасываем флаг камеры перед остановкой
        self.camera_active = False
        
        # Останавливаем трекинг
        eye_tracker.stop()
        
        # Отключаем сигналы BrainBit
        try:
            brain_bit_controller.mindDataWithoutCalibrationUpdated.disconnect()
            brain_bit_controller.spectralDataUpdated.disconnect()
            brain_bit_controller.isArtefacted.disconnect()
        except:
            pass
        
        if brain_bit_controller.connected_devices:
            try:
                brain_bit_controller.stop_calculations(brain_bit_controller.connected_devices[0])
            except:
                pass

        # Сохраняем данные в JSON файл
        if self.record_data:
            filename = f"report_{self.recording_start_time.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            report = {
                'created_at': self.recording_start_time.isoformat(),
                'ended_at': datetime.now().isoformat(),
                'video_file': os.path.basename(self.video_file_path) if self.video_file_path else None,
                'video_path': self.video_file_path,
                'total_records': len(self.record_data),
                'records': self.record_data
            }
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                self.output_path_label.setText(f"Сохранено: {filename}")
                self.output_path_label.setStyleSheet("color: #3fb950;")
            except Exception as e:
                self.output_path_label.setText(f"Ошибка сохранения: {e}")
                self.output_path_label.setStyleSheet("color: #f85149;")
        
        self.record_status.setText("Готово")
        self.record_status.setStyleSheet("color: #3fb950; font-weight: 600;")
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrainBit Monitor")
        self.setMinimumSize(1100, 850)
        self.setup_ui()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.connection_tab = ConnectionTab()
        self.monitoring_tab = MonitoringTab()
        self.video_tab = VideoRecordingTab()
        self.results_tab = ResultsTab()
        
        self.tabs.addTab(self.connection_tab, "Подключение")
        self.tabs.addTab(self.monitoring_tab, "Мониторинг")
        self.tabs.addTab(self.video_tab, "Видео + Взгляд")
        self.tabs.addTab(self.results_tab, "Результаты")
        
        layout.addWidget(self.tabs)
    
    def closeEvent(self, event):
        if self.monitoring_tab.is_monitoring:
            self.monitoring_tab.stop_monitoring()
        if self.video_tab.is_recording:
            self.video_tab.stop_recording()
        eye_tracker.stop()
        brain_bit_controller.stop_all()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
