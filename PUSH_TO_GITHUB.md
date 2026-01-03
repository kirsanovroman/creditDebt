# Инструкция по отправке проекта в GitHub

## Шаг 1: Настройка Git (если ещё не настроено)

```bash
# Настройте ваше имя и email (глобально для всех репозиториев)
git config --global user.name "Ваше Имя"
git config --global user.email "your.email@example.com"

# Или только для этого репозитория
git config user.name "Ваше Имя"
git config user.email "your.email@example.com"
```

## Шаг 2: Создайте репозиторий на GitHub

1. Откройте https://github.com
2. Нажмите кнопку "+" в правом верхнем углу → "New repository"
3. Заполните:
   - **Repository name**: `debt_bot` (или другое имя)
   - **Description**: "Telegram bot for debt tracking"
   - **Visibility**: Public или Private (на ваше усмотрение)
   - **НЕ** создавайте README, .gitignore или license (они уже есть)
4. Нажмите "Create repository"

## Шаг 3: Сделайте первый коммит

```bash
cd /Users/r.kirsanov/debt_bot

# Добавьте все файлы
git add .

# Сделайте коммит
git commit -m "Initial commit: Debt Tracker Telegram Bot MVP

- Complete bot implementation with debt tracking
- PostgreSQL database with migrations
- Services layer with business logic
- Repositories for data access
- Telegram handlers for all features
- Audit logging and transactions
- Security and validation
- Unit tests for PlannerService
- Documentation and deployment guides"
```

## Шаг 4: Подключите удалённый репозиторий

После создания репозитория на GitHub, скопируйте URL (например: `https://github.com/username/debt_bot.git`)

```bash
# Добавьте удалённый репозиторий
git remote add origin https://github.com/ВАШ_USERNAME/debt_bot.git

# Проверьте, что всё правильно
git remote -v
```

## Шаг 5: Отправьте код в GitHub

```bash
# Отправьте код в GitHub (первый раз)
git push -u origin main

# В дальнейшем можно просто использовать
git push
```

## Если используете SSH вместо HTTPS

Если вы настроили SSH ключи для GitHub:

```bash
git remote add origin git@github.com:ВАШ_USERNAME/debt_bot.git
git push -u origin main
```

## Дополнительные команды

```bash
# Проверить статус
git status

# Посмотреть историю коммитов
git log --oneline

# Посмотреть удалённые репозитории
git remote -v

# Изменить URL удалённого репозитория (если нужно)
git remote set-url origin НОВЫЙ_URL
```

## Важно!

⚠️ **Убедитесь, что файл `.env` НЕ попал в репозиторий!**

Проверьте:
```bash
git check-ignore .env
# Должно вывести: .env
```

Если `.env` попал в репозиторий, удалите его:
```bash
git rm --cached .env
git commit -m "Remove .env from repository"
```

Файл `.env.example` должен быть в репозитории - это шаблон для других разработчиков.

