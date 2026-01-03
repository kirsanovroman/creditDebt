# Инструкция по настройке базы данных

## Шаг 1: Установка PostgreSQL

### Способ 1: Postgres.app (РЕКОМЕНДУЕТСЯ для macOS, самый простой)

1. Скачайте Postgres.app с официального сайта:
   https://postgresapp.com/downloads.html

2. Установите приложение (просто перетащите в папку Applications)

3. Запустите Postgres.app из Applications

4. Нажмите кнопку "Initialize" для создания нового сервера

5. PostgreSQL будет доступен на порту 5432, пользователь по умолчанию - ваше системное имя пользователя

6. Добавьте PostgreSQL в PATH (опционально, для использования команд psql из терминала):
   ```bash
   sudo mkdir -p /etc/paths.d &&
   echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp
   ```
   Перезапустите терминал после этого.

### Способ 2: Установщик с официального сайта

1. Перейдите на https://www.postgresql.org/download/macosx/

2. Выберите установщик (рекомендуется использовать установщик от EnterpriseDB)

3. Скачайте и запустите установщик

4. Следуйте инструкциям установщика:
   - Выберите компоненты для установки
   - Укажите директорию для данных
   - Задайте пароль для пользователя `postgres`
   - Выберите порт (по умолчанию 5432)

5. После установки PostgreSQL будет запущен автоматически

6. Для управления используйте:
   - pgAdmin (GUI инструмент, устанавливается вместе с PostgreSQL)
   - Или командную строку: `/Library/PostgreSQL/15/bin/psql`

### Способ 3: Homebrew (если установлен)

1. Установите PostgreSQL через Homebrew:
```bash
brew install postgresql@15
```

2. Запустите PostgreSQL:
```bash
brew services start postgresql@15
```

3. Проверьте, что PostgreSQL запущен:
```bash
psql --version
```

### Проверка установки

После установки любым способом проверьте, что PostgreSQL работает:
```bash
psql --version
```

Если команда не найдена, используйте полный путь:
- Postgres.app: `/Applications/Postgres.app/Contents/Versions/latest/bin/psql --version`
- Официальный установщик: `/Library/PostgreSQL/15/bin/psql --version`

---

## Шаг 2: Создание базы данных

1. Подключитесь к PostgreSQL (по умолчанию используется пользователь `postgres`, но на macOS после Homebrew это ваш системный пользователь):
```bash
psql postgres
```

2. Создайте базу данных:
```sql
CREATE DATABASE debt_bot;
```

3. (Опционально) Создайте отдельного пользователя для бота:
```sql
CREATE USER debt_bot_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE debt_bot TO debt_bot_user;
```

4. Выйдите из psql:
```sql
\q
```

**Или используйте команду из командной строки:**
```bash
createdb debt_bot
```

---

## Шаг 3: Настройка .env файла

1. Убедитесь, что файл `.env` существует (он уже создан в проекте)

2. Откройте `.env` и настройте параметры подключения к БД:

```env
# Telegram Bot Configuration
BOT_TOKEN=8552942310:AAEjkfKCOFWNAop-UBFBUhvFt4-FuQ51LGM

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=debt_bot
DB_USER=your_username  # Обычно это ваш системный пользователь на macOS, или 'postgres'
DB_PASSWORD=           # Оставьте пустым для локального подключения без пароля, или укажите пароль

# Application Configuration
INVITE_TOKEN_EXPIRY_DAYS=7
```

**Важно:**
- **Postgres.app**: Используется ваше системное имя пользователя без пароля
- **Официальный установщик**: Обычно используется пользователь `postgres` с паролем, который вы задали при установке
- **Homebrew**: Используется ваш системный пользователь без пароля
- Если вы создали отдельного пользователя, укажите его имя и пароль
- DB_HOST обычно `localhost` для локальной разработки

---

## Шаг 4: Проверка подключения (опционально)

Проверьте, что можете подключиться к базе данных:

**Postgres.app:**
```bash
/Applications/Postgres.app/Contents/Versions/latest/bin/psql -d debt_bot
```

**Официальный установщик:**
```bash
/Library/PostgreSQL/15/bin/psql -U postgres -d debt_bot
```

**Homebrew:**
```bash
psql -d debt_bot
```

Если подключение успешно, вы увидите приглашение psql. Выйдите командой `\q`.

---

## Шаг 5: Применение миграций

1. Убедитесь, что вы находитесь в директории проекта:
```bash
cd /Users/r.kirsanov/debt_bot
```

2. Активируйте виртуальное окружение (если ещё не активировано):
```bash
source venv/bin/activate
```

3. Убедитесь, что установлены зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите скрипт миграций:
```bash
python migrate.py
```

Вы должны увидеть вывод вида:
```
Применённых миграций: 0
Применяю 001_create_migrations_table...
✓ 001_create_migrations_table успешно применена
Применяю 002_create_users_table...
✓ 002_create_users_table успешно применена
...
```

5. Проверьте, что миграции применены. Подключитесь к базе данных:
```bash
psql -d debt_bot
```

И выполните:
```sql
SELECT version FROM schema_migrations;
```

Вы должны увидеть список применённых миграций.

---

## Устранение проблем

### Ошибка "database does not exist"
Убедитесь, что база данных создана:
```bash
createdb debt_bot
```

### Ошибка "role does not exist"
- **Postgres.app**: Используйте ваше системное имя пользователя. Проверьте: `whoami`
- **Официальный установщик**: Используйте `postgres` или созданного вами пользователя
- **Homebrew**: Используйте ваше системное имя пользователя. Проверьте: `whoami`

Укажите правильное имя в `DB_USER` в `.env`.

### Ошибка подключения
- Проверьте, что PostgreSQL запущен: `brew services list`
- Проверьте порт: `lsof -i :5432`
- Убедитесь, что в `.env` указаны правильные параметры

### Ошибка при применении миграций
- Убедитесь, что база данных пустая (или удалите и создайте заново)
- Проверьте права доступа пользователя к базе данных

---

## После успешной настройки

Теперь можно запускать бота:
```bash
python main.py
```

