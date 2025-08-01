import requests
from config import YANDEX_ID_KEY, YANDEX_API_KEY
import json

async def get(text: str, content: str) -> str:
    try:
        prompt = {
            "modelUri": f"gpt://{YANDEX_ID_KEY}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "user",
                    "text": content + text
                }
            ]
        }

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        response = requests.post(url, headers=headers, json=prompt)
        return json.loads(response.text)["result"]["alternatives"][0]["message"]["text"]
    except:
        return None