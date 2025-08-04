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