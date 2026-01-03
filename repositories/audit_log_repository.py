"""
Репозиторий для работы с записями аудита.
"""
from typing import Optional
from datetime import datetime
from datetime import timezone
import json
import asyncpg
from models.audit_log import AuditLog
from repositories.base import BaseRepository
from database import Database


class AuditLogRepository(BaseRepository):
    """Репозиторий для работы с записями аудита."""
    
    async def create(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        actor_user_id: int,
        before: Optional[dict] = None,
        after: Optional[dict] = None,
        conn: Optional[asyncpg.Connection] = None
    ) -> AuditLog:
        """
        Создаёт новую запись аудита.
        
        Args:
            entity_type: Тип сущности ('debt', 'payment', 'invite')
            entity_id: ID сущности
            action: Действие ('create', 'update', 'delete', 'close')
            actor_user_id: ID пользователя, выполнившего действие
            before: Состояние до изменения (опционально)
            after: Состояние после изменения (опционально)
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            AuditLog: Созданная запись аудита
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            # Преобразуем dict в JSON для JSONB
            before_json = json.dumps(before) if before else None
            after_json = json.dumps(after) if after else None
            
            row = await conn.fetchrow(
                """
                INSERT INTO audit_log (
                    entity_type, entity_id, action, actor_user_id,
                    occurred_at, before, after
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, entity_type, entity_id, action, actor_user_id,
                          occurred_at, before, after
                """,
                entity_type,
                entity_id,
                action,
                actor_user_id,
                datetime.now(timezone.utc),
                before_json,
                after_json
            )
            
            return AuditLog.from_row(row)
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)

