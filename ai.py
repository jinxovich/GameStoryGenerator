import requests
from config import YANDEX_ID_KEY, YANDEX_API_KEY
import json

async def get(story_object) -> dict:
    try:
        prompt = {
            "modelUri": f"gpt://{YANDEX_ID_KEY}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.5,
                "maxTokens": "10000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": """Ты профессиональный сценарист, специализирующийся на интерактивных историях и квестах. 
                    Сгенерируй увлекательный нелинейный сюжет на основе предоставленных параметров. 
                    Результат должен быть в формате JSON с четкой структурой ветвления."""
                },
                {
                    "role": "user",
                    "text": f"""Сгенерируй интерактивную историю в жанре {story_object.genre} со следующими параметрами:
                    
                    Основное описание: {story_object.description}
                    Главные герои: {', '.join(story_object.heroes)}
                    Стиль повествования: {story_object.narrative_style}
                    Настроение: {story_object.mood}
                    Тема: {story_object.theme}
                    Основной конфликт: {story_object.conflict}
                    {'Контент для взрослых: Да' if story_object.adult else ''}
                    
                    Требования к структуре:
                    1. Минимум 5 ключевых сцен (включая вступление и финал)
                    2. Как минимум одна полноценная развилка с выбором, ведущим к разным последствиям
                    3. Глубина хотя бы одной побочной ветви - не менее 3 последовательных сцен
                    4. Каждая сцена должна содержать:
                    - id (уникальный идентификатор)
                    - title (название сцены)
                    - description (описание происходящего)
                    - characters (участвующие персонажи)
                    - choices (массив вариантов выбора, если есть)
                        - text (текст выбора)
                        - next_scene_id (id следующей сцены)
                    - is_ending (флаг финальной сцены)
                    
                    Пример структуры JSON:
                    {{
                        "title": "Название истории",
                        "description": "Краткое описание сюжета",
                        "genre": "{story_object.genre}",
                        "mood": "{story_object.mood}",
                        "scenes": [
                            {{
                                "id": "scene1",
                                "title": "Начало пути",
                                "description": "...",
                                "characters": ["..."],
                                "choices": [
                                    {{
                                        "text": "Выбрать путь через лес",
                                        "next_scene_id": "scene2"
                                    }},
                                    {{
                                        "text": "Пойти по дороге",
                                        "next_scene_id": "scene3"
                                    }}
                                ],
                                "is_ending": false
                            }},
                            ...
                        ],
                        "main_branch": ["scene1", "scene2", ...],
                        "alternative_branches": [
                            {{
                                "path": ["scene1", "scene3", "scene4"],
                                "description": "Альтернативный путь через дорогу"
                            }}
                        ]
                    }}
                    
                    Убедись, что:
                    - Все сцены логически связаны
                    - Выборы имеют значимые последствия
                    - Соблюдены все технические требования
                    - JSON валиден и готов к использованию в программе"""
                }
            ]
        }

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        response = requests.post(url, headers=headers, json=prompt)
        response.raise_for_status()
        
        print(response.text)
        result = json.loads(response.text)
        
        generated_text = result["result"]["alternatives"][0]["message"]["text"]
        
        story_json = json.loads(generated_text)
        return story_json
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    except KeyError as e:
        print(f"Key error in response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None