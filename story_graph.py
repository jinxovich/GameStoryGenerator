from PyQt5.QtWidgets import QSizePolicy, QToolTip
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QApplication
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import numpy as np
import re # Import regular expressions module

class SceneDetailDialog(QDialog):
    """Диалоговое окно для отображения деталей сцены"""
    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.setWindowTitle(f"Сцена: {scene_data.get('title', 'Без названия')}")
        self.setWindowModality(0) # Qt.NonModal - позволяет взаимодействовать с основным окном
        self.resize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d44;
                color: #ffffff;
                border: 2px solid #4a4a6a;
                border-radius: 10px;
            }
            QTextEdit {
                background-color: #1e1e2d;
                color: #e0e0ff;
                border: 1px solid #4a4a6a;
                border-radius: 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                padding: 10px;
            }
            QPushButton {
                background-color: #4dabf7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3b99e6;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок сцены
        title_text = self.scene_data.get('title', 'Без названия')
        scene_id = self.scene_data.get('id', 'N/A')

        # Формируем полный текст для отображения
        scene_text = f"<b>ID Сцены:</b> {scene_id}<br>"
        scene_text += f"<b>Название:</b> {title_text}\n\n"
        scene_text += f"<b>Описание:</b>\n{self.scene_data.get('description', 'Описание отсутствует')}\n\n"

        choices = self.scene_data.get('choices', [])
        if choices:
            scene_text += "<b>Выборы:</b>\n"
            for i, choice in enumerate(choices, 1):
                scene_text += f"{i}. {choice.get('text', '...')} "
                next_scene_id = choice.get('next_scene_id')
                if next_scene_id:
                    scene_text += f"(→ ID: {next_scene_id})"
                scene_text += "\n"
        else:
            scene_text += "<b>Выборы:</b> Это конечная сцена (концовка).\n"

        # Поле для отображения текста
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(scene_text) # Используем setHtml для форматирования
        self.text_edit.setStyleSheet(self.text_edit.styleSheet() + """
            QTextEdit {
                background-color: #1e1e2d;
                color: #e0e0ff;
                border: 1px solid #4a4a6a;
                border-radius: 5px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_edit)

        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept) # accept() закроет диалог
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)


class StoryGraph(FigureCanvas):

    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        super().__init__(self.fig)
        self.setStyleSheet("background-color: transparent;")
        self.G = nx.DiGraph()
        self.story_data = {}
        self.edge_labels = {}  # Словарь для хранения подписей рёбер
        self._setup_colormap()
        self.draw_graph()
        
        # Подключаем событие клика мыши
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Хранилище для позиций узлов в пикселях экрана
        self.node_screen_positions = {}

    def _setup_colormap(self):
        colors = ["#4facfe", "#00f2fe", "#a6c1ee", "#fbc2eb", "#ff9a9e"]
        self.cmap = LinearSegmentedColormap.from_list("custom", colors)

    def draw_graph(self):
        self.ax.clear()
        
        if self.G.number_of_nodes() > 0:
            try:
                pos = self._create_tree_layout()
            except Exception as e:
                print(f"Ошибка при создании layout: {e}")
                pos = nx.spring_layout(self.G, seed=42, k=1, iterations=50)

            # Создаем список узлов для сохранения порядка
            nodes_list = list(self.G.nodes())
            
            # Определяем цвета узлов
            node_colors = []
            for node in nodes_list:
                scene = self._find_scene_by_id(node)
                is_ending = self.G.out_degree(node) == 0
                if scene and (scene.get('is_ending', False) or is_ending):
                    node_colors.append('#ff6b6b')  # Красный для концовок
                elif node == self._get_start_scene():
                    node_colors.append('#51cf66')  # Зелёный для старта
                else:
                    node_colors.append('#4dabf7')  # Синий для обычных сцен
            
            # Рисуем узлы
            nx.draw_networkx_nodes(
                self.G, pos, ax=self.ax,
                node_size=2500,
                node_color=node_colors,
                edgecolors="#ffffff",
                linewidths=2,
                alpha=0.9
            )
            
            # Рисуем рёбра
            nx.draw_networkx_edges(
                self.G, pos, ax=self.ax,
                width=2,
                edge_color="#aaaaaa",
                alpha=0.8,
                arrowsize=25,
                arrowstyle='-|>',
                connectionstyle='arc3,rad=0.05',
                min_source_margin=20,
                min_target_margin=20
            )
            
            # Подписи узлов (отображение только номера сцены)
            labels = {}
            for node in nodes_list:
                # Извлекаем только число из ID сцены
                match = re.search(r'\d+', str(node))
                if match:
                    labels[node] = match.group(0) # Используем найденный номер
                else:
                    labels[node] = str(node) # Если номера нет, используем ID целиком
                
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=11,
                font_color="#ffffff",
                font_family="Segoe UI",
                font_weight="bold",
                horizontalalignment='center'
            )
            
            # Подписи рёбер
            if self.edge_labels:
                self._draw_edge_labels(pos)
            
            self.node_positions = pos
            self._update_node_screen_positions(pos)
            
        else:
            self._draw_empty_message()
            
        self._style_axes()
        self._add_legend()
        self.draw()

    def _update_node_screen_positions(self, pos):
        """Обновляет позиции узлов в экранных координатах"""
        self.node_screen_positions = {}
        for node, (x, y) in pos.items():
            screen_x, screen_y = self.ax.transData.transform((x, y))
            self.node_screen_positions[node] = (screen_x, screen_y)

    def _draw_empty_message(self):
        """Рисует сообщение для пустого графа"""
        self.ax.text(0.5, 0.5, 
                    'Граф истории будет отображен здесь\n\nГенерируйте историю для просмотра схемы сюжета', 
                    horizontalalignment='center', 
                    verticalalignment='center',
                    transform=self.ax.transAxes, 
                    fontsize=14, 
                    color='white',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='#25253d', alpha=0.8))

    def _style_axes(self):
        """Стилизует оси графа"""
        self.ax.set_facecolor('#1e1e2d')
        self.fig.patch.set_facecolor('#1e1e2d')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.axis('off')
        for spine in self.ax.spines.values():
            spine.set_visible(False)

    def _create_tree_layout(self):
        """Создаёт древовидный layout с автоматическим масштабированием"""
        try:
            start_scene = self._get_start_scene()
            if not start_scene or start_scene not in self.G.nodes():
                roots = [n for n in self.G.nodes() if self.G.in_degree(n) == 0]
                start_scene = roots[0] if roots else list(self.G.nodes())[0]
            
            # Создаем уровни с помощью BFS
            levels = {}
            queue = [(start_scene, 0)]
            visited = {start_scene}
            max_level = 0
            
            while queue:
                node, level = queue.pop(0)
                levels[node] = level
                max_level = max(max_level, level)
                
                successors = list(self.G.successors(node))
                for successor in successors:
                    if successor not in visited:
                        visited.add(successor)
                        queue.append((successor, level + 1))
            
            # Убеждаемся, что все узлы имеют уровень
            all_nodes = set(self.G.nodes())
            nodes_with_level = set(levels.keys())
            
            # Обрабатываем узлы, которые могли быть недостижимы из-за циклов или несвязности
            for node in all_nodes:
                if node not in nodes_with_level:
                    # Попробуем найти уровень через предшественников
                    try:
                        pred_levels = [levels[p] for p in self.G.predecessors(node) if p in levels]
                        if pred_levels:
                           levels[node] = max(pred_levels) + 1
                        else:
                           levels[node] = 0 # Если нет достижимых предков, считаем корнем
                    except (nx.NetworkXError, KeyError):
                        levels[node] = 0
            
            # Группируем узлы по уровням
            level_groups = {}
            for node, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(node)
            
            # Вычисляем позиции
            pos = {}
            y_spacing = 2.0
            
            max_nodes_in_level = max(len(nodes) for nodes in level_groups.values()) if level_groups else 1
            x_spacing = max_nodes_in_level * 1.2 # Динамический отступ по X
            
            for level, nodes_at_level in level_groups.items():
                num_nodes = len(nodes_at_level)
                y_position = -level * y_spacing
                if num_nodes > 1:
                    x_positions = np.linspace(-x_spacing, x_spacing, num_nodes)
                else:
                    x_positions = [0]
                
                for i, node in enumerate(nodes_at_level):
                    pos[node] = (x_positions[i], y_position)

            pos = self._optimize_positions(pos, levels, level_groups)
            
            return pos
            
        except Exception as e:
            print(f"Ошибка в tree layout: {e}")
            return nx.spring_layout(self.G, seed=42, k=2, iterations=50)

    def _optimize_positions(self, pos, levels, level_groups):
        """Оптимизирует позиции узлов для уменьшения пересечений рёбер"""
        try:
            # Для каждого уровня (кроме первого) пытаемся оптимизировать позиции
            for level in sorted(level_groups.keys())[1:]:
                nodes_at_level = level_groups[level]
                
                node_parent_centers = {}
                for node in nodes_at_level:
                    parents = list(self.G.predecessors(node))
                    if parents:
                        parent_x_coords = [pos[p][0] for p in parents if p in pos]
                        node_parent_centers[node] = np.mean(parent_x_coords) if parent_x_coords else 0
                    else:
                        node_parent_centers[node] = pos[node][0]

                # Сортируем узлы по "центру масс" их родителей
                sorted_nodes = sorted(nodes_at_level, key=lambda n: node_parent_centers.get(n, 0))
                
                # Перераспределяем X позиции на основе нового порядка
                if len(sorted_nodes) > 1:
                    current_x_coords = sorted([pos[n][0] for n in nodes_at_level])
                    y_pos = pos[nodes_at_level[0]][1]
                    for i, node in enumerate(sorted_nodes):
                        pos[node] = (current_x_coords[i], y_pos)
            
        except Exception as e:
            print(f"Ошибка при оптимизации позиций: {e}")
        
        return pos

    def _draw_edge_labels(self, pos):
        """Рисует подписи рёбер с улучшенным позиционированием"""
        # Эта функция остается без изменений
        edge_label_positions = {}
        processed_edges_per_node = {}
        sorted_edges = sorted(list(self.G.edges()))

        for (node1, node2) in sorted_edges:
            label = self.edge_labels.get((node1, node2), '')
            if node1 in pos and node2 in pos and label:
                x1, y1 = pos[node1]
                x2, y2 = pos[node2] 
                
                if node1 not in processed_edges_per_node:
                    processed_edges_per_node[node1] = 0
                
                t_along_edge = 0.3
                edge_x = x1 + (x2 - x1) * t_along_edge
                edge_y = y1 + (y2 - y1) * t_along_edge
                
                edge_dx, edge_dy = x2 - x1, y2 - y1
                length = np.sqrt(edge_dx**2 + edge_dy**2)
                if length > 0:
                    norm_dx, norm_dy = -edge_dy / length, edge_dx / length
                else:
                    norm_dx, norm_dy = 0, 1
                    
                offset_magnitude = 0.2 + (processed_edges_per_node[node1] * 0.1)
                edge_x += offset_magnitude * norm_dx
                edge_y += offset_magnitude * norm_dy

                edge_label_positions[(node1, node2)] = (edge_x, edge_y)
                processed_edges_per_node[node1] += 1

        for (node1, node2), (x, y) in edge_label_positions.items():
            label = self.edge_labels.get((node1, node2), '')
            if label:
                self.ax.text(x, y, label, fontsize=7, color='#FFD700', weight='bold', ha='center', va='center',
                           bbox=dict(boxstyle="round,pad=0.25", facecolor='#3a3a5a', edgecolor='none', alpha=0.85),
                           zorder=4, clip_on=True)

    def _add_legend(self):
        """Добавляет легенду к графу"""
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#51cf66', 
                      markersize=14, label='Начало', markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4dabf7', 
                      markersize=10, label='Сцена', markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff6b6b', 
                      markersize=12, label='Концовка', markeredgecolor='white', markeredgewidth=2)
        ]
        
        legend = self.ax.legend(handles=legend_elements, loc='upper right', 
                               frameon=True, fancybox=True, shadow=True,
                               fontsize=10)
        legend.get_frame().set_facecolor('#25253d')
        legend.get_frame().set_alpha(0.9)
        for text in legend.get_texts():
            text.set_color('#ffffff')

    def update_graph_from_story(self, story_data):
        """Обновляет граф на основе данных истории"""
        self.story_data = story_data
        self.G.clear()
        self.edge_labels.clear()
        
        try:
            scenes = story_data.get('scenes', [])
            if not scenes:
                self.draw_graph()
                return

            scene_ids = {s.get('id') for s in scenes if s.get('id')}
            
            for scene in scenes:
                scene_id = scene.get('id')
                if scene_id:
                    self.G.add_node(scene_id)
            
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                
                for i, choice in enumerate(choices):
                    next_scene = choice.get('next_scene_id', '')
                    choice_text = f"{i+1}. {choice.get('text', '')[:20]}..." # Сокращаем текст выбора
                    
                    if next_scene and self.G.has_node(next_scene):
                        self.G.add_edge(scene_id, next_scene)
                        self.edge_labels[(scene_id, next_scene)] = choice_text
            
            self.draw_graph()
            
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")

    def _get_start_scene(self):
        """Возвращает ID стартовой сцены"""
        if self.story_data.get('start_scene'):
            return self.story_data['start_scene']
        
        # Если start_scene не указан, ищем узел без входящих рёбер
        if self.G.nodes():
            start_nodes = [n for n, d in self.G.in_degree() if d == 0]
            if start_nodes:
                return start_nodes[0]
        
        # Если ничего не найдено, возвращаем первую сцену из списка
        if self.story_data.get('scenes'):
             return self.story_data['scenes'][0].get('id', '')
        return ''


    def _find_scene_by_id(self, scene_id):
        """Находит сцену по ID"""
        scenes = self.story_data.get('scenes', [])
        for scene in scenes:
            if scene.get('id') == scene_id:
                return scene
        return None
        
    def on_click(self, event):
        """Обработчик клика мыши - открывает диалог с деталями сцены"""
        if event.inaxes != self.ax:
            return
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        mouse_x, mouse_y = event.x, event.y
        clicked_node = None
        # Порог клика (в квадрате для эффективности)
        min_dist_sq = 25**2
        
        # Находим ближайший узел к точке клика
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            dist_sq = (screen_x - mouse_x)**2 + (screen_y - mouse_y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                clicked_node = node
                
        # Если узел найден, открываем диалог
        if clicked_node is not None:
            scene = self._find_scene_by_id(clicked_node)
            if scene:
                # Открываем диалоговое окно
                dialog = SceneDetailDialog(scene, parent=self)
                dialog.show()

    def get_graph_statistics(self):
        """Возвращает статистику графа"""
        if not self.G.nodes():
            return "Граф пуст"
        
        stats = {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges(),
            'endings': len([n for n, d in self.G.out_degree() if d == 0]),
            'start_nodes': len([n for n, d in self.G.in_degree() if d == 0]),
            'max_choices': max((d for n, d in self.G.out_degree()), default=0)
        }
        
        return f"""Статистика графа:
                    • Сцен: {stats['nodes']}
                    • Переходов: {stats['edges']}
                    • Концовок: {stats['endings']}
                    • Стартовых сцен: {stats['start_nodes']}
                    • Макс. выборов в сцене: {stats['max_choices']}"""