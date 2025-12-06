"""
Пользовательские виджеты для BrainBit Monitor
"""
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel


class MetricCard(QFrame):
    """Красивая карточка для отображения метрики"""
    
    SIZE_LARGE = "large"
    SIZE_SMALL = "small"
    
    def __init__(self, title: str, initial_value: str = "—", color: str = "#58a6ff", size: str = "large"):
        super().__init__()
        self.setProperty("class", "card")
        self.color = color
        self.size = size
        
        if size == self.SIZE_SMALL:
            self.value_font_size = 14
            self.title_font_size = 8
            self.setFixedWidth(90)
            self.setFixedHeight(50)
        else:
            self.value_font_size = 22
            self.title_font_size = 9
            self.setMinimumWidth(100)
            self.setFixedHeight(70)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 6, 10, 6)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: #8b949e; font-size: {self.title_font_size}px; font-weight: 500;"
        )
        
        self.value_label = QLabel(initial_value)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: {self.value_font_size}px; font-weight: 700;"
        )
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
    
    def set_value(self, value: str):
        self.value_label.setText(value)
    
    def set_color(self, color: str):
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: {self.value_font_size}px; font-weight: 700;"
        )


class ResistCard(QFrame):
    """Компактная карточка для отображения состояния электрода"""
    
    def __init__(self, title: str, initial_value: str = "—"):
        super().__init__()
        self.setProperty("class", "card")
        self.setMinimumWidth(90)
        self.setMaximumWidth(130)
        self.setMinimumHeight(60)
        self.setMaximumHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 6, 10, 6)
        
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "color: #8b949e; font-size: 12px; font-weight: 600;"
        )
        
        self.value_label = QLabel(initial_value)
        self.value_label.setStyleSheet(
            "color: #8b949e; font-size: 14px; font-weight: 700;"
        )
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
    
    def set_status(self, is_normal: bool):
        if is_normal:
            self.value_label.setText("✓ OK")
            self.value_label.setStyleSheet(
                "color: #3fb950; font-size: 14px; font-weight: 700;"
            )
        else:
            self.value_label.setText("✗ Плохо")
            self.value_label.setStyleSheet(
                "color: #f85149; font-size: 14px; font-weight: 700;"
            )
    
    def reset(self):
        self.value_label.setText("—")
        self.value_label.setStyleSheet(
            "color: #8b949e; font-size: 14px; font-weight: 700;"
        )

