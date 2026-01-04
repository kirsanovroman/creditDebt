"""
Сервис для работы с приглашениями.
"""
from typing import Optional
from datetime import datetime, timedelta
from datetime import timezone
from uuid import UUID, uuid4
import asyncpg
from database import Database
from models.invite import Invite
from repositories.debt_repository import DebtRepository
from repositories.invite_repository import InviteRepository
from services.audit_service import AuditService


class InviteService:
    """Сервис для работы с приглашениями."""
    
    def __init__(self):
        self.invite_repo = InviteRepository()
        self.debt_repo = DebtRepository()
        self.audit_service = AuditService()
    
    async def create_invite(
        self,
        debt_id: int,
        user_id: int
    ) -> Invite:
        """
        Создаёт новое приглашение для кредитора.
        
        Args:
            debt_id: ID долга
            user_id: ID пользователя, создающего приглашение (должен быть должником)
        
        Returns:
            Invite: Созданное приглашение
        
        Raises:
            ValueError: Если долг не найден или закрыт
            PermissionError: Если пользователь не является должником
        """
        # Проверяем доступ
        if not await self.debt_repo.check_access(debt_id, user_id):
            raise PermissionError("Нет доступа к этому долгу")
        
        # Получаем долг
        debt = await self.debt_repo.get_by_id(debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем, что пользователь является должником
        if debt.debtor_user_id != user_id:
            raise PermissionError("Только должник может создавать приглашения")
        
        # Проверяем статус (можно приглашать даже для закрытых долгов, если нужно)
        # Но в MVP, вероятно, лучше разрешить только для активных
        
        # Генерируем токен
        token = uuid4()
        
        # Устанавливаем срок действия на очень далёкое будущее (практически бесконечный)
        # Используем дату через 100 лет для совместимости с БД (NOT NULL constraint)
        expires_at = datetime.now(timezone.utc) + timedelta(days=36500)  # ~100 лет
        
        # Создаём приглашение в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Создаём приглашение
                invite = await self.invite_repo.create(
                    debt_id=debt_id,
                    token=token,
                    expires_at=expires_at,
                    conn=conn
                )
                
                # Логируем создание
                after = {
                    'id': invite.id,
                    'debt_id': invite.debt_id,
                    'token': str(invite.token),
                    'expires_at': str(invite.expires_at),
                }
                await self.audit_service.log_create(
                    entity_type='invite',
                    entity_id=invite.id,
                    actor_user_id=user_id,
                    after=after,
                    conn=conn
                )
                
                return invite
        
        finally:
            await pool.release(conn)
    
    async def accept_invite(
        self,
        token: UUID,
        user_id: int
    ) -> None:
        """
        Принимает приглашение (связывает пользователя с долгом как кредитор).
        
        Args:
            token: UUID токен приглашения
            user_id: ID пользователя, принимающего приглашение
        
        Raises:
            ValueError: Если токен невалиден, использован, или долг не найден
            PermissionError: Если пользователь уже является кредитором или должником
        
        Note:
            Срок действия приглашения не проверяется - приглашения действуют бессрочно.
        """
        # Получаем приглашение
        invite = await self.invite_repo.get_by_token(token)
        if invite is None:
            raise ValueError("Приглашение не найдено")
        
        # Проверяем валидность токена (только проверка на использование, срок действия не проверяем)
        if invite.is_used():
            raise ValueError("Приглашение уже использовано")
        
        # Получаем долг
        debt = await self.debt_repo.get_by_id(invite.debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем, что пользователь не является должником или кредитором
        if debt.debtor_user_id == user_id:
            raise PermissionError("Вы не можете быть кредитором своего долга")
        
        if debt.creditor_user_id == user_id:
            raise ValueError("Вы уже являетесь кредитором этого долга")
        
        # Принимаем приглашение в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Сохраняем состояние долга до изменения
                debt_before = {
                    'debt_id': debt.id,
                    'creditor_user_id': debt.creditor_user_id,
                }
                
                # Сохраняем состояние invite до изменения
                invite_before = {
                    'id': invite.id,
                    'debt_id': invite.debt_id,
                    'used_at': str(invite.used_at) if invite.used_at else None,
                }
                
                # Обновляем долг (назначаем кредитора)
                updated_debt = await self.debt_repo.update(
                    debt_id=debt.id,
                    creditor_user_id=user_id,
                    conn=conn
                )
                
                if updated_debt is None:
                    raise ValueError("Не удалось принять приглашение")
                
                # Отмечаем приглашение как использованное
                updated_invite = await self.invite_repo.mark_as_used(
                    invite_id=invite.id,
                    conn=conn
                )
                
                if updated_invite is None:
                    raise ValueError("Не удалось отметить приглашение как использованное")
                
                # Логируем изменение долга
                debt_after = {
                    'debt_id': updated_debt.id,
                    'creditor_user_id': updated_debt.creditor_user_id,
                }
                await self.audit_service.log_update(
                    entity_type='debt',
                    entity_id=debt.id,
                    actor_user_id=user_id,
                    before=debt_before,
                    after=debt_after,
                    conn=conn
                )
                
                # Логируем изменение invite (mark as used)
                invite_after = {
                    'id': updated_invite.id,
                    'debt_id': updated_invite.debt_id,
                    'used_at': str(updated_invite.used_at) if updated_invite.used_at else None,
                }
                await self.audit_service.log_update(
                    entity_type='invite',
                    entity_id=invite.id,
                    actor_user_id=user_id,
                    before=invite_before,
                    after=invite_after,
                    conn=conn
                )
        
        finally:
            await pool.release(conn)
    
    async def cleanup_expired_invites(self) -> int:
        """
        Очищает истекшие неиспользованные приглашения.
        
        Returns:
            Количество удалённых приглашений
        """
        return await self.invite_repo.cleanup_expired()

