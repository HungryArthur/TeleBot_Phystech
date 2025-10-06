import time
import os
import telebot
import requests
import pytz
from threading import Thread
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)
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

def get_random_cat():
    try:
        response = requests.get('https://api.thecatapi.com/v1/images/search', timeout=10)
        if response.status_code == 200:
            return response.json()[0]['url']
        else:
            return None
    except Exception as e:
        print(f"Ошибка при загрузке котика: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        bot.reply_to(message, "Я буду присылать добрые утра и спокойные вечера с котиками, а также поздравлять с ДР! 😊\n\nРассылки в:\n• 8:00 - Доброе утро\n• 20:00 - Спокойной ночи")
    else:
        bot.reply_to(message, "Я уже работаю в этом чате! 🐱")

@bot.message_handler(commands=['stop'])
def stop(message):
    chat_id = message.chat.id
    if chat_id in chat_ids:
        chat_ids.remove(chat_id)
        bot.reply_to(message, "Рассылка остановлена. Используйте /start чтобы снова включить.")
    else:
        bot.reply_to(message, "Рассылка и так не активна в этом чате.")

@bot.message_handler(commands=['info'])
def info(message):
    chat_id = message.chat.id
    status = "активна" if chat_id in chat_ids else "не активна"
    bot.reply_to(message, f"Рассылка {status}.\n\nВремя рассылок:\n• 8:00 - Доброе утро с котиком\n• 20:00 - Спокойной ночи с котиком\n\nВсего чатов в рассылке: {len(chat_ids)}")

def check_birthdays_and_send_messages():
    global sent_birthdays, last_reset_date, morning_sent_today, evening_sent_today
    
    while True:
        try:
            now = datetime.now(TIMEZONE)
            today_date = now.strftime("%d.%m")
            
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

            # Утренняя рассылка (8:00)
            if now.hour == 8 and now.minute == 0 and not morning_sent_today:
                print("Время утренней рассылки!")
                cat_image_url = get_random_cat()
                
                for chat_id in list(chat_ids):
                    try:
                        if cat_image_url:
                            bot.send_photo(chat_id, cat_image_url, 
                                         caption="Доброе утро! ☀️ Лови котика для хорошего настроения! Пусть день будет прекрасным! 😊")
                        else:
                            bot.send_message(chat_id, 
                                          "Доброе утро! ☀️ Котик сбежал, но пожелание осталось! Хорошего дня! 😊")
                    except Exception as e:
                        print(f"Ошибка утренней рассылки в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                morning_sent_today = True
                time.sleep(60)

            # Вечерняя рассылка (20:00) - ТОЛЬКО КОТИКИ
            elif now.hour == 20 and now.minute == 0 and not evening_sent_today:
                print("Время вечерней рассылки!")
                cat_image_url = get_random_cat()
                
                for chat_id in list(chat_ids):
                    try:
                        if cat_image_url:
                            bot.send_photo(chat_id, cat_image_url, 
                                         caption="Спокойной ночи! 🌙 Лови котика для сладких снов! Хорошего отдыха! 😴💫")
                        else:
                            bot.send_message(chat_id, 
                                          "Спокойной ночи! 🌙 Котик уже спит, но пожелание осталось! Приятных снов! 😴✨")
                    except Exception as e:
                        print(f"Ошибка вечерней рассылки в чат {chat_id}: {e}")
                        chat_ids.discard(chat_id)
                
                evening_sent_today = True
                time.sleep(60)
            
            time.sleep(30)
            
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
            time.sleep(60)

def start_bot():
    print("Бот запущен... :)")
    print("Рассылки запланированы на 8:00 и 20:00")
    
    Thread(target=check_birthdays_and_send_messages, daemon=True).start()
    
    while True:
        try:
            bot.polling(timeout=30, long_polling_timeout=30, non_stop=True)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
