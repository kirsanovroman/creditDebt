"""
Сервис для работы с долгами.
"""
from typing import Optional, List
from decimal import Decimal
import asyncpg
from database import Database
from models.debt import Debt
from repositories.debt_repository import DebtRepository
from services.audit_service import AuditService


class DebtService:
    """Сервис для работы с долгами."""
    
    def __init__(self):
        self.debt_repo = DebtRepository()
        self.audit_service = AuditService()
    
    async def create_debt(
        self,
        debtor_user_id: int,
        creditor_user_id: Optional[int],
        principal_amount: Decimal,
        currency: str = 'RUB',
        monthly_payment: Optional[Decimal] = None,
        due_day: Optional[int] = None,
        actor_user_id: Optional[int] = None
    ) -> Debt:
        """
        Создаёт новый долг с аудитом.
        
        Args:
            debtor_user_id: ID должника
            creditor_user_id: ID кредитора (опционально)
            principal_amount: Основная сумма долга
            currency: Валюта (по умолчанию 'RUB')
            monthly_payment: Ежемесячный платёж (опционально)
            due_day: День месяца для платежа (опционально, 1-31)
            actor_user_id: ID пользователя, создающего долг (по умолчанию debtor_user_id)
        
        Returns:
            Debt: Созданный долг
        
        Raises:
            ValueError: Если параметры невалидны
        """
        # Валидация
        if principal_amount <= 0:
            raise ValueError("Сумма долга должна быть больше нуля")
        
        if due_day is not None and (due_day < 1 or due_day > 31):
            raise ValueError("День платежа должен быть от 1 до 31")
        
        if monthly_payment is not None and monthly_payment <= 0:
            raise ValueError("Ежемесячный платёж должен быть больше нуля")
        
        if actor_user_id is None:
            actor_user_id = debtor_user_id
        
        # Создаём долг в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Создаём долг
                debt = await self.debt_repo.create(
                    debtor_user_id=debtor_user_id,
                    creditor_user_id=creditor_user_id,
                    principal_amount=principal_amount,
                    currency=currency,
                    monthly_payment=monthly_payment,
                    due_day=due_day,
                    conn=conn
                )
                
                # Логируем создание
                after = {
                    'id': debt.id,
                    'debtor_user_id': debt.debtor_user_id,
                    'creditor_user_id': debt.creditor_user_id,
                    'principal_amount': str(debt.principal_amount),
                    'currency': debt.currency,
                    'monthly_payment': str(debt.monthly_payment) if debt.monthly_payment else None,
                    'due_day': debt.due_day,
                    'status': debt.status,
                }
                await self.audit_service.log_create(
                    entity_type='debt',
                    entity_id=debt.id,
                    actor_user_id=actor_user_id,
                    after=after,
                    conn=conn
                )
                
                return debt
        
        finally:
            await pool.release(conn)
    
    async def get_user_debts(self, user_id: int) -> List[Debt]:
        """
        Получает все долги пользователя (как должника и как кредитора).
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Список долгов
        """
        # Получаем долги как должника и как кредитора параллельно
        debtor_debts = await self.debt_repo.get_by_debtor(user_id)
        creditor_debts = await self.debt_repo.get_by_creditor(user_id)
        
        # Объединяем списки
        all_debts = debtor_debts + creditor_debts
        
        # Убираем дубликаты (если пользователь одновременно должник и кредитор)
        seen_ids = set()
        unique_debts = []
        for debt in all_debts:
            if debt.id not in seen_ids:
                seen_ids.add(debt.id)
                unique_debts.append(debt)
        
        return unique_debts
    
    async def get_debt_by_id(self, debt_id: int) -> Optional[Debt]:
        """
        Получает долг по ID.
        
        Args:
            debt_id: ID долга
        
        Returns:
            Debt или None, если долг не найден
        """
        return await self.debt_repo.get_by_id(debt_id)
    
    async def check_access(self, debt_id: int, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя доступ к долгу.
        
        Args:
            debt_id: ID долга
            user_id: ID пользователя
        
        Returns:
            True, если пользователь является должником или кредитором
        """
        return await self.debt_repo.check_access(debt_id, user_id)
    
    async def update_debt_conditions(
        self,
        debt_id: int,
        user_id: int,
        monthly_payment: Optional[Decimal] = None,
        due_day: Optional[int] = None,
        creditor_user_id: Optional[int] = None
    ) -> Debt:
        """
        Обновляет условия долга (monthly_payment, due_day, creditor_user_id).
        
        Args:
            debt_id: ID долга
            user_id: ID пользователя, выполняющего действие
            monthly_payment: Новый ежемесячный платёж (опционально)
            due_day: Новый день платежа (опционально, 1-31)
            creditor_user_id: ID кредитора (опционально)
        
        Returns:
            Обновлённый Debt
        
        Raises:
            ValueError: Если долг закрыт или параметры невалидны
            PermissionError: Если пользователь не имеет прав
        """
        # Проверяем доступ
        if not await self.check_access(debt_id, user_id):
            raise PermissionError("Нет доступа к этому долгу")
        
        # Получаем текущий долг
        debt = await self.debt_repo.get_by_id(debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем статус
        if debt.status == 'closed':
            raise ValueError("Нельзя изменять закрытый долг")
        
        # Проверяем, что пользователь является должником (только должник может изменять)
        if debt.debtor_user_id != user_id:
            raise PermissionError("Только должник может изменять условия долга")
        
        # Валидация параметров
        if due_day is not None and (due_day < 1 or due_day > 31):
            raise ValueError("День платежа должен быть от 1 до 31")
        
        if monthly_payment is not None and monthly_payment <= 0:
            raise ValueError("Ежемесячный платёж должен быть больше нуля")
        
        # Обновляем в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Сохраняем состояние до изменения
                before = {
                    'id': debt.id,
                    'monthly_payment': str(debt.monthly_payment) if debt.monthly_payment else None,
                    'due_day': debt.due_day,
                    'creditor_user_id': debt.creditor_user_id,
                }
                
                # Обновляем долг
                updated_debt = await self.debt_repo.update(
                    debt_id=debt_id,
                    creditor_user_id=creditor_user_id,
                    monthly_payment=monthly_payment,
                    due_day=due_day,
                    conn=conn
                )
                
                if updated_debt is None:
                    raise ValueError("Не удалось обновить долг")
                
                # Логируем изменение
                after = {
                    'id': updated_debt.id,
                    'monthly_payment': str(updated_debt.monthly_payment) if updated_debt.monthly_payment else None,
                    'due_day': updated_debt.due_day,
                    'creditor_user_id': updated_debt.creditor_user_id,
                }
                await self.audit_service.log_update(
                    entity_type='debt',
                    entity_id=debt_id,
                    actor_user_id=user_id,
                    before=before,
                    after=after,
                    conn=conn
                )
                
                return updated_debt
        
        finally:
            await pool.release(conn)
    
    async def close_debt(
        self,
        debt_id: int,
        user_id: int,
        close_note: Optional[str] = None
    ) -> Debt:
        """
        Закрывает долг.
        
        Args:
            debt_id: ID долга
            user_id: ID пользователя, закрывающего долг
            close_note: Примечание при закрытии (опционально)
        
        Returns:
            Закрытый Debt
        
        Raises:
            ValueError: Если долг уже закрыт или не найден
            PermissionError: Если пользователь не имеет прав
        """
        # Проверяем доступ
        if not await self.check_access(debt_id, user_id):
            raise PermissionError("Нет доступа к этому долгу")
        
        # Получаем текущий долг
        debt = await self.debt_repo.get_by_id(debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем статус
        if debt.status == 'closed':
            raise ValueError("Долг уже закрыт")
        
        # Проверяем, что пользователь является должником (только должник может закрывать)
        if debt.debtor_user_id != user_id:
            raise PermissionError("Только должник может закрыть долг")
        
        # Закрываем в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Сохраняем состояние до закрытия
                before = {
                    'id': debt.id,
                    'status': debt.status,
                    'closed_at': str(debt.closed_at) if debt.closed_at else None,
                    'close_note': debt.close_note,
                }
                
                # Закрываем долг
                closed_debt = await self.debt_repo.close_debt(
                    debt_id=debt_id,
                    close_note=close_note,
                    conn=conn
                )
                
                if closed_debt is None:
                    raise ValueError("Не удалось закрыть долг")
                
                # Логируем закрытие
                after = {
                    'id': closed_debt.id,
                    'status': closed_debt.status,
                    'closed_at': str(closed_debt.closed_at) if closed_debt.closed_at else None,
                    'close_note': closed_debt.close_note,
                }
                await self.audit_service.log_close(
                    entity_type='debt',
                    entity_id=debt_id,
                    actor_user_id=user_id,
                    before=before,
                    after=after,
                    conn=conn
                )
                
                return closed_debt
        
        finally:
            await pool.release(conn)

