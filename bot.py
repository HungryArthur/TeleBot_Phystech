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
TIMEZONE = pytz.timezone('Europe/Moscow') # Временная зона GMT+3(время по мск)
chat_ids = set() # Множество для хранения ID чатов
sent_birthdays = set()  # сюда будем записывать даты, по которым уже поздравили
birthdays = {
	"10.01": ["Михаил 🎂","Никита 🎂"],
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
	"03.02": ["Мухаммад 🥳"]
	"01.10": ["Ирина Александровна 🎂🥳🎉"]
}


# Функция для получения случайного котика
def get_random_cat():
	try:
		response = requests.get('https://api.thecatapi.com/v1/images/search')
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

# Рассылка во врмея которое я укажу
def check_birthdays_and_send_messages():
	while True:
		now = datetime.now(TIMEZONE)
		today_date = now.strftime("%d.%m")

		# Проверка ДР
		if today_date in birthdays:
			names = ", ".join(birthdays[today_date])
			for chat_id in chat_ids:
				bot.send_message(chat_id, f"🎉 Сегодня День рождения у {names}! Поздравляем! 🎂")
	        sent_birthdays.add(today_date)  # пометили, что поздравили

        # Сбросить флаги на следующий день
        if today_date not in sent_birthdays:
            sent_birthdays.clear()

		# Доброе утро + Котики
		if now.hour == 8 and now.minute == 00: # Указываю время
			cat_image_url = get_random_cat()
			for chat_id in chat_ids:
					try:
						if cat_image_url:
							bot.send_photo(chat_id, cat_image_url, caption="Доброе утро! ☀️ Лови котика для хорошего настроения! 😊")
						else:
								bot.send_message(chat_id, "Доброе утро! ☀️ Котик сбежал, но пожелание осталось! 😅")
					except Exception as e:
						print(f"Ошибка отправки в чат {chat_id}: {e}")
			time.sleep(60)  # Защита от дублирования
		time.sleep(30)  # Проверка каждые 30 секунд

# Запуск бота
if __name__ == "__main__":
	print("Бот запущен... :)")
	Thread(target=check_birthdays_and_send_messages, daemon=True).start()
	bot.polling()


