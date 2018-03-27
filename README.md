# README

Здесь представлен исходный код бота для Telegram [@accent_ege_bot](https://t.me/accent_ege_bot)

## Требования

* Python 3.5 или выше
* [Flask](http://flask.pocoo.org/) – используется для рассылки
* [PyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) – используется для взаимодействия с Telegram API

## Для работы нужны следующие файлы

### data/difficultWords.json

Содержание:

```json
{"errors": {}}
```

### data/logs.log

Содержание: пусто

### data/reports.txt

Содержание: пусто

### data/stats.json

Содержание:

```json
{
	"total": 0,
	"hours": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0, "10": 0, "11": 0, "12": 0,
				"13": 0, "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0, "20": 0, "21": 0, "22": 0, "23": 0},
	"dailyUniqueUsers": 0,
	"users": []
}
```

### data/users.db (SQLite)

Create statements:

```sql
CREATE TABLE `users` (
	`id`	INTEGER,
	`name`	TEXT,
	`correct`	INTEGER DEFAULT 0,
	`incorrect`	INTEGER DEFAULT 0,
	`lastWord`	TEXT DEFAULT 'None',
	`errors`	TEXT DEFAULT '',
	`severalLastWords`	TEXT DEFAULT '',
	PRIMARY KEY(`id`)
);

CREATE TABLE `words` (
	`origin` TEXT,
	`variants` TEXT,
	`errorsNumber` INTEGER,
	PRIMARY KEY(`origin`)
);
```

Слова нужно добавить в базу, используя скрипт data/words/script.py, отредактировав при этом путь до файла

## Лицензия

[MIT License](LICENSE)