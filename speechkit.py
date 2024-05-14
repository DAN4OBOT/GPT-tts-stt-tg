import requests
from creds import IAM_TOKEN, FOLDER_ID

def speech_to_text(audio_data):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'audio/ogg'
    }
    params = {
        'folderId': FOLDER_ID,
        'lang': 'ru-RU'
    }
    response = requests.post("https://stt.api.cloud.yandex.net/speech/v1/stt:recognize", headers=headers, params=params, data=audio_data)
    if response.status_code == 200:
        result = response.json()
        return True, result.get('result')
    else:
        return False, f"Ошибка распознавания речи: {response.status_code}, {response.text}"

def text_to_speech(text):
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}'
    }
    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'alyss',
        'emotion': 'good',
        'folderId': FOLDER_ID,
        'format': 'oggopus'
    }
    response = requests.post("https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize", headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content
    else:
        print(f"Ошибка синтеза речи: {response.status_code}, {response.text}")
        return False, None