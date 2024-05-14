import telebot
import re
from config import TOKEN
from yandex_gpt import ask_gpt
from speechkit import speech_to_text, text_to_speech
from database import Database
from validators import check_token_limits, check_block_limits, check_char_limits

bot = telebot.TeleBot(TOKEN)
db = Database('bot_data.db')

# Включение/выключение отладочного режима
debug_mode = {}

# Список разрешенных пользователей
AUTHORIZED_USERS = set()
MAX_USERS = 10

# История сообщений
user_histories = {}


def add_to_history(user_id, message):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append(message)
    if len(user_histories[user_id]) > 2:  # Ограничение на количество сообщений в истории
        user_histories[user_id].pop(0)


def filter_greeting(message):
    greetings = ["привет", "здравствуйте", "добрый день", "добрый вечер", "доброе утро", "hi", "hello"]
    return any(greet in message.lower() for greet in greetings)


def clean_message(text):
    return re.sub(r'[*]', '', text)  # Удаление символа *


def filter_response(response):
    return re.sub(
        r'Человек:.*?AI:.*?Этот вариант продолжения диалога является лишь примером возможного развития событий\.', '',
        response, flags=re.DOTALL)


def is_new_topic(user_id, message):
    keywords = ["апельсин", "автомобиль", "фрукт", "машина"]  # Пример списка ключевых слов
    if user_id not in user_histories or len(user_histories[user_id]) == 0:
        return True
    last_message = user_histories[user_id][-1]
    for keyword in keywords:
        if keyword in last_message.lower() and keyword not in message.lower():
            return True
    return False


def get_chat_history(user_id):
    history = db.get_user_history(user_id)
    if not history:
        return ""

    # Создаем новый список, где сообщения переставлены
    reordered_history = []
    for i in range(0, len(history), 2):
        if i + 1 < len(history):
            # Добавляем сначала сообщение пользователя, потом ответ бота
            reordered_history.append(history[i + 1])  # Сообщение бота
            reordered_history.append(history[i])  # Сообщение пользователя
        else:
            # Если нечетное количество сообщений, добавляем оставшееся сообщение пользователя
            reordered_history.append(history[i])

    return "\n".join(reversed(reordered_history))  # Убедитесь, что порядок соответствует последовательно


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if len(AUTHORIZED_USERS) >= MAX_USERS:
        bot.reply_to(message, "Извините, достигнуто максимальное количество пользователей.")
        return

    AUTHORIZED_USERS.add(user_id)
    bot.reply_to(message, "Привет! Я готов общаться с тобой. Просто напиши мне или отправь голосовое сообщение.")
    db.add_user(user_id)


