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
                    "text": """Ты профессиональный сценарист, специализирующийся на интерактивных квестах. 
                    Создай увлекательный нелинейный квест на основе предоставленных параметров. 
                    Результат должен быть ТОЛЬКО в формате JSON без дополнительных объяснений или форматирования markdown.
                    
                    Структура каждой сцены:
                    - scene_id: уникальный идентификатор сцены
                    - text: основной текст сцены с описанием ситуации, окружения, действий персонажей
                    - choices: массив вариантов действий, каждый с полями text и next_scene
                    
                    Создай минимум 5-7 взаимосвязанных сцен с разветвлениями и как минимум 2 концовками."""
                },
                {
                    "role": "user",
                    "text": f"""Создай интерактивный квест в жанре {story_object.genre} со следующими параметрами:
                    
                    Основное описание: {story_object.description}
                    Главные герои: {', '.join(story_object.heroes)}
                    Стиль повествования: {story_object.narrative_style}
                    Настроение: {story_object.mood}
                    Тема: {story_object.theme}
                    Основной конфликт: {story_object.conflict}
                    
                    Верни ТОЛЬКО валидный JSON в следующем формате:
                    {{
                        "title": "Название квеста",
                        "description": "Краткое описание квеста",
                        "start_scene": "scene1",
                        "scenes": {{
                            "scene1": {{
                                "scene_id": "scene1",
                                "text": "Подробный текст первой сцены с описанием ситуации...",
                                "choices": [
                                    {{
                                        "text": "Выбрать действие 1",
                                        "next_scene": "scene2"
                                    }},
                                    {{
                                        "text": "Выбрать действие 2", 
                                        "next_scene": "scene3"
                                    }}
                                ]
                            }},
                            "scene2": {{
                                "scene_id": "scene2",
                                "text": "Текст второй сцены...",
                                "choices": [
                                    {{
                                        "text": "Продолжить",
                                        "next_scene": "scene4"
                                    }}
                                ]
                            }},
                            "scene3": {{
                                "scene_id": "scene3", 
                                "text": "Текст третьей сцены...",
                                "choices": [
                                    {{
                                        "text": "Действие",
                                        "next_scene": "scene5"
                                    }}
                                ]
                            }},
                            "scene4": {{
                                "scene_id": "scene4",
                                "text": "Концовка 1. Подробное описание завершения истории...",
                                "choices": []
                            }},
                            "scene5": {{
                                "scene_id": "scene5",
                                "text": "Концовка 2. Альтернативное завершение истории...", 
                                "choices": []
                            }}
                        }}
                    }}
                    
                    Важно: создай насыщенные текстом сцены с атмосферными описаниями, диалогами и действиями персонажей."""
                }
            ]
        }

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=prompt) as response:
                response.raise_for_status()
                
                response_text = await response.text()
                print("Raw response:", response_text)
                
                result = json.loads(response_text)

                generated_text = result["result"]["alternatives"][0]["message"]["text"]
                print("Generated text:", generated_text)
                
                cleaned_text = clean_json_response(generated_text)
                print("Cleaned text:", cleaned_text)

                quest_json = json.loads(cleaned_text)

                converted_story = convert_to_old_format(quest_json)
                
                return converted_story
                
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

def convert_to_old_format(quest_data):
    try:
        scenes_list = []
        scenes_dict = quest_data.get('scenes', {})
        
        for scene_id, scene_data in scenes_dict.items():
            scene = {
                'id': scene_data.get('scene_id', scene_id),
                'title': f"Сцена {scene_id}",  # Можно улучшить, извлекая из текста
                'description': scene_data.get('text', ''),
                'characters': [],  # Можно попытаться извлечь из текста
                'choices': [],
                'is_ending': len(scene_data.get('choices', [])) == 0
            }
            
            # Конвертируем выборы
            for choice in scene_data.get('choices', []):
                scene['choices'].append({
                    'text': choice.get('text', ''),
                    'next_scene_id': choice.get('next_scene', '')
                })
            
            scenes_list.append(scene)
        
        converted = {
            'title': quest_data.get('title', 'Интерактивная история'),
            'description': quest_data.get('description', ''),
            'genre': 'Интерактивный квест',
            'mood': 'Увлекательный',
            'scenes': scenes_list,
            'main_branch': [],
            'alternative_branches': []
        }

        start_scene = quest_data.get('start_scene')
        if start_scene and start_scene in scenes_dict:
            main_path = []
            current_scene = start_scene
            visited = set()
            
            while current_scene and current_scene not in visited and current_scene in scenes_dict:
                main_path.append(current_scene)
                visited.add(current_scene)
                
                choices = scenes_dict[current_scene].get('choices', [])
                if choices:
                    current_scene = choices[0].get('next_scene')
                else:
                    break
            
            converted['main_branch'] = main_path
        
        return converted
        
    except Exception as e:
        print(f"Error converting quest format: {e}")
        return quest_data

def clean_json_response(text):
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    
    text = text.strip()
    
    if not text.startswith('{'):
        start_index = text.find('{')
        if start_index != -1:
            text = text[start_index:]
    
    if not text.endswith('}'):
        end_index = text.rfind('}')
        if end_index != -1:
            text = text[:end_index + 1]
    
    return text