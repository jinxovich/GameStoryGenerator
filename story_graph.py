import re
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                             QHBoxLayout, QToolTip)
from PyQt5.QtGui import QCursor
import matplotlib.patches as mpatches
import aiohttp
import json
import re

from config import YANDEX_ID_KEY, YANDEX_API_KEY
from StoryObject import StoryObject

def clean_json_response(text: str) -> str:
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    start = text.find('[')
    end = text.rfind(']')
    
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("Не удалось найти валидный JSON-массив в ответе.", text, 0)
        
    content = text[start+1:end].strip()
    
    fixed_content = re.sub(r'\}\s*\{', '}, {', content, flags=re.DOTALL)
    
    return f"[{fixed_content}]"

def convert_ai_array_to_graph_format(scene_list: list[dict], story_object: StoryObject) -> dict:
    if not scene_list:
        raise ValueError("AI вернул пустой список сцен.")
        
    scene_id_to_id = {}
    formatted_scenes = []
    
    for i, scene_data in enumerate(scene_list):
        original_scene_id = scene_data.get('scene_id', str(i+1))
        new_id = str(i+1)
        scene_id_to_id[original_scene_id] = new_id
        
        formatted_scenes.append({
            'scene_id': new_id,
            'text': scene_data.get('text', scene_data.get('description', 'Описание отсутствует.')),
            'choices': [{
                'text': c.get('text', '...'),
                'next_scene': c.get('next_scene', c.get('next_scene', ''))
            } for c in scene_data.get('choices', [])],
            'is_ending': not scene_data.get('choices', not scene_data.get('is_ending', False))
        })
    
    for scene in formatted_scenes:
        for choice in scene['choices']:
            original_next_scene_id = choice['next_scene']
            if original_next_scene_id in scene_id_to_id:
                choice['next_scene'] = scene_id_to_id[original_next_scene_id]
    
    start_scene_id = scene_id_to_id.get("1", "1")
    
    title_text = story_object.description[:50]
    if len(story_object.description) > 50:
        title_text += "..."
        
    return {
        'title': title_text,
        'description': story_object.description,
        'start_scene': start_scene_id,
        'scenes': formatted_scenes
    }

