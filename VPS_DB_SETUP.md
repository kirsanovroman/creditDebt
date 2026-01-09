# Установка PostgreSQL на VPS сервере

Эта инструкция поможет установить PostgreSQL на VPS сервере с Ubuntu/Debian.

## Шаг 1: Подключение к серверу

```bash
ssh user@your_server_ip
```

## Шаг 2: Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

## Шаг 3: Установка PostgreSQL

```bash
# Установка PostgreSQL и необходимых пакетов
sudo apt install postgresql postgresql-contrib -y
```

После установки PostgreSQL автоматически запустится как системный сервис.

## Шаг 4: Проверка установки

```bash
# Проверка статуса сервиса
sudo systemctl status postgresql

# Проверка версии
psql --version
```

## Шаг 5: Настройка пароля для пользователя postgres

По умолчанию PostgreSQL создаёт пользователя `postgres` без пароля. Нужно задать пароль:

```bash
# Переключитесь на пользователя postgres
sudo -u postgres psql

# В psql выполните:
ALTER USER postgres WITH PASSWORD 'ваш_надежный_пароль';
\q
```

**Важно:** Запишите этот пароль! Он понадобится для настройки `.env` файла.

## Шаг 6: Создание базы данных

**Важно:** Используйте пользователя `postgres` для создания базы данных, а не вашего системного пользователя.

```bash
# Подключитесь к PostgreSQL от имени пользователя postgres
sudo -u postgres psql

# Создайте базу данных для бота
CREATE DATABASE debt_bot;

# (Опционально) Создайте отдельного пользователя для бота (рекомендуется)
CREATE USER debt_bot_user WITH PASSWORD 'пароль_для_бота';
GRANT ALL PRIVILEGES ON DATABASE debt_bot TO debt_bot_user;

# Выйдите из psql
\q
```

**Альтернативный способ (без входа в psql):**

```bash
# Создать базу данных одной командой
sudo -u postgres createdb debt_bot
```

**⚠️ Если система запрашивает пароль sudo:**

Если при выполнении `sudo -u postgres createdb debt_bot` система запрашивает пароль для вашего системного пользователя (например, "password for debtbot"), это пароль sudo, а не пароль PostgreSQL.

**Варианты решения:**

1. **Введите пароль sudo** (если знаете):
   - Это пароль, который вы используете для входа на сервер или для выполнения административных команд

2. **Войдите напрямую как postgres** (если настроен вход):
   ```bash
   su - postgres
   createdb debt_bot
   exit
   ```

3. **Используйте psql с одной командой** (может не требовать sudo пароль):
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE debt_bot;"
   ```

4. **Если у вас есть доступ к root:**
   ```bash
   su -
   createdb -U postgres debt_bot
   exit
   ```

5. **Если пароль sudo неизвестен**, обратитесь к администратору сервера или используйте другой способ доступа к серверу.

**Если система запрашивает пароль для вашего системного пользователя:**

Если вы видите запрос "password for debtbot" (или ваше имя пользователя), это означает, что PostgreSQL пытается использовать вашего системного пользователя. В этом случае:

1. **Используйте пользователя postgres** (рекомендуется):
   ```bash
   sudo -u postgres createdb debt_bot
   ```

2. **Или задайте пароль для вашего пользователя в PostgreSQL:**
   ```bash
   # Войдите как postgres
   sudo -u postgres psql
   
   # Создайте пользователя с паролем (если его нет)
   CREATE USER debtbot WITH PASSWORD 'ваш_пароль';
   ALTER USER debtbot CREATEDB;  # Дать права на создание БД
   \q
   
   # Теперь можно создать БД
   createdb debt_bot
   ```

3. **Или просто нажмите Enter** (если пароль не задан, может сработать подключение без пароля)

## Шаг 7: Настройка удалённого доступа (опционально)

Если нужно подключаться к базе данных с другого сервера:

### 7.1. Редактирование postgresql.conf

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Найдите строку:
```
#listen_addresses = 'localhost'
```

Измените на:
```
listen_addresses = '*'  # или укажите конкретный IP
```

### 7.2. Редактирование pg_hba.conf

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Добавьте в конец файла (для подключения по паролю):
```
host    all             all             0.0.0.0/0               md5
```

Или для подключения только с конкретного IP:
```
host    all             all             ваш_IP/32               md5
```

### 7.3. Перезапуск PostgreSQL

```bash
sudo systemctl restart postgresql
```

### 7.4. Настройка файрвола (если используется)

```bash
# Для UFW
sudo ufw allow 5432/tcp

# Для firewalld
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

