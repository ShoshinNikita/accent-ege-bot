# -*- coding: utf-8 -*-

# Стандартные библиотеки
import sys
import random
import unicodedata
from threading import Thread
import os
from datetime import datetime
import json
import re
# Скачанные библиотеки
import flask
from flask import request, redirect
import telebot
from telebot import types
# Файлы проекта
import constants
from DataBase import dbAdapter
from Statistics import statsAdapter
from Logger import logAdapter


bot = telebot.AsyncTeleBot(constants.BOT_TOKEN)
bot.threaded = False
app = flask.Flask(__name__)


def choose_word():
	"""
	Выбирает слово, которое будет оправленно пользователю
	:return: возвращает tuple, где первый элемент - dict, содержащий информацию о слове, второй - markup
	"""
	word = dbAdapter.get_random_word()

	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	words_order = [i for i in range(len(word["variants"]))]
	random.shuffle(words_order)
	
	if len(words_order) == 2:
		first = types.KeyboardButton(word["variants"][words_order[0]])
		second = types.KeyboardButton(word["variants"][words_order[1]])
		markup.row(first, second)
	elif len(words_order) == 3:
		first = types.KeyboardButton(word["variants"][words_order[0]])
		second = types.KeyboardButton(word["variants"][words_order[1]])
		third = types.KeyboardButton(word["variants"][words_order[2]])
		markup.row(first, second, third)

	return word, markup


def mailout(text):
	"""
	Поддерживается HTML
	:param text: сообщение, которое будет отправленно всем пользователям
	"""
	users_id = dbAdapter.get_all_users_id()
	for i in users_id:
		try:
			bot.send_message(i, text, parse_mode="HTML")
		except Exception as e:
			logAdapter.log(str(e))


def strip_accents(s):
	"""
	Удаляет символ ударения
	:param s: слово, содержащее символ ударения
	:return: возвращает слово без символа ударения
	"""
	return "".join(c for c in unicodedata.normalize("NFC", s) if unicodedata.category(c) != "Mn")


# ~~~~~ Flask ~~~~~
@app.route("/")
def main():
	return flask.render_template("page.html", stats=statsAdapter.get_stats())


@app.route("/", methods=["POST"])
def send():
	message = request.form["message"]
	password = request.form["password"]
	if password == constants.MAILOUT_PASSWORD:
		mailout(message)
	return redirect("/")


