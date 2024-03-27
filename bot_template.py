import os
import telebot
import requests
import logging

BOT_TOKEN = "6547363557:AAGANK3kV2ywllU3LAAXzO7AxIUrtiHj0G0"

LOGS_DIR = "C:/Users/hot-z/Bot+GPT/"

logging.basicConfig(level=logging.DEBUG,
                    filename=os.path.join(LOGS_DIR, "example.log"),
                    format='%(asctime)s - %(levelname)s - %(message)s')

GPT_API_URL = "http://localhost:1234/v1/chat/completions"
REQUEST_HEADER = {"Content-Type": "application/json"}

CHAT_HISTORY_LIMIT = 20
TEMPERATURE = 0.7
MAX_TOKENS = 150
SYSTEM_PROMPT = "Следуй инструкции и отвечай коротко на русском языке."

bot = telebot.TeleBot(BOT_TOKEN)

chat_history = {}

@bot.message_handler(commands=["logging"])
def send_logs(message):
    logging.debug(f"User {message.from_user.id} requested logs")
    log_file_path = os.path.join(LOGS_DIR, "example.log")


    try:
        with open(log_file_path, 'rb') as file:
            bot.send_document(message.chat.id, file)
    except FileNotFoundError:
        bot.reply_to(message, "Извините, файл логов не найден.")

def ask_chatgpt(user_id: int, question: str):
    # Не добавляем сообщение пользователя в историю сразу, на случай если GPT не ответит
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + chat_history[user_id] 
        + [{"role": "user", "content": question}]
    )

    data = {
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "stop": "[INST]"
    }

    response = requests.post(GPT_API_URL, headers=REQUEST_HEADER, json=data)

    answer = None

    if response.status_code == 200:
        json_data = response.json()
        if "choices" in json_data and json_data["choices"]:
            answer = json_data["choices"][0]["message"]["content"]
            logging.debug(f"Получили ответ от  GPT: {answer}")
        else:
            logging.error(f"Нет ответа от GPT: {json_data}")
    else:
        logging.error(
            f"Ошибка в ответе - код ошибки: {str(response.status_code)}"
        )
    return answer

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    logging.debug(f"User {message.from_user.id} started the bot")

    bot.reply_to(
        message,
        "Привет! Я бот, который использует GPT для ответов на ваши вопросы. Просто напиши мне что-нибудь.",
    )

@bot.message_handler(commands=["history"])
def send_history(message):
    logging.debug(f"User {message.from_user.id} requested chat history")

    user_id = message.from_user.id
    if user_id in chat_history and len(chat_history[user_id]) > 0:
        history = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in chat_history[user_id]]
        )
        bot.reply_to(message, f"Ваша история сообщений:\n{history}")
    else:
        bot.reply_to(message, "У вас нет истории сообщений.")

@bot.message_handler()
def handle_message(message):
    logging.debug(f"User {message.from_user.id} sent a message: {message.text}")

    user_id = message.from_user.id
    if user_id not in chat_history:
        chat_history[user_id] = []

    # Получаем ответ от GPT
    response = ask_chatgpt(user_id, message.text)

    if response is None:
        logging.debug("Ошибка в запросе к GPT")
        bot.reply_to(
            message, "Извините, что-то не так с доступом к GPT. Попробуйте позже. "
        )
    else:
        logging.debug(f"Сохранение истории от пользователя {user_id}")
        # Добавляем сообщение пользователя в историю чата
        chat_history[user_id].append({"role": "user", "content": message.text})

        # Добавляем ответ бота в историю чата
        chat_history[user_id].append({"role": "assistant", "content": response})

        if len(chat_history[user_id]) > CHAT_HISTORY_LIMIT:
            logging.debug(f"История сообщений пользователя {user_id}")
            chat_history[user_id] = chat_history[user_id][-CHAT_HISTORY_LIMIT:]

        bot.reply_to(message, response)



bot.infinity_polling()