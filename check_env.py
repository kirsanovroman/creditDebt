#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки загрузки переменных окружения.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

print("=" * 60)
print("Проверка загрузки переменных окружения")
print("=" * 60)

# Проверяем файлы
env_path = Path('.env')
env_local_path = Path('.env.local')

print(f"\n1. Проверка файлов:")
print(f"   .env существует: {env_path.exists()}")
print(f"   .env.local существует: {env_local_path.exists()}")

if env_path.exists():
    print(f"\n2. Содержимое .env (BOT_TOKEN):")
    load_dotenv(dotenv_path=env_path, override=True)
    token = os.getenv("BOT_TOKEN", "")
    if token:
        print(f"   {token[:20]}...{token[-10:]}")
    else:
        print("   BOT_TOKEN не найден")

if env_local_path.exists():
    print(f"\n3. Содержимое .env.local (BOT_TOKEN):")
    load_dotenv(dotenv_path=env_local_path, override=True)
    token = os.getenv("BOT_TOKEN", "")
    if token:
        if token == "your_bot_token_here":
            print(f"   ⚠️  ВНИМАНИЕ: Токен не заменён! Всё ещё 'your_bot_token_here'")
            print(f"   Замените BOT_TOKEN в .env.local на токен от BotFather")
        else:
            print(f"   ✅ {token[:20]}...{token[-10:]}")
    else:
        print("   BOT_TOKEN не найден")

# Финальная проверка
print(f"\n4. Итоговое значение BOT_TOKEN (после загрузки .env.local):")
if env_local_path.exists():
    load_dotenv(dotenv_path=env_local_path, override=True)
    load_dotenv(dotenv_path=env_path, override=False)
else:
    load_dotenv(dotenv_path=env_path, override=True)

final_token = os.getenv("BOT_TOKEN", "")
if final_token:
    if final_token == "your_bot_token_here":
        print(f"   ❌ ОШИБКА: Используется placeholder токен!")
        print(f"   Замените BOT_TOKEN в .env.local на реальный токен от BotFather")
    else:
        print(f"   ✅ {final_token[:20]}...{final_token[-10:]}")
else:
    print("   ❌ BOT_TOKEN не найден")

print("\n" + "=" * 60)
