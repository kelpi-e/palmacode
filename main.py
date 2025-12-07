import sys
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from collections import deque
import threading
try:
    import websocket
except ImportError:
    websocket = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QLineEdit, QGroupBox, QFileDialog, QFrame, QSlider, QSplitter,
    QDialog, QScrollArea, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QPen, QBrush, QLinearGradient
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

# API конфигурация
API_BASE_URL = "http://10.128.7.187:8099"

# Папка для хранения скачанных видео
VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
VIDEOS_METADATA_FILE = os.path.join(VIDEOS_DIR, "video_metadata.json")

def ensure_videos_dir():
    """Создать папку для видео, если её нет"""
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)
    return VIDEOS_DIR

def load_video_metadata():
    """Загрузить метаданные видео (путь -> video_id)"""
    if not os.path.exists(VIDEOS_METADATA_FILE):
        return {}
    try:
        with open(VIDEOS_METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_video_metadata(metadata):
    """Сохранить метаданные видео"""
    ensure_videos_dir()
    try:
        with open(VIDEOS_METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения метаданных: {e}")

def get_video_id(video_path):
    """Получить ID видео по пути. Если файл не из папки videos, вернуть 12345"""
    if not video_path:
        return "12345"
    
    # Нормализуем путь
    video_path = os.path.normpath(os.path.abspath(video_path))
    videos_dir = os.path.normpath(os.path.abspath(VIDEOS_DIR))
    
    # Проверяем, находится ли файл в папке videos (case-insensitive для Windows)
    try:
        if not os.path.commonpath([video_path, videos_dir]) == videos_dir:
            return "12345"
    except ValueError:
        # Пути на разных дисках
        return "12345"
    
    # Загружаем метаданные
    metadata = load_video_metadata()
    
    # Ищем ID по пути (нормализуем все пути для сравнения)
    video_path_normalized = os.path.normpath(os.path.abspath(video_path)).lower()
    for path, video_id in metadata.items():
        path_normalized = os.path.normpath(os.path.abspath(path)).lower()
        if path_normalized == video_path_normalized:
            return str(video_id)
    
    # Если не найдено, возвращаем 12345
    return "12345"

def save_video_with_id(video_path, video_id):
    """Сохранить соответствие пути видео и его ID"""
    metadata = load_video_metadata()
    # Нормализуем путь для сохранения
    video_path_normalized = os.path.normpath(os.path.abspath(video_path))
    metadata[video_path_normalized] = int(video_id) if isinstance(video_id, str) else video_id
    save_video_metadata(metadata)


class AuthManager:
    """Менеджер аутентификации"""
    def __init__(self):
        self.access_token = None
        self.user_email = None
        self.user_role = None
        self.admin_id = None
    
    def is_authenticated(self):
        return self.access_token is not None
    
    def set_token(self, token, email=None, role=None):
        self.access_token = token
        self.user_email = email
        self.user_role = role
    
    def clear(self):
        self.access_token = None
        self.user_email = None
        self.user_role = None
        self.admin_id = None
    
    def get_headers(self):
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}


# Глобальный менеджер авторизации
auth_manager = AuthManager()


class AuthTab(QWidget):
    """Вкладка авторизации и регистрации"""
    auth_changed = pyqtSignal(bool)  # Сигнал об изменении статуса авторизации
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Заголовок
        header = QLabel("Авторизация")
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #ffffff;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Статус авторизации
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setSpacing(12)
        
        self.status_label = QLabel("Вы не авторизованы")
        self.status_label.setStyleSheet("font-size: 16px; color: #8b949e;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setStyleSheet("font-size: 14px; color: #58a6ff;")
        self.user_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_info_label.setWordWrap(True)
        self.user_info_label.setVisible(False)
        status_layout.addWidget(self.user_info_label)
        
        self.logout_btn = QPushButton("Выйти")
        self.logout_btn.setFixedWidth(150)
        self.logout_btn.setVisible(False)
        self.logout_btn.clicked.connect(self.logout)
        logout_container = QWidget()
        logout_layout = QHBoxLayout(logout_container)
        logout_layout.setContentsMargins(0, 0, 0, 0)
        logout_layout.addStretch()
        logout_layout.addWidget(self.logout_btn)
        logout_layout.addStretch()
        status_layout.addWidget(logout_container)
        
        # Информация о привязке к админу
        self.admin_info_label = QLabel("")
        self.admin_info_label.setStyleSheet("font-size: 13px; color: #8b949e;")
        self.admin_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.admin_info_label.setWordWrap(True)
        self.admin_info_label.setVisible(False)
        status_layout.addWidget(self.admin_info_label)
        
        layout.addWidget(self.status_frame)
        
        # === Секция присоединения к админу ===
        self.admin_join_frame = QFrame()
        self.admin_join_frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        self.admin_join_frame.setVisible(False)
        admin_join_layout = QVBoxLayout(self.admin_join_frame)
        admin_join_layout.setSpacing(12)
        
        admin_join_header = QLabel("Присоединиться к администратору")
        admin_join_header.setStyleSheet("font-size: 16px; font-weight: 600; color: #d29922;")
        admin_join_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        admin_join_header.setWordWrap(True)
        admin_join_layout.addWidget(admin_join_header)
        
        admin_join_desc = QLabel("Введите код администратора для привязки вашего аккаунта")
        admin_join_desc.setStyleSheet("font-size: 12px; color: #8b949e;")
        admin_join_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        admin_join_desc.setWordWrap(True)
        admin_join_layout.addWidget(admin_join_desc)
        
        # Поле ввода кода админа
        admin_input_container = QWidget()
        admin_input_layout = QHBoxLayout(admin_input_container)
        admin_input_layout.setContentsMargins(0, 8, 0, 0)
        admin_input_layout.setSpacing(12)
        
        admin_input_layout.addStretch()
        
        admin_code_label = QLabel("Пригласительный код:")
        admin_code_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        admin_input_layout.addWidget(admin_code_label)
        
        self.admin_code_input = QLineEdit()
        self.admin_code_input.setPlaceholderText("Введите код")
        self.admin_code_input.setFixedWidth(320)
        self.admin_code_input.setFixedHeight(36)
        self.admin_code_input.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #d29922;
            }
        """)
        admin_input_layout.addWidget(self.admin_code_input)
        
        self.join_admin_btn = QPushButton("Присоединиться")
        self.join_admin_btn.setFixedHeight(36)
        self.join_admin_btn.setFixedWidth(140)
        self.join_admin_btn.setStyleSheet("""
            QPushButton {
                background-color: #d29922;
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e3b341;
            }
            QPushButton:pressed {
                background-color: #d29922;
            }
            QPushButton:disabled {
                background-color: #21262d;
                color: #8b949e;
            }
        """)
        self.join_admin_btn.clicked.connect(self.join_admin)
        admin_input_layout.addWidget(self.join_admin_btn)
        
        admin_input_layout.addStretch()
        admin_join_layout.addWidget(admin_input_container)
        
        # Сообщения об ошибке/успехе
        self.admin_join_error = QLabel("")
        self.admin_join_error.setStyleSheet("color: #f85149; font-size: 12px;")
        self.admin_join_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.admin_join_error.setWordWrap(True)
        self.admin_join_error.setVisible(False)
        admin_join_layout.addWidget(self.admin_join_error)
        
        self.admin_join_success = QLabel("")
        self.admin_join_success.setStyleSheet("color: #3fb950; font-size: 12px;")
        self.admin_join_success.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.admin_join_success.setWordWrap(True)
        self.admin_join_success.setVisible(False)
        admin_join_layout.addWidget(self.admin_join_success)
        
        layout.addWidget(self.admin_join_frame)
        
        # Контейнер для форм
        forms_container = QWidget()
        forms_layout = QHBoxLayout(forms_container)
        forms_layout.setSpacing(30)
        forms_layout.setContentsMargins(0, 0, 0, 0)
        
        # === Форма входа ===
        login_group = QGroupBox("Вход")
        login_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: 600;
                color: #58a6ff;
                border: 1px solid #30363d;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        login_layout = QVBoxLayout(login_group)
        login_layout.setSpacing(16)
        login_layout.setContentsMargins(24, 32, 24, 24)
        
        # Email для входа
        login_email_label = QLabel("Email")
        login_email_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        login_layout.addWidget(login_email_label)
        
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("user@example.com")
        self.login_email.setFixedHeight(40)
        self.login_email.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
            }
        """)
        login_layout.addWidget(self.login_email)
        
        # Пароль для входа
        login_pass_label = QLabel("Пароль")
        login_pass_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        login_layout.addWidget(login_pass_label)
        
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("Введите пароль")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setFixedHeight(40)
        self.login_password.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #58a6ff;
            }
        """)
        login_layout.addWidget(self.login_password)
        
        # Кнопка входа
        self.login_btn = QPushButton("Войти")
        self.login_btn.setFixedHeight(44)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-size: 16px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QPushButton:pressed {
                background-color: #238636;
            }
            QPushButton:disabled {
                background-color: #21262d;
                color: #8b949e;
            }
        """)
        self.login_btn.clicked.connect(self.login)
        login_layout.addWidget(self.login_btn)
        
        # Сообщение об ошибке входа
        self.login_error = QLabel("")
        self.login_error.setStyleSheet("color: #f85149; font-size: 12px;")
        self.login_error.setWordWrap(True)
        self.login_error.setVisible(False)
        login_layout.addWidget(self.login_error)
        
        login_layout.addStretch()
        forms_layout.addWidget(login_group)
        
        # === Форма регистрации ===
        register_group = QGroupBox("Регистрация")
        register_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: 600;
                color: #a371f7;
                border: 1px solid #30363d;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        register_layout = QVBoxLayout(register_group)
        register_layout.setSpacing(16)
        register_layout.setContentsMargins(24, 32, 24, 24)
        
        # Email для регистрации
        reg_email_label = QLabel("Email")
        reg_email_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        register_layout.addWidget(reg_email_label)
        
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("user@example.com")
        self.reg_email.setFixedHeight(40)
        self.reg_email.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #a371f7;
            }
        """)
        register_layout.addWidget(self.reg_email)
        
        # Пароль для регистрации
        reg_pass_label = QLabel("Пароль")
        reg_pass_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        register_layout.addWidget(reg_pass_label)
        
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("Минимум 6 символов")
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password.setFixedHeight(40)
        self.reg_password.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #a371f7;
            }
        """)
        register_layout.addWidget(self.reg_password)
        
        # Подтверждение пароля
        reg_pass2_label = QLabel("Подтвердите пароль")
        reg_pass2_label.setStyleSheet("color: #e6edf3; font-size: 14px;")
        register_layout.addWidget(reg_pass2_label)
        
        self.reg_password2 = QLineEdit()
        self.reg_password2.setPlaceholderText("Повторите пароль")
        self.reg_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password2.setFixedHeight(40)
        self.reg_password2.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 8px 12px;
                color: #e6edf3;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #a371f7;
            }
        """)
        register_layout.addWidget(self.reg_password2)
        
        # Кнопка регистрации
        self.register_btn = QPushButton("Зарегистрироваться")
        self.register_btn.setFixedHeight(44)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #8957e5;
                color: white;
                font-size: 16px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #a371f7;
            }
            QPushButton:pressed {
                background-color: #8957e5;
            }
            QPushButton:disabled {
                background-color: #21262d;
                color: #8b949e;
            }
        """)
        self.register_btn.clicked.connect(self.register)
        register_layout.addWidget(self.register_btn)
        
        # Сообщение об ошибке регистрации
        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet("color: #f85149; font-size: 12px;")
        self.reg_error.setWordWrap(True)
        self.reg_error.setVisible(False)
        register_layout.addWidget(self.reg_error)
        
        # Сообщение об успехе
        self.reg_success = QLabel("")
        self.reg_success.setStyleSheet("color: #3fb950; font-size: 12px;")
        self.reg_success.setWordWrap(True)
        self.reg_success.setVisible(False)
        register_layout.addWidget(self.reg_success)
        
        register_layout.addStretch()
        forms_layout.addWidget(register_group)
        
        layout.addWidget(forms_container)
        
        # Настройки сервера
        server_group = QGroupBox("Настройки сервера")
        server_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #8b949e;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
        """)
        server_layout = QHBoxLayout(server_group)
        server_layout.setContentsMargins(16, 24, 16, 16)
        
        server_label = QLabel("URL сервера:")
        server_label.setStyleSheet("color: #8b949e;")
        server_layout.addWidget(server_label)
        
        self.server_url = QLineEdit(API_BASE_URL)
        self.server_url.setFixedHeight(36)
        self.server_url.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e6edf3;
                font-size: 13px;
            }
        """)
        server_layout.addWidget(self.server_url, stretch=1)
        
        layout.addWidget(server_group)
        
        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def _make_request(self, endpoint, data):
        """Отправить POST запрос к API"""
        url = f"{self.server_url.text()}{endpoint}"
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8')), None
                
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                if 'detail' in error_body:
                    if isinstance(error_body['detail'], list):
                        msg = "; ".join([d.get('msg', str(d)) for d in error_body['detail']])
                    else:
                        msg = str(error_body['detail'])
                    return None, msg
            except:
                pass
            return None, f"Ошибка {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return None, f"Ошибка подключения: {e.reason}"
        except Exception as e:
            return None, f"Ошибка: {str(e)}"
    
    def login(self):
        """Вход в систему"""
        email = self.login_email.text().strip()
        password = self.login_password.text()
        
        if not email or not password:
            self.login_error.setText("Заполните все поля")
            self.login_error.setVisible(True)
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Вход...")
        self.login_error.setVisible(False)
        
        # Делаем запрос
        data = {"email": email, "password": password}
        result, error = self._make_request("/auth/login", data)
        
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Войти")
        
        if error:
            self.login_error.setText(error)
            self.login_error.setVisible(True)
            return
        
        # Успешный вход
        token = result.get('access_token')
        auth_manager.set_token(token, email)
        
        self._update_auth_status()
        self.auth_changed.emit(True)
        
        # Очищаем форму
        self.login_password.clear()
    
    def register(self):
        """Регистрация нового пользователя"""
        email = self.reg_email.text().strip()
        password = self.reg_password.text()
        password2 = self.reg_password2.text()
        
        if not email or not password or not password2:
            self.reg_error.setText("Заполните все поля")
            self.reg_error.setVisible(True)
            self.reg_success.setVisible(False)
            return
        
        if password != password2:
            self.reg_error.setText("Пароли не совпадают")
            self.reg_error.setVisible(True)
            self.reg_success.setVisible(False)
            return
        
        if len(password) < 6:
            self.reg_error.setText("Пароль должен быть минимум 6 символов")
            self.reg_error.setVisible(True)
            self.reg_success.setVisible(False)
            return
        
        self.register_btn.setEnabled(False)
        self.register_btn.setText("Регистрация...")
        self.reg_error.setVisible(False)
        self.reg_success.setVisible(False)
        
        # Делаем запрос
        data = {"email": email, "password": password, "role": "user"}
        result, error = self._make_request("/auth/register", data)
        
        self.register_btn.setEnabled(True)
        self.register_btn.setText("Зарегистрироваться")
        
        if error:
            self.reg_error.setText(error)
            self.reg_error.setVisible(True)
            return
        
        # Успешная регистрация
        self.reg_success.setText(f"Регистрация успешна! Теперь войдите с email: {email}")
        self.reg_success.setVisible(True)
        
        # Копируем email в форму входа
        self.login_email.setText(email)
        
        # Очищаем форму регистрации
        self.reg_email.clear()
        self.reg_password.clear()
        self.reg_password2.clear()
    
    def logout(self):
        """Выход из системы"""
        auth_manager.clear()
        self._update_auth_status()
        self.auth_changed.emit(False)
    
    def join_admin(self):
        """Присоединиться к администратору"""
        invite_code = self.admin_code_input.text().strip()
        
        if not invite_code:
            self.admin_join_error.setText("Введите пригласительный код")
            self.admin_join_error.setVisible(True)
            self.admin_join_success.setVisible(False)
            return
        
        if not auth_manager.is_authenticated():
            self.admin_join_error.setText("Сначала войдите в систему")
            self.admin_join_error.setVisible(True)
            self.admin_join_success.setVisible(False)
            return
        
        self.join_admin_btn.setEnabled(False)
        self.join_admin_btn.setText("Отправка...")
        self.admin_join_error.setVisible(False)
        self.admin_join_success.setVisible(False)
        
        # Делаем запрос с авторизацией
        result, error = self._make_auth_request("/adminuser/join", {"code": invite_code})
        
        self.join_admin_btn.setEnabled(True)
        self.join_admin_btn.setText("Присоединиться")
        
        if error:
            self.admin_join_error.setText(error)
            self.admin_join_error.setVisible(True)
            return
        
        # Успешное присоединение
        auth_manager.admin_id = result.get('admin_id')
        self.admin_join_success.setText("Успешно присоединились к администратору!")
        self.admin_join_success.setVisible(True)
        self.admin_code_input.clear()
        
        # Обновляем статус
        self._update_auth_status()
    
    def _make_auth_request(self, endpoint, data):
        """Отправить авторизованный POST запрос к API"""
        url = f"{self.server_url.text()}{endpoint}"
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            # Добавляем токен авторизации
            if auth_manager.is_authenticated():
                headers['Authorization'] = f'Bearer {auth_manager.access_token}'
            
            req = urllib.request.Request(
                url,
                data=json_data,
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode('utf-8')), None
                
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                if 'detail' in error_body:
                    if isinstance(error_body['detail'], list):
                        msg = "; ".join([d.get('msg', str(d)) for d in error_body['detail']])
                    else:
                        msg = str(error_body['detail'])
                    return None, msg
            except:
                pass
            return None, f"Ошибка {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            return None, f"Ошибка подключения: {e.reason}"
        except Exception as e:
            return None, f"Ошибка: {str(e)}"
    
    def _update_auth_status(self):
        """Обновить отображение статуса авторизации"""
        if auth_manager.is_authenticated():
            self.status_label.setText("Вы авторизованы")
            self.status_label.setStyleSheet("font-size: 16px; color: #3fb950;")
            self.user_info_label.setText(f"Email: {auth_manager.user_email}")
            self.user_info_label.setVisible(True)
            self.logout_btn.setVisible(True)
            
            # Показываем секцию присоединения к админу
            self.admin_join_frame.setVisible(True)
            
            # Загружаем список админов
            self._load_my_admins()
            
            # Скрываем формы
            self.login_btn.setEnabled(False)
            self.register_btn.setEnabled(False)
        else:
            self.status_label.setText("Вы не авторизованы")
            self.status_label.setStyleSheet("font-size: 16px; color: #8b949e;")
            self.user_info_label.setVisible(False)
            self.logout_btn.setVisible(False)
            self.admin_info_label.setVisible(False)
            self.admin_join_frame.setVisible(False)
            
            # Показываем формы
            self.login_btn.setEnabled(True)
            self.register_btn.setEnabled(True)
    
    def _load_my_admins(self):
        """Загрузить список моих админов"""
        if not auth_manager.is_authenticated():
            self.admin_info_label.setVisible(False)
            return
        
        # GET запрос для получения списка админов
        url = f"{self.server_url.text()}/adminuser/my-admins"
        
        try:
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {auth_manager.access_token}'
            }
            
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                admins = json.loads(response.read().decode('utf-8'))
                
                if admins and isinstance(admins, list) and len(admins) > 0:
                    # Формируем список админов
                    admin_texts = [f"{a.get('email', 'ID:' + str(a.get('id', '?')))}" for a in admins]
                    self.admin_info_label.setText(f"Привязан к: {', '.join(admin_texts)}")
                    self.admin_info_label.setStyleSheet("font-size: 13px; color: #3fb950;")
                    self.admin_info_label.setVisible(True)
                    
                    # Сохраняем в auth_manager
                    auth_manager.admin_id = admins[0].get('id')
                else:
                    self.admin_info_label.setText("Не привязан к админу")
                    self.admin_info_label.setStyleSheet("font-size: 13px; color: #8b949e;")
                    self.admin_info_label.setVisible(True)
                    auth_manager.admin_id = None
                    
        except urllib.error.HTTPError as e:
            self.admin_info_label.setText("Не привязан к админу")
            self.admin_info_label.setStyleSheet("font-size: 13px; color: #8b949e;")
            self.admin_info_label.setVisible(True)
        except Exception as e:
            self.admin_info_label.setText(f"Ошибка проверки: {str(e)[:30]}")
            self.admin_info_label.setStyleSheet("font-size: 13px; color: #f85149;")
            self.admin_info_label.setVisible(True)


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
            
            self.blink_timer = QTimer(self)
            self.blink_timer.timeout.connect(self._blink_indicator)
            self.blink_timer.start(500)
            self.blink_state = True
        
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
        
        self.media_player.setVideoOutput(self.video_widget)
        self.showFullScreen()
        QTimer.singleShot(100, self._position_elements)
    
    def _position_elements(self):
        self.hint_label.move(
            (self.width() - self.hint_label.width()) // 2,
            self.height() - self.hint_label.height() - 20
        )
        self.electrode_warning.move(
            (self.width() - self.electrode_warning.width()) // 2,
            60
        )
    
    def show_electrode_warning(self, show: bool):
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
        self.media_player.setVideoOutput(self.original_output)
        event.accept()


