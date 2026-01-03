# Debt Tracker - Telegram Bot

Telegram-бот для учёта задолженностей. MVP версия с поддержкой нескольких долгов на пользователя, учётом платежей, планом погашения и приглашением кредиторов с правами только на чтение.

## Описание

Debt Tracker позволяет:
- Создавать и управлять несколькими долгами
- Учитывать платежи и автоматически пересчитывать остаток
- Просматривать план погашения
- Приглашать кредиторов с правами только на чтение
- Ведёт полный аудит всех изменений

## Требования

- Python 3.10+
- PostgreSQL 12+
- Telegram Bot Token

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository_url>
cd debt_bot
```

2. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env и укажите свои настройки
```

## Конфигурация

Создайте файл `.env` на основе `.env.example` и настройте следующие переменные:

- `BOT_TOKEN` - токен вашего Telegram бота (получить у [@BotFather](https://t.me/BotFather))
- `DB_HOST` - хост PostgreSQL (по умолчанию: localhost)
- `DB_PORT` - порт PostgreSQL (по умолчанию: 5432)
- `DB_NAME` - имя базы данных
- `DB_USER` - пользователь базы данных
- `DB_PASSWORD` - пароль базы данных
- `INVITE_TOKEN_EXPIRY_DAYS` - срок действия invite-токенов в днях (по умолчанию: 7)

## Запуск

1. Убедитесь, что PostgreSQL установлен и запущен (см. подробные инструкции в [SETUP_DB.md](SETUP_DB.md)):
```bash
# Установка через Homebrew (macOS)
brew install postgresql@15
brew services start postgresql@15

# Создание базы данных
createdb debt_bot
```

2. Настройте файл `.env` с параметрами подключения к БД (см. `.env.example`)

3. Активируйте виртуальное окружение и установите зависимости:
```bash
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Выполните миграции базы данных:
```bash
python migrate.py
```

5. Запустите бота:
```bash
python main.py
```

**Подробные инструкции по настройке БД см. в [SETUP_DB.md](SETUP_DB.md)**  
**Инструкции по деплою на сервер см. в [DEPLOY.md](DEPLOY.md)**

## Тестирование

Проект использует `pytest` для тестирования. Основные тесты находятся в папке `tests/`.

Для запуска тестов:

```bash
# Установите зависимости (если ещё не установлены)
pip install -r requirements.txt

# Запустите все тесты
pytest

# Запустите тесты с подробным выводом
pytest -v

# Запустите конкретный тестовый файл
pytest tests/test_planner_service.py -v
```

**Примечание:** Полное тестирование всех компонентов требует настройки тестовой базы данных. В настоящее время реализованы unit-тесты для `PlannerService`, которые не требуют подключения к БД.

## Структура проекта

```
debt_bot/
├── handlers/          # Обработчики Telegram команд и callback-ов
│   ├── start.py       # Обработчик /start
│   ├── debts.py       # Управление долгами
│   ├── payments.py    # Управление платежами
│   ├── invites.py     # Приглашения кредиторов
│   ├── create_debt.py # Создание долга (ConversationHandler)
│   ├── edit_debt.py   # Редактирование долга (ConversationHandler)
│   ├── keyboards.py   # Утилиты для клавиатур
│   ├── utils.py       # Вспомогательные функции
│   └── help.py        # Справка
├── services/          # Бизнес-логика приложения
│   ├── debt_service.py      # Логика работы с долгами
│   ├── payment_service.py   # Логика работы с платежами
│   ├── invite_service.py    # Логика приглашений
│   ├── planner_service.py   # Расчёт плана погашения
│   └── audit_service.py     # Аудит операций
├── repositories/      # Слой доступа к базе данных
│   ├── base.py              # Базовый класс репозитория
│   ├── debt_repository.py   # Репозиторий долгов
│   ├── payment_repository.py # Репозиторий платежей
│   ├── invite_repository.py  # Репозиторий приглашений
│   ├── user_repository.py    # Репозиторий пользователей
│   └── audit_log_repository.py # Репозиторий аудита
├── models/            # Модели данных (dataclasses)
│   ├── debt.py
│   ├── payment.py
│   ├── invite.py
│   ├── user.py
│   └── audit_log.py
├── migrations/        # SQL миграции базы данных
│   ├── 001_create_migrations_table.sql
│   ├── 002_create_users_table.sql
│   ├── 003_create_debts_table.sql
│   ├── 005_create_invites_table.sql
│   └── 006_create_audit_log_table.sql
├── tests/             # Тесты
│   ├── conftest.py    # Конфигурация pytest
│   └── test_planner_service.py # Тесты PlannerService
├── config.py          # Конфигурация приложения
├── database.py        # Управление подключением к БД
├── migrate.py         # Скрипт применения миграций
├── main.py            # Точка входа приложения
├── requirements.txt   # Зависимости проекта
├── pytest.ini         # Конфигурация pytest
├── .env.example       # Пример файла конфигурации
├── .gitignore         # Git ignore правила
├── SETUP_DB.md        # Инструкции по настройке БД
└── README.md          # Документация
```

## Разработка

Проект следует принципам:
- Все операции асинхронные (async/await)
- Handlers - тонкие, только разбор входа/выхода
- Вся бизнес-логика в services/
- Репозитории только для работы с БД
- Все секреты через .env
- Навигация через inline-кнопки

## Лицензия

[Укажите лицензию если нужно]

