"""
Репозиторий для работы с приглашениями.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from datetime import timezone
from uuid import UUID
import asyncpg
from models.invite import Invite
from repositories.base import BaseRepository
from database import Database


class InviteRepository(BaseRepository):
    """Репозиторий для работы с приглашениями."""
    
    async def create(
        self,
        debt_id: int,
        token: UUID,
        expires_at: datetime,
        conn: Optional[asyncpg.Connection] = None
    ) -> Invite:
        """
        Создаёт новое приглашение.
        
        Args:
            debt_id: ID долга
            token: UUID токен
            expires_at: Дата истечения токена
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Invite: Созданное приглашение
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO invites (debt_id, token, expires_at, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, debt_id, token, expires_at, used_at, created_at
                """,
                debt_id,
                str(token),
                expires_at,
                datetime.now(timezone.utc)
            )
            
            return Invite.from_row(row)
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_token(
        self,
        token: UUID,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Invite]:
        """
        Получает приглашение по токену.
        
        Args:
            token: UUID токен
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Invite или None, если приглашение не найдено
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                SELECT id, debt_id, token, expires_at, used_at, created_at
                FROM invites
                WHERE token = $1
                """,
                str(token)
            )
            
            if row:
                return Invite.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def mark_as_used(
        self,
        invite_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Invite]:
        """
        Отмечает приглашение как использованное.
        
        Args:
            invite_id: ID приглашения
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Обновлённое Invite или None, если приглашение не найдено
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                UPDATE invites
                SET used_at = $1
                WHERE id = $2 AND used_at IS NULL
                RETURNING id, debt_id, token, expires_at, used_at, created_at
                """,
                datetime.now(timezone.utc),
                invite_id
            )
            
            if row:
                return Invite.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def cleanup_expired(
        self,
        conn: Optional[asyncpg.Connection] = None
    ) -> int:
        """
        Удаляет истекшие приглашения (опциональная функция для очистки).
        
        Args:
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Количество удалённых записей
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            deleted_count = await conn.execute(
                """
                DELETE FROM invites
                WHERE expires_at < NOW() AND used_at IS NULL
                """
            )
            
            # execute возвращает строку типа "DELETE 5", извлекаем число
            if isinstance(deleted_count, str):
                try:
                    return int(deleted_count.split()[-1])
                except (ValueError, IndexError):
                    return 0
            return 0
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)