@app.route('/favicon.ico')
def favicon():
	return flask.send_from_directory(os.path.join(app.root_path, 'static'),
	                                 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/api/get")
def api_get():
	return json.dumps(statsAdapter.get_stats())


# ~~~~~ Bot ~~~~~
@bot.message_handler(commands=["start"])
def start(message):
	result = choose_word()
	dbAdapter.create_record(message.chat, result[0]["origin"])
	bot.send_message(message.chat.id, result[0]["origin"], reply_markup=result[1])


@bot.message_handler(commands=["status"])
def status(message):
	data = dbAdapter.get_user(message.chat.id)
	bot.send_message(message.chat.id, "Всего ответов: {0}\nПравильно: {1}\nНеправильно: {2}".format(data["correct"] +
																									data["incorrect"],
																									data["correct"],
																									data["incorrect"]))


@bot.message_handler(commands=["setname"])
def set_name(message):	
	name = message.text[9:]
	name = re.sub("[\n\t\r/]", "", name)
	if 5 <= len(name) <= 19:
		dbAdapter.set_name(message.chat.id, name)
		bot.send_message(message.chat.id, "Установлено имя: " + name)
	else:
		bot.send_message(message.chat.id, "Длина должна быть не менее 5 и не более 19 символов")


@bot.message_handler(commands=["top"])
def top(message):
	top = dbAdapter.get_top_list()
	result = "Топ: (имя – лучший счёт)\n"

	if len(top) == 0:
		result = "Топ: пусто"
	else:
		counter = 1
		for i in top:
			mark = "🏅"
			if counter == 1:
				mark = "🥇"
			elif counter == 2:
				mark = "🥈"
			elif counter == 3:
				mark = "🥉"

			result += "{counter} {name} – {score}\n".format(counter=mark, name=i[0].rstrip(), score=i[1])
			counter += 1
		
	bot.send_message(message.chat.id, result)


@bot.message_handler(commands=["toperrors"])
def top_errors(message):
	data = dbAdapter.get_top_errors()
	result = "Топ ошибок:\n"
	for i in data:
		result += "❗️" + i[0] + "\n"
	bot.send_message(message.chat.id, result)


@bot.message_handler(commands=["help"])
def help(message):
	bot.send_message(message.chat.id, constants.HELP_COMMAND_TEXT)
	

@bot.message_handler(commands=["report"])
def report(message):
	logAdapter.add_report(message.chat.id, message.text[8:])
	bot.send_message(message.chat.id, "Ваше сообщение получено. Спасибо")


@bot.message_handler(commands=["myerrors"])
def user_errors(message):
	user_errors = dbAdapter.get_user(message.chat.id)["errors"].replace(" ", "\n")
	bot.send_message(message.chat.id, "Список ошибок:\n" + user_errors)


@bot.message_handler(content_types=["text"])
def check(message):
	# Слово, которое отправил пользователь
	user_choice = message.text
	# Инфорация о слове, которое отправил пользователь
	word_info = dbAdapter.get_word_info(strip_accents(user_choice))
	# Информация о пользователе
	user = dbAdapter.get_user(message.chat.id)

	if user is None or user["lastWord"] == "None":
		bot.send_message(message.chat.id, "Введите /start")
	elif word_info is None or user["lastWord"] != word_info["origin"]:
		bot.send_message(message.chat.id, "Неверное слово")
	else:
		# Убирается возможность отправки одинаковых слов подряд
		next_word, next_markup = choose_word()
		while next_word["origin"] in user["severalLastWords"].split():
			next_word, next_markup = choose_word()
			
		if word_info["answer"] == user_choice:
			dbAdapter.update(message.chat.id, "correct", word_info["answer"], next_word["origin"])
			score = dbAdapter.get_score(message.chat.id)

			answer = "✅ Правильно Счет: {0}\n\n➡️ {1}".format(score["score"], next_word["origin"])
			if len(next_word["comment"]) != 0:
				answer += " " + next_word["comment"]

			bot.send_message(message.chat.id, answer, reply_markup=next_markup)

		else:
			# Получаем счёт раньше, чем обновляем, чтобы показать пользователю
			score = dbAdapter.get_score(message.chat.id)
			dbAdapter.update(message.chat.id, "incorrect", word_info["answer"], next_word["origin"])

			answer = "❌ Неправильно. Правильно - {0}\n\n🏆 Ваш счет: {1}, лучший: {2}\n\n➡️ {3}".format(
					word_info["answer"], score["score"], score["bestScore"], next_word["origin"])
			if len(next_word["comment"]) != 0:
				answer = answer + " " + next_word["comment"]

			bot.send_message(message.chat.id, answer, reply_markup=next_markup)
						
		statsAdapter.update_stats(message.chat.id)


if __name__ == "__main__":
	"""
	Без аргументов запускается полноценная программа
	Аргументы:
	-bot: запускается только бот (имеет самый высокий приоритет), работает до первой ошибки
	-web: запускается только сайт
	"""
	args = sys.argv
	
	if(len(args) == 1):
		flask_thread = Thread(target=app.run, kwargs={"host": constants.HOST, "port": constants.PORT, "debug": False})
		flask_thread.start()
	
		while True:
			try:
				logAdapter.log("Launch")
				bot.polling()
			except Exception as e:
				logAdapter.log(str(e))
				bot.stop_polling()
	elif "-bot" in args:
		try:
			logAdapter.log("Launch")
			bot.polling()
		except Exception as e:
			logAdapter.log(str(e))
			bot.stop_polling()
	elif "-web" in args:
		app.run(host=constants.HOST, port=constants.PORT, debug=constants.IS_DEBUG_MODE)
	else:
		print("Bad arguments")
