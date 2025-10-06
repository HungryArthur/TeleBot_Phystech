import time
import os
import telebot
import requests
import pytz
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Функция для создания сессии с повторными попытками
def create_session():
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; TelegramBot/1.0)'
    })
    
    return session

# Функция для получения случайного котика
def get_random_cat():
    try:
        response = bot.session.get(
            'https://api.thecatapi.com/v1/images/search', 
            timeout=10
        )
        if response.status_code == 200:
            return response.json()[0]['url']
        else:
            print(f"Ошибка API котиков: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка при загрузке котика: {e}")
        return None

# Функция для получения случайной собачки
def get_random_dog():
    try:
        response = bot.session.get(
            'https://dog.ceo/api/breeds/image/random', 
            timeout=10
        )
        if response.status_code == 200:
            return response.json()['message']
        else:
            print(f"Ошибка API собачек: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка при загрузке собачки: {e}")
        return None

# Создаем бота с кастомной сессией
bot = telebot.TeleBot(TOKEN)
bot.session = create_session()

TIMEZONE = pytz.timezone('Europe/Moscow')
chat_ids = set()
sent_birthdays = set()
last_reset_date = None
morning_sent_today = False
evening_sent_today = False

birthdays = {
    "10.01": ["Михаил 🎂", "Никита 🎂"],
    "24.04": ["Никита 🥳", "Мария 🎂"],
    "30.05": ["Артем 🎂", "Евгений 🥳"],
    "23.12": ["Денис 🎉"],
    "13.01": ["Диана 🎂"],
    "14.04": ["Алла 🥳"],
    "14.01": ["Владислав 🥳"],
    "01.02": ["Даниил 🎂"],
    "19.02": ["Вероника 🥳"],
    "20.03": ["Ксюша 🎂"],
    "29.03": ["Полина 🎂"],
    "30.04": ["Вадим 🥳"],
    "08.06": ["Александр 🎂"],
    "20.06": ["Даниэль 🥳"],
    "22.06": ["Игорь 🎉"],
    "04.07": ["Егор 🎂"],
    "29.07": ["Егор 🥳"],
    "10.08": ["Матвей 🎂"],
    "28.08": ["Максим 🥳"],
    "26.09": ["Анастасия 🎂"],
    "08.10": ["Артур 🥳"],
    "26.10": ["Дарья 🎂"],
    "13.11": ["Никита 🥳"],
    "16.11": ["Кирилл 🎂"],
    "25.11": ["Кирилл 🥳"],
    "03.02": ["Мухаммад 🥳"],
    "01.10": ["Ирина Александровна 🎂🥳🎉"]
}

# Команда /start добавляет чат в рассылку
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        bot.reply_to(message, "Я буду присылать добрые утра и спокойные вечера с котиками, а также поздравлять с ДР! 😊\n\nРассылки в:\n• 8:00 - Доброе утро с котиком\n• 20:00 - Спокойной ночи с котиком/собачкой")
    else:
        bot.reply_to(message, "Я уже работаю в этом чате! 🐱")

# Команда /stop удаляет чат из рассылки
@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        bot.reply_to(message, "Рассылка остановлена. Используйте /start чтобы снова включить.")
    else:
        bot.reply_to(message, "Рассылка и так не активна в этом чате.")

# Команда /status показывает статус сессии
@bot.message_handler(commands=['status'])
def status(message):
    chat_id = message.chat.id
    if hasattr(bot, 'session') and bot.session:
        status_text = "✅ Сессия активна\n"
        status_text += f"📊 Чатов в рассылке: {len(chat_ids)}\n"
        status_text += f"📅 Сегодня: {datetime.now(TIMEZONE).strftime('%d.%m.%Y')}"
    else:
        status_text = "❌ Сессия не активна"
    
    bot.reply_to(message, status_text)