class GazeOverlayWindow(QWidget):
    """Отдельное окно-оверлей для карты взгляда поверх видео"""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.gaze_points = []
        self.current_x = None
        self.current_y = None
    
    def set_data(self, points):
        self.gaze_points = points
        self.update()
    
    def set_current_position(self, x, y):
        self.current_x = x
        self.current_y = y
        self.update()
    
    def clear_current_position(self):
        self.current_x = None
        self.current_y = None
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        area_rect = self.rect().adjusted(10, 10, -10, -10)
        
        # Только текущая позиция взгляда (без истории)
        if self.current_x is not None and self.current_y is not None:
            px = area_rect.left() + int(self.current_x * area_rect.width())
            py = area_rect.top() + int(self.current_y * area_rect.height())
            
            # Свечение
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 0, 60)))
            painter.drawEllipse(px - 20, py - 20, 40, 40)
            
            # Средний круг
            painter.setBrush(QBrush(QColor(255, 200, 0, 150)))
            painter.drawEllipse(px - 12, py - 12, 24, 24)
            
            # Центр
            painter.setBrush(QBrush(QColor("#ffcc00")))
            painter.drawEllipse(px - 6, py - 6, 12, 12)
            
            # Перекрестие
            painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
            painter.drawLine(px - 25, py, px - 9, py)
            painter.drawLine(px + 9, py, px + 25, py)
            painter.drawLine(px, py - 25, px, py - 9)
            painter.drawLine(px, py + 9, px, py + 25)


