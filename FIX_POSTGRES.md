# Исправление ошибки подключения к PostgreSQL

## Проблема

Ошибка: `OSError: Multiple exceptions: [Errno 61] Connect call failed ('::1', 5432, 0, 0), [Errno 61] Connect call failed ('127.0.0.1', 5432)`

Это означает, что PostgreSQL не запущен или не установлен.

## Решение

### Вариант 1: Если PostgreSQL установлен, но не запущен

#### Postgres.app (macOS)

1. Откройте приложение **Postgres.app** из папки Applications
2. Нажмите кнопку "Initialize" если сервер не инициализирован
3. Убедитесь, что сервер запущен (зелёный индикатор)

#### Homebrew

```bash
brew services start postgresql@15
# или
brew services start postgresql
```

#### Официальный установщик

```bash
# Запустите через Launchpad или:
/Library/PostgreSQL/15/bin/pg_ctl -D /Library/PostgreSQL/15/data start
```

### Вариант 2: Если PostgreSQL не установлен

#### Способ 1: Postgres.app (РЕКОМЕНДУЕТСЯ для macOS)

1. Скачайте с https://postgresapp.com/downloads.html
2. Установите (перетащите в Applications)
3. Запустите Postgres.app
4. Нажмите "Initialize"
5. Добавьте в PATH (опционально):
```bash
sudo mkdir -p /etc/paths.d &&
echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp
```
Перезапустите терминал.

#### Способ 2: Homebrew

```bash
brew install postgresql@15
brew services start postgresql@15
```

#### Способ 3: Официальный установщик

1. Скачайте с https://www.postgresql.org/download/macosx/
2. Установите через установщик
3. Задайте пароль для пользователя `postgres`

### Шаг 3: Создайте базу данных

После запуска PostgreSQL создайте базу данных:

```bash
# Если используете Postgres.app или Homebrew (ваш системный пользователь):
createdb debt_bot

# Если используете официальный установщик (пользователь postgres):
/Library/PostgreSQL/15/bin/createdb -U postgres debt_bot
```

### Шаг 4: Настройте .env.local

Откройте `.env.local` и настройте параметры подключения:

**Для Postgres.app или Homebrew:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=debt_bot
DB_USER=r.kirsanov  # Ваше системное имя пользователя (проверьте: whoami)
DB_PASSWORD=        # Оставьте пустым
```

**Для официального установщика:**
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=debt_bot
DB_USER=postgres
DB_PASSWORD=ваш_пароль_от_postgres
```

### Шаг 5: Примените миграции

```bash
source venv/bin/activate
python migrate.py
```

### Шаг 6: Проверьте подключение

```bash
# Для Postgres.app:
/Applications/Postgres.app/Contents/Versions/latest/bin/psql -d debt_bot

# Для Homebrew:
psql -d debt_bot

# Для официального установщика:
/Library/PostgreSQL/15/bin/psql -U postgres -d debt_bot
```

Если подключение успешно, вы увидите приглашение `psql`. Выйдите командой `\q`.

## Быстрая проверка

```bash
# Проверьте, запущен ли PostgreSQL
lsof -i :5432

# Проверьте версию (если установлен)
psql --version
# или
/Applications/Postgres.app/Contents/Versions/latest/bin/psql --version
```

## Готово!

После выполнения этих шагов бот должен подключиться к базе данных.
