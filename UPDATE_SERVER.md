# Инструкция по обновлению бота на сервере

Пошаговая инструкция для обновления кода после мерджа в main на GitHub.

## Шаг 1: Подключение к серверу

```bash
ssh user@your_server_ip
# или если вы используете root
ssh root@your_server_ip
```

## Шаг 2: Переключение на пользователя debtbot

```bash
# Если вы подключились как root, переключитесь на пользователя debtbot
su - debtbot
# или
sudo su - debtbot
```

## Шаг 3: Переход в директорию проекта

```bash
cd /home/debtbot/debt_bot
```

## Шаг 4: Проверка текущего состояния

```bash
# Проверьте текущую ветку и статус
git status
git branch
```

## Шаг 5: Обновление кода из репозитория

```bash
# Переключитесь на ветку main (если не на ней)
git checkout main

# Получите последние изменения из GitHub
git pull origin main
```

## Шаг 6: Проверка изменений

```bash
# Посмотрите последние коммиты
git log --oneline -5

# Убедитесь, что файл миграции появился
ls -la migrations/004_create_payments_table.sql
```

## Шаг 7: Активация виртуального окружения

```bash
# Активируйте виртуальное окружение
source venv/bin/activate
```

## Шаг 8: Применение миграций (если были изменения в БД)

```bash
# Примените новые миграции
python migrate.py
```

Вы должны увидеть вывод вида:
```
Применённых миграций: X
Применяю 004_create_payments_table...
✓ 004_create_payments_table успешно применена
```

## Шаг 9: Перезапуск бота

```bash
# Выйдите из виртуального окружения (если нужно)
deactivate

# Перезапустите systemd сервис (нужны права root)
exit  # вернуться к root, если вы были debtbot
# или просто выполните с sudo:
sudo systemctl restart debtbot
```

## Шаг 10: Проверка статуса

```bash
# Проверьте, что бот запустился успешно
sudo systemctl status debtbot
```

Вы должны увидеть:
```
● debtbot.service - Debt Tracker Telegram Bot
   Loaded: loaded (/etc/systemd/system/debtbot.service; enabled)
   Active: active (running) since ...
```

## Шаг 11: Просмотр логов (опционально)

```bash
# Посмотрите последние логи
sudo journalctl -u debtbot -n 50

# Или следите за логами в реальном времени
sudo journalctl -u debtbot -f
```

## Полная последовательность команд (для копирования)

```bash
# 1. Подключение и переход
su - debtbot
cd /home/debtbot/debt_bot

# 2. Обновление кода
git checkout main
git pull origin main

# 3. Применение миграций
source venv/bin/activate
python migrate.py
deactivate

# 4. Перезапуск (от root)
exit
sudo systemctl restart debtbot

# 5. Проверка
sudo systemctl status debtbot
```

## Если что-то пошло не так

### Бот не запускается

```bash
# Посмотрите логи с ошибками
sudo journalctl -u debtbot -n 100 --no-pager

# Проверьте, что все файлы на месте
ls -la /home/debtbot/debt_bot/

# Проверьте права доступа
ls -la /home/debtbot/debt_bot/.env
```

### Ошибки при применении миграций

```bash
# Проверьте подключение к базе данных
source venv/bin/activate
python -c "from config import config; print(config.DB_NAME)"
python migrate.py
```

### Нужно откатить изменения

```bash
cd /home/debtbot/debt_bot
git log --oneline -10  # посмотрите коммиты
git checkout HEAD~1    # откатитесь на один коммит назад
sudo systemctl restart debtbot
```

### Проверка версии кода

```bash
cd /home/debtbot/debt_bot
git log --oneline -1   # последний коммит
git show HEAD --stat   # изменения в последнем коммите
```

---

**Готово!** Бот обновлён и перезапущен.

