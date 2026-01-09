# Инструкция по обновлению бота на сервере

Простая пошаговая инструкция для обновления кода бота после изменений в репозитории GitHub.

## Быстрая инструкция (для копирования)

```bash
# 1. Подключитесь к серверу
ssh user@your_server_ip

# 2. Переключитесь на пользователя debtbot
su - debtbot

# 3. Перейдите в директорию проекта
cd /home/debtbot/debt_bot

# 4. Обновите код из репозитория
git checkout main
git pull origin main

# 5. Примените миграции (если были изменения в БД)
source venv/bin/activate
python migrate.py
deactivate

# 6. Выйдите из пользователя debtbot
exit

# 7. Перезапустите бота
sudo systemctl restart debtbot

# 8. Проверьте статус
sudo systemctl status debtbot
```

---

## Подробная инструкция

### Шаг 1: Подключение к серверу

```bash
ssh user@your_server_ip
```

Или если используете root:
```bash
ssh root@your_server_ip
```

### Шаг 2: Переключение на пользователя debtbot

```bash
su - debtbot
```

Если требуется пароль, введите пароль пользователя debtbot.

### Шаг 3: Переход в директорию проекта

```bash
cd /home/debtbot/debt_bot
```

### Шаг 4: Обновление кода из репозитория

```bash
# Убедитесь, что вы на ветке main
git checkout main

# Получите последние изменения из GitHub
git pull origin main
```

**Вывод должен быть примерно таким:**
```
Updating abc1234..def5678
Fast-forward
 handlers/utils.py          | 45 ++++++++++++++++++++
 services/planner_service.py |  2 +-
 2 files changed, 46 insertions(+), 1 deletion(-)
```

### Шаг 5: Применение миграций (если были изменения в БД)

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Примените новые миграции
python migrate.py

# Выйдите из виртуального окружения
deactivate
```

**Вывод должен быть примерно таким:**
```
Применённых миграций: 7
Применяю 008_new_migration...
✓ 008_new_migration успешно применена
```

**Если миграций нет:**
```
Все миграции уже применены.
```

### Шаг 6: Выход из пользователя debtbot

```bash
exit
```

Это вернёт вас к предыдущему пользователю (root или вашему пользователю).

### Шаг 7: Перезапуск бота

```bash
sudo systemctl restart debtbot
```

### Шаг 8: Проверка статуса

```bash
sudo systemctl status debtbot
```

**Успешный статус должен показывать:**
```
● debtbot.service - Debt Tracker Telegram Bot
   Loaded: loaded (/etc/systemd/system/debtbot.service; enabled)
   Active: active (running) since ...
```

### Шаг 9: Просмотр логов (опционально)

```bash
# Последние 50 строк логов
sudo journalctl -u debtbot -n 50

# Логи в реальном времени (Ctrl+C для выхода)
sudo journalctl -u debtbot -f
```

---

## Обновление конкретной ветки

Если нужно обновить код из конкретной ветки (не main):

```bash
# Переключитесь на нужную ветку
git checkout feature/branch-name

# Получите изменения
git pull origin feature/branch-name

# Остальные шаги те же (миграции, перезапуск)
```

---

## Откат изменений (если что-то пошло не так)

Если после обновления бот не работает, можно откатиться к предыдущей версии:

```bash
cd /home/debtbot/debt_bot

# Посмотрите историю коммитов
git log --oneline -10

# Откатитесь на предыдущий коммит
git checkout HEAD~1

# Или на конкретный коммит
git checkout abc1234

# Перезапустите бота
exit
sudo systemctl restart debtbot
```

---

## Проверка изменений перед обновлением

Перед обновлением можно посмотреть, что изменилось:

```bash
cd /home/debtbot/debt_bot

# Посмотрите последние коммиты на GitHub
git fetch origin
git log HEAD..origin/main --oneline

# Посмотрите детали изменений
git diff HEAD origin/main
```

---

## Частые проблемы и решения

### Ошибка "Your local changes would be overwritten"

Если у вас есть локальные изменения, которые конфликтуют:

```bash
# Сохраните изменения (если нужны)
git stash

# Или отмените изменения (если не нужны)
git reset --hard HEAD

# Затем повторите git pull
git pull origin main
```

### Ошибка при применении миграций

```bash
# Проверьте подключение к БД
source venv/bin/activate
python -c "from config import config; print(config.DB_NAME)"

# Проверьте логи миграций
python migrate.py
```

### Бот не запускается после обновления

```bash
# Посмотрите логи с ошибками
sudo journalctl -u debtbot -n 100 --no-pager

# Проверьте синтаксис Python файлов
cd /home/debtbot/debt_bot
source venv/bin/activate
python -m py_compile main.py
```

### Проверка версии кода

```bash
cd /home/debtbot/debt_bot
git log --oneline -1   # Последний коммит
git show HEAD --stat   # Изменения в последнем коммите
```

---

## Автоматизация (опционально)

Можно создать скрипт для автоматического обновления:

```bash
# Создайте файл update_bot.sh
nano /home/debtbot/update_bot.sh
```

Содержимое скрипта:
```bash
#!/bin/bash
cd /home/debtbot/debt_bot
git checkout main
git pull origin main
source venv/bin/activate
python migrate.py
deactivate
sudo systemctl restart debtbot
echo "Бот обновлён!"
```

Сделайте скрипт исполняемым:
```bash
chmod +x /home/debtbot/update_bot.sh
```

Затем можно обновлять одной командой:
```bash
sudo -u debtbot /home/debtbot/update_bot.sh
```

---

**Готово!** Теперь вы знаете, как обновить бота на сервере.

