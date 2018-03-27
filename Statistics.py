# -*- coding: utf-8 -*-

# Стандартные библиотеки
import json
import datetime
# Файлы проекта
import constants


class Statistics:
	"""
	Класс, работающий со статистикой использования бота (количество запросов в день/час)
	Нужен файл stats.json, содержащий
	{
		"total": 0,
		"hours": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0, "10": 0, "11": 0,
				"12": 0, "13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0},
		"dailyUniqueUsers": 0,
		"users": []
	}
	"""
	
	def __init__(self):
		self.path =  "data/stats.json"
		self.stats = self.load()
		self.update_counter = 0
		self.last_time = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
		
	def write(self, dictionary):
		"""
		Записывает передаваемый словарь в файл
		:param dictionary: словарь
		:param path: путь до файла
		"""
		file = open(self.path, "w")
		file.write(json.dumps(dictionary))
		file.close()
	
	def load(self):
		"""
		Загружает словарь из файла
		:param path: путь до файла
		:return: dictionary с данными из файла
		"""
		file = open(self.path, "r+")
		data = json.loads(file.read())
		file.close()
		return data
	
	def update_stats(self, id):
		"""
		Обновляет ежедневную статистику использования бота
		:param id: id пользователя
		"""
		now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
		# Час приравнивается к нулю, чтобы статистика сбрасывалась только раз в день
		if self.last_time < now.replace(hour=0):
			self.last_time = now
			for i in self.stats["hours"]:
				self.stats["hours"][i] = 0
			self.stats["dailyUniqueUsers"] = 0
			self.stats["users"] = []
			self.update_counter = constants.DELAY_BETWEEN_WRITE
		
		self.stats["total"] += 1
		self.stats["hours"][str(now.hour)] += 1
		self.update_counter += 1
		
		# Обновление количества уникадьных пользователей
		if id not in self.stats["users"]:
			self.stats["dailyUniqueUsers"] += 1
			self.stats["users"].append(id)
		
		if self.update_counter >= constants.DELAY_BETWEEN_WRITE:
			self.update_counter = 0
			self.write(self.stats)
	
	def get_stats(self):
		"""
		:return result: количество ответов за последний час и за все время, количество уникальных пользователей
		"""
		result = {"day": 0, "total": 0, "all_day": [], "dailyUniqueUsers": 0}
		
		result["day"] = sum([self.stats["hours"][i] for i in self.stats["hours"]])
		result["total"] = self.stats["total"]
		for i in range(24):
			result["all_day"].append(self.stats["hours"][str(i)])
		
		result["dailyUniqueUsers"] = self.stats["dailyUniqueUsers"]
		
		return result

statsAdapter = Statistics()