import aiohttp
import asyncio
from config import YANDEX_ID_KEY, YANDEX_API_KEY
import json
import re

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
                    Результат должен быть ТОЛЬКО в формате JSON без дополнительных объяснений или форматирования markdown."""
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
                    
                    Верни ТОЛЬКО валидный JSON без дополнительного текста или markdown разметки:
                    {{
                        "title": "Название истории",
                        "description": "Краткое описание сюжета",
                        "genre": "{story_object.genre}",
                        "mood": "{story_object.mood}",
                        "scenes": [
                            {{
                                "id": "scene1",
                                "title": "Начало пути",
                                "description": "Подробное описание сцены...",
                                "characters": ["имя_персонажа"],
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
                            }}
                        ],
                        "main_branch": ["scene1", "scene2"],
                        "alternative_branches": [
                            {{
                                "path": ["scene1", "scene3"],
                                "description": "Альтернативный путь"
                            }}
                        ]
                    }}"""
                }
            ]
        }

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        # Используем aiohttp для асинхронного запроса
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=prompt) as response:
                response.raise_for_status()
                
                response_text = await response.text()
                print("Raw response:", response_text)
                
                # Парсим основной ответ от Yandex API
                result = json.loads(response_text)
                
                # Извлекаем текст генерации
                generated_text = result["result"]["alternatives"][0]["message"]["text"]
                print("Generated text:", generated_text)
                
                # Очищаем текст от возможных markdown блоков
                cleaned_text = clean_json_response(generated_text)
                print("Cleaned text:", cleaned_text)
                
                # Парсим JSON истории
                story_json = json.loads(cleaned_text)
                return story_json
                
    except aiohttp.ClientError as e:
        print(f"HTTP request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Problematic text: {cleaned_text if 'cleaned_text' in locals() else 'N/A'}")
        return None
    except KeyError as e:
        print(f"Key error in response: {e}")
        print(f"Response structure: {result if 'result' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def clean_json_response(text):
    """Очищает ответ от markdown разметки и лишних символов"""
    # Убираем markdown код блоки
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    
    # Убираем лишние пробелы и переносы в начале и конце
    text = text.strip()
    
    # Если текст не начинается с {, ищем первую {
    if not text.startswith('{'):
        start_index = text.find('{')
        if start_index != -1:
            text = text[start_index:]
    
    # Если текст не заканчивается на }, ищем последнюю }
    if not text.endswith('}'):
        end_index = text.rfind('}')
        if end_index != -1:
            text = text[:end_index + 1]
    
    return text