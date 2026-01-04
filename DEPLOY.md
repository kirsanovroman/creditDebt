# Инструкции по деплою Debt Tracker Bot

Этот документ описывает процесс деплоя Telegram-бота Debt Tracker.

## Требования

- Python 3.10+
- PostgreSQL 12+
- Telegram Bot Token
- Система управления процессами (systemd, supervisor, или подобная)

## Предварительная подготовка

1. **Получите токен бота:**
   - Откройте [@BotFather](https://t.me/BotFather) в Telegram
   - Создайте нового бота командой `/newbot`
   - Сохраните полученный токен

2. **Настройте PostgreSQL:**
   - Для локальной разработки: см. [SETUP_DB.md](SETUP_DB.md)
   - Для VPS сервера: см. [VPS_DB_SETUP.md](VPS_DB_SETUP.md)
   - Создайте базу данных: `createdb debt_bot`
   - Настройте пользователя и права доступа

## Вариант 1: Деплой на VPS/сервер с systemd

### 1. Подготовка окружения

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Python и PostgreSQL (если не установлены)
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib -y

# Создайте пользователя для бота
sudo useradd -m -s /bin/bash debtbot
sudo su - debtbot
```

### 2. Клонирование и настройка проекта

```bash
# Клонируйте репозиторий (или скопируйте файлы проекта)
git clone <repository_url> debt_bot
cd debt_bot

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка конфигурации

```bash
# Создайте файл .env
cp .env.example .env
nano .env
```

Заполните переменные:
```env
BOT_TOKEN=your_bot_token_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=debt_bot
DB_USER=postgres
DB_PASSWORD=your_db_password
INVITE_TOKEN_EXPIRY_DAYS=7
```

**Где взять пароль для DB_PASSWORD?**

Пароль зависит от способа установки PostgreSQL:

1. **Официальный установщик PostgreSQL** (EnterpriseDB):
   - Пароль задаётся **при установке PostgreSQL**
   - Это тот пароль, который вы указали для пользователя `postgres` во время установки
   - Если забыли пароль, можно сбросить его (см. ниже)

2. **Postgres.app (macOS)**:
   - Обычно пароль **не требуется** (оставьте поле пустым)
   - Используется ваше системное имя пользователя без пароля
   - `DB_USER` должен быть вашим системным именем пользователя (проверьте: `whoami`)

3. **Homebrew**:
   - Обычно пароль **не требуется** (оставьте поле пустым)
   - Используется ваш системный пользователь без пароля
   - `DB_USER` должен быть вашим системным именем пользователя

4. **Отдельный пользователь** (если создавали):
   - Пароль, который вы указали при создании пользователя:
   ```sql
   CREATE USER debt_bot_user WITH PASSWORD 'your_password_here';
   ```
   - В этом случае `DB_USER=debt_bot_user` и `DB_PASSWORD=your_password_here`

**Если забыли пароль пользователя `postgres`:**

На Linux/Ubuntu можно сбросить пароль:
```bash
# Переключитесь на пользователя postgres
sudo -u postgres psql

# В psql выполните:
ALTER USER postgres WITH PASSWORD 'новый_пароль';
\q
```

Или через командную строку:
```bash
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'новый_пароль';"
```

### 4. Настройка базы данных

```bash
# Примените миграции
python migrate.py
```

### 5. Создание systemd сервиса

```bash
# Вернитесь в root
exit

# Создайте файл сервиса
sudo nano /etc/systemd/system/debtbot.service
```

Содержимое файла:
```ini
[Unit]
Description=Debt Tracker Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=debtbot
WorkingDirectory=/home/debtbot/debt_bot
Environment="PATH=/home/debtbot/debt_bot/venv/bin"
ExecStart=/home/debtbot/debt_bot/venv/bin/python /home/debtbot/debt_bot/main.py
Restart=always
RestartSec=10

# Логирование
StandardOutput=journal
StandardError=journal
SyslogIdentifier=debtbot

[Install]
WantedBy=multi-user.target
```

### 6. Запуск и управление сервисом

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable debtbot

# Запустите бота
sudo systemctl start debtbot

# Проверьте статус
sudo systemctl status debtbot

# Просмотр логов
sudo journalctl -u debtbot -f
```

## Вариант 2: Деплой с использованием supervisor

### 1. Установка supervisor

```bash
sudo apt install supervisor -y
```

### 2. Создание конфигурации

```bash
sudo nano /etc/supervisor/conf.d/debtbot.conf
```

Содержимое:
```ini
[program:debtbot]
command=/home/debtbot/debt_bot/venv/bin/python /home/debtbot/debt_bot/main.py
directory=/home/debtbot/debt_bot
user=debtbot
autostart=true
autorestart=true
stderr_logfile=/var/log/debtbot/error.log
stdout_logfile=/var/log/debtbot/out.log
environment=PATH="/home/debtbot/debt_bot/venv/bin"
```

### 3. Создание директории для логов

```bash
sudo mkdir -p /var/log/debtbot
sudo chown debtbot:debtbot /var/log/debtbot
```

### 4. Запуск

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start debtbot
```

## Вариант 3: Docker (опционально)

Можно создать Dockerfile для контейнеризации приложения:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Запуск приложения
CMD ["python", "main.py"]
```

## Мониторинг

### Логи

- **systemd:** `sudo journalctl -u debtbot -f`
- **supervisor:** `sudo tail -f /var/log/debtbot/out.log`

### Проверка работоспособности

1. Отправьте боту команду `/start` в Telegram
2. Проверьте логи на наличие ошибок
3. Проверьте подключение к базе данных: `psql -U postgres -d debt_bot -c "SELECT COUNT(*) FROM users;"`

## Обновление бота

```bash
# Остановите бота
sudo systemctl stop debtbot  # или supervisorctl stop debtbot

# Обновите код
cd /home/debtbot/debt_bot
git pull  # или скопируйте новые файлы

# Примените новые миграции (если есть)
source venv/bin/activate
python migrate.py

# Запустите бота
sudo systemctl start debtbot  # или supervisorctl start debtbot
```

## Резервное копирование

Рекомендуется настроить регулярное резервное копирование базы данных:

```bash
# Создайте скрипт бэкапа
sudo nano /usr/local/bin/debtbot-backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/debtbot"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U postgres debt_bot > $BACKUP_DIR/debtbot_$DATE.sql
# Удаляем старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "debtbot_*.sql" -mtime +7 -delete
```

Добавьте в crontab:
```bash
sudo crontab -e
# Бэкап каждый день в 2:00
0 2 * * * /usr/local/bin/debtbot-backup.sh
```

## Безопасность

1. **Защита .env файла:**
   ```bash
   chmod 600 /home/debtbot/debt_bot/.env
   chown debtbot:debtbot /home/debtbot/debt_bot/.env
   ```

2. **Firewall:**
   Убедитесь, что порт PostgreSQL (5432) не доступен извне, если это возможно.

3. **Обновления:**
   Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`

## Устранение неполадок

### Бот не отвечает

1. Проверьте логи: `sudo journalctl -u debtbot -n 50`
2. Проверьте статус: `sudo systemctl status debtbot`
3. Проверьте токен в .env файле
4. Проверьте подключение к БД

### Ошибки подключения к БД

1. Проверьте, что PostgreSQL запущен: `sudo systemctl status postgresql`
2. Проверьте настройки в .env
3. Проверьте права доступа: `psql -U postgres -d debt_bot`

### Ошибки миграций

1. Убедитесь, что база данных создана
2. Проверьте права пользователя БД
3. Проверьте логи миграций

## Производительность

Проект использует:
- Пул подключений к БД (min_size=1, max_size=10)
- Индексы на ключевых полях
- Асинхронные операции

Для высоких нагрузок можно:
- Увеличить размер пула подключений в `database.py`
- Настроить параметры PostgreSQL (shared_buffers, max_connections и т.д.)
- Использовать connection pooling на уровне БД (PgBouncer)

