#!/usr/bin/env python3
"""
Скрипт для применения миграций базы данных.
"""
import asyncio
import os
import sys
from pathlib import Path
import asyncpg
from config import config


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    """Возвращает множество применённых миграций."""
    try:
        rows = await conn.fetch("SELECT version FROM schema_migrations")
        return {row['version'] for row in rows}
    except asyncpg.PostgresError:
        # Таблица schema_migrations ещё не существует
        return set()


async def apply_migration(conn: asyncpg.Connection, version: str, sql: str) -> None:
    """Применяет миграцию в транзакции."""
    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO schema_migrations (version) VALUES ($1)",
            version
        )


async def run_migrations() -> None:
    """Запускает все неприменённые миграции."""
    # Проверяем конфигурацию
    try:
        config.validate()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    
    # Подключаемся к базе данных
    try:
        conn = await asyncpg.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        sys.exit(1)
    
    try:
        # Получаем список применённых миграций
        applied = await get_applied_migrations(conn)
        print(f"Применённых миграций: {len(applied)}")
        
        # Находим все файлы миграций
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted([
            f for f in migrations_dir.glob("*.sql")
            if f.name != "__init__.py"
        ])
        
        applied_count = 0
        for migration_file in migration_files:
            version = migration_file.stem
            if version in applied:
                print(f"✓ {version} уже применена")
                continue
            
            print(f"Применяю {version}...")
            sql = migration_file.read_text(encoding='utf-8')
            
            try:
                await apply_migration(conn, version, sql)
                applied_count += 1
                print(f"✓ {version} успешно применена")
            except Exception as e:
                print(f"✗ Ошибка при применении {version}: {e}")
                raise
        
        if applied_count == 0:
            print("Все миграции уже применены.")
        else:
            print(f"\nВсего применено миграций: {applied_count}")
    
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())

