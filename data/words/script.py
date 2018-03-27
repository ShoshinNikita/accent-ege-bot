# -*- coding: utf-8 -*-
# Скрипт добавляет слова из файла words.json в базу данных. Путь до базы данных должен быть полным. Имя таблицы - words

import sqlite3
import json

connection = sqlite3.connect(r"*********")
cursor = connection.cursor()

file = open("words.json", "r", encoding="utf-8")
words = json.loads(file.read())
file.close()

for i in words:
	data = words[i]
	cursor.execute("INSERT INTO words(origin, answer, variants, comment) VALUES (:origin, :ans, :vars, :comment)", 
					{"origin": data["origin"], "ans": data["answer"], "vars": " ".join(data["variants"]), "comment": data["comment"]})

connection.commit()