**⚠️ Внимание:** Открытие порта 5432 для всех (0.0.0.0/0) может быть небезопасно. Используйте только для доверенных сетей или настройте VPN.

## Шаг 8: Проверка подключения

### Локально на сервере:

```bash
# С пользователем postgres
sudo -u postgres psql -d debt_bot

# Или с созданным пользователем
psql -U debt_bot_user -d debt_bot -h localhost
```

### Удалённо (если настроили):

```bash
psql -U postgres -d debt_bot -h ваш_IP_сервера
```

## Шаг 9: Настройка .env файла на сервере

В файле `.env` вашего бота укажите:

```env
DB_HOST=localhost  # или IP сервера, если подключаетесь удалённо
DB_PORT=5432
DB_NAME=debt_bot
DB_USER=postgres  # или debt_bot_user, если создали отдельного пользователя
DB_PASSWORD=ваш_пароль_из_шага_5
```

## Шаг 10: Применение миграций

```bash
cd /path/to/debt_bot
source venv/bin/activate  # если используете venv
python migrate.py
```

## Полезные команды

### Управление сервисом PostgreSQL:

```bash
# Запуск
sudo systemctl start postgresql

# Остановка
sudo systemctl stop postgresql

# Перезапуск
sudo systemctl restart postgresql

# Статус
sudo systemctl status postgresql

# Автозапуск при загрузке (обычно уже включен)
sudo systemctl enable postgresql
```

### Резервное копирование:

```bash
# Создание бэкапа
sudo -u postgres pg_dump debt_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
sudo -u postgres psql debt_bot < backup_file.sql
```

### Просмотр баз данных:

```bash
sudo -u postgres psql -l
```

### Подключение к конкретной базе:

```bash
sudo -u postgres psql -d debt_bot
```

## Безопасность

1. **Используйте сильные пароли** для пользователей PostgreSQL
2. **Ограничьте доступ** в `pg_hba.conf` только доверенным IP
3. **Не открывайте порт 5432** для всех, если не требуется удалённый доступ
4. **Регулярно обновляйте** PostgreSQL: `sudo apt update && sudo apt upgrade postgresql`
5. **Настройте бэкапы** базы данных

## Устранение проблем

### Ошибка "could not connect to server"

```bash
# Проверьте, запущен ли PostgreSQL
sudo systemctl status postgresql

# Если не запущен, запустите
sudo systemctl start postgresql
```

### Ошибка "Peer authentication failed"

Эта ошибка возникает, когда вы пытаетесь подключиться к PostgreSQL от имени пользователя, который не совпадает с системным пользователем PostgreSQL.

**Решение:**

1. **Войдите как системный пользователь postgres:**
   ```bash
   su - postgres
   createdb debt_bot
   exit
   ```

2. **Или используйте sudo:**
   ```bash
   sudo -u postgres createdb debt_bot
   ```

3. **Или измените метод аутентификации в pg_hba.conf:**
   ```bash
   sudo nano /etc/postgresql/*/main/pg_hba.conf
   ```
   
   Найдите строку:
   ```
   local   all             postgres                                peer
   ```
   
   Измените на:
   ```
   local   all             postgres                                md5
   ```
   
   Затем перезапустите PostgreSQL:
   ```bash
   sudo systemctl restart postgresql
   ```
   
   Теперь можно будет подключиться с паролем:
   ```bash
   psql -U postgres -d postgres
   # Введите пароль, который вы задали в шаге 5
   ```

### Ошибка "password authentication failed"

- Проверьте правильность пароля в `.env`
- Убедитесь, что в `pg_hba.conf` настроена аутентификация `md5` или `password`

### Ошибка "database does not exist"

```bash
# Создайте базу данных
sudo -u postgres createdb debt_bot
```

### Ошибка "role does not exist"

```bash
# Создайте пользователя
sudo -u postgres createuser --interactive debt_bot_user
# Или с паролем:
sudo -u postgres psql -c "CREATE USER debt_bot_user WITH PASSWORD 'пароль';"
```

### Просмотр логов PostgreSQL

```bash
# Логи systemd
sudo journalctl -u postgresql -f

# Или файл логов
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

## Дополнительные настройки производительности (опционально)

Для продакшена можно оптимизировать PostgreSQL:

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

Основные параметры:
- `shared_buffers` - обычно 25% от RAM
- `effective_cache_size` - обычно 50-75% от RAM
- `maintenance_work_mem` - для операций обслуживания
- `checkpoint_completion_target` - для сглаживания нагрузки

После изменений перезапустите:
```bash
sudo systemctl restart postgresql
```

---

**Готово!** Теперь PostgreSQL установлен и настроен на вашем VPS сервере.

