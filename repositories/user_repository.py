"""
Репозиторий для работы с пользователями.
"""
from typing import Optional
from datetime import datetime
from datetime import timezone
import asyncpg
from models.user import User
from repositories.base import BaseRepository
from database import Database


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""
    
    async def create_or_get_by_tg_id(
        self,
        tg_user_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> User:
        """
        Создаёт пользователя или возвращает существующего по tg_user_id.
        
        Args:
            tg_user_id: Telegram user ID
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            User: Созданный или найденный пользователь
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            # Пытаемся найти существующего пользователя
            row = await conn.fetchrow(
                "SELECT id, tg_user_id, created_at FROM users WHERE tg_user_id = $1",
                tg_user_id
            )
            
            if row:
                return User.from_row(row)
            
            # Создаём нового пользователя
            row = await conn.fetchrow(
                """
                INSERT INTO users (tg_user_id, created_at)
                VALUES ($1, $2)
                RETURNING id, tg_user_id, created_at
                """,
                tg_user_id,
                datetime.now(timezone.utc)
            )
            
            return User.from_row(row)
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_id(
        self,
        user_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[User]:
        """
        Получает пользователя по ID.
        
        Args:
            user_id: ID пользователя
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            User или None, если пользователь не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                "SELECT id, tg_user_id, created_at FROM users WHERE id = $1",
                user_id
            )
            
            if row:
                return User.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)

