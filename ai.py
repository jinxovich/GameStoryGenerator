import aiohttp
import json
import re

from config import YANDEX_ID_KEY, YANDEX_API_KEY
from StoryObject import StoryObject

def clean_json_response(text: str) -> str:
    """
    Очищает и исправляет ответ от AI, удаляя лишние символы и вставляя
    недостающие запятые между объектами в JSON-массиве.
    """
    # Удаление markdown-блоков ```json и ```
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # Поиск первого '[' и последнего ']' для извлечения массива
    start = text.find('[')
    end = text.rfind(']')
    
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("Не удалось найти валидный JSON-массив в ответе.", text, 0)
        
    # Извлекаем содержимое массива
    content = text[start+1:end].strip()
    
    # **Ключевое исправление**: Вставляем запятые между объектами.
    # Заменяем "}\s*{" на "}, {". Это исправляет ошибку отсутствия запятой.
    fixed_content = re.sub(r'\}\s*\{', '}, {', content, flags=re.DOTALL)
    
    # Собираем исправленный JSON-массив
    return f"[{fixed_content}]"

def convert_ai_array_to_graph_format(scene_list: list[dict], story_object: StoryObject) -> dict:
    """
    Собирает единый объект истории из списка сцен, полученных от AI.
    """
    if not scene_list:
        raise ValueError("AI вернул пустой список сцен.")
        
    all_scene_ids = {scene['scene_id'] for scene in scene_list if 'scene_id' in scene}
    referenced_ids = set()
    for scene in scene_list:
        for choice in scene.get('choices', []):
            if 'next_scene' in choice and choice['next_scene'] in all_scene_ids:
                referenced_ids.add(choice['next_scene'])
            
    # Стартовая сцена — это та, на которую не ссылается ни одна другая сцена.
    start_scene_ids = all_scene_ids - referenced_ids
    
    if not start_scene_ids:
        # В случае ошибки или цикла, предполагаем, что сцена "1" является стартовой
        start_scene_id = "1"
        if start_scene_id not in all_scene_ids:
            raise ValueError("Не удалось определить стартовую сцену, и сцена '1' отсутствует.")
    else:
        start_scene_id = list(start_scene_ids)[0]
        
    # Форматирование сцен в формат, который использует остальное приложение.
    formatted_scenes = []
    for scene_data in scene_list:
        scene_id = scene_data['scene_id']
        formatted_scenes.append({
            'id': scene_id,
            'title': scene_data.get('title', f"Сцена {scene_id}"),
            'description': scene_data.get('text', 'Описание отсутствует.'),
            'choices': [{
                'text': c.get('text', '...'),
                'next_scene_id': c.get('next_scene', '')
            } for c in scene_data.get('choices', [])],
            'is_ending': not scene_data.get('choices')
        })
        
    # Сборка финального объекта для GUI и графа.
    return {
        'title': f"RPG: {story_object.genre}",
        'description': story_object.description,
        'start_scene': start_scene_id,
        'scenes': formatted_scenes
    }

async def get_story_from_ai(story_object: StoryObject) -> dict:
    """Асинхронно запрашивает историю у YandexGPT и возвращает ее в виде словаря."""
    if not YANDEX_API_KEY or not YANDEX_ID_KEY:
        raise ValueError("YANDEX_API_KEY и YANDEX_ID_KEY должны быть установлены в .env файле.")

    prompt = {
        "modelUri": f"gpt://{YANDEX_ID_KEY}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.75, # Немного увеличена для разнообразия
            "maxTokens": "16000" # Увеличен запас токенов
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
                      "scene_id": "НОМЕР_СЦЕНЫ_В_ВИДЕ_СТРОКИ",
                      "text": "Полное, насыщенное описание сцены (80-150 слов).",
                      "choices": [
                        {"text": "Краткое описание выбора (2-5 слов)", "next_scene": "НОМЕР_СЛЕДУЮЩЕЙ_СЦЕНЫ"}
                      ]
                    }
                3.  **ЗАПЯТЫЕ**: Между КАЖДЫМ объектом в массиве (например, между `}` и `{`) ДОЛЖНА стоять запятая.
                
                СТРОГИЕ СТРУКТУРНЫЕ ОГРАНИЧЕНИЯ:
                - **ID СЦЕН**: `scene_id` — это **ЧИСЛО В ВИДЕ СТРОКИ** (например, "1", "2", "3"). Стартовая сцена **ВСЕГДА** имеет `scene_id: "1"`.
                - **ЗАПРЕТ НА ВОЗВРАТ К НАЧАЛУ**: Никакой `next_scene` не должен ссылаться на `"1"`.
                - **ЗАПРЕТ НА ДВИЖЕНИЕ ВВЕРХ**: Сцена с большим `scene_id` **НЕ МОЖЕТ** ссылаться на сцену с меньшим `scene_id`. Например, выбор в сцене `"5"` не может вести в `"3"`. Движение только вперед!
                
                ТРЕБОВАНИЯ К КОНТЕНТУ:
                -   **Жанр**: Строго Ролевая игра (RPG).
                -   **Язык**: Русский.
                -   **Количество сцен**: От 5 до 10.
                -   **ДВЕ КОНЦОВКИ**: Обязательно создай минимум две разные концовки (сцены с `choices: []`). Одна концовка должна быть условно "хорошей", а другая — "плохой".
                -   **Ветвление**: Обязательно создай минимум одну развилку. Хотя бы одна ветка сюжета (последовательность из 2-3 сцен после выбора) должна приводить к уникальному результату.
                -   **Связность**: ВСЕ сцены, кроме стартовой (`"1"`), должны быть достижимы. Не должно быть "висячих" сцен.
                """
            },
            {
                "role": "user",
                "text": f"""Создай RPG квест по параметрам:
                - **Описание**: {story_object.description}
                - **Персонажи**: {', '.join(story_object.heroes)}
                - **Настроение**: {story_object.mood}
                - **Тема**: {story_object.theme}
                - **Конфликт**: {story_object.conflict}

                Напоминаю: единый JSON-массив, `scene_id` - это числа, движение сюжета только вперед, 2 концовки (хорошая/плохая).
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