from PyQt5.QtWidgets import (
    QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QScrollArea, QFrame, QSizePolicy, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from story_graph import StoryGraph
import settings
from gui_style import style
from StoryObject import StoryObject

class MainWindow(QWidget):
    storyRequested = pyqtSignal(StoryObject)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Story Generator")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(style)
        self.current_story = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.create_left_panel()
        self.create_right_panel()
        
        splitter.addWidget(self.left_container)
        splitter.addWidget(self.right_container)
        splitter.setSizes([450, 1150])
        
        main_layout.addWidget(splitter)

    def create_left_panel(self):
        self.left_container = QFrame()
        self.left_container.setObjectName("leftContainer")
        self.left_container.setMinimumWidth(400)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        left_layout = QVBoxLayout(content_widget)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)
        left_layout.setAlignment(Qt.AlignTop)

        left_layout.addWidget(QLabel("Game Story Generator", objectName="header"))

        self.desc_input = self._create_labeled_widget(QTextEdit, "Описание истории:", 150)
        self.genre_input = self._create_labeled_widget(QTextEdit, "Жанр:", 80)
        self.genre_input.widget.setText("RPG")
        self.heroes_input = self._create_labeled_widget(QTextEdit, "Персонажи (через точку с запятой):", 80)

        self.mood_combo = self._create_labeled_combo("Настроение:", settings.MOODS)

        for widget in [self.desc_input, self.genre_input, self.heroes_input,
                       self.mood_combo]:
            left_layout.addWidget(widget)
        
        left_layout.addStretch()

        self.generate_btn = QPushButton("Сгенерировать историю", objectName="actionButton")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.clicked.connect(self.on_generate_button_clicked)
        left_layout.addWidget(self.generate_btn)
        
        scroll_area.setWidget(content_widget)
        main_left_layout = QVBoxLayout(self.left_container)
        main_left_layout.addWidget(scroll_area)
        main_left_layout.setContentsMargins(0,0,0,0)


    def create_right_panel(self):
        self.right_container = QFrame()
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Схема сюжета", objectName="graphTitle"))
        header_layout.addStretch()
        self.info_label = QLabel("Заполните параметры и сгенерируйте историю.", objectName="infoLabel")
        header_layout.addWidget(self.info_label)
        
        self.graph_canvas = StoryGraph()
        
        footer_layout = QHBoxLayout()
        self.export_btn = QPushButton("Экспорт в JSON", objectName="actionButton")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_story)
        footer_layout.addWidget(self.export_btn)
        footer_layout.addStretch()
        self.stats_label = QLabel("Статистика: ожидание...", objectName="statsLabel")
        footer_layout.addWidget(self.stats_label)
        
        right_layout.addLayout(header_layout)
        right_layout.addWidget(self.graph_canvas, 1)
        right_layout.addLayout(footer_layout)
        
    def _create_labeled_widget(self, widget_class, label_text, height=None):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(QLabel(label_text, objectName="inputLabel"))
        
        widget = widget_class()
        if height:
            widget.setMinimumHeight(height)
        
        container.widget = widget
        layout.addWidget(widget)
        return container

    def _create_labeled_combo(self, label_text, settings_dict):
        container = self._create_labeled_widget(QComboBox, label_text)
        combo = container.widget
        
        for item in settings_dict['options']:
            combo.addItem(item['name'], item['value'])
        
        default_index = combo.findData(settings_dict['default'])
        if default_index != -1:
            combo.setCurrentIndex(default_index)
            
        return container

    def on_generate_button_clicked(self):
        story_obj = StoryObject(
            description=self.desc_input.widget.toPlainText(),
            genre=self.genre_input.widget.toPlainText(),
            heroes=[h.strip() for h in self.heroes_input.widget.toPlainText().split(';')],
            mood=self.mood_combo.widget.currentData()
        )
        
        error_msg = story_obj.validate()
        if error_msg:
            self.show_message("Ошибка валидации", error_msg, QMessageBox.Warning)
            return

        self.set_ui_for_generation(True)
        self.storyRequested.emit(story_obj)

    def set_story_data(self, story_data):
        self.current_story = story_data
        self.graph_canvas.update_graph(story_data)
        self.info_label.setText(f"История сгенерирована.")
        self.stats_label.setText(self.graph_canvas.get_graph_statistics())
        self.export_btn.setEnabled(True)
        self.set_ui_for_generation(False)

    def handle_generation_error(self, message):
        self.show_message("Ошибка генерации", message, QMessageBox.Critical)
        self.graph_canvas.draw_empty_graph(f"Ошибка:\n{message}")
        self.info_label.setText("Произошла ошибка.")
        self.stats_label.setText("Статистика: ошибка")
        self.set_ui_for_generation(False)

    def set_ui_for_generation(self, is_generating):
        self.generate_btn.setEnabled(not is_generating)
        self.generate_btn.setText("Генерация..." if is_generating else "Сгенерировать историю")
        if is_generating:
            self.info_label.setText("Идёт генерация, пожалуйста, подождите...")
            self.graph_canvas.draw_empty_graph("Генерация схемы сюжета...")

    def export_story(self):
        if not self.current_story: return
        
        from PyQt5.QtWidgets import QFileDialog
        import json

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить историю", "story.json", "JSON (*.json)")
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_story, f, ensure_ascii=False, indent=2)
                self.show_message("Экспорт", "История успешно сохранена.", QMessageBox.Information)
            except Exception as e:
                self.show_message("Ошибка экспорта", f"Не удалось сохранить файл: {e}", QMessageBox.Critical)

    def show_message(self, title, text, icon):
        msg_box = QMessageBox(icon, title, text, QMessageBox.Ok, self)
        msg_box.exec_()