# Рассылка в указанное время
def check_birthdays_and_send_messages():
    global sent_birthdays, last_reset_date, morning_sent_today, evening_sent_today
    
    while True:
        try:
            now = datetime.now(TIMEZONE)
            today_date = now.strftime("%d.%m")
            current_time = now.strftime("%H:%M")
            
            # Сброс флагов при смене дня
            if last_reset_date != today_date:
                sent_birthdays.clear()
                morning_sent_today = False
                evening_sent_today = False
                last_reset_date = today_date
                print(f"Новый день: {today_date}, сброс флагов рассылки")

            # Проверка ДР
            if today_date in birthdays and today_date not in sent_birthdays:
                names = ", ".join(birthdays[today_date])
                print(f"Обнаружены ДР: {names}")
                
                for chat_id in list(chat_ids):
                    try:
                        bot.send_message(chat_id, f"🎉 Сегодня День рождения у {names}! Поздравляем! 🎂")
                        print(f"Поздравление отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка отправки поздравления в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                sent_birthdays.add(today_date)
                print(f"ДР на {today_date} отмечены как отправленные")

            # Утренняя рассылка (8:00)
            if now.hour == 8 and now.minute == 0 and not morning_sent_today:
                print("Время утренней рассылки!")
                cat_image_url = get_random_cat()
                
                for chat_id in list(chat_ids):
                    try:
                        if cat_image_url:
                            bot.send_photo(chat_id, cat_image_url, 
                                         caption="Доброе утро! ☀️ Лови котика для хорошего настроения! Пусть день будет продуктивным и радостным! 😊")
                            print(f"Утренний котик отправлен в чат {chat_id}")
                        else:
                            bot.send_message(chat_id, 
                                          "Доброе утро! ☀️ Котик сбежал, но пожелание осталось! Пусть ваш день будет прекрасным! 😊")
                            print(f"Утреннее сообщение без котика отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка утренней рассылки в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                morning_sent_today = True
                print("Утренняя рассылка завершена")
                time.sleep(60)  # Защита от дублирования

            # Вечерняя рассылка (20:00)
            elif now.hour == 20 and now.minute == 0 and not evening_sent_today:
                print("Время вечерней рассылки!")
                # Чередуем котиков и собачек для разнообразия
                if now.day % 2 == 0:  # Четные дни - котики
                    pet_image_url = get_random_cat()
                    pet_type = "котика"
                else:  # Нечетные дни - собачки
                    pet_image_url = get_random_dog()
                    pet_type = "собачку"
                
                for chat_id in list(chat_ids):
                    try:
                        if pet_image_url:
                            caption = f"Спокойной ночи! 🌙 Лови {pet_type} для сладких снов! Отдыхайте и набирайтесь сил на завтра! 😴💫"
                            
                            bot.send_photo(chat_id, pet_image_url, caption=caption)
                            print(f"Вечерний питомец отправлен в чат {chat_id}")
                        else:
                            bot.send_message(chat_id, 
                                          "Спокойной ночи! 🌙 Питомец убежал спать, но пожелание осталось! Хороших снов и приятных сновидений! 😴✨")
                            print(f"Вечернее сообщение без питомца отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка вечерней рассылки в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                evening_sent_today = True
                print("Вечерняя рассылка завершена")
                time.sleep(60)  # Защита от дублирования
            
            time.sleep(30)  # Проверка каждые 30 секунд
            
        except Exception as e:
            print(f"Критическая ошибка в основном цикле: {e}")
            time.sleep(60)

# Запуск бота с обработкой ошибок
def start_bot():
    print("Бот запущен... :)")
    print("Рассылки запланированы на:")
    print("• 8:00 - Доброе утро с котиком")
    print("• 20:00 - Спокойной ночи с котиком/собачкой")
    print("Используется кастомная сессия с повторными попытками")
    
    # Запускаем фоновый поток для рассылки
    Thread(target=check_birthdays_and_send_messages, daemon=True).start()
    
    # Запускаем polling с обработкой ошибок
    while True:
        try:
            print("Запуск polling...")
            bot.polling(
                timeout=30,
                long_polling_timeout=30,
                non_stop=True
            )
        except Exception as e:
            print(f"Ошибка в polling: {e}")
            print("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
