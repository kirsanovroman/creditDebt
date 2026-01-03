"""
Сервис для аудита операций.
"""
from typing import Optional
import asyncpg
from repositories.audit_log_repository import AuditLogRepository


class AuditService:
    """Сервис для аудита операций."""
    
    def __init__(self):
        self.audit_repo = AuditLogRepository()
    
    async def log_create(
        self,
        entity_type: str,
        entity_id: int,
        actor_user_id: int,
        after: dict,
        conn: Optional[asyncpg.Connection] = None
    ) -> None:
        """
        Логирует создание сущности.
        
        Args:
            entity_type: Тип сущности ('debt', 'payment', 'invite')
            entity_id: ID сущности
            actor_user_id: ID пользователя, выполнившего действие
            after: Состояние после создания
            conn: Подключение к БД (для транзакции)
        """
        await self.audit_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action='create',
            actor_user_id=actor_user_id,
            before=None,
            after=after,
            conn=conn
        )
    
    async def log_update(
        self,
        entity_type: str,
        entity_id: int,
        actor_user_id: int,
        before: dict,
        after: dict,
        conn: Optional[asyncpg.Connection] = None
    ) -> None:
        """
        Логирует обновление сущности.
        
        Args:
            entity_type: Тип сущности ('debt', 'payment', 'invite')
            entity_id: ID сущности
            actor_user_id: ID пользователя, выполнившего действие
            before: Состояние до изменения
            after: Состояние после изменения
            conn: Подключение к БД (для транзакции)
        """
        await self.audit_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action='update',
            actor_user_id=actor_user_id,
            before=before,
            after=after,
            conn=conn
        )
    
    async def log_delete(
        self,
        entity_type: str,
        entity_id: int,
        actor_user_id: int,
        before: dict,
        conn: Optional[asyncpg.Connection] = None
    ) -> None:
        """
        Логирует удаление сущности (soft delete).
        
        Args:
            entity_type: Тип сущности ('debt', 'payment', 'invite')
            entity_id: ID сущности
            actor_user_id: ID пользователя, выполнившего действие
            before: Состояние до удаления
            conn: Подключение к БД (для транзакции)
        """
        await self.audit_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action='delete',
            actor_user_id=actor_user_id,
            before=before,
            after=None,
            conn=conn
        )
    
    async def log_close(
        self,
        entity_type: str,
        entity_id: int,
        actor_user_id: int,
        before: dict,
        after: dict,
        conn: Optional[asyncpg.Connection] = None
    ) -> None:
        """
        Логирует закрытие долга.
        
        Args:
            entity_type: Тип сущности (обычно 'debt')
            entity_id: ID сущности
            actor_user_id: ID пользователя, выполнившего действие
            before: Состояние до закрытия
            after: Состояние после закрытия
            conn: Подключение к БД (для транзакции)
        """
        await self.audit_repo.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action='close',
            actor_user_id=actor_user_id,
            before=before,
            after=after,
            conn=conn
        )

