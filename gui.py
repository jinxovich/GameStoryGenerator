from PyQt5.QtWidgets import (
    QWidget, QLabel, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QScrollArea, QCheckBox,
    QFrame, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPainter, QLinearGradient, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
from StoryObject import StoryObject
import settings
import ai
import asyncio
import json

class StoryGeneratorWorker(QThread):
    """Отдельный поток для генерации истории"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, story_object):
        super().__init__()
        self.story_object = story_object

    def run(self):
        """Запускаем генерацию в отдельном потоке"""
        try:
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем асинхронную генерацию
            result = loop.run_until_complete(ai.get(self.story_object))
            
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Не удалось получить ответ от AI")
                
        except Exception as e:
            self.error.emit(f"Ошибка при генерации: {str(e)}")
        finally:
            # Закрываем loop
            try:
                loop.close()
            except:
                pass

class GradientButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(200)
        self._color1 = QColor("#4facfe")
        self._color2 = QColor("#00f2fe")
        self._pressed_color1 = QColor("#3a7bd5")
        self._pressed_color2 = QColor("#00d2ff")
        self._current_color1 = self._color1
        self._current_color2 = self._color2
        self._text_color = QColor("#ffffff")
        self.setMinimumHeight(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        self.setFont(font)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, self._current_color1)
        gradient.setColorAt(1, self._current_color2)
        
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        painter.setPen(self._text_color)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

    def enterEvent(self, event):
        self._animate_hover(True)

    def leaveEvent(self, event):
        self._animate_hover(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._current_color1 = self._pressed_color1
            self._current_color2 = self._pressed_color2
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._current_color1 = self._color1
        self._current_color2 = self._color2
        self.update()
        super().mouseReleaseEvent(event)

    def _animate_hover(self, hover):
        self._animation.stop()
        if hover:
            new_rect = QRect(self.x()-2, self.y()-2, self.width()+4, self.height()+4)
            self._animation.setEasingCurve(QEasingCurve.OutBack)
            self._animation.setEndValue(new_rect)
            self._animation.start()
        else:
            self._animation.setEasingCurve(QEasingCurve.InOutQuad)
            self._animation.setEndValue(QRect(self.x()+2, self.y()+2, self.width()-4, self.height()-4))
            self._animation.start()


class GraphCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        super().__init__(self.fig)
        self.setStyleSheet("background-color: transparent;")
        self.G = nx.DiGraph()  # Используем направленный граф для историй
        self._setup_colormap()
        self.draw_graph()

    def _setup_colormap(self):
        colors = ["#4facfe", "#00f2fe", "#a6c1ee", "#fbc2eb", "#ff9a9e"]
        self.cmap = LinearSegmentedColormap.from_list("custom", colors)

    def draw_graph(self):
        self.ax.clear()
        if self.G.number_of_nodes() > 0:
            # Используем иерархический layout для лучшего отображения сюжета
            try:
                pos = nx.spring_layout(self.G, seed=42, k=1, iterations=50)
            except:
                pos = nx.random_layout(self.G)
                
            node_colors = [self.cmap(i/max(len(self.G.nodes()), 1)) for i in range(len(self.G.nodes()))]
            
            # Рисуем узлы
            nx.draw_networkx_nodes(
                self.G, pos, ax=self.ax,
                node_size=2000,
                node_color=node_colors,
                edgecolors="#ffffff",
                linewidths=2
            )
            
            # Рисуем рёбра
            nx.draw_networkx_edges(
                self.G, pos, ax=self.ax,
                width=2,
                edge_color="#aaaaaa",
                alpha=0.8,
                arrowsize=15,
                arrowstyle='->'
            )
            
            # Рисуем подписи (короткие версии названий сцен)
            labels = {}
            for node in self.G.nodes():
                # Сокращаем длинные названия
                label = str(node)
                if len(label) > 10:
                    label = label[:8] + "..."
                labels[node] = label
                
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=8,
                font_color="#ffffff",
                font_family="Segoe UI",
                font_weight="bold"
            )

        self.ax.set_facecolor('#1e1e2d')
        self.fig.patch.set_facecolor('#1e1e2d')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.draw()

    def update_graph_from_story(self, story_data):
        """Обновляет граф на основе данных истории"""
        self.G.clear()
        
        try:
            scenes = story_data.get('scenes', [])
            
            # Добавляем узлы (сцены)
            for scene in scenes:
                scene_id = scene.get('id', '')
                self.G.add_node(scene_id)
            
            # Добавляем рёбра (переходы между сценами)
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                
                for choice in choices:
                    next_scene = choice.get('next_scene_id', '')
                    if next_scene and next_scene in [s.get('id') for s in scenes]:
                        self.G.add_edge(scene_id, next_scene)
            
            self.draw_graph()
            
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")

    def update_graph(self, nodes, edges):
        """Альтернативный метод для обновления графа"""
        self.G.clear()
        self.G.add_nodes_from(nodes)
        self.G.add_edges_from(edges)
        self.draw_graph()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Story Generator")
        self.setGeometry(100, 100, 1400, 800)
        self.setStyleSheet(self.dark_theme_stylesheet())
        self.current_story = None
        self.worker = None
        self.init_ui()
        self.setup_animations()

    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_left_panel()
        self.create_right_panel()

        main_layout.addWidget(self.left_container, 1)
        main_layout.addWidget(self.right_container, 2)
        self.setLayout(main_layout)

    def create_left_panel(self):
        self.left_container = QFrame()
        self.left_container.setObjectName("leftContainer")
        
        left_main_layout = QVBoxLayout()
        left_main_layout.setContentsMargins(0, 0, 0, 0)
        left_main_layout.setSpacing(0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a45;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4facfe;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(25, 25, 25, 25)
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignTop)

        header = QLabel("Game Story Generator")
        header.setObjectName("header")
        left_layout.addWidget(header)

        self.desc_input = self.labeled_textedit("Описание истории:", 150)
        self.heroes_input = self.labeled_textedit("Персонажей (через запятую):", 120)
        self.genre_input = self.labeled_textedit("Жанр:", 100)

        self.narrative_style_combo = self.labeled_combobox("Стиль повествования:", settings.NARRATIVE_STYLES)
        self.mood_combo = self.labeled_combobox("Настроение:", settings.MOODS)
        self.theme_combo = self.labeled_combobox("Тема:", settings.THEMES)
        self.conflict_combo = self.labeled_combobox("Конфликт:", settings.CONFLICTS)    

        self.adult_checkbox = QCheckBox("Взрослый контент")
        self.adult_checkbox.setCursor(Qt.PointingHandCursor)
        
        self.generate_btn = GradientButton("Сгенерировать")
        self.generate_btn.clicked.connect(self.generate_story)

        for widget in [
            self.desc_input, self.heroes_input, self.genre_input,
            self.narrative_style_combo, self.mood_combo,
            self.theme_combo, self.conflict_combo,
            self.adult_checkbox, self.generate_btn
        ]:
            left_layout.addWidget(widget)

        left_layout.addStretch(1)
        
        scroll_content.setLayout(left_layout)
        self.scroll_area.setWidget(scroll_content)
        
        left_main_layout.addWidget(self.scroll_area)
        self.left_container.setLayout(left_main_layout)

    def create_right_panel(self):
        self.right_container = QFrame()
        self.right_container.setObjectName("rightContainer")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(10)

        # Заголовок для графа
        graph_title = QLabel("Схема сюжета")
        graph_title.setObjectName("graphTitle")
        graph_title.setAlignment(Qt.AlignCenter)
        
        graph_frame = QFrame()
        graph_frame.setObjectName("graphFrame")
        graph_layout = QVBoxLayout()
        graph_layout.setContentsMargins(10, 10, 10, 10)
        
        self.graph_canvas = GraphCanvas()
        self.graph_canvas.setMinimumSize(600, 500)
        graph_layout.addWidget(self.graph_canvas)
        graph_frame.setLayout(graph_layout)
        
        # Информация о текущей истории
        self.story_info = QLabel("Сгенерируйте историю для отображения схемы сюжета")
        self.story_info.setObjectName("storyInfo")
        self.story_info.setWordWrap(True)
        self.story_info.setAlignment(Qt.AlignCenter)
        
        right_layout.addWidget(graph_title)
        right_layout.addWidget(graph_frame, 1)
        right_layout.addWidget(self.story_info)
        self.right_container.setLayout(right_layout)

    def labeled_textedit(self, label_text, height):
        container = QWidget()
        container.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("inputLabel")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        edit = QTextEdit()
        edit.setMinimumHeight(height)
        edit.setObjectName("textEdit")
        edit.setFont(QFont("Segoe UI", 12))
        edit.setPlaceholderText(f"Введите {label_text.lower()}")
        
        layout.addWidget(label)
        layout.addWidget(edit)
        container.setLayout(layout)
        container.edit = edit
        return container

    def labeled_combobox(self, label_text, items):
        container = QWidget()
        container.setMinimumWidth(350)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        label = QLabel(label_text)
        label.setObjectName("inputLabel")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        combo = QComboBox()
        combo.addItems(items)
        combo.setObjectName("comboBox")
        combo.setCursor(Qt.PointingHandCursor)
        combo.setFont(QFont("Segoe UI", 12))
        combo.setMinimumHeight(40)
        
        layout.addWidget(label)
        layout.addWidget(combo)
        container.setLayout(layout)
        container.combo = combo
        return container

    def setup_animations(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def resizeEvent(self, event):
        left_width = max(400, self.width() // 3)
        self.left_container.setMinimumWidth(left_width)
        self.left_container.setMaximumWidth(left_width)
        super().resizeEvent(event)

    def generate_story(self):
        # Проверяем заполненность полей
        desc = self.desc_input.edit.toPlainText().strip()
        heroes_text = self.heroes_input.edit.toPlainText().strip()
        genre = self.genre_input.edit.toPlainText().strip()
        
        if not desc or not heroes_text or not genre:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните основные поля: описание, персонажи и жанр")
            return

        heroes = [h.strip() for h in heroes_text.split(',') if h.strip()]
        narrative_style = self.narrative_style_combo.combo.currentText()
        mood = self.mood_combo.combo.currentText()
        theme = self.theme_combo.combo.currentText()
        conflict = self.conflict_combo.combo.currentText()
        is_adult = self.adult_checkbox.isChecked()

        story_object = StoryObject(
            description=desc,
            genre=genre,
            heroes=heroes,
            narrative_style=narrative_style,
            mood=mood,
            theme=theme,
            conflict=conflict,
            adult=is_adult
        )

        # Отключаем кнопку и показываем процесс генерации
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Генерация...")
        self.story_info.setText("Генерируется история...")
        
        # Создаем и запускаем worker thread
        self.worker = StoryGeneratorWorker(story_object)
        self.worker.finished.connect(self.handle_story_generated)
        self.worker.error.connect(self.handle_generation_error)
        self.worker.start()

    def handle_story_generated(self, result):
        """Обрабатываем успешную генерацию истории"""
        try:
            print("Сгенерированная история:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            self.current_story = result
            
            # Обновляем граф
            self.graph_canvas.update_graph_from_story(result)
            
            # Обновляем информацию
            story_title = result.get('title', 'Без названия')
            story_desc = result.get('description', 'Описание отсутствует')
            scenes_count = len(result.get('scenes', []))
            
            info_text = f"<b>{story_title}</b><br><br>{story_desc}<br><br>Количество сцен: {scenes_count}"
            self.story_info.setText(info_text)
            
        except Exception as e:
            self.handle_generation_error(f"Ошибка при обработке результата: {str(e)}")
        finally:
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Сгенерировать")

    def handle_generation_error(self, error_msg):
        """Обрабатываем ошибки генерации"""
        print(f"Ошибка генерации: {error_msg}")
        
        QMessageBox.critical(self, "Ошибка генерации", f"Произошла ошибка при генерации истории:\n\n{error_msg}")
        
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Сгенерировать")
        self.story_info.setText("Произошла ошибка при генерации. Попробуйте еще раз.")

    def closeEvent(self, event):
        """Корректно завершаем работу при закрытии приложения"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()

    def dark_theme_stylesheet(self):
        return """
            QWidget {
                background-color: #1e1e2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            #leftContainer {
                background-color: #25253d;
                border-right: 1px solid #3a3a5a;
                min-width: 400px;
            }
            
            #rightContainer {
                background-color: #1e1e2d;
            }
            
            #header {
                font-size: 32px;
                font-weight: bold;
                color: #ffffff;
                padding-bottom: 15px;
                border-bottom: 2px solid #4facfe;
            }
            
            #graphTitle {
                font-size: 18px;
                font-weight: bold;
                color: #a6c1ee;
                padding: 10px;
            }
            
            #storyInfo {
                font-size: 18px;
                color: #a6c1ee;
                padding: 15px;
                background-color: #25253d;
                border-radius: 8px;
                margin-top: 10px;
            }
            
            #inputLabel {
                font-size: 18px;
                font-weight: bold;
                color: #a6c1ee;
                margin-bottom: 5px;
            }
            
            #textEdit {
                background-color: #2a2a45;
                border: 2px solid #3a3a5a;
                border-radius: 8px;
                color: #ffffff;
                padding: 12px;
                font-size: 18px;
                selection-background-color: #4facfe;
                min-width: 350px;
            }
            
            #textEdit:focus {
                border: 2px solid #4facfe;
            }
            
            #comboBox {
                background-color: #2a2a45;
                border: 2px solid #3a3a5a;
                border-radius: 8px;
                color: #ffffff;
                padding: 8px;
                font-size: 18px;
                min-height: 40px;
                min-width: 350px;
            }
            
            #comboBox:hover {
                border: 2px solid #4facfe;
            }
            
            #comboBox::drop-down {
                border: none;
                width: 30px;
                padding-right: 5px;
            }
            
            #comboBox QAbstractItemView {
                background-color: #2a2a45;
                color: #ffffff;
                selection-background-color: #4facfe;
                selection-color: #ffffff;
                border: 2px solid #3a3a5a;
                font-size: 18px;
                padding: 8px;
                outline: none;
                min-width: 200px;
            }
            
            QCheckBox {
                spacing: 10px;
                font-size: 18px;
                color: #a6c1ee;
                padding: 5px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3a3a5a;
                border-radius: 5px;
                background-color: #2a2a45;
            }
            
            QCheckBox::indicator:hover {
                border: 2px solid #4facfe;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4facfe;
                border: 2px solid #4facfe;
            }
            
            #graphFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #25253d, stop:1 #1e1e2d);
                border-radius: 12px;
                border: none;
                min-width: 600px;
                min-height: 500px;
            }
            
            QMessageBox {
                background-color: #25253d;
                color: #ffffff;
            }
            
            QMessageBox QLabel {
                color: #ffffff;
            }
            
            QMessageBox QPushButton {
                background-color: #4facfe;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QMessageBox QPushButton:hover {
                background-color: #3a7bd5;
            }
        """