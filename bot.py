import time
import os
import telebot
import requests
import pytz
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env
TOKEN = os.getenv("TOKEN")  # Безопасное получение токена

bot = telebot.TeleBot(TOKEN)
TIMEZONE = pytz.timezone('Europe/Moscow')  # Временная зона GMT+3(время по мск)
chat_ids = set()  # Множество для хранения ID чатов
sent_birthdays = set()  # сюда будем записывать даты, по которым уже поздравили
last_reset_date = None  # Для отслеживания смены дня

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

# Функция для получения случайного котика
def get_random_cat():
    try:
        response = requests.get('https://api.thecatapi.com/v1/images/search', timeout=10)
        if response.status_code == 200:
            return response.json()[0]['url']  # Ссылка на картинку
        else:
            return None
    except Exception as e:
        print(f"Ошибка при загрузке котика: {e}")
        return None

# Команда /start добавляет чат в рассылку
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        bot.reply_to(message, "Я буду присылать добрые утра с котиками и поздравлять с ДР! 😊")
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

# Рассылка во время которое я укажу
def check_birthdays_and_send_messages():
    global sent_birthdays, last_reset_date
    
    while True:
        try:
            now = datetime.now(TIMEZONE)
            today_date = now.strftime("%d.%m")
            
            # Сброс sent_birthdays при смене дня
            if last_reset_date != today_date:
                sent_birthdays.clear()
                last_reset_date = today_date
                print(f"Новый день: {today_date}, сброс sent_birthdays")

            # Проверка ДР
            if today_date in birthdays and today_date not in sent_birthdays:
                names = ", ".join(birthdays[today_date])
                print(f"Обнаружены ДР: {names}")
                
                for chat_id in list(chat_ids):  # Используем list для копии на случай изменений
                    try:
                        bot.send_message(chat_id, f"🎉 Сегодня День рождения у {names}! Поздравляем! 🎂")
                        print(f"Поздравление отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка отправки поздравления в чат {chat_id}: {e}")
                        # Удаляем невалидный chat_id
                        chat_ids.discard(chat_id)
                
                sent_birthdays.add(today_date)
                print(f"ДР на {today_date} отмечены как отправленные")

            # Доброе утро + Котики
            if now.hour == 8 and now.minute == 0:  # Указываю время
                print("Время отправки доброго утра!")
                cat_image_url = get_random_cat()
                
                for chat_id in list(chat_ids):
                    try:
                        if cat_image_url:
                            bot.send_photo(chat_id, cat_image_url, 
                                         caption="Доброе утро! ☀️ Лови котика для хорошего настроения! 😊")
                            print(f"Котик отправлен в чат {chat_id}")
                        else:
                            bot.send_message(chat_id, 
                                          "Доброе утро! ☀️ Котик сбежал, но пожелание осталось! 😅")
                            print(f"Сообщение без котика отправлено в чат {chat_id}")
                    except Exception as e:
                        print(f"Ошибка отправки утреннего сообщения в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                time.sleep(60)  # Защита от дублирования
            
            time.sleep(30)  # Проверка каждые 30 секунд
            
        except Exception as e:
            print(f"Критическая ошибка в основном цикле: {e}")
            time.sleep(60)

# Запуск бота с обработкой ошибок
def start_bot():
    print("Бот запущен... :)")
    
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