class ResultsFullscreenDialog(QDialog):
    """Полноэкранный просмотр результатов с картой взгляда"""
    position_changed = pyqtSignal(int)
    
    def __init__(self, media_player: QMediaPlayer, data, times, gaze_x, gaze_y, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты - Полный экран")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.media_player = media_player
        self.original_output = media_player.videoOutput()
        self.data = data
        self.times = times
        self.gaze_x = gaze_x
        self.gaze_y = gaze_y
        
        # Извлекаем данные внимания и расслабленности
        self.attention = []
        self.relaxation = []
        if data and times:
            for i, record in enumerate(data):
                try:
                    if i < len(times):
                        self.attention.append(float(record.get('attention', 0)))
                        self.relaxation.append(float(record.get('relaxation', 0)))
                except:
                    continue
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Видео виджет
        self.video_widget = QVideoWidget()
        main_layout.addWidget(self.video_widget, stretch=1)
        
        # Полупрозрачный график внимания и расслабленности
        graph_container = QWidget()
        graph_container.setFixedHeight(120)
        graph_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.7);")
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(10, 5, 10, 5)
        graph_layout.setSpacing(0)
        
        pg.setConfigOptions(antialias=True)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('transparent')
        self.mental_plot.setLabel('left', 'Значение', units='%')
        self.mental_plot.setLabel('bottom', 'Время', units='сек')
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_plot.setMouseEnabled(x=False, y=False)
        self.mental_plot.hideButtons()
        
        # Настройка стиля осей для полупрозрачности
        self.mental_plot.getAxis('left').setPen(pg.mkPen(color='#ffffff', width=1, alpha=0.7))
        self.mental_plot.getAxis('bottom').setPen(pg.mkPen(color='#ffffff', width=1, alpha=0.7))
        self.mental_plot.getAxis('left').setTextPen(pg.mkPen(color='#ffffff', alpha=0.7))
        self.mental_plot.getAxis('bottom').setTextPen(pg.mkPen(color='#ffffff', alpha=0.7))
        
        # Вертикальная линия для текущей позиции
        self.mental_vline = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#ffffff', width=2, alpha=0.8))
        self.mental_plot.addItem(self.mental_vline)
        
        # Построение графиков
        if self.times and self.attention and self.relaxation:
            self.mental_plot.plot(self.times, self.attention, pen=pg.mkPen('#58a6ff', width=2, alpha=0.9), name='Внимание')
            self.mental_plot.plot(self.times, self.relaxation, pen=pg.mkPen('#a371f7', width=2, alpha=0.9), name='Расслабление')
        
        # Легенда
        legend = self.mental_plot.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(color='#000000', alpha=150))
        legend.setPen(pg.mkPen(color='#ffffff', width=1, alpha=0.5))
        
        graph_layout.addWidget(self.mental_plot)
        main_layout.addWidget(graph_container)
        
        # Панель управления внизу
        controls = QWidget()
        controls.setFixedHeight(60)
        controls.setStyleSheet("background-color: rgba(0, 0, 0, 0.9);")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(20, 10, 20, 10)
        
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedSize(50, 40)
        self.play_btn.clicked.connect(self._toggle_play)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self._seek)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white; font-size: 14px;")
        self.time_label.setFixedWidth(120)
        
        # Кнопка показать/скрыть взгляд
        self.toggle_gaze_btn = QPushButton("Взгляд: ВКЛ")
        self.toggle_gaze_btn.setFixedWidth(110)
        self.toggle_gaze_btn.setCheckable(True)
        self.toggle_gaze_btn.setChecked(True)
        self.toggle_gaze_btn.clicked.connect(self._toggle_gaze)
        
        self.close_btn = QPushButton("✕ Закрыть")
        self.close_btn.setFixedWidth(100)
        self.close_btn.clicked.connect(self.close)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.slider, stretch=1)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.toggle_gaze_btn)
        controls_layout.addWidget(self.close_btn)
        
        main_layout.addWidget(controls)
        
        # Подсказка
        self.hint_label = QLabel("Esc — выход | Пробел — пауза | ← → — перемотка | G — взгляд", self)
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
        
        # Создаём отдельное окно-оверлей для карты взгляда
        self.gaze_overlay = GazeOverlayWindow()
        
        # Загружаем точки взгляда
        gaze_points = [(gaze_x[i], gaze_y[i], times[i]) 
                       for i in range(len(times)) 
                       if gaze_x[i] > 0 or gaze_y[i] > 0]
        self.gaze_overlay.set_data(gaze_points)
        
        # Подключаем сигналы плеера
        self.media_player.positionChanged.connect(self._on_position)
        self.media_player.durationChanged.connect(self._on_duration)
        self.media_player.playbackStateChanged.connect(self._on_state)
        
        # Переключаем вывод
        self.media_player.setVideoOutput(self.video_widget)
        
        # Таймер для обновления позиции взгляда
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_gaze_position)
        self.update_timer.setInterval(50)
        self.update_timer.start()
        
        self.showFullScreen()
        QTimer.singleShot(300, self._position_elements)
    
    def _position_elements(self):
        # Позиционируем оверлей поверх видео
        video_geom = self.video_widget.geometry()
        global_pos = self.video_widget.mapToGlobal(video_geom.topLeft())
        
        self.gaze_overlay.setGeometry(
            global_pos.x(), 
            global_pos.y(), 
            video_geom.width(), 
            video_geom.height() - 180  # Минус график (120px) и панель управления (60px)
        )
        self.gaze_overlay.show()
        
        # Подсказка вверху по центру
        self.hint_label.move(
            (self.width() - self.hint_label.width()) // 2, 20)
        self.hint_label.raise_()
    
    def _toggle_gaze(self):
        """Показать/скрыть карту взгляда"""
        if self.toggle_gaze_btn.isChecked():
            self.gaze_overlay.show()
            self.toggle_gaze_btn.setText("Взгляд: ВКЛ")
        else:
            self.gaze_overlay.hide()
            self.toggle_gaze_btn.setText("Взгляд: ВЫКЛ")
    
    def moveEvent(self, event):
        super().moveEvent(event)
        QTimer.singleShot(50, self._position_elements)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(100, self._position_elements)
    
    def _toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def _seek(self, pos):
        self.media_player.setPosition(pos)
    
    def _on_position(self, pos):
        self.slider.setValue(pos)
        duration = self.media_player.duration()
        self.time_label.setText(f"{self._format_time(pos)} / {self._format_time(duration)}")
        self.position_changed.emit(pos)
        
        # Обновить позицию вертикальной линии на графике
        if self.times and len(self.times) > 0:
            pos_sec = pos / 1000.0  # Конвертируем миллисекунды в секунды
            # Найти ближайшую позицию во времени
            if pos_sec <= self.times[-1]:
                self.mental_vline.setValue(pos_sec)
            else:
                self.mental_vline.setValue(self.times[-1] if self.times else 0)
    
    def _on_duration(self, duration):
        self.slider.setRange(0, duration)
    
    def _on_state(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")
    
    def _format_time(self, ms):
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
    
    def _update_gaze_position(self):
        """Обновить текущую позицию взгляда"""
        if not self.data or not self.times:
            return
        
        video_pos_ms = self.media_player.position()
        
        # Найти ближайшую запись
        closest_idx = 0
        min_diff = float('inf')
        for i, record in enumerate(self.data):
            diff = abs(record.get('video_ms', 0) - video_pos_ms)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        if closest_idx < len(self.data):
            record = self.data[closest_idx]
            gaze_x = record.get('gaze_x', 0)
            gaze_y = record.get('gaze_y', 0)
            
            if gaze_x and gaze_y:
                self.gaze_overlay.set_current_position(gaze_x, gaze_y)
            else:
                self.gaze_overlay.clear_current_position()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Space:
            self._toggle_play()
        elif event.key() == Qt.Key.Key_Left:
            self.media_player.setPosition(max(0, self.media_player.position() - 5000))
        elif event.key() == Qt.Key.Key_Right:
            self.media_player.setPosition(min(self.media_player.duration(), 
                                              self.media_player.position() + 5000))
        elif event.key() == Qt.Key.Key_G:
            self.toggle_gaze_btn.setChecked(not self.toggle_gaze_btn.isChecked())
            self._toggle_gaze()
    
    def closeEvent(self, event):
        self.update_timer.stop()
        self.gaze_overlay.close()
        self.media_player.setVideoOutput(self.original_output)
        event.accept()


class GazeHeatmapWidget(QWidget):
    ASPECT_RATIO = 16 / 10
    
    def __init__(self, overlay_mode=False):
        super().__init__()
        self.overlay_mode = overlay_mode
        self.setMinimumSize(160, 100)
        self.gaze_points = []
        self.current_x = None
        self.current_y = None
        if not overlay_mode:
            self.setStyleSheet("background-color: #0d1117; border-radius: 8px;")
    
    def set_data(self, points):
        self.gaze_points = points
        self.update()
    
    def set_current_position(self, x, y):
        self.current_x = x
        self.current_y = y
        self.update()
    
    def clear_current_position(self):
        self.current_x = None
        self.current_y = None
        self.update()
    
    def _get_screen_rect(self):
        from PyQt6.QtCore import QRect
        margin = 5 if self.overlay_mode else 10
        aw = self.width() - margin * 2
        ah = self.height() - margin * 2
        if self.overlay_mode:
            return QRect(margin, margin, aw, ah)
        if aw / ah > self.ASPECT_RATIO:
            h = ah
            w = int(h * self.ASPECT_RATIO)
        else:
            w = aw
            h = int(w / self.ASPECT_RATIO)
        return QRect((self.width() - w) // 2, (self.height() - h) // 2, w, h)
    
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.overlay_mode:
            p.fillRect(self.rect(), QColor(0, 0, 0, 40))
        else:
            p.fillRect(self.rect(), QColor("#0d1117"))
        rect = self._get_screen_rect()
        if not self.overlay_mode:
            p.setPen(QPen(QColor("#30363d"), 2))
            p.setBrush(QBrush(QColor("#161b22")))
            p.drawRect(rect)
            p.setPen(QPen(QColor("#21262d"), 1))
            for i in range(1, 4):
                x = rect.left() + rect.width() * i // 4
                p.drawLine(x, rect.top(), x, rect.bottom())
                y = rect.top() + rect.height() * i // 4
                p.drawLine(rect.left(), y, rect.right(), y)
        if not self.gaze_points and self.current_x is None:
            if not self.overlay_mode:
                p.setPen(QColor("#8b949e"))
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Нет данных")
            return
        total = len(self.gaze_points)
        for i, (gx, gy, _) in enumerate(self.gaze_points):
            px = rect.left() + int(gx * rect.width())
            py = rect.top() + int(gy * rect.height())
            prog = i / total if total > 0 else 0
            if self.overlay_mode:
                r, g, b = int(100 + prog * 155), int(200 - prog * 150), int(255 - prog * 155)
                alpha = 100 + int(prog * 80)
            else:
                r, g, b = int(88 + prog * 160), int(166 - prog * 166), int(255 - prog * 174)
                alpha = 80
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(r, g, b, alpha)))
            sz = 4 + int(prog * 4) if self.overlay_mode else 3 + int(prog * 3)
            p.drawEllipse(px - sz//2, py - sz//2, sz, sz)
        if self.current_x is not None and self.current_y is not None:
            px = rect.left() + int(self.current_x * rect.width())
            py = rect.top() + int(self.current_y * rect.height())
            if self.overlay_mode:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 0, 80)))
                p.drawEllipse(px - 15, py - 15, 30, 30)
                p.setBrush(QBrush(QColor(255, 200, 0, 150)))
                p.drawEllipse(px - 9, py - 9, 18, 18)
                p.setBrush(QBrush(QColor("#ffcc00")))
                p.drawEllipse(px - 4, py - 4, 8, 8)
                p.setPen(QPen(QColor(255, 255, 255, 200), 2))
                p.drawLine(px - 18, py, px - 6, py)
                p.drawLine(px + 6, py, px + 18, py)
                p.drawLine(px, py - 18, px, py - 6)
                p.drawLine(px, py + 6, px, py + 18)
            else:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(248, 81, 73, 60)))
                p.drawEllipse(px - 10, py - 10, 20, 20)
                p.setBrush(QBrush(QColor(248, 81, 73, 120)))
                p.drawEllipse(px - 6, py - 6, 12, 12)
                p.setBrush(QBrush(QColor("#f85149")))
                p.drawEllipse(px - 3, py - 3, 6, 6)
                p.setPen(QPen(QColor("#f85149"), 1))
                p.drawLine(px - 12, py, px - 4, py)
                p.drawLine(px + 4, py, px + 12, py)
                p.drawLine(px, py - 12, px, py - 4)
                p.drawLine(px, py + 4, px, py + 12)


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
        self.relaxation = []
        self.alpha = []
        self.beta = []
        self.theta = []
        self.gaze_x = []
        self.gaze_y = []
        self.data_indices = []  # Соответствие индексов массивов индексам в self.data
        self.attention_peaks = []  # Список пиков внимания [(time, value, data_index), ...]
        self.peak_markers = []  # Маркеры на графике
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(50)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("Просмотр результатов")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.load_btn = QPushButton("Загрузить JSON")
        self.load_btn.setFixedHeight(36)
        self.load_btn.setMinimumWidth(130)
        self.load_btn.clicked.connect(self.load_json)
        header_layout.addWidget(self.load_btn)
        
        self.load_video_btn = QPushButton("Загрузить видео")
        self.load_video_btn.setFixedHeight(36)
        self.load_video_btn.setMinimumWidth(140)
        self.load_video_btn.setProperty("class", "secondary")
        self.load_video_btn.clicked.connect(self.load_video)
        self.load_video_btn.setEnabled(False)
        header_layout.addWidget(self.load_video_btn)
        main_layout.addWidget(header_widget)
        
        # File info
        self.file_label = QLabel("Файл не загружен")
        self.file_label.setMinimumHeight(20)
        self.file_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.file_label.setWordWrap(True)
        main_layout.addWidget(self.file_label)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 0, 8, 0)
        
        # Top section: Video + Gaze heatmap side by side
        top_widget = QWidget()
        top_widget.setFixedHeight(280)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # Video player
        video_container = QFrame()
        video_container.setStyleSheet("QFrame { background-color: #000; border: 1px solid #30363d; border-radius: 8px; }")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(4, 4, 4, 4)
        video_layout.setSpacing(4)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        video_layout.addWidget(self.video_widget, stretch=1)
        
        # Video controls
        controls_widget = QWidget()
        controls_widget.setFixedHeight(36)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(4, 0, 4, 4)
        controls_layout.setSpacing(8)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 28)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        
        self.video_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_slider.setEnabled(False)
        self.video_slider.sliderMoved.connect(self.seek_video)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(90)
        self.time_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        
        # Кнопка полноэкранного режима
        self.fullscreen_btn = QPushButton("[ ]")
        self.fullscreen_btn.setToolTip("Полный экран с картой взгляда")
        self.fullscreen_btn.setFixedSize(36, 28)
        self.fullscreen_btn.setEnabled(False)
        self.fullscreen_btn.clicked.connect(self._open_fullscreen)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.video_slider, stretch=1)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.fullscreen_btn)
        video_layout.addWidget(controls_widget)
        
        top_layout.addWidget(video_container, stretch=2)
        
        # Gaze heatmap (рядом с видео в режиме превью)
        heatmap_container = QFrame()
        heatmap_container.setFixedWidth(280)
        heatmap_container.setStyleSheet("QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }")
        heatmap_layout = QVBoxLayout(heatmap_container)
        heatmap_layout.setContentsMargins(8, 8, 8, 8)
        heatmap_layout.setSpacing(4)
        
        heatmap_header = QLabel("Карта взгляда")
        heatmap_header.setFixedHeight(20)
        heatmap_header.setStyleSheet("font-size: 13px; font-weight: 600; color: #58a6ff;")
        heatmap_layout.addWidget(heatmap_header)
        
        self.gaze_heatmap = GazeHeatmapWidget(overlay_mode=False)
        heatmap_layout.addWidget(self.gaze_heatmap, stretch=1)
        
        top_layout.addWidget(heatmap_container)
        scroll_layout.addWidget(top_widget)
        
        # Metric cards
        cards_widget = QWidget()
        cards_widget.setFixedHeight(80)
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(6)
        
        self.cur_attention = MetricCard("Внимание", "--", "#58a6ff")
        self.cur_relaxation = MetricCard("Расслаб.", "--", "#a371f7")
        self.cur_alpha = MetricCard("Альфа", "--", "#3fb950")
        self.cur_beta = MetricCard("Бета", "--", "#f0883e")
        self.cur_theta = MetricCard("Тета", "--", "#d29922")
        self.cur_gaze_x = MetricCard("Взгляд X", "--", "#8b949e")
        self.cur_gaze_y = MetricCard("Взгляд Y", "--", "#8b949e")
        
        for card in [self.cur_attention, self.cur_relaxation, self.cur_alpha, self.cur_beta, self.cur_theta, self.cur_gaze_x, self.cur_gaze_y]:
            cards_layout.addWidget(card)
        cards_layout.addStretch()
        scroll_layout.addWidget(cards_widget)
        
        # Graphs
        pg.setConfigOptions(antialias=True)
        
        # Attention + Relaxation graph
        mental_group = QGroupBox("Внимание / Расслабление")
        mental_group.setFixedHeight(150)
        mental_layout = QVBoxLayout(mental_group)
        mental_layout.setContentsMargins(8, 20, 8, 8)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('#161b22')
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.mental_plot.addItem(self.mental_vline)
        mental_layout.addWidget(self.mental_plot)
        scroll_layout.addWidget(mental_group)
        
        # Spectral graph
        spectral_group = QGroupBox("Альфа / Бета / Тета")
        spectral_group.setFixedHeight(150)
        spectral_layout = QVBoxLayout(spectral_group)
        spectral_layout.setContentsMargins(8, 20, 8, 8)
        self.spectral_plot = pg.PlotWidget()
        self.spectral_plot.setBackground('#161b22')
        self.spectral_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectral_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.spectral_plot.addItem(self.spectral_vline)
        spectral_layout.addWidget(self.spectral_plot)
        scroll_layout.addWidget(spectral_group)
        
        # Gaze graph
        gaze_group = QGroupBox("Позиция взгляда")
        gaze_group.setFixedHeight(150)
        gaze_layout = QVBoxLayout(gaze_group)
        gaze_layout.setContentsMargins(8, 20, 8, 8)
        self.gaze_plot = pg.PlotWidget()
        self.gaze_plot.setBackground('#161b22')
        self.gaze_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gaze_plot.setYRange(0, 1)
        self.gaze_vline = pg.InfiniteLine(angle=90, pen=pg.mkPen('#f85149', width=2))
        self.gaze_plot.addItem(self.gaze_vline)
        gaze_layout.addWidget(self.gaze_plot)
        scroll_layout.addWidget(gaze_group)
        
        # Главные моменты (пики внимания)
        highlights_group = QGroupBox("Главные моменты")
        highlights_group.setMinimumHeight(150)
        highlights_layout = QVBoxLayout(highlights_group)
        highlights_layout.setContentsMargins(8, 20, 8, 8)
        
        self.highlights_list = QListWidget()
        self.highlights_list.setStyleSheet("""
            QListWidget {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #21262d;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #21262d;
            }
        """)
        self.highlights_list.itemClicked.connect(self._on_highlight_clicked)
        highlights_layout.addWidget(self.highlights_list)
        scroll_layout.addWidget(highlights_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)
        
        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_data_with_video)
        self.sync_timer.setInterval(100)
        
        # Диалог полноэкранного режима
        self.fullscreen_dialog = None
    
    def _open_fullscreen(self):
        """Открыть видео в полноэкранном режиме с картой взгляда"""
        if not self.video_path:
            return
        self.fullscreen_dialog = ResultsFullscreenDialog(
            self.media_player, 
            self.data,
            self.times,
            self.gaze_x,
            self.gaze_y,
            self
        )
        self.fullscreen_dialog.position_changed.connect(self._on_fullscreen_position)
    
    def _on_fullscreen_position(self, pos_ms):
        """Синхронизация при изменении позиции в полноэкранном режиме"""
        self.sync_data_with_video()
    
    def load_json(self):
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
            self.file_label.setStyleSheet("color: #3fb950; font-size: 12px;")
            
            self.update_graphs()
            self.load_video_btn.setEnabled(True)
            
            video_path = self.json_data.get('video_path')
            if video_path and os.path.exists(video_path):
                self.video_path = video_path
                self.media_player.setSource(QUrl.fromLocalFile(video_path))
                self.play_btn.setEnabled(True)
                self.video_slider.setEnabled(True)
                self.fullscreen_btn.setEnabled(True)
            
        except Exception as e:
            self.file_label.setText(f"Ошибка: {str(e)}")
            self.file_label.setStyleSheet("color: #f85149; font-size: 12px;")
    
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
        self.fullscreen_btn.setEnabled(True)
    
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
            self.play_btn.setText("⏸")
            self.sync_timer.start()
        else:
            self.play_btn.setText("▶")
            self.sync_timer.stop()
            # Обновляем позицию взгляда при паузе
            self.sync_data_with_video()
    
    def _format_time(self, ms):
        s = ms // 1000
        return f"{s // 60:02d}:{s % 60:02d}"
    
    def sync_data_with_video(self):
        if not self.data or not self.times:
            return
        
        video_pos_ms = self.media_player.position()
        
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
            
            attention_val = record.get('attention', 0)
            relaxation_val = record.get('relaxation', 0)
            self.cur_attention.set_value(f"{attention_val:.0f}%" if attention_val else "--")
            self.cur_relaxation.set_value(f"{relaxation_val:.0f}%" if relaxation_val else "--")
            self.cur_alpha.set_value(f"{record.get('alpha', 0)}%")
            self.cur_beta.set_value(f"{record.get('beta', 0)}%")
            self.cur_theta.set_value(f"{record.get('theta', 0)}%")
            
            gaze_x = record.get('gaze_x', 0)
            gaze_y = record.get('gaze_y', 0)
            self.cur_gaze_x.set_value(f"{gaze_x:.2f}" if gaze_x else "--")
            self.cur_gaze_y.set_value(f"{gaze_y:.2f}" if gaze_y else "--")
            
            # Обновляем текущую позицию взгляда на карте
            if gaze_x and gaze_y:
                self.gaze_heatmap.set_current_position(gaze_x, gaze_y)
            else:
                self.gaze_heatmap.clear_current_position()
            
            self.mental_vline.setPos(elapsed)
            self.spectral_vline.setPos(elapsed)
            self.gaze_vline.setPos(elapsed)
    
    def update_graphs(self):
        if not self.data:
            return
        
        self.times = []
        self.attention = []
        self.relaxation = []
        self.alpha = []
        self.beta = []
        self.theta = []
        self.gaze_x = []
        self.gaze_y = []
        self.data_indices = []
        
        for data_idx, row in enumerate(self.data):
            try:
                self.times.append(float(row.get('elapsed_sec', 0)))
                self.attention.append(float(row.get('attention', 0)))
                self.relaxation.append(float(row.get('relaxation', 0)))
                self.alpha.append(float(row.get('alpha', 0)))
                self.beta.append(float(row.get('beta', 0)))
                self.theta.append(float(row.get('theta', 0)))
                gx = row.get('gaze_x', 0)
                gy = row.get('gaze_y', 0)
                self.gaze_x.append(float(gx) if gx else 0)
                self.gaze_y.append(float(gy) if gy else 0)
                self.data_indices.append(data_idx)  # Сохраняем соответствие
            except:
                continue
        
        self.mental_plot.clear()
        self.mental_plot.addItem(self.mental_vline)
        if self.times:
            self.mental_plot.plot(self.times, self.attention, pen=pg.mkPen('#58a6ff', width=2), name='Внимание')
            self.mental_plot.plot(self.times, self.relaxation, pen=pg.mkPen('#a371f7', width=2), name='Расслабление')
            
            # Находим и отображаем пики внимания
            self._find_attention_peaks()
            self._display_attention_peaks()
        
        self.spectral_plot.clear()
        self.spectral_plot.addItem(self.spectral_vline)
        if self.times:
            self.spectral_plot.plot(self.times, self.alpha, pen=pg.mkPen('#3fb950', width=2))
            self.spectral_plot.plot(self.times, self.beta, pen=pg.mkPen('#f0883e', width=2))
            self.spectral_plot.plot(self.times, self.theta, pen=pg.mkPen('#d29922', width=2))
        
        self.gaze_plot.clear()
        self.gaze_plot.addItem(self.gaze_vline)
        if self.times:
            self.gaze_plot.plot(self.times, self.gaze_x, pen=pg.mkPen('#a371f7', width=2))
            self.gaze_plot.plot(self.times, self.gaze_y, pen=pg.mkPen('#f778ba', width=2))
        
        gaze_points = [(self.gaze_x[i], self.gaze_y[i], self.times[i]) for i in range(len(self.times)) if self.gaze_x[i] > 0 or self.gaze_y[i] > 0]
        self.gaze_heatmap.set_data(gaze_points)
    
    def _find_attention_peaks(self):
        """Найти пики внимания в данных"""
        if not self.times or not self.attention or len(self.times) < 3:
            self.attention_peaks = []
            return
        
        # Вычисляем среднее и стандартное отклонение
        attention_values = [a for a in self.attention if a > 0]
        if not attention_values:
            self.attention_peaks = []
            return
        
        mean_attention = sum(attention_values) / len(attention_values)
        variance = sum((a - mean_attention) ** 2 for a in attention_values) / len(attention_values)
        std_dev = variance ** 0.5
        
        # Порог для пика: среднее + 1.5 * стандартное отклонение
        threshold = mean_attention + 1.5 * std_dev
        
        # Находим локальные максимумы выше порога
        peaks = []
        window_size = max(3, len(self.times) // 50)  # Адаптивный размер окна
        
        for i in range(window_size, len(self.attention) - window_size):
            if self.attention[i] < threshold:
                continue
            
            # Проверяем, является ли это локальным максимумом
            is_peak = True
            for j in range(i - window_size, i + window_size + 1):
                if j != i and self.attention[j] >= self.attention[i]:
                    is_peak = False
                    break
            
            if is_peak:
                # Используем индекс из data_indices для соответствия с self.data
                data_idx = self.data_indices[i] if i < len(self.data_indices) else i
                peaks.append((self.times[i], self.attention[i], data_idx))
        
        # Сортируем по значению внимания (от большего к меньшему) и берем топ-10
        peaks.sort(key=lambda x: x[1], reverse=True)
        self.attention_peaks = peaks[:10]
    
    def _display_attention_peaks(self):
        """Отобразить пики внимания на графике и в списке"""
        # Очищаем предыдущие маркеры
        for marker in self.peak_markers:
            self.mental_plot.removeItem(marker)
        self.peak_markers.clear()
        
        # Очищаем список
        self.highlights_list.clear()
        
        if not self.attention_peaks:
            return
        
        # Добавляем маркеры на график
        for time, value, data_index in self.attention_peaks:
            # Вертикальная линия на графике
            vline = pg.InfiniteLine(
                pos=time, 
                angle=90, 
                pen=pg.mkPen('#f85149', width=2, style=Qt.PenStyle.DashLine),
                movable=False
            )
            self.mental_plot.addItem(vline)
            self.peak_markers.append(vline)
            
            # Точка на графике
            scatter = pg.ScatterPlotItem(
                x=[time], 
                y=[value],
                pen=pg.mkPen('#f85149', width=2),
                brush=pg.mkBrush('#f85149'),
                size=10,
                symbol='star'
            )
            self.mental_plot.addItem(scatter)
            self.peak_markers.append(scatter)
        
        # Заполняем список главных моментов
        for i, (time, value, data_index) in enumerate(self.attention_peaks, 1):
            time_str = f"{int(time // 60):02d}:{int(time % 60):02d}"
            item_text = f"#{i} - {time_str} | Внимание: {value:.1f}%"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, (time, data_index))  # Сохраняем время и индекс в data
            self.highlights_list.addItem(item)
    
    def _on_highlight_clicked(self, item):
        """Переход к выбранному моменту при клике на элемент списка"""
        time, index = item.data(Qt.ItemDataRole.UserRole)
        
        # Перемещаем вертикальную линию на графике
        self.mental_vline.setPos(time)
        self.spectral_vline.setPos(time)
        self.gaze_vline.setPos(time)
        
        # Перемещаем видео на этот момент (если видео загружено)
        if self.video_path and self.media_player.duration() > 0:
            # Конвертируем время в миллисекунды
            video_pos_ms = int(time * 1000)
            if video_pos_ms <= self.media_player.duration():
                self.media_player.setPosition(video_pos_ms)
                self.video_slider.setValue(video_pos_ms)
        
        # Обновляем данные для текущей позиции
        if index < len(self.data):
            record = self.data[index]
            attention_val = record.get('attention', 0)
            relaxation_val = record.get('relaxation', 0)
            self.cur_attention.set_value(f"{attention_val:.0f}%" if attention_val else "--")
            self.cur_relaxation.set_value(f"{relaxation_val:.0f}%" if relaxation_val else "--")
            self.cur_alpha.set_value(f"{record.get('alpha', 0)}%")
            self.cur_beta.set_value(f"{record.get('beta', 0)}%")
            self.cur_theta.set_value(f"{record.get('theta', 0)}%")
            
            gaze_x = record.get('gaze_x', 0)
            gaze_y = record.get('gaze_y', 0)
            self.cur_gaze_x.set_value(f"{gaze_x:.2f}" if gaze_x else "--")
            self.cur_gaze_y.set_value(f"{gaze_y:.2f}" if gaze_y else "--")
            
            # Обновляем карту взгляда
            if gaze_x and gaze_y:
                self.gaze_heatmap.set_current_position(gaze_x, gaze_y)
            else:
                self.gaze_heatmap.clear_current_position()