async def get_story_from_ai(story_object: StoryObject) -> dict:
    if not YANDEX_API_KEY or not YANDEX_ID_KEY:
        raise ValueError("YANDEX_API_KEY и YANDEX_ID_KEY должны быть установлены в .env файле.")

    prompt = {
        "modelUri": f"gpt://{YANDEX_ID_KEY}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.75,
            "maxTokens": "16000"
        },
        "messages": [
            {
                "role": "system",
                "text": """Ты — профессиональный сценарист для RPG.
                Твоя задача — сгенерировать ЕДИНЫЙ JSON-МАССИВ, где каждый элемент — это одна сцена квеста.
                
                КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
                1.  **ФОРМАТ ВЫВОДА**: Верни ТОЛЬКО валидный JSON-массив `[ ... ]`. Без комментариев и markdown.
                2.  **СТРУКТУРА ОБЪЕКТА**: Каждый объект в массиве должен иметь СТРОГУЮ структуру:
                    {
                      "scene_id": "1",  
                      "text": "Полное, насыщенное описание сцены (80-150 слов).",
                      "choices": [
                        {"text": "Краткое описание выбора (2-5 слов)", "next_scene": "2"}
                      ]
                    }
                3.  **ЗАПЯТЫЕ**: Между КАЖДЫМ объектом в массиве (например, между `}` и `{`) ДОЛЖНА стоять запятая.
                4.  **ID СЦЕН**: scene_id должны быть последовательными числами от 1 до N в виде строк ("1", "2", "3" и т.д.)
                5.  **КОНЦОВКИ**: Создай минимум две концовки (сцены без choices)
                6.  **ВЕТВЛЕНИЕ**: Создай ветвление сюжета с уникальными путями
                
                ТРЕБОВАНИЯ К КОНТЕНТУ:
                -   **Жанр**: Строго Ролевая игра (RPG).
                -   **Язык**: Русский.
                -   **Количество сцен**: От 6 до 12.
                """
            },
            {
                "role": "user",
                "text": f"""Создай RPG квест по параметрам:
                - **Описание**: {story_object.description}
                - **Жанр**: {story_object.genre}
                - **Персонажи**: {', '.join(story_object.heroes)}
                - **Настроение**: {story_object.mood}
                """
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=prompt, timeout=120) as response:
                response.raise_for_status()
                raw_response = await response.text()
                
                try:
                    result_data = json.loads(raw_response)
                    generated_text = result_data["result"]["alternatives"][0]["message"]["text"]
                except (json.JSONDecodeError, KeyError):
                    generated_text = raw_response

                cleaned_json_text = clean_json_response(generated_text)
                scene_list = json.loads(cleaned_json_text)
                
                return convert_ai_array_to_graph_format(scene_list, story_object)

    except aiohttp.ClientError as e:
        raise ConnectionError(f"Ошибка сети при обращении к AI: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"AI вернул некорректный JSON, который не удалось исправить. Ошибка: {e}")
    except Exception as e:
        raise RuntimeError(f"Неожиданная ошибка при работе с AI: {e}")

class SceneDetailDialog(QDialog):
    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.setWindowTitle(f"Детали сцены: {scene_data.get('scene_id', 'N/A')}")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #2d2d44; border: 1px solid #4a4a6a; }
            QTextEdit {
                background-color: #1e1e2d; color: #e0e0ff; border: none;
                font-size: 11pt; padding: 10px;
            }
            QPushButton {
                background-color: #4dabf7; color: white; border: none;
                padding: 8px 16px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3b99e6; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        description_text = self.scene_data.get('text', 'Описание отсутствует.')
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(description_text)
        layout.addWidget(self.text_edit)

        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)


class StoryGraph(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots(figsize=(12, 10), facecolor='#1e1e2d')
        super().__init__(self.fig)
        self.G = nx.DiGraph()
        self.story_data = {}
        self.node_positions = {}
        self.edge_labels = {}
        self.selected_node = None
        self.hovered_edge = None
        self.edge_paths = {}
        self.press = None

        self.draw_empty_graph("Ожидание генерации истории...")

        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)

    
    def on_press(self, event):
        if event.inaxes != self.ax:
            return
        self.press = (self.ax.get_xlim(), self.ax.get_ylim(), event.xdata, event.ydata)
        self.ax.figure.canvas.draw()



    def on_release(self, event):
        self.press = None
        self.ax.figure.canvas.draw()

    def draw_empty_graph(self, message):
        self.ax.clear()
        self.ax.set_facecolor('#1e1e2d')
        self.ax.text(0.5, 0.5, message, ha='center', va='center',
                     transform=self.ax.transAxes, fontsize=14, color='white', wrap=True)
        self.ax.axis('off')
        self.draw()

    def update_graph(self, story_data):
        self.story_data = story_data
        self.G.clear()
        self.edge_labels.clear()
        self.selected_node = None
        self.hovered_edge = None

        scenes = story_data.get('scenes', [])
        if not scenes:
            self.draw_empty_graph("В сгенерированной истории нет сцен."); return

        for scene in scenes:
            self.G.add_node(scene['scene_id'])

        for scene in scenes:
            for choice in scene.get('choices', []):
                next_scene_id = choice.get('next_scene')
                if next_scene_id and self.G.has_node(next_scene_id):
                    self.G.add_edge(scene['scene_id'], next_scene_id)
                    self.edge_labels[(scene['scene_id'], next_scene_id)] = choice.get('text', '...')

        self.redraw_graph()

    def _custom_hierarchical_layout(self):
        if not self.G.nodes(): return {}
        start_node = self.story_data.get('start_scene')
        pos = {}
        
        reachable_nodes = set()
        if start_node and self.G.has_node(start_node):
            reachable_nodes = set(nx.dfs_preorder_nodes(self.G, start_node))

        if reachable_nodes:
            subgraph = self.G.subgraph(reachable_nodes)
            levels = {start_node: 0}
            queue = [start_node]; head = 0
            while head < len(queue):
                u = queue[head]; head += 1
                for v in sorted(list(subgraph.successors(u))):
                    if v not in levels:
                        levels[v] = levels[u] + 1
                        queue.append(v)
            
            nodes_by_level = {}
            for node, level in levels.items():
                nodes_by_level.setdefault(level, []).append(node)
            
            y_spacing = -2.0; x_spacing = 2.0
            max_level = max(levels.values()) if levels else 0
            for level, nodes in sorted(nodes_by_level.items()):
                width = (len(nodes) - 1) * x_spacing
                start_x = -width / 2
                for i, node in enumerate(sorted(nodes)):
                    pos[node] = (start_x + i * x_spacing, level * y_spacing)
        else:
            max_level = -1

        unreachable_nodes = set(self.G.nodes()) - reachable_nodes
        if unreachable_nodes:
            subgraph = self.G.subgraph(unreachable_nodes)
            center_y = (max_level + 2) * -2.0
            sub_pos = nx.spring_layout(subgraph, seed=42, scale=len(unreachable_nodes), center=(0, center_y))
            pos.update(sub_pos)

        if len(pos) != len(self.G.nodes()):
            return nx.spring_layout(self.G, seed=42)

        return pos

    def redraw_graph(self):
        self.ax.clear()
        self.ax.set_facecolor('#1e1e2d')
        self.ax.axis('off')

        if not self.G.nodes:
            self.draw_empty_graph("Граф пуст."); return
            
        self.node_positions = self._custom_hierarchical_layout()

        if self.node_positions:
            if self.ax.get_xlim() == (0.0, 1.0) and self.ax.get_ylim() == (0.0, 1.0):
                x_coords, y_coords = zip(*self.node_positions.values())
                x_margin = (max(x_coords) - min(x_coords)) * 0.1
                y_margin = (max(y_coords) - min(y_coords)) * 0.1
                if x_margin < 1: x_margin = 1
                if y_margin < 1: y_margin = 1
                self.ax.set_xlim(min(x_coords) - x_margin, max(x_coords) + x_margin)
                self.ax.set_ylim(min(y_coords) - y_margin, max(y_coords) + y_margin)

        start_node = self.story_data.get('start_scene')
        end_nodes = [n for n, d in self.G.out_degree() if d == 0]
        node_colors = ['#51cf66' if n == start_node else '#ff6b6b' if n in end_nodes else '#4dabf7' for n in self.G.nodes()]

        self.edge_paths.clear()
        for edge in self.G.edges():
            source, target = edge
            pos_s = self.node_positions[source]
            pos_t = self.node_positions[target]
            
            edge_color = '#FFD700' if edge == self.hovered_edge else '#aaaaaa'
            edge_width = 3.0 if edge == self.hovered_edge else 2.0

            arrow = mpatches.FancyArrowPatch(
                posA=pos_s, posB=pos_t, 
                connectionstyle=f"arc3,rad=0.1",
                color=edge_color, 
                linewidth=edge_width, 
                arrowstyle='-|>',
                mutation_scale=30,
                shrinkA=30,
                shrinkB=30,
                alpha=0.8
            )
            self.ax.add_patch(arrow)
            self.edge_paths[edge] = arrow.get_path().vertices

        nx.draw_networkx_nodes(self.G, self.node_positions, ax=self.ax, node_size=2500, 
                              node_color=node_colors, edgecolors="white", linewidths=1.5)
        nx.draw_networkx_labels(self.G, self.node_positions, {n: str(n) for n in self.G.nodes()}, 
                               font_size=11, font_color="white", font_weight="bold")

        if self.selected_node:
            nx.draw_networkx_nodes(self.G, self.node_positions, nodelist=[self.selected_node], ax=self.ax, node_size=2600, node_color='none', edgecolors='#FFD700', linewidths=3)

        self.draw()

    def on_hover(self, event):
        if not event.inaxes or not self.node_positions or not self.G.edges():
            if self.hovered_edge:
                self.hovered_edge = None; self.redraw_graph(); QToolTip.hideText()
            return

        x, y = event.xdata, event.ydata
        hovered_edge = None
        min_distance_sq = float('inf')

        for edge in self.G.edges():
            u, v = edge
            pos_u = self.node_positions[u]
            pos_v = self.node_positions[v]
            mid_point = ((pos_u[0] + pos_v[0]) / 2, (pos_u[1] + pos_v[1]) / 2)
            dist_sq = (mid_point[0] - x)**2 + (mid_point[1] - y)**2

            if dist_sq < 0.1 and dist_sq < min_distance_sq:
                min_distance_sq = dist_sq
                hovered_edge = edge

        if hovered_edge != self.hovered_edge:
            self.hovered_edge = hovered_edge
            self.redraw_graph()

            if hovered_edge:
                QToolTip.showText(QCursor.pos(), self.edge_labels.get(hovered_edge, ""), self)
            else:
                QToolTip.hideText()

    def on_click(self, event):
        if not event.inaxes or not self.node_positions: return

        clicked_node = None
        min_dist_sq = float('inf')
        x, y = event.xdata, event.ydata

        for node, pos in self.node_positions.items():
            dist_sq = (pos[0] - x)**2 + (pos[1] - y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                clicked_node = node

        if min_dist_sq < 0.5:
            if self.selected_node == clicked_node:
                scene = next((s for s in self.story_data['scenes'] if s['scene_id'] == clicked_node), None)
                if scene:
                    dialog = SceneDetailDialog(scene, parent=self)
                    dialog.exec_()
            else:
                self.selected_node = clicked_node
        else:
            self.selected_node = None

        self.redraw_graph()

    def get_graph_statistics(self):
        if not self.G.nodes(): return "Статистика недоступна."
        num_endings = len([n for n, d in self.G.out_degree() if d == 0])
        return f"Сцен: {self.G.number_of_nodes()} | Концовок: {num_endings} | Переходов: {self.G.number_of_edges()}"