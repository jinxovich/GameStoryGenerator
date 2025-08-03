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
        
        # Переменная для хранения последнего tooltip
        self.last_tooltip_node = None

    def _setup_colormap(self):
        colors = ["#4facfe", "#00f2fe", "#a6c1ee", "#fbc2eb", "#ff9a9e"]
        self.cmap = LinearSegmentedColormap.from_list("custom", colors)

    def draw_graph(self):
        self.ax.clear()
        
        if self.G.number_of_nodes() > 0:
            try:
                # Создаём древовидный layout
                pos = self._create_tree_layout()
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
                    node_sizes.append(3500)  # Немного больше для начальной сцены
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
            
            # Рисуем рёбра с улучшенным стилем для древовидной структуры
            nx.draw_networkx_edges(
                self.G, pos, ax=self.ax,
                width=2,
                edge_color="#aaaaaa",
                alpha=0.8,
                arrowsize=25,
                arrowstyle='-|>',
                connectionstyle='arc3,rad=0.05',  # Меньший изгиб для дерева
                min_source_margin=20,
                min_target_margin=20
            )
            
            # Подписи узлов - просто номера сцен темным шрифтом
            labels = {}
            node_list = list(self.G.nodes())
            for i, node in enumerate(node_list, 1):
                labels[node] = str(i)
                    
            nx.draw_networkx_labels(
                self.G, pos, labels, ax=self.ax,
                font_size=12,
                font_color="#000000",  # Темный шрифт
                font_family="Segoe UI",
                font_weight="bold"
            )
            
            # Подписи рёбер (выборы) с улучшенным позиционированием
            if self.edge_labels:
                self._draw_edge_labels(pos)
            
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
        self.ax.axis('off')  # Полностью скрываем оси
        for spine in self.ax.spines.values():
            spine.set_visible(False)
            
        # Добавляем легенду
        self._add_legend()
        
        self.draw()

    def _create_tree_layout(self):
        """Создаёт древовидный layout с начальной сценой сверху"""
        try:
            # Находим стартовую сцену
            start_scene = self._get_start_scene()
            if not start_scene or start_scene not in self.G.nodes():
                # Если стартовая сцена не найдена, берем узел без входящих рёбер
                roots = [n for n in self.G.nodes() if self.G.in_degree(n) == 0]
                start_scene = roots[0] if roots else list(self.G.nodes())[0]
            
            print(f"Стартовая сцена: {start_scene}")
            
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
                
                print(f"Узел '{node}' на уровне {level}")
                
                # Получаем потомков текущего узла
                successors = list(self.G.successors(node))
                for successor in successors:
                    if successor not in visited:
                        queue.append((successor, level + 1))
            
            # Убеждаемся, что все узлы имеют уровень
            all_nodes = set(self.G.nodes())
            nodes_without_level = all_nodes - set(levels.keys())
            
            if nodes_without_level:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Узлы без уровня: {nodes_without_level}")
                # Назначаем этим узлам уровень на основе их входящих связей
                for node in nodes_without_level:
                    predecessors = list(self.G.predecessors(node))
                    if predecessors:
                        # Берём максимальный уровень предшественников + 1
                        pred_levels = [levels.get(pred, 0) for pred in predecessors]
                        levels[node] = max(pred_levels) + 1
                    else:
                        # Если нет предшественников, ставим на уровень 0
                        levels[node] = 0
                    max_level = max(max_level, levels[node])
            
            print(f"Итоговые уровни: {levels}")
            print(f"Максимальный уровень: {max_level}")
            
            # Группируем узлы по уровням
            level_groups = {}
            for node, level in levels.items():
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(node)
            
            print(f"Группы по уровням: {level_groups}")
            
            # Вычисляем позиции
            pos = {}
            y_spacing = 2.0  # Расстояние между уровнями
            
            for level in range(max_level + 1):
                nodes_at_level = level_groups.get(level, [])
                num_nodes = len(nodes_at_level)
                
                if num_nodes == 0:
                    continue
                
                # Y координата (сверху вниз)
                y_position = -level * y_spacing
                
                if num_nodes == 1:
                    # Если один узел, размещаем по центру
                    pos[nodes_at_level[0]] = (0, y_position)
                    print(f"Узел '{nodes_at_level[0]}' размещён в (0, {y_position})")
                else:
                    # Если несколько узлов, распределяем равномерно
                    total_width = min(num_nodes * 2.5, 12)  # Ограничиваем максимальную ширину
                    
                    for i, node in enumerate(nodes_at_level):
                        # Распределяем узлы симметрично относительно центра
                        if num_nodes == 1:
                            x_position = 0
                        else:
                            x_position = (i - (num_nodes - 1) / 2) * (total_width / (num_nodes - 1))
                        
                        pos[node] = (x_position, y_position)
                        print(f"Узел '{node}' размещён в ({x_position}, {y_position})")
            
            print(f"Итоговые позиции: {pos}")
            
            # Проверяем, что все узлы имеют позиции
            missing_pos = set(self.G.nodes()) - set(pos.keys())
            if missing_pos:
                print(f"ОШИБКА: Узлы без позиций: {missing_pos}")
                # Добавляем недостающие позиции
                for i, node in enumerate(missing_pos):
                    pos[node] = (i * 2, -(max_level + 1) * y_spacing)
                    print(f"Добавлена позиция для '{node}': {pos[node]}")
            
            return pos
            
        except Exception as e:
            print(f"Ошибка в tree layout: {e}")
            import traceback
            traceback.print_exc()
            # Fallback к spring layout
            return nx.spring_layout(self.G, seed=42, k=2, iterations=50)

    def _optimize_positions(self, pos, levels):
        """Оптимизирует позиции узлов для уменьшения пересечений рёбер"""
        try:
            print("Запуск оптимизации позиций...")
            print(f"Входные позиции: {pos}")
            print(f"Входные уровни: {levels}")
            
            # Проверяем, что все узлы из levels есть в pos
            missing_in_pos = set(levels.keys()) - set(pos.keys())
            if missing_in_pos:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Узлы из levels отсутствуют в pos: {missing_in_pos}")
                return pos
            
            # Группируем узлы по уровням для оптимизации
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
                
                print(f"Оптимизируем уровень {level} с узлами: {nodes_at_level}")
                
                # Вычисляем "центр масс" родителей для каждого узла
                node_parent_centers = {}
                for node in nodes_at_level:
                    if node not in pos:
                        print(f"ПРЕДУПРЕЖДЕНИЕ: Узел '{node}' отсутствует в pos")
                        continue
                        
                    parents = list(self.G.predecessors(node))
                    if parents:
                        parent_x_coords = []
                        for parent in parents:
                            if parent in pos:
                                parent_x_coords.append(pos[parent][0])
                            else:
                                print(f"ПРЕДУПРЕЖДЕНИЕ: Родитель '{parent}' отсутствует в pos")
                        
                        if parent_x_coords:
                            node_parent_centers[node] = sum(parent_x_coords) / len(parent_x_coords)
                        else:
                            node_parent_centers[node] = 0
                    else:
                        node_parent_centers[node] = 0
                
                print(f"Центры родителей: {node_parent_centers}")
                
                # Сортируем узлы по центру масс их родителей
                valid_nodes = [node for node in nodes_at_level if node in pos and node in node_parent_centers]
                sorted_nodes = sorted(valid_nodes, key=lambda n: node_parent_centers.get(n, 0))
                
                print(f"Отсортированные узлы: {sorted_nodes}")
                
                # Перераспределяем позиции
                num_nodes = len(sorted_nodes)
                if num_nodes > 0 and sorted_nodes[0] in pos:
                    y_position = pos[sorted_nodes[0]][1]  # Сохраняем Y координату
                    
                    if num_nodes > 1:
                        total_width = min(num_nodes * 2.5, 12)
                        for i, node in enumerate(sorted_nodes):
                            x_position = (i - (num_nodes - 1) / 2) * (total_width / (num_nodes - 1))
                            pos[node] = (x_position, y_position)
                            print(f"Обновлена позиция '{node}': ({x_position}, {y_position})")
            
            print(f"Оптимизированные позиции: {pos}")
            
        except Exception as e:
            print(f"Ошибка при оптимизации позиций: {e}")
            import traceback
            traceback.print_exc()
        
        return pos

    def _draw_edge_labels(self, pos):
        """Рисует подписи рёбер с улучшенным позиционированием для древовидной структуры"""
        edge_label_positions = {}
        
        for (node1, node2), label in self.edge_labels.items():
            if node1 in pos and node2 in pos:
                x1, y1 = pos[node1]
                x2, y2 = pos[node2] 
                
                # Для древовидной структуры размещаем подписи ближе к исходному узлу
                # но сдвигаем в сторону для избежания наложений
                edge_x = x1 + (x2 - x1) * 0.3  # 30% пути от исходного узла
                edge_y = y1 + (y2 - y1) * 0.3
                
                # Добавляем горизонтальное смещение для избежания наложений
                siblings = list(self.G.successors(node1))
                if len(siblings) > 1:
                    sibling_index = siblings.index(node2)
                    horizontal_offset = (sibling_index - (len(siblings) - 1) / 2) * 0.3
                    edge_x += horizontal_offset
                
                edge_label_positions[(node1, node2)] = (edge_x, edge_y)
        
        # Рисуем подписи рёбер
        for (node1, node2), (x, y) in edge_label_positions.items():
            label = self.edge_labels.get((node1, node2), '')
            if label:
                # Сокращаем длинные подписи
                if len(label) > 18:
                    label = label[:15] + "..."
                
                self.ax.text(x, y, label, 
                           fontsize=8, 
                           color='#ffeb3b',
                           weight='bold',
                           ha='center', 
                           va='center',
                           bbox=dict(boxstyle="round,pad=0.3", 
                                   facecolor='#2a2a45', 
                                   edgecolor='#4facfe',
                                   alpha=0.9,
                                   linewidth=1),
                           zorder=5)  # Поверх всех элементов

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
            for scene in scenes:
                scene_id = scene.get('id', '')
        except:
            pass
    def update_graph_from_story(self, story_data):
        """Обновляет граф на основе данных истории"""
        print(f"=== ОТЛАДКА ГРАФА ===")
        print(f"Получены данные истории: {type(story_data)}")
        print(f"Ключи в story_data: {list(story_data.keys()) if isinstance(story_data, dict) else 'Не словарь'}")
        
        self.story_data = story_data
        self.G.clear()
        self.edge_labels.clear()
        
        try:
            scenes = story_data.get('scenes', [])
            print(f"Найдено сцен: {len(scenes)}")
            
            if scenes:
                print("Первые 3 сцены:")
                for i, scene in enumerate(scenes[:3]):
                    print(f"  Сцена {i+1}: {scene}")
            
            # Добавляем узлы
            added_nodes = []
            for scene in scenes:
                scene_id = scene.get('id', '')
                print(f"Обрабатываем сцену с ID: '{scene_id}'")
                if scene_id:
                    self.G.add_node(scene_id)
                    added_nodes.append(scene_id)
                else:
                    print(f"  ПРЕДУПРЕЖДЕНИЕ: Сцена без ID: {scene}")
            
            print(f"Добавлено узлов: {added_nodes}")
            
            # Добавляем рёбра с подписями
            added_edges = []
            scene_ids = [s.get('id') for s in scenes if s.get('id')]
            
            for scene in scenes:
                scene_id = scene.get('id', '')
                choices = scene.get('choices', [])
                print(f"Сцена '{scene_id}' имеет {len(choices)} выборов")
                
                for choice in choices:
                    next_scene = choice.get('next_scene_id', '')
                    choice_text = choice.get('text', '')
                    
                    print(f"  Выбор: '{choice_text}' -> '{next_scene}'")
                    
                    if next_scene and next_scene in scene_ids:
                        self.G.add_edge(scene_id, next_scene)
                        self.edge_labels[(scene_id, next_scene)] = choice_text
                        added_edges.append((scene_id, next_scene))
                    else:
                        print(f"    ПРЕДУПРЕЖДЕНИЕ: Некорректная связь {scene_id} -> {next_scene}")
            
            print(f"Добавлено рёбер: {added_edges}")
            print(f"Итого граф: {len(self.G.nodes())} узлов, {len(self.G.edges())} рёбер")
            print(f"Узлы графа: {list(self.G.nodes())}")
            print(f"Рёбра графа: {list(self.G.edges())}")
            
            # Вызываем отрисовку
            print("Вызываем draw_graph()...")
            self.draw_graph()
            print("draw_graph() завершён")
            
        except Exception as e:
            print(f"Ошибка при обновлении графа: {e}")
            import traceback
            traceback.print_exc()
            if 'choices' in locals():
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
            if self.last_tooltip_node is not None:
                QToolTip.hideText()
                self.last_tooltip_node = None
            return
            
        if not hasattr(self, 'node_screen_positions') or not self.node_screen_positions:
            return
            
        # Получаем позицию мыши в координатах canvas
        mouse_x, mouse_y = event.x, event.y
        
        # Проверяем каждый узел
        current_hover_node = None
        for node, (screen_x, screen_y) in self.node_screen_positions.items():
            # Вычисляем расстояние от мыши до центра узла
            distance = np.sqrt((screen_x - mouse_x)**2 + (screen_y - mouse_y)**2)
            
            # Если мышь находится над узлом (радиус ~35 пикселей)
            if distance < 35:
                current_hover_node = node
                break
        
        # Показываем/скрываем tooltip только при изменении узла
        if current_hover_node != self.last_tooltip_node:
            QToolTip.hideText()
            
            if current_hover_node is not None:
                scene = self._find_scene_by_id(current_hover_node)
                if scene:
                    tooltip_text = self._create_tooltip_text(scene)
                    cursor_pos = QCursor.pos()
                    # Создаем простой текстовый tooltip без HTML
                    QToolTip.showText(cursor_pos, tooltip_text, self)
            
            self.last_tooltip_node = current_hover_node

    def _create_tooltip_text(self, scene):
        """Создаёт простой текстовый tooltip без HTML"""
        title = scene.get('title', 'Без названия')
        description = scene.get('description', 'Описание отсутствует')
        characters = scene.get('characters', [])
        is_ending = scene.get('is_ending', False)
        choices = scene.get('choices', [])
        
        # Ограничиваем длину описания для tooltip
        if len(description) > 150:
            description = description[:147] + "..."
        
        tooltip_parts = [f"СЦЕНА: {title}"]
        
        if description:
            tooltip_parts.append(f"\nОПИСАНИЕ: {description}")
        
        if characters:
            char_text = ', '.join(characters[:3])  # Показываем максимум 3 персонажа
            if len(characters) > 3:
                char_text += f" и ещё {len(characters) - 3}..."
            tooltip_parts.append(f"\nПЕРСОНАЖИ: {char_text}")
        
        if choices and not is_ending:
            tooltip_parts.append("\nДОСТУПНЫЕ ДЕЙСТВИЯ:")
            for i, choice in enumerate(choices[:3]):  # Показываем максимум 3 выбора
                choice_text = choice.get('text', '')
                if choice_text:
                    tooltip_parts.append(f"• {choice_text}")
            if len(choices) > 3:
                tooltip_parts.append(f"• ... и ещё {len(choices) - 3}")
        
        if is_ending:
            tooltip_parts.append("\nКОНЦОВКА")
        
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