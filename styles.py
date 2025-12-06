# ==================== MODERN DARK THEME ====================
STYLESHEET = """
QMainWindow {
    background-color: #0d1117;
}

QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #30363d;
    border-radius: 8px;
    background-color: #161b22;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #21262d;
    color: #8b949e;
    padding: 12px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #161b22;
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    background-color: #30363d;
    color: #e6edf3;
}

QPushButton {
    background-color: #238636;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #2ea043;
}

QPushButton:pressed {
    background-color: #196c2e;
}

QPushButton:disabled {
    background-color: #21262d;
    color: #484f58;
}

QPushButton[class="danger"] {
    background-color: #da3633;
}

QPushButton[class="danger"]:hover {
    background-color: #f85149;
}

QPushButton[class="secondary"] {
    background-color: #21262d;
    border: 1px solid #30363d;
}

QPushButton[class="secondary"]:hover {
    background-color: #30363d;
    border-color: #8b949e;
}

QLineEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 14px;
    color: #e6edf3;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #58a6ff;
    outline: none;
}

QLineEdit::placeholder {
    color: #484f58;
}

QListWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px;
}

QListWidget::item {
    padding: 12px;
    border-radius: 6px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}

QListWidget::item:hover:!selected {
    background-color: #21262d;
}

QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    border-radius: 6px;
}

QGroupBox {
    font-weight: 600;
    font-size: 14px;
    border: 1px solid #30363d;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    background-color: #161b22;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #58a6ff;
}

QLabel {
    color: #e6edf3;
}

QLabel[class="header"] {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}

QLabel[class="subheader"] {
    font-size: 14px;
    color: #8b949e;
}

QLabel[class="value"] {
    font-size: 28px;
    font-weight: 700;
    color: #58a6ff;
}

QLabel[class="value-green"] {
    font-size: 28px;
    font-weight: 700;
    color: #3fb950;
}

QLabel[class="value-orange"] {
    font-size: 28px;
    font-weight: 700;
    color: #d29922;
}

QLabel[class="status-good"] {
    color: #3fb950;
    font-weight: 600;
}

QLabel[class="status-bad"] {
    color: #f85149;
    font-weight: 600;
}

QFrame[class="card"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px;
}

QFrame[class="divider"] {
    background-color: #30363d;
    max-height: 1px;
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background-color: #21262d;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #58a6ff;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::sub-page:horizontal {
    background-color: #58a6ff;
    border-radius: 3px;
}

QComboBox {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e6edf3;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b949e;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    selection-background-color: #1f6feb;
}

QScrollBar:vertical {
    background-color: #0d1117;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""

