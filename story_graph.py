from PyQt5.QtWidgets import QSizePolicy, QToolTip
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import numpy as np
from textwrap import fill

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
        
        # Подключаем события мыши
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Хранилище для позиций узлов в пикселях экрана
        self.node_screen_positions = {}
        
        # Переменная для хранения последнего tooltip
        self.last_tooltip_node = None

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
                if scene and scene.get('is_ending', False):
                    node_colors.append('#ff6b6b')  # Красный для концовок
                elif node == self._get_start_scene():
                    node_colors.append('#51cf66')  # Зелёный для старта
                else:
                    node_colors.append('#4dabf7')  # Синий для обычных сцен
            
            # Рисуем узлы
            nx.draw_networkx_nodes(
                self.G, pos, ax=self.ax,
                node_size=3000,
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
            
            # Подписи узлов
            labels = {}
            for node in nodes_list:
                scene = self._find_scene_by_id(node)
                labels[node] = scene.get('description', 'Нет описания') if scene else "Неизвестно"
                
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=9,
                font_color="#ffffff",
                font_family="Segoe UI",
                font_weight="normal",
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
            visited = set()
            max_level = 0
            
            while queue:
                node, level = queue.pop(0)
                if node in visited:
                    continue
                    
                visited.add(node)
                levels[node] = level
                max_level = max(max_level, level)
                
                successors = list(self.G.successors(node))
                for successor in successors:
                    if successor not in visited:
                        queue.append((successor, level + 1))
            
            # Убеждаемся, что все узлы имеют уровень
            all_nodes = set(self.G.nodes())
            nodes_without_level = all_nodes - set(levels.keys())
            
            if nodes_without_level:
                for node in nodes_without_level:
                    predecessors = list(self.G.predecessors(node))
                    if predecessors:
                        pred_levels = [levels.get(pred, 0) for pred in predecessors]
                        levels[node] = max(pred_levels) + 1
                    else:
                        levels[node] = 0
                    max_level = max(max_level, levels[node])
            
            # Группируем узлы по уровням
            level_groups = {}
            for node, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(node)
            
            # Вычисляем позиции с учетом размеров текста
            pos = {}
            y_spacing = 2.0  # Базовое расстояние между уровнями
            
            for level in range(max_level + 1):
                nodes_at_level = level_groups.get(level, [])
                num_nodes = len(nodes_at_level)
                
                if num_nodes == 0:
                    continue
                
                # Y координата (сверху вниз)
                y_position = -level * y_spacing
                
                if num_nodes == 1:
                    pos[nodes_at_level[0]] = (0, y_position)
                else:
                    # Вычисляем суммарную ширину всех узлов на этом уровне
                    total_width = sum(2.0 for _ in nodes_at_level)  # Базовый отступ
                    
                    # Распределяем узлы с равными интервалами
                    for i, node in enumerate(nodes_at_level):
                        x_position = (i - (num_nodes - 1) / 2) * (total_width / num_nodes)
                        pos[node] = (x_position, y_position)
            
            # Оптимизируем позиции для минимизации пересечений
            pos = self._optimize_positions(pos, levels)
            
            return pos
            
        except Exception as e:
            print(f"Ошибка в tree layout: {e}")
            return nx.spring_layout(self.G, seed=42, k=2, iterations=50)

    def _optimize_positions(self, pos, levels):
        """Оптимизирует позиции узлов для уменьшения пересечений рёбер"""
        try:
            level_groups = {}
            for node, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(node)
            
            # Для каждого уровня (кроме первого) пытаемся оптимизировать позиции
            for level in sorted(level_groups.keys())[1:]:
                nodes_at_level = level_groups[level]
                if len(nodes_at_level) <= 1:
                    continue
                
                # Вычисляем "центр масс" родителей для каждого узла
                node_parent_centers = {}
                for node in nodes_at_level:
                    parents = list(self.G.predecessors(node))
                    if parents:
                        parent_x_coords = [pos[parent][0] for parent in parents if parent in pos]
                        if parent_x_coords:
                            node_parent_centers[node] = sum(parent_x_coords) / len(parent_x_coords)
                        else:
                            node_parent_centers[node] = 0
                    else:
                        node_parent_centers[node] = 0
                
                # Сортируем узлы по центру масс их родителей
                sorted_nodes = sorted(nodes_at_level, key=lambda n: node_parent_centers.get(n, 0))
                
                # Перераспределяем позиции
                num_nodes = len(sorted_nodes)
                if num_nodes > 0:
                    y_position = pos[sorted_nodes[0]][1]  # Сохраняем Y координату
                    
                    if num_nodes > 1:
                        total_width = min(num_nodes * 2.5, 12)
                        for i, node in enumerate(sorted_nodes):
                            x_position = (i - (num_nodes - 1) / 2) * (total_width / (num_nodes - 1))
                            pos[node] = (x_position, y_position)
            
        except Exception as e:
            print(f"Ошибка при оптимизации позиций: {e}")
        
        return pos

    def _draw_edge_labels(self, pos):
        """Рисует подписи рёбер с улучшенным позиционированием"""
        edge_label_positions = {}
        processed_edges_per_node = {}

        # Сортируем рёбра для предсказуемости
        sorted_edges = []
        for node1 in self.G.nodes():
             outgoing_edges = list(self.G.out_edges(node1))
             sorted_edges.extend(outgoing_edges)

        for (node1, node2) in sorted_edges:
            label = self.edge_labels.get((node1, node2), '')
            if node1 in pos and node2 in pos and label:
                x1, y1 = pos[node1]
                x2, y2 = pos[node2] 
                
                if node1 not in processed_edges_per_node:
                    processed_edges_per_node[node1] = 0
                
                # Позиция вдоль ребра (ближе к исходному узлу)
                t_along_edge = 0.25 + 0.1 * processed_edges_per_node[node1]
                t_along_edge = min(t_along_edge, 0.7)
                
                edge_x = x1 + (x2 - x1) * t_along_edge
                edge_y = y1 + (y2 - y1) * t_along_edge
                
                # Перпендикулярное смещение для исключения наложений
                num_outgoing = self.G.out_degree(node1)
                if num_outgoing > 1:
                    try:
                        outgoing_from_node1 = [e for e in sorted_edges if e[0] == node1]
                        edge_index = outgoing_from_node1.index((node1, node2))
                    except ValueError:
                        edge_index = processed_edges_per_node[node1]

                    edge_dx = x2 - x1
                    edge_dy = y2 - y1
                    
                    length = np.sqrt(edge_dx**2 + edge_dy**2)
                    if length > 0:
                        norm_dx = -edge_dy / length
                        norm_dy = edge_dx / length
                    else:
                        norm_dx, norm_dy = 0, 1

                    perpendicular_offset_magnitude = 0.15
                    direction = 1 if edge_index % 2 == 0 else -1
                    extra_offset = (edge_index // 2) * 0.1 if edge_index > 1 else 0

                    perpendicular_offset_x = (perpendicular_offset_magnitude + extra_offset) * norm_dx * direction
                    perpendicular_offset_y = (perpendicular_offset_magnitude + extra_offset) * norm_dy * direction
                    
                    edge_x += perpendicular_offset_x
                    edge_y += perpendicular_offset_y

                edge_label_positions[(node1, node2)] = (edge_x, edge_y)
                processed_edges_per_node[node1] += 1

        # Рисуем подписи рёбер
        for (node1, node2), (x, y) in edge_label_positions.items():
            label = self.edge_labels.get((node1, node2), '')
            if label:
                self.ax.text(x, y, label,
                           fontsize=7,
                           color='#FFD700',
                           weight='bold',
                           ha='center',
                           va='center',
                           bbox=dict(boxstyle="round,pad=0.25",
                                   facecolor='#3a3a5a',
                                   edgecolor='none',
                                   alpha=0.85),
                           zorder=4,
                           clip_on=True)

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
            
            # Добавляем узлы
            for scene in scenes:
                scene_id = scene.get('id', '')
                if scene_id:
                    self.G.add_node(scene_id)
            
            # Добавляем рёбра с подписями
            scene_ids = [s.get('id') for s in scenes if s.get('id')]
            
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                
                for choice in choices:
                    next_scene = choice.get('next_scene_id', '')
                    choice_text = choice.get('text', '')
                    
                    if next_scene and next_scene in scene_ids:
                        self.G.add_edge(scene_id, next_scene)
                        self.edge_labels[(scene_id, next_scene)] = choice_text
            
            self.draw_graph()
            
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")

    def _get_start_scene(self):
        """Возвращает ID стартовой сцены"""
        return self.story_data.get('start_scene', 
               self.story_data.get('scenes', [{}])[0].get('id', '') if self.story_data.get('scenes') else '')

    def _find_scene_by_id(self, scene_id):
        """Находит сцену по ID"""
        scenes = self.story_data.get('scenes', [])
        for scene in scenes:
            if scene.get('id') == scene_id:
                return scene
        return None
        
    def on_hover(self, event):
        """Обработчик наведения мыши для показа tooltip"""
        if event.inaxes != self.ax:
            if self.last_tooltip_node is not None:
                QToolTip.hideText()
                self.last_tooltip_node = None
            return
            
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        mouse_x, mouse_y = event.x, event.y
        current_hover_node = None
        
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            distance = np.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
            if distance < 35:
                current_hover_node = node
                break
                
        if current_hover_node != self.last_tooltip_node:
            QToolTip.hideText()
            if current_hover_node is not None:
                scene = self._find_scene_by_id(current_hover_node)
                if scene:
                    description = scene.get('description', 'Описание отсутствует')
                    cursor_pos = QCursor.pos()
                    QToolTip.showText(cursor_pos, description, self, QRect(), 0)
                    
            self.last_tooltip_node = current_hover_node

    def on_click(self, event):
        """Обработчик клика мыши"""
        if event.inaxes != self.ax:
            return
            
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        mouse_x, mouse_y = event.x, event.y
        
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            distance = np.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
            
            if distance < 35:
                scene = self._find_scene_by_id(node)
                if scene:
                    self._highlight_scene_path(node)
                    break

    def _highlight_scene_path(self, selected_node):
        """Подсвечивает путь от выбранной сцены"""
        scene = self._find_scene_by_id(selected_node)
        if scene:
            print(f"Выбрана сцена: {scene.get('title', selected_node)}")
            choices = scene.get('choices', [])
            if choices:
                print("Доступные выборы:")
                for choice in choices:
                    print(f"  - {choice.get('text', '')} → {choice.get('next_scene_id', '')}")
            else:
                print("Это концовка истории")

    def get_graph_statistics(self):
        """Возвращает статистику графа"""
        if not self.G.nodes():
            return "Граф пуст"
        
        stats = {
            'nodes': len(self.G.nodes()),
            'edges': len(self.G.edges()),
            'endings': len([n for n in self.G.nodes() if self.G.out_degree(n) == 0]),
            'start_nodes': len([n for n in self.G.nodes() if self.G.in_degree(n) == 0]),
            'max_choices': max([self.G.out_degree(n) for n in self.G.nodes()]) if self.G.nodes() else 0
        }
        
        return f"""Статистика графа:
                    • Сцен: {stats['nodes']}
                    • Переходов: {stats['edges']}
                    • Концовок: {stats['endings']}
                    • Стартовых сцен: {stats['start_nodes']}
                    • Макс. выборов в сцене: {stats['max_choices']}"""