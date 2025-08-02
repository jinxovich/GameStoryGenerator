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
                "temperature": 0.7,
                "maxTokens": "10000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": """Ты профессиональный сценарист, специализирующийся на интерактивных квестах. 
                    Создай увлекательный ПОЛНОСТЬЮ ВЗАИМОСВЯЗАННЫЙ нелинейный квест на основе предоставленных параметров. 
                    
                    КРИТИЧЕСКИ ВАЖНО:
                    1. ВСЕ сцены должны быть доступны через выборы из других сцен
                    2. Создай МИНИМУМ 5-12 сцен с разветвлениями
                    3. Должно быть минимум 2 различных концовки
                    4. Каждый выбор должен иметь КРАТКОЕ но ОСМЫСЛЕННОЕ название (2-4 слова)
                    5. НЕ должно быть "висячих" сцен, до которых нельзя добраться
                    
                    Результат должен быть ТОЛЬКО в формате JSON без дополнительных объяснений или форматирования markdown."""
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
                    """ + 
                    """ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
                    1. Минимум 5-12 взаимосвязанных сцен
                    2. Минимум 2 концовки (хорошая, плохая)
                    3. Каждая сцена должна быть доступна через выборы
                    4. Названия выборов: краткие и понятные (2-4 слова)
                    5. Насыщенные описания сцен (100-200 слов каждая)
                    
                    Верни ТОЛЬКО валидный JSON в следующем формате:
                    {
                        "title": "Название квеста",
                        "description": "Общее описание квеста",
                        "start_scene": "начальная_сцена",
                        "scenes": {
                            "scene_id_1": {
                                "text": "Описание сцены",
                                "choices": [
                                    {
                                        "text": "Выбор 1",
                                        "next_scene": "scene_id_2"
                                    },
                                    {
                                        "text": "Выбор 2",
                                        "next_scene": "scene_id_3"
                                    }
                                ]
                            },
                            "scene_id_2": {
                                "text": "Описание сцены",
                                "choices": []
                            }
                        }
                    }"""
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
                
                try:
                    # First try to parse the full response
                    result = json.loads(response_text)
                    generated_text = result["result"]["alternatives"][0]["message"]["text"]
                except (json.JSONDecodeError, KeyError):
                    # If that fails, maybe we got the raw JSON directly
                    generated_text = response_text
                
                print("Generated text:", generated_text)
                
                # Clean the response text
                cleaned_text = clean_json_response(generated_text)
                print("Cleaned text:", cleaned_text)

                # Try to parse the cleaned JSON
                try:
                    quest_json = json.loads(cleaned_text)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    # Try to find the JSON part in the text
                    json_start = cleaned_text.find('{')
                    json_end = cleaned_text.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        quest_json = json.loads(cleaned_text[json_start:json_end])
                    else:
                        raise

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
                'title': extract_title_from_text(scene_data.get('text', ''), scene_id),
                'description': scene_data.get('text', ''),
                'characters': extract_characters_from_text(scene_data.get('text', '')),
                'choices': [],
                'is_ending': len(scene_data.get('choices', [])) == 0
            }
            
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

def extract_title_from_text(text, fallback_id):
    """Извлекает заголовок из первых слов текста"""
    if not text:
        return fallback_id
    
    words = text.split()[:3]
    title = ' '.join(words)
    if len(title) > 20:
        title = title[:17] + "..."
    return title if title else fallback_id

def extract_characters_from_text(text):
    import re
    names = re.findall(r'\b[А-ЯA-Z][а-яa-z]+\b', text)
    common_words = {'Вы', 'Ваш', 'Ваша', 'Вас', 'Они', 'Он', 'Она', 'Это', 'Там', 'Тут'}
    names = [name for name in names if name not in common_words]
    return list(set(names))[:3]

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