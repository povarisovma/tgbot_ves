# VesBot — Telegram-бот для учёта массы тела

Бот помогает фиксировать вес и отслеживать его динамику. Поддерживает нескольких пользователей, хранит историю взвешиваний и строит графики.

## Возможности

- Запись веса один раз в день
- Принимает числа в любом формате: `75`, `75.3`, `75,3`
- Просмотр истории взвешиваний
- График динамики веса с линией среднего значения
- Команда `/stats` для администратора — количество пользователей, записей и активность за день

## Стек

- Python 3.11+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21
- SQLite
- Matplotlib

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ВАШ_АККАУНТ/tgbot_ves.git
cd tgbot_ves
```

### 2. Создать виртуальное окружение и установить зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Настроить токен

Создать файл `.env` в корне проекта:

```
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_telegram_id
```

Узнать свой Telegram ID можно через @userinfobot.

### 4. Запустить

```bash
python bot.py
```

## Деплой на сервер (Linux + systemd)

### Создать пользователя

```bash
sudo useradd -r -s /bin/false vesbot
```

### Скопировать файлы и выдать права

```bash
sudo cp -r . /opt/tgbot_ves
sudo chown -R vesbot:vesbot /opt/tgbot_ves
```

### Создать `.env` на сервере

```bash
sudo nano /opt/tgbot_ves/.env
# Вписать: BOT_TOKEN=ваш_токен
```

### Установить зависимости

```bash
sudo -u vesbot python3 -m venv /opt/tgbot_ves/venv
sudo -u vesbot /opt/tgbot_ves/venv/bin/pip install -r /opt/tgbot_ves/requirements.txt
```

### Установить и запустить сервис

```bash
sudo cp /opt/tgbot_ves/tgbot_ves.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tgbot_ves
sudo systemctl start tgbot_ves
```

### Проверить статус

```bash
sudo systemctl status tgbot_ves
```

## Структура проекта

```
tgbot_ves/
├── bot.py               # основной код бота
├── db.py                # работа с SQLite
├── chart.py             # построение графика
├── tgbot_ves.service    # systemd unit
├── requirements.txt
├── .env                 # токен (не коммитить!)
└── .gitignore
```