class ConnectionTab(QWidget):
    """Вкладка подключения устройства"""
    def __init__(self):
        super().__init__()
        self._founded_sensors = []
        self._current_address = None
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Подключение BrainBit")
        header.setFixedHeight(36)
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)
        
        subtitle = QLabel("Найдите и подключите ваше устройство BrainBit")
        subtitle.setFixedHeight(20)
        subtitle.setStyleSheet("color: #8b949e; font-size: 13px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Search and disconnect buttons
        search_widget = QWidget()
        search_widget.setFixedHeight(50)
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        self.search_btn = QPushButton("Начать поиск")
        self.search_btn.setFixedHeight(40)
        self.search_btn.setMinimumWidth(150)
        self.disconnect_btn = QPushButton("Отключить устройство")
        self.disconnect_btn.setFixedHeight(40)
        self.disconnect_btn.setMinimumWidth(180)
        self.disconnect_btn.setProperty("class", "secondary")
        self.disconnect_btn.setEnabled(False)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.disconnect_btn)
        search_layout.addStretch()
        layout.addWidget(search_widget)
        
        # Devices list with scroll
        devices_group = QGroupBox("Найденные устройства")
        devices_group.setMinimumHeight(120)
        devices_group.setMaximumHeight(200)
        devices_layout = QVBoxLayout(devices_group)
        devices_layout.setContentsMargins(12, 24, 12, 12)
        self.devices_list = QListWidget()
        self.devices_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.devices_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        devices_layout.addWidget(self.devices_list)
        layout.addWidget(devices_group)
        
        # Resistance check
        resist_group = QGroupBox("Проверка контакта электродов")
        resist_group.setFixedHeight(140)
        resist_layout = QVBoxLayout(resist_group)
        resist_layout.setContentsMargins(12, 24, 12, 12)
        resist_layout.setSpacing(12)
        
        buttons_widget = QWidget()
        buttons_widget.setFixedHeight(36)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        self.start_resist_btn = QPushButton("Начать проверку")
        self.start_resist_btn.setFixedHeight(32)
        self.start_resist_btn.setMinimumWidth(130)
        self.start_resist_btn.setEnabled(False)
        self.stop_resist_btn = QPushButton("Остановить")
        self.stop_resist_btn.setFixedHeight(32)
        self.stop_resist_btn.setMinimumWidth(100)
        self.stop_resist_btn.setProperty("class", "secondary")
        self.stop_resist_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_resist_btn)
        buttons_layout.addWidget(self.stop_resist_btn)
        buttons_layout.addStretch()
        resist_layout.addWidget(buttons_widget)
        
        cards_widget = QWidget()
        cards_widget.setFixedHeight(70)
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
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
        resist_layout.addWidget(cards_widget)
        layout.addWidget(resist_group)
        
        # Calibration
        calib_group = QGroupBox("Калибровка")
        calib_group.setFixedHeight(150)
        calib_layout = QVBoxLayout(calib_group)
        calib_layout.setContentsMargins(12, 24, 12, 12)
        calib_layout.setSpacing(10)
        
        calib_buttons_widget = QWidget()
        calib_buttons_widget.setFixedHeight(36)
        calib_buttons = QHBoxLayout(calib_buttons_widget)
        calib_buttons.setContentsMargins(0, 0, 0, 0)
        calib_buttons.setSpacing(8)
        self.start_calc_btn = QPushButton("Начать калибровку")
        self.start_calc_btn.setFixedHeight(32)
        self.start_calc_btn.setMinimumWidth(150)
        self.start_calc_btn.setEnabled(False)
        self.stop_calc_btn = QPushButton("Остановить")
        self.stop_calc_btn.setFixedHeight(32)
        self.stop_calc_btn.setMinimumWidth(100)
        self.stop_calc_btn.setProperty("class", "secondary")
        self.stop_calc_btn.setEnabled(False)
        calib_buttons.addWidget(self.start_calc_btn)
        calib_buttons.addWidget(self.stop_calc_btn)
        calib_buttons.addStretch()
        calib_layout.addWidget(calib_buttons_widget)
        
        progress_widget = QWidget()
        progress_widget.setFixedHeight(30)
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        progress_label = QLabel("Прогресс:")
        progress_label.setFixedWidth(70)
        self.calib_progress = QProgressBar()
        self.calib_progress.setValue(0)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.calib_progress)
        calib_layout.addWidget(progress_widget)
        
        artifact_widget = QWidget()
        artifact_widget.setFixedHeight(24)
        artifact_layout = QHBoxLayout(artifact_widget)
        artifact_layout.setContentsMargins(0, 0, 0, 0)
        artifact_layout.setSpacing(8)
        artifact_label = QLabel("Артефакты:")
        artifact_label.setFixedWidth(70)
        self.artifact_label = QLabel("—")
        artifact_layout.addWidget(artifact_label)
        artifact_layout.addWidget(self.artifact_label)
        artifact_layout.addStretch()
        calib_layout.addWidget(artifact_widget)
        layout.addWidget(calib_group)
        
        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def connect_signals(self):
        self.search_btn.clicked.connect(self.start_search)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.devices_list.itemClicked.connect(self.connect_to_device)
        self.start_resist_btn.clicked.connect(self.start_resist)
        self.stop_resist_btn.clicked.connect(self.stop_resist)
        self.start_calc_btn.clicked.connect(self.start_calc)
        self.stop_calc_btn.clicked.connect(self.stop_calc)
    
    def start_search(self):
        # Отключаем все устройства перед поиском
        self.disconnect_all_devices()
        
        self.devices_list.clear()
        self.search_btn.setText("Поиск...")
        self.search_btn.setEnabled(False)
        
        def on_founded(sensors):
            self._founded_sensors = sensors
            self.devices_list.addItems([f"{s.Name} ({s.Address})" for s in sensors])
            self.search_btn.setText("Искать снова")
            self.search_btn.setEnabled(True)
            try:
                brain_bit_controller.foundedDevices.disconnect(on_founded)
            except:
                pass
        
        brain_bit_controller.foundedDevices.connect(on_founded)
        brain_bit_controller.search_with_result(5, [])
    
    def disconnect_all_devices(self):
        """Отключить все подключенные устройства"""
        # Отключаем каждое устройство отдельно (не используем stop_all, т.к. он уничтожает сканер)
        try:
            for addr in list(brain_bit_controller.connected_devices):
                try:
                    brain_bit_controller.stop_resist(addr)
                except:
                    pass
                try:
                    brain_bit_controller.stop_calculations(addr)
                except:
                    pass
                try:
                    brain_bit_controller.disconnect_from(addr)
                except:
                    pass
        except:
            pass
        # Сбрасываем состояние UI
        self.start_resist_btn.setEnabled(False)
        self.stop_resist_btn.setEnabled(False)
        self.start_calc_btn.setEnabled(False)
        self.stop_calc_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        self.calib_progress.setValue(0)
        self.artifact_label.setText("—")
        self.artifact_label.setStyleSheet("")
        self.o1_card.reset()
        self.o2_card.reset()
        self.t3_card.reset()
        self.t4_card.reset()
    
    def disconnect_device(self):
        """Отключить текущее устройство"""
        self.disconnect_all_devices()
        # Обновляем список устройств
        for i in range(self.devices_list.count()):
            item = self.devices_list.item(i)
            if item and ": Connected" in item.text():
                # Убираем статус подключения из текста
                text = item.text()
                if self._founded_sensors and i < len(self._founded_sensors):
                    info = self._founded_sensors[i]
                    item.setText(f"{info.Name} ({info.Address}): Disconnected")

    def connect_to_device(self, item):
        idx = self.devices_list.row(item)
        info = self._founded_sensors[idx]
        
        def on_connected(address, state):
            item.setText(f"{info.Name} ({info.Address}): {state.name}")
            if address == info.Address and state == ConnectionState.Connected:
                self.start_resist_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(True)
            elif address == info.Address and state == ConnectionState.Disconnected:
                self.start_resist_btn.setEnabled(False)
                self.start_calc_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(False)
        
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
                # Автоматически завершаем калибровку при 100%
                if progress >= 100:
                    QTimer.singleShot(500, self._on_calibration_complete)
        
        brain_bit_controller.isArtefacted.connect(on_artifact)
        brain_bit_controller.calibrationProcessChanged.connect(on_progress)
        brain_bit_controller.start_calculations(addr)
        self.start_calc_btn.setEnabled(False)
        self.stop_calc_btn.setEnabled(True)
    
    def _on_calibration_complete(self):
        """Вызывается когда калибровка завершена"""
        self.stop_calc()
        self.calib_progress.setStyleSheet("""
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #238636, stop:1 #3fb950);
            }
        """)

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
        self.relaxation_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.alpha_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.beta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.theta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.is_monitoring = False
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_widget = QWidget()
        header_widget.setFixedHeight(44)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("Мониторинг в реальном времени")
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.start_monitor_btn = QPushButton("Начать")
        self.start_monitor_btn.setFixedHeight(36)
        self.start_monitor_btn.setMinimumWidth(100)
        self.stop_monitor_btn = QPushButton("Стоп")
        self.stop_monitor_btn.setFixedHeight(36)
        self.stop_monitor_btn.setMinimumWidth(100)
        self.stop_monitor_btn.setProperty("class", "secondary")
        self.stop_monitor_btn.setEnabled(False)
        header_layout.addWidget(self.start_monitor_btn)
        header_layout.addWidget(self.stop_monitor_btn)
        layout.addWidget(header_widget)
        
        # Warning
        self.electrode_warning = QLabel("")
        self.electrode_warning.setMinimumHeight(40)
        self.electrode_warning.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 6px;
                padding: 8px;
                color: #f85149;
                font-weight: 600;
            }
        """)
        self.electrode_warning.setWordWrap(True)
        self.electrode_warning.setVisible(False)
        layout.addWidget(self.electrode_warning)
        
        # Metric cards
        cards_widget = QWidget()
        cards_widget.setFixedHeight(80)
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)
        self.attention_card = MetricCard("Внимание", "0%", "#58a6ff")
        self.relaxation_card = MetricCard("Расслабление", "0%", "#a371f7")
        self.alpha_card = MetricCard("Альфа", "0%", "#3fb950")
        self.beta_card = MetricCard("Бета", "0%", "#f0883e")
        self.theta_card = MetricCard("Тета", "0%", "#d29922")
        cards_layout.addWidget(self.attention_card)
        cards_layout.addWidget(self.relaxation_card)
        cards_layout.addWidget(self.alpha_card)
        cards_layout.addWidget(self.beta_card)
        cards_layout.addWidget(self.theta_card)
        cards_layout.addStretch()
        layout.addWidget(cards_widget)
        
        pg.setConfigOptions(antialias=True)
        
        # Attention + Relaxation graph
        mental_group = QGroupBox("Внимание / Расслабление")
        mental_group.setMinimumHeight(180)
        mental_layout = QVBoxLayout(mental_group)
        mental_layout.setContentsMargins(8, 24, 8, 8)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('#161b22')
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_plot.setYRange(0, 100)
        self.attention_curve = self.mental_plot.plot(pen=pg.mkPen('#58a6ff', width=2))
        self.relaxation_curve = self.mental_plot.plot(pen=pg.mkPen('#a371f7', width=2))
        mental_layout.addWidget(self.mental_plot)
        layout.addWidget(mental_group)
        
        # Spectral graph
        spectral_group = QGroupBox("Спектральные данные")
        spectral_group.setMinimumHeight(180)
        spectral_layout = QVBoxLayout(spectral_group)
        spectral_layout.setContentsMargins(8, 24, 8, 8)
        self.spectral_plot = pg.PlotWidget()
        self.spectral_plot.setBackground('#161b22')
        self.spectral_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectral_plot.setYRange(0, 100)
        self.alpha_curve = self.spectral_plot.plot(pen=pg.mkPen('#3fb950', width=2))
        self.beta_curve = self.spectral_plot.plot(pen=pg.mkPen('#f0883e', width=2))
        self.theta_curve = self.spectral_plot.plot(pen=pg.mkPen('#d29922', width=2))
        spectral_layout.addWidget(self.spectral_plot)
        layout.addWidget(spectral_group)
        
        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
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
        
        def on_inst_mind(address, data):
            if address == addr and self.is_monitoring:
                self.attention_data.append(data.attention)
                self.relaxation_data.append(data.relaxation)
                self.attention_card.set_value(f"{data.attention:.0f}%")
                self.relaxation_card.set_value(f"{data.relaxation:.0f}%")
        
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
        self.relaxation_curve.setData(x, list(self.relaxation_data))
        self.alpha_curve.setData(x, list(self.alpha_data))
        self.beta_curve.setData(x, list(self.beta_data))
        self.theta_curve.setData(x, list(self.theta_data))


class VideoRecordingTab(QWidget):
    """Вкладка с видео, трекингом взгляда и записью"""
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recording_start_time = None
        self.record_data = []
        self.record_count_value = 0
        self.current_brain_data = {}
        self.current_gaze_data = None
        self.video_loaded = False
        self.video_file_path = None
        self.camera_active = False
        self.fullscreen_dialog = None
        self.reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        
        # Data for real-time graphs
        self.data_points = 500
        self.attention_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.relaxation_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.alpha_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.beta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.theta_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.gaze_x_data = deque([0] * self.data_points, maxlen=self.data_points)
        self.gaze_y_data = deque([0] * self.data_points, maxlen=self.data_points)
        
        self.setup_ui()
        self.connect_signals()
        # Initialize graphs with empty data
        QTimer.singleShot(100, self.update_plots)
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Видео + Трекинг взгляда + Запись")
        header.setMinimumHeight(32)
        header.setStyleSheet("font-size: 22px; font-weight: 700; color: #ffffff;")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Top section: Video + Camera
        top_widget = QWidget()
        top_widget.setFixedHeight(300)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(12)
        
        # Video player
        video_container = QFrame()
        video_container.setStyleSheet("QFrame { background-color: #000; border: 1px solid #30363d; border-radius: 8px; }")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(6, 6, 6, 6)
        video_layout.setSpacing(4)
        
        # Video file select
        video_file_widget = QWidget()
        video_file_widget.setFixedHeight(28)
        video_file_layout = QHBoxLayout(video_file_widget)
        video_file_layout.setContentsMargins(0, 0, 0, 0)
        video_file_layout.setSpacing(6)
        
        self.video_path_label = QLabel("Видео не выбрано")
        self.video_path_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        self.video_path_label.setWordWrap(True)
        self.select_video_btn = QPushButton("MP4")
        self.select_video_btn.setProperty("class", "secondary")
        self.select_video_btn.setFixedSize(60, 24)
        self.fullscreen_btn = QPushButton("[ ]")
        self.fullscreen_btn.setToolTip("Полный экран (F)")
        self.fullscreen_btn.setFixedSize(32, 24)
        self.fullscreen_btn.setEnabled(False)
        video_file_layout.addWidget(self.video_path_label, stretch=1)
        video_file_layout.addWidget(self.select_video_btn)
        video_file_layout.addWidget(self.fullscreen_btn)
        video_layout.addWidget(video_file_widget)
        
        self.video_widget = QVideoWidget()
        video_layout.addWidget(self.video_widget, stretch=1)
        
        # Video controls
        controls_widget = QWidget()
        controls_widget.setFixedHeight(32)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(36, 26)
        self.play_btn.setEnabled(False)
        self.video_slider = QSlider(Qt.Orientation.Horizontal)
        self.video_slider.setEnabled(False)
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(85)
        self.time_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.video_slider, stretch=1)
        controls_layout.addWidget(self.time_label)
        video_layout.addWidget(controls_widget)
        
        top_layout.addWidget(video_container, stretch=3)
        
        # Camera
        camera_container = QFrame()
        camera_container.setFixedWidth(320)
        camera_container.setStyleSheet("QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setContentsMargins(8, 8, 8, 8)
        camera_layout.setSpacing(6)
        
        cam_header = QLabel("Трекинг взгляда")
        cam_header.setFixedHeight(20)
        cam_header.setStyleSheet("font-size: 13px; font-weight: 600; color: #58a6ff;")
        camera_layout.addWidget(cam_header)
        
        self.camera_label = QLabel("Камера запустится при записи")
        self.camera_label.setMinimumHeight(160)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: #0d1117; border-radius: 6px; color: #8b949e;")
        camera_layout.addWidget(self.camera_label, stretch=1)
        
        gaze_widget = QWidget()
        gaze_widget.setFixedHeight(22)
        gaze_info = QHBoxLayout(gaze_widget)
        gaze_info.setContentsMargins(0, 0, 0, 0)
        gaze_info.setSpacing(8)
        self.gaze_direction_label = QLabel("Направление: —")
        self.gaze_direction_label.setStyleSheet("color: #e6edf3; font-size: 11px;")
        self.gaze_direction_label.setWordWrap(True)
        self.eyes_status_label = QLabel("Глаза: —")
        self.eyes_status_label.setStyleSheet("color: #e6edf3; font-size: 11px;")
        self.eyes_status_label.setWordWrap(True)
        gaze_info.addWidget(self.gaze_direction_label)
        gaze_info.addWidget(self.eyes_status_label)
        gaze_info.addStretch()
        camera_layout.addWidget(gaze_widget)
        
        cam_controls_widget = QWidget()
        cam_controls_widget.setFixedHeight(30)
        cam_controls = QHBoxLayout(cam_controls_widget)
        cam_controls.setContentsMargins(0, 0, 0, 0)
        cam_controls.setSpacing(4)
        self.start_camera_btn = QPushButton("Тест")
        self.start_camera_btn.setProperty("class", "secondary")
        self.start_camera_btn.setFixedHeight(26)
        self.start_camera_btn.setMinimumWidth(60)
        self.calibrate_btn = QPushButton("Калибровка")
        self.calibrate_btn.setFixedHeight(26)
        self.calibrate_btn.setMinimumWidth(100)
        self.calibrate_btn.setEnabled(False)
        self.stop_camera_btn = QPushButton("Стоп")
        self.stop_camera_btn.setProperty("class", "secondary")
        self.stop_camera_btn.setMinimumSize(50, 26)
        self.stop_camera_btn.setEnabled(False)
        cam_controls.addWidget(self.start_camera_btn)
        cam_controls.addWidget(self.calibrate_btn)
        cam_controls.addWidget(self.stop_camera_btn)
        camera_layout.addWidget(cam_controls_widget)
        
        self.calibration_status = QLabel("Требуется калибровка")
        self.calibration_status.setMinimumHeight(28)
        self.calibration_status.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 4px;
                padding: 4px 8px;
                color: #f85149;
                font-size: 11px;
            }
        """)
        self.calibration_status.setWordWrap(True)
        camera_layout.addWidget(self.calibration_status)
        
        top_layout.addWidget(camera_container)
        layout.addWidget(top_widget)
        
        # Warning
        self.electrode_warning = QLabel("")
        self.electrode_warning.setMinimumHeight(36)
        self.electrode_warning.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 6px;
                padding: 8px;
                color: #f85149;
                font-weight: 600;
            }
        """)
        self.electrode_warning.setWordWrap(True)
        self.electrode_warning.setVisible(False)
        layout.addWidget(self.electrode_warning)
        
        # Recording section
        record_group = QGroupBox("Запись")
        record_group.setFixedHeight(200)
        record_layout = QVBoxLayout(record_group)
        record_layout.setContentsMargins(12, 24, 12, 12)
        record_layout.setSpacing(10)
        
        self.output_path_label = QLabel("Отчёты сохраняются в: reports/")
        self.output_path_label.setMinimumHeight(18)
        self.output_path_label.setStyleSheet("color: #8b949e; font-size: 12px;")
        self.output_path_label.setWordWrap(True)
        record_layout.addWidget(self.output_path_label)
        
        buttons_widget = QWidget()
        buttons_widget.setFixedHeight(50)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        self.start_record_btn = QPushButton("НАЧАТЬ ЗАПИСЬ")
        self.start_record_btn.setStyleSheet("""
            QPushButton { background-color: #da3633; color: white; font-weight: 700; font-size: 14px; }
            QPushButton:hover { background-color: #f85149; }
            QPushButton:disabled { background-color: #21262d; color: #484f58; }
        """)
        self.start_record_btn.setFixedHeight(44)
        self.start_record_btn.setMinimumWidth(150)
        
        self.stop_record_btn = QPushButton("СТОП")
        self.stop_record_btn.setStyleSheet("""
            QPushButton { background-color: #21262d; border: 2px solid #da3633; color: #da3633; font-weight: 700; }
            QPushButton:disabled { border-color: #484f58; color: #484f58; }
        """)
        self.stop_record_btn.setFixedHeight(44)
        self.stop_record_btn.setMinimumWidth(100)
        self.stop_record_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_record_btn)
        buttons_layout.addWidget(self.stop_record_btn)
        record_layout.addWidget(buttons_widget)
        
        status_widget = QWidget()
        status_widget.setFixedHeight(22)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        self.record_status = QLabel("Готов")
        self.record_status.setStyleSheet("font-weight: 600;")
        self.record_count = QLabel("Записей: 0")
        self.record_count.setStyleSheet("color: #8b949e;")
        status_layout.addWidget(self.record_status)
        status_layout.addStretch()
        status_layout.addWidget(self.record_count)
        record_layout.addWidget(status_widget)
        
        values_widget = QWidget()
        values_widget.setFixedHeight(60)
        values_layout = QHBoxLayout(values_widget)
        values_layout.setContentsMargins(0, 0, 0, 0)
        values_layout.setSpacing(6)
        self.rec_attention = MetricCard("Внимание", "—", "#58a6ff", size="small")
        self.rec_relaxation = MetricCard("Расслаб.", "—", "#a371f7", size="small")
        self.rec_gaze_x = MetricCard("Взгляд X", "—", "#8b949e", size="small")
        self.rec_gaze_y = MetricCard("Взгляд Y", "—", "#8b949e", size="small")
        values_layout.addWidget(self.rec_attention)
        values_layout.addWidget(self.rec_relaxation)
        values_layout.addWidget(self.rec_gaze_x)
        values_layout.addWidget(self.rec_gaze_y)
        values_layout.addStretch()
        record_layout.addWidget(values_widget)
        
        layout.addWidget(record_group)
        
        # Graphs section
        pg.setConfigOptions(antialias=True)
        
        # Attention + Relaxation graph
        mental_group = QGroupBox("Внимание / Расслабление")
        mental_group.setMinimumHeight(150)
        mental_layout = QVBoxLayout(mental_group)
        mental_layout.setContentsMargins(8, 24, 8, 8)
        self.mental_plot = pg.PlotWidget()
        self.mental_plot.setBackground('#161b22')
        self.mental_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mental_plot.setYRange(0, 100)
        self.attention_curve = self.mental_plot.plot(pen=pg.mkPen('#58a6ff', width=2))
        self.relaxation_curve = self.mental_plot.plot(pen=pg.mkPen('#a371f7', width=2))
        mental_layout.addWidget(self.mental_plot)
        layout.addWidget(mental_group)
        
        # Spectral graph
        spectral_group = QGroupBox("Спектральные данные")
        spectral_group.setMinimumHeight(150)
        spectral_layout = QVBoxLayout(spectral_group)
        spectral_layout.setContentsMargins(8, 24, 8, 8)
        self.spectral_plot = pg.PlotWidget()
        self.spectral_plot.setBackground('#161b22')
        self.spectral_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectral_plot.setYRange(0, 100)
        self.alpha_curve = self.spectral_plot.plot(pen=pg.mkPen('#3fb950', width=2))
        self.beta_curve = self.spectral_plot.plot(pen=pg.mkPen('#f0883e', width=2))
        self.theta_curve = self.spectral_plot.plot(pen=pg.mkPen('#d29922', width=2))
        spectral_layout.addWidget(self.spectral_plot)
        layout.addWidget(spectral_group)
        
        # Gaze graph
        gaze_graph_group = QGroupBox("Позиция взгляда")
        gaze_graph_group.setMinimumHeight(150)
        gaze_graph_layout = QVBoxLayout(gaze_graph_group)
        gaze_graph_layout.setContentsMargins(8, 24, 8, 8)
        self.gaze_plot = pg.PlotWidget()
        self.gaze_plot.setBackground('#161b22')
        self.gaze_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gaze_plot.setYRange(0, 1)
        self.gaze_x_curve = self.gaze_plot.plot(pen=pg.mkPen('#a371f7', width=2))
        self.gaze_y_curve = self.gaze_plot.plot(pen=pg.mkPen('#f778ba', width=2))
        gaze_graph_layout.addWidget(self.gaze_plot)
        layout.addWidget(gaze_graph_group)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self._write_record)
        
        # Timer for updating graphs
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plots)
    
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
            self.video_file_path = filename
            self.video_path_label.setText(os.path.basename(filename))
            self.video_path_label.setStyleSheet("color: #3fb950; font-size: 11px;")
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
        if eye_tracker.is_calibrated:
            self.calibration_status.setText("Калибровка выполнена")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #23863622;
                    border: 1px solid #238636;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #3fb950;
                    font-size: 11px;
                }
            """)
        else:
            self.calibration_status.setText("Требуется калибровка")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #da363322;
                    border: 1px solid #da3633;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #f85149;
                    font-size: 11px;
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
        if not eye_tracker.is_running:
            return
        self.calibration_dialog = CalibrationDialog(eye_tracker, self)
        self.calibration_dialog.calibration_complete.connect(self.on_calibration_complete)
        self.calibration_dialog.start_calibration()
    
    def on_calibration_complete(self, calibration_data):
        if calibration_data:
            eye_tracker.set_calibration(calibration_data)
            self.calibration_status.setText("Калибровка выполнена")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #23863622;
                    border: 1px solid #238636;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #3fb950;
                    font-size: 11px;
                }
            """)
        else:
            self.calibration_status.setText("Ошибка калибровки")
            self.calibration_status.setStyleSheet("""
                QLabel {
                    background-color: #da363322;
                    border: 1px solid #da3633;
                    border-radius: 4px;
                    padding: 4px 8px;
                    color: #f85149;
                    font-size: 11px;
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
                self.rec_gaze_x.set_value(f"{gaze.screen_x:.2f}")
                self.rec_gaze_y.set_value(f"{gaze.screen_y:.2f}")
                self.gaze_x_data.append(gaze.screen_x if gaze.screen_x else 0)
                self.gaze_y_data.append(gaze.screen_y if gaze.screen_y else 0)
        except Exception:
            pass
    
    def update_plots(self):
        """Обновить графики в реальном времени"""
        x = list(range(self.data_points))
        self.attention_curve.setData(x, list(self.attention_data))
        self.relaxation_curve.setData(x, list(self.relaxation_data))
        self.alpha_curve.setData(x, list(self.alpha_data))
        self.beta_curve.setData(x, list(self.beta_data))
        self.theta_curve.setData(x, list(self.theta_data))
        self.gaze_x_curve.setData(x, list(self.gaze_x_data))
        self.gaze_y_curve.setData(x, list(self.gaze_y_data))
    
    def _check_ready(self):
        self.start_record_btn.setEnabled(True)
    
    def start_recording(self):
        if not eye_tracker.is_calibrated:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Требуется калибровка")
            msg.setText("Трекинг взгляда не откалиброван!")
            msg.setInformativeText("Сначала включите камеру и выполните калибровку.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet("""
                QMessageBox { background-color: #161b22; }
                QLabel { color: #e6edf3; }
                QPushButton { background-color: #238636; color: white; padding: 8px 16px; border-radius: 6px; }
            """)
            msg.exec()
            return
        
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
        if not eye_tracker.is_running:
            eye_tracker.start(0)
        
        if self.video_loaded:
            self.media_player.setPosition(0)
            self.media_player.play()
            self.fullscreen_dialog = FullscreenVideoDialog(self.media_player, self, is_recording=True)
        
        self.is_recording = True
        self.recording_start_time = datetime.now()
        self.record_count_value = 0
        self.record_data = []
        
        self.current_brain_data = {'attention': 0, 'relaxation': 0, 'alpha': 0, 'beta': 0, 'theta': 0}
        
        if brain_bit_controller.connected_devices:
            addr = brain_bit_controller.connected_devices[0]
            
            def on_inst_mind(address, data):
                if address == addr and self.is_recording:
                    self.current_brain_data['attention'] = data.attention
                    self.current_brain_data['relaxation'] = data.relaxation
                    self.attention_data.append(data.attention)
                    self.relaxation_data.append(data.relaxation)
                    self.rec_attention.set_value(f"{data.attention:.0f}%")
                    self.rec_relaxation.set_value(f"{data.relaxation:.0f}%")
            
            def on_spec(address, data):
                if address == addr and self.is_recording:
                    self.current_brain_data['alpha'] = data.alpha
                    self.current_brain_data['beta'] = data.beta
                    self.current_brain_data['theta'] = data.theta
                    self.alpha_data.append(data.alpha)
                    self.beta_data.append(data.beta)
                    self.theta_data.append(data.theta)
            
            def on_artifact(address, is_art):
                if address == addr and self.is_recording:
                    if self.fullscreen_dialog and self.fullscreen_dialog.isVisible():
                        self.fullscreen_dialog.show_electrode_warning(is_art)
                    else:
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
        self.update_timer.start(100)  # Update graphs every 100ms
        self.record_status.setText("ЗАПИСЬ")
        self.record_status.setStyleSheet("color: #f85149; font-weight: 600;")
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
    
    def _write_record(self):
        if not self.is_recording:
            return
        now = datetime.now(timezone.utc)
        elapsed = (now - self.recording_start_time).total_seconds()
        video_pos = self.media_player.position() if self.video_loaded else 0
        gaze = self.current_gaze_data
        
        record = {
            'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.') + f'{now.microsecond:06d}Z',
            'elapsed_sec': round(elapsed, 2),
            'video_ms': video_pos,
            'attention': self.current_brain_data.get('attention', 0),
            'relaxation': self.current_brain_data.get('relaxation', 0),
            'audio_level': 0.0,
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
        self.is_recording = False
        self.record_timer.stop()
        self.update_timer.stop()
        
        # Clear graph data
        self.attention_data.clear()
        self.relaxation_data.clear()
        self.alpha_data.clear()
        self.beta_data.clear()
        self.theta_data.clear()
        self.gaze_x_data.clear()
        self.gaze_y_data.clear()
        # Fill with zeros
        for _ in range(self.data_points):
            self.attention_data.append(0)
            self.relaxation_data.append(0)
            self.alpha_data.append(0)
            self.beta_data.append(0)
            self.theta_data.append(0)
            self.gaze_x_data.append(0)
            self.gaze_y_data.append(0)
        self.update_plots()  # Clear graphs
        
        self.electrode_warning.setVisible(False)
        
        if self.fullscreen_dialog and self.fullscreen_dialog.isVisible():
            self.fullscreen_dialog.close()
            self.fullscreen_dialog = None
        
        self.media_player.pause()
        self.camera_active = False
        eye_tracker.stop()
        
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

        if self.record_data:
            filename = f"report_{self.recording_start_time.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            end_time = datetime.now()
            report = {
                'created_at': self.recording_start_time.strftime('%Y-%m-%dT%H:%M:%S.') + f'{self.recording_start_time.microsecond:06d}Z',
                'ended_at': end_time.strftime('%Y-%m-%dT%H:%M:%S.') + f'{end_time.microsecond:06d}Z',
                'video_file': os.path.basename(self.video_file_path) if self.video_file_path else None,
                'video_path': self.video_file_path,
                'total_records': len(self.record_data),
                'records': self.record_data
            }
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                self.output_path_label.setText(f"Сохранено: {filename}")
                self.output_path_label.setStyleSheet("color: #3fb950; font-size: 12px;")
            except Exception as e:
                self.output_path_label.setText(f"Ошибка сохранения: {e}")
                self.output_path_label.setStyleSheet("color: #f85149; font-size: 12px;")
        
        # Отправка данных по WebSocket
        if self.record_data:
            # Определяем ID видео
            video_id = get_video_id(self.video_file_path)
            self._send_data_via_websocket(self.record_data, video_id)
        
        self.record_status.setText("Готово")
        self.record_status.setStyleSheet("color: #3fb950; font-weight: 600;")
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
    
    def _send_data_via_websocket(self, data, video_id="12345"):
        """Отправка данных по WebSocket в отдельном потоке"""
        if websocket is None:
            print("Библиотека websocket-client не установлена. Установите: pip install websocket-client")
            return
        
        def send_in_thread():
            try:
                # Используем video_id в URL
                ws_url = f"ws://10.128.7.6:8099/influxdbpoints/ws/login/{video_id}"
                ws = websocket.create_connection(ws_url)
                
                # Отправляем данные как JSON массив
                json_data = json.dumps(data, ensure_ascii=False)
                ws.send(json_data)
                
                # Получаем ответ
                try:
                    response = ws.recv()
                    print(f"WebSocket ответ: {response}")
                except:
                    pass
                
                ws.close()
                print("Данные успешно отправлены по WebSocket")
            except Exception as e:
                print(f"Ошибка отправки данных по WebSocket: {e}")
        
        # Запускаем отправку в отдельном потоке
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()


class VideoLibraryTab(QWidget):
    """Вкладка библиотеки видео"""
    def __init__(self):
        super().__init__()
        self.videos = []
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Заголовок
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("Библиотека видео")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: #ffffff;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setFixedWidth(120)
        self.refresh_btn.clicked.connect(self.load_videos)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(header_widget)
        
        # Статус авторизации
        self.auth_warning = QLabel("Войдите в систему для просмотра видео")
        self.auth_warning.setStyleSheet("""
            QLabel {
                background-color: #da363322;
                border: 1px solid #da3633;
                border-radius: 8px;
                padding: 16px;
                color: #f85149;
                font-size: 14px;
            }
        """)
        self.auth_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.auth_warning)
        
        # Статус загрузки
        self.loading_label = QLabel("Загрузка...")
        self.loading_label.setStyleSheet("color: #8b949e; font-size: 14px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
        
        # Сообщение об ошибке
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f85149; font-size: 14px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Пустой список
        self.empty_label = QLabel("Нет доступных видео")
        self.empty_label.setStyleSheet("color: #8b949e; font-size: 14px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
        
        # Контейнер для списка видео
        self.videos_container = QWidget()
        self.videos_layout = QVBoxLayout(self.videos_container)
        self.videos_layout.setSpacing(8)
        self.videos_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.videos_container)
        
        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.update_auth_state()
    
    def update_auth_state(self):
        """Обновить состояние в зависимости от авторизации"""
        if auth_manager.is_authenticated():
            self.auth_warning.setVisible(False)
            self.refresh_btn.setEnabled(True)
            self.load_videos()
        else:
            self.auth_warning.setVisible(True)
            self.refresh_btn.setEnabled(False)
            self.clear_videos()
    
    def clear_videos(self):
        """Очистить виджеты списка видео"""
        while self.videos_layout.count():
            item = self.videos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def load_videos(self):
        """Загрузить список видео с сервера"""
        if not auth_manager.is_authenticated():
            return
        
        self.loading_label.setVisible(True)
        self.error_label.setVisible(False)
        self.empty_label.setVisible(False)
        self.refresh_btn.setEnabled(False)
        
        # Делаем GET запрос
        result, error, raw_response = self._make_get_request("/video/")
        
        self.loading_label.setVisible(False)
        self.refresh_btn.setEnabled(True)
        
        if error:
            self.error_label.setText(f"Ошибка: {error}")
            self.error_label.setVisible(True)
            return
        
        self.videos = result if isinstance(result, list) else []
        self.display_videos()
    
    def _make_get_request(self, endpoint):
        """GET запрос к API"""
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            headers = {'Accept': 'application/json'}
            if auth_manager.is_authenticated():
                headers['Authorization'] = f'Bearer {auth_manager.access_token}'
            
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                raw = response.read().decode('utf-8')
                data = json.loads(raw)
                return data, None, raw
                
        except urllib.error.HTTPError as e:
            raw = ""
            try:
                raw = e.read().decode('utf-8')
                error_body = json.loads(raw)
                if 'detail' in error_body:
                    return None, str(error_body['detail']), raw
            except:
                pass
            return None, f"Ошибка {e.code}: {e.reason}", raw
        except urllib.error.URLError as e:
            return None, f"Ошибка подключения: {e.reason}", str(e)
        except Exception as e:
            return None, str(e), str(e)
    
    def display_videos(self):
        """Отобразить список видео"""
        self.clear_videos()
        
        if not self.videos:
            self.empty_label.setVisible(True)
            return
        
        self.empty_label.setVisible(False)
        
        for video in self.videos:
            video_widget = self._create_video_item(video)
            self.videos_layout.addWidget(video_widget)
        
        # Добавляем растяжку в конец
        self.videos_layout.addStretch()
    
    def _create_video_item(self, video):
        """Создать виджет для одного видео"""
        frame = QFrame()
        frame.setMinimumHeight(70)
        frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #58a6ff;
                background-color: #1c2128;
            }
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Иконка видео
        icon_label = QLabel("🎬")
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedWidth(40)
        layout.addWidget(icon_label)
        
        # Информация о видео
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        name_label = QLabel(video.get('name', 'Без названия'))
        name_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #e6edf3;")
        name_label.setWordWrap(True)
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addWidget(name_label)
        
        details_label = QLabel(f"ID: {video.get('id', '?')} • Загружено пользователем #{video.get('uploaded_by', '?')}")
        details_label.setStyleSheet("font-size: 12px; color: #8b949e;")
        details_label.setWordWrap(True)
        info_layout.addWidget(details_label)
        
        layout.addWidget(info_widget, stretch=1)
        
        # Кнопка скачать
        download_btn = QPushButton("Скачать")
        download_btn.setFixedHeight(32)
        download_btn.setFixedWidth(100)
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
            QPushButton:pressed {
                background-color: #238636;
            }
            QPushButton:disabled {
                background-color: #21262d;
                color: #8b949e;
            }
        """)
        video_id = video.get('id')
        video_name = video.get('name', f'video_{video_id}')
        download_btn.clicked.connect(lambda checked, vid=video_id, vname=video_name: self.download_video(vid, vname))
        layout.addWidget(download_btn)
        
        return frame
    
    def download_video(self, video_id, video_name):
        """Скачать видео"""
        if not auth_manager.is_authenticated():
            return
        
        # Создаем папку для видео
        ensure_videos_dir()
        
        # Формируем имя файла с ID
        if not video_name.endswith('.mp4'):
            video_name = f"{video_name}.mp4"
        # Убираем расширение, добавляем ID и снова добавляем расширение
        name_without_ext = os.path.splitext(video_name)[0]
        filename = f"{name_without_ext}_id{video_id}.mp4"
        save_path = os.path.join(VIDEOS_DIR, filename)
        
        # Если файл уже существует, спрашиваем подтверждение
        if os.path.exists(save_path):
            reply = QMessageBox.question(
                self,
                "Файл существует",
                f"Файл уже существует:\n{save_path}\n\nПерезаписать?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Скачиваем файл
        url = f"{API_BASE_URL}/video/file/{video_id}"
        
        try:
            headers = {}
            if auth_manager.is_authenticated():
                headers['Authorization'] = f'Bearer {auth_manager.access_token}'
            
            req = urllib.request.Request(url, headers=headers, method='GET')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(save_path, 'wb') as f:
                    f.write(response.read())
            
            # Сохраняем метаданные (путь -> video_id)
            save_video_with_id(save_path, video_id)
            
            # Успех
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Успех")
            msg.setText(f"Видео сохранено:\n{save_path}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            
        except urllib.error.HTTPError as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Ошибка")
            msg.setText(f"Ошибка скачивания: {e.code} {e.reason}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Ошибка")
            msg.setText(f"Ошибка: {str(e)}")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BrainBit Monitor")
        self.setMinimumSize(1000, 700)
        self.setup_ui()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.auth_tab = AuthTab()
        self.connection_tab = ConnectionTab()
        self.monitoring_tab = MonitoringTab()
        self.video_tab = VideoRecordingTab()
        self.results_tab = ResultsTab()
        self.video_library_tab = VideoLibraryTab()
        
        self.tabs.addTab(self.auth_tab, "Авторизация")
        self.tabs.addTab(self.connection_tab, "Подключение")
        self.tabs.addTab(self.monitoring_tab, "Мониторинг")
        self.tabs.addTab(self.video_tab, "Видео + Взгляд")
        self.tabs.addTab(self.results_tab, "Результаты")
        self.tabs.addTab(self.video_library_tab, "Видео")
        
        layout.addWidget(self.tabs)
    
    def closeEvent(self, event):
        if self.monitoring_tab.is_monitoring:
            self.monitoring_tab.stop_monitoring()
        if self.video_tab.is_recording:
            self.video_tab.stop_recording()
        eye_tracker.stop()
        try:
            brain_bit_controller.stop_all()
        except:
            pass
        event.accept()


def main():
    # Создаем папку для видео при запуске
    ensure_videos_dir()
    
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
