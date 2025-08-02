# story_graph.py
from PyQt5.QtWidgets import QSizePolicy, QToolTip
from PyQt5.QtCore import QPoint, QRect
from PyQt5.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches

class StoryGraph(FigureCanvas):
    """
    Canvas для отображения графа истории.
    """
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        super().__init__(self.fig)
        self.setStyleSheet("background-color: transparent;")
        self.G = nx.DiGraph()  # Используем направленный граф для историй
        self.story_data = {} # Сохраняем исходные данные для тултипов
        self._setup_colormap()
        self.draw_graph()
        
        # Включаем интерактивность
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)

    def _setup_colormap(self):
        colors = ["#4facfe", "#00f2fe", "#a6c1ee", "#fbc2eb", "#ff9a9e"]
        self.cmap = LinearSegmentedColormap.from_list("custom", colors)

    def draw_graph(self):
        self.ax.clear()
        if self.G.number_of_nodes() > 0:
            try:
                # Используем иерархический layout для лучшего отображения сюжета
                # Попробуем сначала найти "корень" (сцена без входящих рёбер)
                roots = [n for n in self.G.nodes() if self.G.in_degree(n) == 0]
                if roots:
                    # Используем multipartite_layout для создания уровневого дерева
                    # Сначала определим уровни
                    levels = {}
                    for root in roots:
                        levels[root] = 0
                        queue = [(root, 0)]
                        while queue:
                            node, level = queue.pop(0)
                            for neighbor in self.G.successors(node):
                                if neighbor not in levels or levels[neighbor] < level + 1:
                                    levels[neighbor] = level + 1
                                    queue.append((neighbor, level + 1))
                    
                    # Создаем словарь для layout
                    pos = {}
                    level_nodes = {}
                    for node, level in levels.items():
                        if level not in level_nodes:
                            level_nodes[level] = []
                        level_nodes[level].append(node)
                    
                    # Располагаем узлы по уровням
                    for level, nodes in level_nodes.items():
                        num_nodes = len(nodes)
                        for i, node in enumerate(nodes):
                            # Центрируем узлы на уровне
                            x_offset = (i - (num_nodes - 1) / 2) * 2
                            pos[node] = (x_offset, -level) # Отрицательный Y для "падения" вниз
                else:
                    # fallback если корень не найден
                    pos = nx.spring_layout(self.G, seed=42, k=3, iterations=50)
            except Exception as e:
                print(f"Ошибка при создании layout: {e}")
                pos = nx.spring_layout(self.G, seed=42, k=1, iterations=50)

            # Подготавливаем цвета и размеры узлов
            node_colors = [self.cmap(i/max(len(self.G.nodes()), 1)) for i in range(len(self.G.nodes()))]
            node_sizes = [2500 for _ in self.G.nodes()] # Фиксированный размер
            
            # Рисуем узлы
            nx.draw_networkx_nodes(
                self.G, pos, ax=self.ax,
                node_size=node_sizes,
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
                arrowsize=20,
                arrowstyle='->',
                connectionstyle='arc3,rad=0.1' # Слегка изогнутые линии для лучшего вида
            )
            
            # Рисуем подписи (названия сцен)
            labels = {}
            for node in self.G.nodes():
                scene = self._find_scene_by_id(node)
                if scene:
                    title = scene.get('title', node)
                    # Сокращаем длинные названия
                    if len(title) > 15:
                        title = title[:13] + "..."
                    labels[node] = title
                else:
                    label = str(node)
                    if len(label) > 15:
                        label = label[:13] + "..."
                    labels[node] = label
                    
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=9,
                font_color="#ffffff",
                font_family="Segoe UI",
                font_weight="bold"
            )
            
            # Сохраняем позиции узлов для обработки hover
            self.node_positions = pos
            
        else:
            self.ax.text(0.5, 0.5, 'Граф истории будет отображен здесь', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=14, color='white')
            
        self.ax.set_facecolor('#1e1e2d')
        self.fig.patch.set_facecolor('#1e1e2d')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.draw()

    def update_graph_from_story(self, story_data):
        """Обновляет граф на основе данных истории"""
        self.story_data = story_data # Сохраняем данные для тултипов
        self.G.clear()
        try:
            scenes = story_data.get('scenes', [])
            # Добавляем узлы (сцены)
            for scene in scenes:
                scene_id = scene.get('id', '')
                # Можно добавить атрибуты узла, если нужно
                self.G.add_node(scene_id)
            # Добавляем рёбра (переходы между сценами)
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                for choice in choices:
                    next_scene = choice.get('next_scene_id', '')
                    if next_scene and next_scene in [s.get('id') for s in scenes]:
                        # Можно добавить атрибуты ребра, если нужно
                        self.G.add_edge(scene_id, next_scene)
            self.draw_graph()
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")
            # Можно эмитировать сигнал ошибки или просто логировать

    def update_graph(self, nodes, edges):
        """Альтернативный метод для обновления графа"""
        self.G.clear()
        self.G.add_nodes_from(nodes)
        self.G.add_edges_from(edges)
        self.draw_graph()
        
    def _find_scene_by_id(self, scene_id):
        """Находит сцену в story_data по её ID"""
        scenes = self.story_data.get('scenes', [])
        for scene in scenes:
            if scene.get('id') == scene_id:
                return scene
        return None
        
    def on_hover(self, event):
        """Обработчик события наведения мыши"""
        if event.inaxes == self.ax:
            # Проверяем, находится ли курсор над каким-либо узлом
            for node, (x, y) in self.node_positions.items():
                # Преобразуем координаты узла в пиксели
                node_x, node_y = self.ax.transData.transform((x, y))
                event_x, event_y = event.x, event.y
                
                # Вычисляем расстояние между курсором и центром узла
                distance = ((node_x - event_x)**2 + (node_y - event_y)**2)**0.5
                
                # Радиус узла в пикселях (примерно)
                node_radius_px = 30 
                
                if distance < node_radius_px:
                    # Нашли узел под курсором, показываем тултип
                    scene = self._find_scene_by_id(node)
                    if scene:
                        title = scene.get('title', 'Без названия')
                        description = scene.get('description', 'Описание отсутствует')
                        characters = ', '.join(scene.get('characters', []))
                        is_ending = scene.get('is_ending', False)
                        
                        tooltip_text = f"<b>{title}</b>\n\n{description}\n\nПерсонажи: {characters}"
                        if is_ending:
                            tooltip_text += "\n\n(Конец истории)"
                            
                        # Позиционируем тултип рядом с курсором
                        cursor_pos = QCursor.pos()
                        QToolTip.showText(cursor_pos, tooltip_text, self)
                        return
                        
            # Если курсор не над узлом, скрываем тултип
            QToolTip.hideText()
