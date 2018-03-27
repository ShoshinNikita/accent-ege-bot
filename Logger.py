from datetime import datetime


class Logger:
	def __init__(self):
		self.log_file = open("data/logs.log", "a", encoding="utf-8")
		self.report_file = open("data/reports.txt", "a", encoding="utf-8")
	
	def add_report(self, user_id, message):
		self.report_file.write("{0}\t id: {1} \t message: {2}\n".format(datetime.now().strftime("%d-%m-%Y %H:%M"), user_id, message))
		self.report_file.flush()

	def log(self, message):
		self.log_file.write("{0}\t message: {1}\n".format(datetime.now().strftime("%d-%m-%Y %H:%M"), message))
		self.log_file.flush()

logAdapter = Logger()