@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    help_text = """
    Просто отправь мне текст или голосовое сообщение, и я отвечу тебе так же.
    /stt - отправка голосового сообщения для тестирования распознавания речи.
    /tts - отправка текстового сообщения для тестирования синтеза речи.
    /help - показать эту справку.
    /debug - включение/выключение отладочного режима.
    /about - описание бота.
    """
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['about'])
def send_about(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    about_text = """
    Этот бот использует распознавание и синтез речи. Преобразует голос в текст и текст в голос. Поддерживает отладку и лимиты использования.
    """
    bot.reply_to(message, about_text)


@bot.message_handler(commands=['debug'])
def toggle_debug_mode(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    debug_mode[user_id] = not debug_mode.get(user_id, False)
    status = "включен" if debug_mode[user_id] else "выключен"
    bot.reply_to(message, f"Отладочный режим {status}")


@bot.message_handler(commands=['stt'])
def test_stt(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    bot.reply_to(message, "Пожалуйста, отправьте голосовое сообщение для тестирования распознавания речи.")
    debug_mode[user_id] = 'stt'


@bot.message_handler(commands=['tts'])
def test_tts(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    bot.reply_to(message, "Пожалуйста, отправьте текстовое сообщение для тестирования синтеза речи.")
    debug_mode[user_id] = 'tts'


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    if not check_token_limits(user_id, db) or not check_block_limits(user_id, db) or not check_char_limits(user_id, db):
        bot.reply_to(message, "Вы превысили лимит использования.")
        return

    if debug_mode.get(user_id) == 'tts':
        bot.reply_to(message, "Вы находитесь в режиме /tts. Отправьте текстовое сообщение или смените режим.")
        return

    try:
        file_info = bot.get_file(message.voice.file_id)
        voice_data = bot.download_file(file_info.file_path)
        success, text = speech_to_text(voice_data)

        if not success or not text:
            bot.reply_to(message, "Не удалось распознать речь или текст пуст.")
            return

        text = clean_message(text)

        if debug_mode.get(user_id, False):
            bot.reply_to(message, f"[DEBUG] Распознанный текст: {text}")

        if debug_mode.get(user_id) == 'stt':
            bot.reply_to(message, f"Распознанный текст: {text}")
            debug_mode[user_id] = False
            return

        if is_new_topic(user_id, text):
            user_histories[user_id] = []

        if not filter_greeting(text):
            add_to_history(user_id, text)

        history = get_chat_history(user_id)
        context = f"В контексте нашего разговора \n{history}\n user:у \n{text}"

        max_tokens = 1000
        context_tokens = context.split()
        if len(context_tokens) > max_tokens:
            excess_tokens = len(context_tokens) - max_tokens
            context_tokens = context_tokens[excess_tokens:]
            context = " ".join(context_tokens)
        print(context)
        try:
            response_text = ask_gpt(context)
        except RuntimeError as e:
            bot.reply_to(message, f"Ошибка при получении ответа от GPT: {str(e)}")
            return

        if not response_text:
            bot.reply_to(message, "Не удалось получить ответ от GPT.")
            return

        response_text = clean_message(response_text)
        response_text = filter_response(response_text)

        add_to_history(user_id, response_text)
        success, audio_response = text_to_speech(response_text)
        if success:
            bot.send_voice(chat_id=user_id, voice=audio_response)
        else:
            bot.reply_to(message, "Ошибка при создании аудио ответа.")

        # Сохранение сообщений в базе данных после отправки ответа
        db.save_message(user_id, f"user: {text}", "voice")
        db.save_message(user_id, f"bot: {response_text}", "text")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке голосового сообщения: {str(e)}")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        bot.reply_to(message, "Извините, вы не авторизованы для использования этого бота.")
        return

    if len(message.text) > 1000:
        bot.reply_to(message, "Ваше сообщение слишком длинное.")
        return

    if not check_token_limits(user_id, db) or not check_block_limits(user_id, db) or not check_char_limits(user_id, db):
        bot.reply_to(message, "Вы превысили лимит использования.")
        return

    if debug_mode.get(user_id) == 'stt':
        bot.reply_to(message, "Вы находитесь в режиме /stt. Отправьте голосовое сообщение или смените режим.")
        return

    try:
        clean_text = clean_message(message.text)

        if debug_mode.get(user_id) == 'tts':
            success, audio_response = text_to_speech(clean_text)
            if success:
                bot.send_voice(chat_id=user_id, voice=audio_response)
                if debug_mode.get(user_id, False):
                    bot.reply_to(message, f"[DEBUG] Текст для синтеза: {clean_text}")
            else:
                bot.reply_to(message, "Ошибка при создании аудио ответа.")
            debug_mode[user_id] = False
            return

        if is_new_topic(user_id, clean_text):
            user_histories[user_id] = []

        if not filter_greeting(clean_text):
            add_to_history(user_id, clean_text)

        history = get_chat_history(user_id)
        context = f"В контексте нашего разговора \n{history}\n user:\n{clean_text}"

        max_tokens = 1000
        context_tokens = context.split()
        if len(context_tokens) > max_tokens:
            excess_tokens = len(context_tokens) - max_tokens
            context_tokens = context_tokens[excess_tokens:]
            context = " ".join(context_tokens)
        print(context)
        try:
            response_text = ask_gpt(context)
        except RuntimeError as e:
            bot.reply_to(message, f"Ошибка при получении ответа от GPT: {str(e)}")
            return

        if not response_text:
            bot.reply_to(message, "Не удалось получить ответ от GPT.")
            return

        response_text = clean_message(response_text)
        response_text = filter_response(response_text)

        db.update_chars_used(user_id, len(clean_text))
        add_to_history(user_id, response_text)
        bot.reply_to(message, response_text)

        if debug_mode.get(user_id, False):
            bot.reply_to(message, f"[DEBUG] Текст ответа: {response_text}")

        # Сохранение сообщений в базе данных после отправки ответа
        db.save_message(user_id, f"user: {clean_text}", "text")
        db.save_message(user_id, f"bot: {response_text}", "text")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке текстового сообщения: {str(e)}")


if __name__ == "__main__":
    bot.polling(non_stop=True)
