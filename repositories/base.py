"""
Базовый класс для репозиториев.
"""
from typing import Optional
import asyncpg
from database import Database


class BaseRepository:
    """Базовый класс для всех репозиториев."""
    
    @staticmethod
    async def _get_connection() -> asyncpg.Connection:
        """Получает подключение из пула."""
        pool = await Database.get_pool()
        return await pool.acquire()
    
    @staticmethod
    async def _release_connection(conn: asyncpg.Connection) -> None:
        """Освобождает подключение обратно в пул."""
        pool = await Database.get_pool()
        await pool.release(conn)
    
    @staticmethod
    async def _transaction(conn: Optional[asyncpg.Connection] = None) -> asyncpg.Connection:
        """
        Начинает транзакцию или использует существующую.
        
        Args:
            conn: Существующее подключение с транзакцией, если есть
        
        Returns:
            Подключение с начатой транзакцией
        """
        if conn is not None:
            return conn
        
        pool = await Database.get_pool()
        conn = await pool.acquire()
        return conn
    
    @staticmethod
    async def _commit(conn: asyncpg.Connection, own_connection: bool = True) -> None:
        """Завершает транзакцию с коммитом."""
        if own_connection:
            await conn.close()
        # Если транзакция была передана извне, коммит делается там
    
    @staticmethod
    async def _rollback(conn: asyncpg.Connection, own_connection: bool = True) -> None:
        """Откатывает транзакцию."""
        if own_connection:
            await conn.close()
        # Если транзакция была передана извне, rollback делается там

