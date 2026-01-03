"""
Модуль для подключения к базе данных PostgreSQL.
"""
import asyncpg
from typing import Optional
from config import config


class Database:
    """Класс для управления подключением к базе данных."""
    
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def create_pool(cls) -> asyncpg.Pool:
        """Создаёт и возвращает пул подключений к базе данных."""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME,
                min_size=1,
                max_size=10,
            )
        return cls._pool
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Возвращает пул подключений, создавая его при необходимости."""
        if cls._pool is None:
            return await cls.create_pool()
        return cls._pool
    
    @classmethod
    async def close_pool(cls) -> None:
        """Закрывает пул подключений."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None
    
    @classmethod
    async def execute(cls, query: str, *args) -> str:
        """Выполняет запрос и возвращает результат."""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    @classmethod
    async def fetch(cls, query: str, *args):
        """Выполняет запрос и возвращает все строки."""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    @classmethod
    async def fetchrow(cls, query: str, *args):
        """Выполняет запрос и возвращает одну строку."""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.fetchrow(query, *args)
    
    @classmethod
    async def fetchval(cls, query: str, *args):
        """Выполняет запрос и возвращает одно значение."""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            return await connection.fetchval(query, *args)

