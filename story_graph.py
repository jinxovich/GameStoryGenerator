from PyQt5.QtWidgets import QSizePolicy, QToolTip
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import numpy as np

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

    def _setup_colormap(self):
        colors = ["#4facfe", "#00f2fe", "#a6c1ee", "#fbc2eb", "#ff9a9e"]
        self.cmap = LinearSegmentedColormap.from_list("custom", colors)

    def draw_graph(self):
        self.ax.clear()
        if self.G.number_of_nodes() > 0:
            try:
                # Создаём иерархический layout для лучшего отображения
                roots = [n for n in self.G.nodes() if self.G.in_degree(n) == 0]
                if roots:
                    pos = self._create_hierarchical_layout()
                else:
                    pos = nx.spring_layout(self.G, seed=42, k=3, iterations=100)
            except Exception as e:
                print(f"Ошибка при создании layout: {e}")
                pos = nx.spring_layout(self.G, seed=42, k=1, iterations=50)

            # Определяем цвета узлов в зависимости от типа
            node_colors = []
            node_sizes = []
            for node in self.G.nodes():
                scene = self._find_scene_by_id(node)
                if scene and scene.get('is_ending', False):
                    node_colors.append('#ff6b6b')  # Красный для концовок
                    node_sizes.append(3000)
                elif node == self._get_start_scene():
                    node_colors.append('#51cf66')  # Зелёный для старта
                    node_sizes.append(3000)
                else:
                    node_colors.append('#4dabf7')  # Синий для обычных сцен
                    node_sizes.append(2500)
            
            # Рисуем узлы
            nx.draw_networkx_nodes(
                self.G, pos, ax=self.ax,
                node_size=node_sizes,
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
                alpha=0.7,
                arrowsize=20,
                arrowstyle='->',
                connectionstyle='arc3,rad=0.1',
                min_source_margin=15,
                min_target_margin=15
            )
            
            # Подписи узлов
            labels = {}
            for node in self.G.nodes():
                scene = self._find_scene_by_id(node)
                if scene:
                    title = scene.get('title', node)
                    if len(title) > 12:
                        title = title[:10] + "..."
                    labels[node] = title
                else:
                    label = str(node)
                    if len(label) > 12:
                        label = label[:10] + "..."
                    labels[node] = label
                    
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=8,
                font_color="#ffffff",
                font_family="Segoe UI",
                font_weight="bold"
            )
            
            # Подписи рёбер (выборы)
            if self.edge_labels:
                # Вычисляем позиции для подписей рёбер
                edge_pos = {}
                for (node1, node2), label in self.edge_labels.items():
                    if node1 in pos and node2 in pos:
                        x1, y1 = pos[node1]
                        x2, y2 = pos[node2] 
                        # Размещаем подпись в середине ребра, слегка смещённую
                        edge_x = (x1 + x2) / 2
                        edge_y = (y1 + y2) / 2
                        
                        # Добавляем небольшое смещение для лучшей читаемости
                        offset_x = (y2 - y1) * 0.1  # Перпендикулярное смещение
                        offset_y = -(x2 - x1) * 0.1
                        
                        edge_pos[(node1, node2)] = (edge_x + offset_x, edge_y + offset_y)
                
                # Рисуем подписи рёбер
                for (node1, node2), (x, y) in edge_pos.items():
                    label = self.edge_labels.get((node1, node2), '')
                    if label:
                        # Сокращаем длинные подписи
                        if len(label) > 15:
                            label = label[:13] + "..."
                        
                        self.ax.text(x, y, label, 
                                   fontsize=7, 
                                   color='#ffeb3b',
                                   weight='bold',
                                   ha='center', 
                                   va='center',
                                   bbox=dict(boxstyle="round,pad=0.2", 
                                           facecolor='#2a2a45', 
                                           edgecolor='none',
                                           alpha=0.8))
            
            self.node_positions = pos
            
            # Сохраняем позиции узлов в экранных координатах для hover
            self.node_screen_positions = {}
            for node, (x, y) in pos.items():
                screen_x, screen_y = self.ax.transData.transform((x, y))
                self.node_screen_positions[node] = (screen_x, screen_y)
            
        else:
            self.ax.text(0.5, 0.5, 'Граф истории будет отображен здесь\n\nГенерируйте историю для просмотра схемы сюжета', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=14, color='white',
                        bbox=dict(boxstyle="round,pad=0.5", facecolor='#25253d', alpha=0.8))
            
        self.ax.set_facecolor('#1e1e2d')
        self.fig.patch.set_facecolor('#1e1e2d')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
            
        # Добавляем легенду
        self._add_legend()
        
        self.draw()

    def _create_hierarchical_layout(self):
        """Создаёт иерархический layout для графа"""
        try:
            # Определяем уровни узлов
            levels = {}
            roots = [n for n in self.G.nodes() if self.G.in_degree(n) == 0]
            
            for root in roots:
                levels[root] = 0
                queue = [(root, 0)]
                visited = {root}
                
                while queue:
                    node, level = queue.pop(0)
                    
                    for neighbor in self.G.successors(node):
                        if neighbor not in visited:
                            levels[neighbor] = level + 1
                            queue.append((neighbor, level + 1))
                            visited.add(neighbor)
                        elif levels[neighbor] < level + 1:
                            levels[neighbor] = level + 1
            
            # Группируем узлы по уровням
            level_nodes = {}
            for node, level in levels.items():
                if level not in level_nodes:
                    level_nodes[level] = []
                level_nodes[level].append(node)
            
            # Вычисляем позиции
            pos = {}
            max_level = max(level_nodes.keys()) if level_nodes else 0
            
            for level, nodes in level_nodes.items():
                num_nodes = len(nodes)
                y_position = max_level - level  # Инвертируем для отображения сверху вниз
                
                for i, node in enumerate(nodes):
                    if num_nodes == 1:
                        x_position = 0
                    else:
                        # Распределяем узлы равномерно по горизонтали
                        x_position = (i - (num_nodes - 1) / 2) * 3
                    
                    pos[node] = (x_position, y_position)
            
            return pos
            
        except Exception as e:
            print(f"Ошибка в hierarchical layout: {e}")
            return nx.spring_layout(self.G, seed=42, k=2, iterations=50)

    def _add_legend(self):
        """Добавляет легенду к графу"""
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#51cf66', 
                      markersize=12, label='Начало', markeredgecolor='white', markeredgewidth=2),
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
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                
                for choice in choices:
                    next_scene = choice.get('next_scene_id', '')
                    choice_text = choice.get('text', '')
                    
                    if next_scene and next_scene in [s.get('id') for s in scenes]:
                        self.G.add_edge(scene_id, next_scene)
                        # Сохраняем текст выбора как подпись ребра
                        self.edge_labels[(scene_id, next_scene)] = choice_text
            
            print(f"Загружен граф: {len(self.G.nodes())} узлов, {len(self.G.edges())} рёбер")
            self.draw_graph()
            
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")

    def _get_start_scene(self):
        """Возвращает ID стартовой сцены"""
        return self.story_data.get('start_scene', 
               self.story_data.get('scenes', [{}])[0].get('id', '') if self.story_data.get('scenes') else '')

    def update_graph(self, nodes, edges):
        """Обновляет граф с заданными узлами и рёбрами"""
        self.G.clear()
        self.edge_labels.clear()
        self.G.add_nodes_from(nodes)
        self.G.add_edges_from(edges)
        self.draw_graph()
        
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
            QToolTip.hideText()
            return
            
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        # Получаем позицию мыши в координатах canvas
        mouse_x, mouse_y = event.x, event.y
        
        # Проверяем каждый узел
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            # Вычисляем расстояние от мыши до центра узла
            distance = np.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
            
            # Если мышь находится над узлом (радиус ~25 пикселей)
            if distance < 35:
                scene = self._find_scene_by_id(node)
                if scene:
                    tooltip_text = self._create_tooltip_text(scene)
                    cursor_pos = QCursor.pos()
                    QToolTip.showText(cursor_pos, tooltip_text, self)
                    return
                    
        QToolTip.hideText()

    def _create_tooltip_text(self, scene):
        """Создаёт текст для tooltip"""
        title = scene.get('title', 'Без названия')
        description = scene.get('description', 'Описание отсутствует')
        characters = scene.get('characters', [])
        is_ending = scene.get('is_ending', False)
        choices = scene.get('choices', [])
        
        # Ограничиваем длину описания для tooltip
        if len(description) > 200:
            description = description[:197] + "..."
        
        tooltip_parts = [f"<b>{title}</b>"]
        
        if description:
            tooltip_parts.append(f"<br><br><i>{description}</i>")
        
        if characters:
            char_text = ', '.join(characters[:3])  # Показываем максимум 3 персонажа
            if len(characters) > 3:
                char_text += f" и ещё {len(characters) - 3}..."
            tooltip_parts.append(f"<br><br><b>Персонажи:</b> {char_text}")
        
        if choices:
            tooltip_parts.append(f"<br><br><b>Доступные действия:</b>")
            for i, choice in enumerate(choices[:3]):  # Показываем максимум 3 выбора
                choice_text = choice.get('text', '')
                if choice_text:
                    tooltip_parts.append(f"<br>• {choice_text}")
            if len(choices) > 3:
                tooltip_parts.append(f"<br>• ... и ещё {len(choices) - 3}")
        
        if is_ending:
            tooltip_parts.append("<br><br><b>🏁 КОНЦОВКА</b>")
        
        return ''.join(tooltip_parts)

    def on_click(self, event):
        """Обработчик клика мыши"""
        if event.inaxes != self.ax:
            return
            
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        mouse_x, mouse_y = event.x, event.y
        
        # Проверяем клик по узлам
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            distance = np.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
            
            if distance < 35:
                scene = self._find_scene_by_id(node)
                if scene:
                    self._highlight_scene_path(node)
                    break

    def _highlight_scene_path(self, selected_node):
        """Подсвечивает путь от выбранной сцены"""
        # Можно добавить логику подсветки путей
        # Пока просто выводим информацию в консоль
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