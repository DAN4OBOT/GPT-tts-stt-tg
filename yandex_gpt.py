from creds import IAM_TOKEN, FOLDER_ID
import requests
def ask_gpt(text):
    if not text.strip():
        return "Текст не был получен или он пуст."

    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 200
        },
        "messages": [
            {
                "role": "user",
                "text": text
            }
        ]
    }
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    else:
        raise RuntimeError(f'Invalid response received: code: {response.status_code}, message: {response.text}')
