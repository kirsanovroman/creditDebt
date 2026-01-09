#!/bin/bash
# Скрипт для настройки локальной базы данных

echo "🔧 Настройка локальной базы данных для Debt Tracker Bot"
echo ""

# Проверяем, запущен ли PostgreSQL
if ! /Applications/Postgres.app/Contents/Versions/latest/bin/pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️  PostgreSQL не запущен!"
    echo ""
    echo "1. Откройте Postgres.app из папки Applications"
    echo "2. Нажмите кнопку 'Initialize' если сервер не инициализирован"
    echo "3. Убедитесь, что сервер запущен (зелёный индикатор)"
    echo "4. Запустите этот скрипт снова"
    exit 1
fi

echo "✅ PostgreSQL запущен"
echo ""

# Получаем имя пользователя
DB_USER=$(whoami)
echo "Используется пользователь: $DB_USER"
echo ""

# Проверяем, существует ли база данных
if /Applications/Postgres.app/Contents/Versions/latest/bin/psql -lqt | cut -d \| -f 1 | grep -qw debt_bot; then
    echo "ℹ️  База данных 'debt_bot' уже существует"
    read -p "Пересоздать базу данных? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Удаляю старую базу данных..."
        /Applications/Postgres.app/Contents/Versions/latest/bin/dropdb debt_bot 2>/dev/null
        echo "Создаю новую базу данных..."
        /Applications/Postgres.app/Contents/Versions/latest/bin/createdb debt_bot
        echo "✅ База данных создана"
    else
        echo "Используется существующая база данных"
    fi
else
    echo "Создаю базу данных 'debt_bot'..."
    /Applications/Postgres.app/Contents/Versions/latest/bin/createdb debt_bot
    echo "✅ База данных создана"
fi

echo ""
echo "📝 Следующие шаги:"
echo ""
echo "1. Убедитесь, что в .env.local указаны правильные параметры:"
echo "   DB_USER=$DB_USER"
echo "   DB_PASSWORD= (пусто)"
echo ""
echo "2. Примените миграции:"
echo "   source venv/bin/activate"
echo "   python migrate.py"
echo ""
echo "3. Запустите бота:"
echo "   python3 main.py"
echo ""
