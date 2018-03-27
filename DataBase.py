# -*- coding: utf-8 -*-

# Стандартные библиотеки
import sqlite3
# Файлы проекта
import constants

class DataBase:
	"""
	Необходимо создать файл data/database.db
	Create statement:
	CREATE TABLE `users` (
		`id`	INTEGER,
		`name`	TEXT,
		`correct`	INTEGER DEFAULT 0,
		`incorrect`	INTEGER DEFAULT 0,
		`score` INTEGER DEFAULT 0,
		`bestScore` INTEGER DEFAULT 0,
		`lastWord`	TEXT DEFAULT 'None',
		`errors`	TEXT DEFAULT '',
		`severalLastWords`	TEXT DEFAULT '',
		PRIMARY KEY(`id`)
	);

	CREATE TABLE "words" ( `origin` TEXT,
		`answer` TEXT,
		`variants` TEXT,
		`comment` TEXT,
		`errorsNumber`
		INTEGER DEFAULT 0,
		PRIMARY KEY(`origin`) );
	"""

	def __init__(self):
		self.connection = sqlite3.connect("data/database.db", check_same_thread=False)
		self.cursor = self.connection.cursor()
		self.user_columns = self.get_columns_names("users")
		self.word_columns = self.get_columns_names("words")

	def get_columns_names(self, name):
		"""
		:param name: имя таблицы
		:return: возвращает list, содержщий имена столбцов базы данных
		"""
		if name == "users":
			self.cursor.execute("PRAGMA table_info(users)")
		elif name == "words":
			self.cursor.execute("PRAGMA table_info(words)")

		result = [i[1] for i in self.cursor.fetchall()]
		return result

	#~~~~~ Users ~~~~~	
	def create_record(self, chat_info, word):
		"""
		:param chat_info: информация о чате пользователя
		:param word: слово, которое получил пользователь
		"""
		id = str(chat_info.id)
		is_none = lambda s: s or ""
		
		name = "Аноним"
		if chat_info.username is not None:
			name = chat_info.username
		elif chat_info.first_name is not None or chat_info.last_name is not None:
			if chat_info.first_name is not None and chat_info.last_name is not None:
				name = is_none(chat_info.first_name) + " " + is_none(chat_info.last_name)
			else:
				name = is_none(chat_info.first_name) + is_none(chat_info.last_name)
			
		# Если такого id ранее не было то создается "новая учетная запись"
		self.cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (:id, :name)", {"id": id, "name": name})
		
		self.cursor.execute("UPDATE users SET lastWord=:lastWord, severalLastWords=:lastWords WHERE id=:id",
							{"lastWord": word, "lastWords": word, "id": id})
		
		self.connection.commit()

	def set_name(self, id, name):
		"""
		:param id: chat id пользователя
		:param name: имя пользователя
		"""
		self.cursor.execute("UPDATE users SET name=:name WHERE id=:id", {"name": name, "id": id})
		self.connection.commit()

	def update(self, id, tag, old_word, new_word):
		"""
		:param id: информация о чате пользователя
		:param tag: correct/incorrect
		:param old_word: слово, на которое пользователь отвечал (с ударением)
		:param new_word: новое слово (без ударений)
		"""

		if tag == "correct":
			self.cursor.execute("""UPDATE users
								SET correct=correct+1, lastWord=:lastWord, 
								bestScore = CASE WHEN score+1 > bestScore THEN score+1 ELSE bestScore END,
								score=score+1
								WHERE id=:id""", {"lastWord": new_word, "id": id})
		else:
			self.cursor.execute("""UPDATE users
								SET incorrect=incorrect+1, lastWord=:lastWord, score=0
								WHERE id=:id""", {"lastWord": new_word, "id": id})
			# Обновление счетчика ошибок
			self.cursor.execute("""UPDATE words 
								SET errorsNumber=errorsNumber+1 
								WHERE answer=:word""", {"word": old_word})
			
		# Обновление severalLastWords, чтобы слова повторялись реже (кроме тех, на которые пользователь ответил неверно)
		if tag == "correct":
			self.cursor.execute("SELECT severalLastWords FROM users WHERE id=:id", {"id": id})
			last_words = self.cursor.fetchall()[0][0].split()
			
			if len(last_words) >= constants.NUMBER_OF_SAVED_WORDS:
				last_words.pop(0)
			last_words.append(new_word)
			self.cursor.execute("UPDATE users SET severalLastWords=:lastWords WHERE id=:id", {"lastWords": " ".join(last_words), "id": id})
			
		# Обновление ошибок, которые совершил пользователь
		self.cursor.execute("SELECT errors FROM users WHERE id=:id", {"id": id})
		errors = set(self.cursor.fetchall()[0][0].split())
		if tag == "correct":
			errors = errors - set([old_word])
		elif tag == "incorrect":
			errors.add(old_word)
		self.cursor.execute("UPDATE users SET errors=:errors WHERE id=:id", {"errors": " ".join(errors), "id": id})
		
		self.connection.commit()

	def get_user(self, id):
		"""
		:param id: chat id пользователя
		:return: данные пользователя, если запись существует ({id, name, correct, incorrect, score, bestScore, lastWord, errors, severalLastWords})
		"""

		records = self.cursor.execute("SELECT * FROM users WHERE id=:id", {"id": id}).fetchall()
		records = records[0]
		result = {}
		for i in range(len(self.user_columns)):
			result[self.user_columns[i]] = records[i]
		return result

	def get_all_users_id(self):
		"""
		:return: возвращает list, содержащий id всех пользователей типа int
		"""
		self.cursor.execute("SELECT id FROM users")
		users_id = [i[0] for i in self.cursor.fetchall()]

		return users_id
		
	def get_top_list(self):
		"""
		:return: топ пользователей в виде списка из tuple (name, bestScore)
		"""
		# По убыванию
		self.cursor.execute("SELECT name, bestScore FROM users WHERE bestScore>=10 ORDER BY bestScore DESC LIMIT 10")
		return self.cursor.fetchall()

	def get_score(self, id):
		"""
		:param id: id пользователя
		:return: {"score": int, "bestScore": int}
		"""
		result = {"score": 0, "bestScore": 0}

		self.cursor.execute("SELECT score, bestScore FROM users WHERE id=:id", {"id": id})
		data = self.cursor.fetchall()

		result["score"] = data[0][0]
		result["bestScore"] = data[0][1]

		return result

	# ~~~~~ Words ~~~~~~
	def get_word_info(self, word):
		"""
		Получить информацию о слове ({"origin", "answer", "variants", "errorsNumber"})
		:param word: слово БЕЗ ударением, которое отправил пользователь
		"""
		self.cursor.execute("SELECT * FROM words WHERE origin=:word", {"word": word})
		data = self.cursor.fetchall()
		if len(data) == 0:
			return None
		else:
			data = data[0]
			result = {}
			for i in range(len(self.word_columns)):
				result[self.word_columns[i]] = data[i]
			result["variants"] = result["variants"].split()
			return result

	def get_random_word(self):
		"""
		:return: возвращает случайное слово (+ всю информацию) из базы данных
		"""
		# Такая сложность для отпимизации
		self.cursor.execute("SELECT * FROM words WHERE origin IN (SELECT origin FROM words ORDER BY RANDOM() LIMIT 1)")
		data = self.cursor.fetchall()[0]
		result = {}
		for i in range(len(self.word_columns)):
			result[self.word_columns[i]] = data[i]
		result["variants"] = result["variants"].split()
		return result

	def get_top_errors(self):
		"""
		:return: list, содержащий 10 наиболее сложных слов (наибольшее количество ошибок)
		"""
		self.cursor.execute("SELECT answer FROM words WHERE errorsNumber>0 ORDER BY errorsNumber DESC LIMIT 10")
		return self.cursor.fetchall()


dbAdapter = DataBase()