"""
Сервис для работы с платежами.
"""
from typing import Optional, List
from datetime import date
from decimal import Decimal
import asyncpg
from database import Database
from models.debt import Debt
from models.payment import Payment
from repositories.debt_repository import DebtRepository
from repositories.payment_repository import PaymentRepository
from services.audit_service import AuditService


class PaymentService:
    """Сервис для работы с платежами."""
    
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.debt_repo = DebtRepository()
        self.audit_service = AuditService()
    
    async def add_payment(
        self,
        debt_id: int,
        amount: Decimal,
        payment_date: date,
        user_id: int
    ) -> Payment:
        """
        Добавляет платёж.
        
        Args:
            debt_id: ID долга
            amount: Сумма платежа
            payment_date: Дата платежа
            user_id: ID пользователя, добавляющего платёж
        
        Returns:
            Payment: Созданный платёж
        
        Raises:
            ValueError: Если долг закрыт, не найден, или сумма невалидна
            PermissionError: Если пользователь не является должником
        """
        # Проверяем доступ
        if not await self.debt_repo.check_access(debt_id, user_id):
            raise PermissionError("Нет доступа к этому долгу")
        
        # Получаем долг
        debt = await self.debt_repo.get_by_id(debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем статус
        if debt.status == 'closed':
            raise ValueError("Нельзя добавлять платежи к закрытому долгу")
        
        # Проверяем, что пользователь является должником (только должник может добавлять платежи)
        if debt.debtor_user_id != user_id:
            raise PermissionError("Только должник может добавлять платежи")
        
        # Валидация суммы
        if amount <= 0:
            raise ValueError("Сумма платежа должна быть больше нуля")
        
        # Создаём платёж в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Создаём платёж
                payment = await self.payment_repo.create(
                    debt_id=debt_id,
                    amount=amount,
                    payment_date=payment_date,
                    conn=conn
                )
                
                # Логируем создание
                after = {
                    'id': payment.id,
                    'debt_id': payment.debt_id,
                    'amount': str(payment.amount),
                    'payment_date': str(payment.payment_date),
                }
                await self.audit_service.log_create(
                    entity_type='payment',
                    entity_id=payment.id,
                    actor_user_id=user_id,
                    after=after,
                    conn=conn
                )
                
                return payment
        
        finally:
            await pool.release(conn)
    
    async def delete_payment(
        self,
        payment_id: int,
        user_id: int
    ) -> Payment:
        """
        Удаляет платёж (soft delete).
        
        Args:
            payment_id: ID платежа
            user_id: ID пользователя, удаляющего платёж
        
        Returns:
            Удалённый Payment
        
        Raises:
            ValueError: Если платёж не найден, долг закрыт
            PermissionError: Если пользователь не имеет прав
        """
        # Получаем платёж
        payment = await self.payment_repo.get_by_id(payment_id)
        if payment is None:
            raise ValueError("Платёж не найден")
        
        if payment.is_deleted():
            raise ValueError("Платёж уже удалён")
        
        # Получаем долг
        debt = await self.debt_repo.get_by_id(payment.debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Проверяем статус долга
        if debt.status == 'closed':
            raise ValueError("Нельзя удалять платежи у закрытого долга")
        
        # Проверяем доступ и права
        if not await self.debt_repo.check_access(debt.id, user_id):
            raise PermissionError("Нет доступа к этому долгу")
        
        if debt.debtor_user_id != user_id:
            raise PermissionError("Только должник может удалять платежи")
        
        # Удаляем в транзакции с аудитом
        pool = await Database.get_pool()
        conn = await pool.acquire()
        
        try:
            async with conn.transaction():
                # Сохраняем состояние до удаления
                before = {
                    'id': payment.id,
                    'debt_id': payment.debt_id,
                    'amount': str(payment.amount),
                    'payment_date': str(payment.payment_date),
                    'deleted_at': str(payment.deleted_at) if payment.deleted_at else None,
                }
                
                # Удаляем платёж
                deleted_payment = await self.payment_repo.soft_delete(
                    payment_id=payment_id,
                    conn=conn
                )
                
                if deleted_payment is None:
                    raise ValueError("Не удалось удалить платёж")
                
                # Логируем удаление
                await self.audit_service.log_delete(
                    entity_type='payment',
                    entity_id=payment_id,
                    actor_user_id=user_id,
                    before=before,
                    conn=conn
                )
                
                return deleted_payment
        
        finally:
            await pool.release(conn)
    
    async def get_payments_by_debt(
        self,
        debt_id: int,
        include_deleted: bool = False
    ) -> List[Payment]:
        """
        Получает все платежи по долгу.
        
        Args:
            debt_id: ID долга
            include_deleted: Включать ли удалённые платежи
        
        Returns:
            Список платежей
        """
        return await self.payment_repo.get_by_debt_id(
            debt_id=debt_id,
            include_deleted=include_deleted
        )
    
    async def calculate_balance(
        self,
        debt_id: int
    ) -> Decimal:
        """
        Рассчитывает остаток долга.
        
        Args:
            debt_id: ID долга
        
        Returns:
            Остаток долга (может быть отрицательным при переплате)
        
        Raises:
            ValueError: Если долг не найден
        """
        # Получаем долг
        debt = await self.debt_repo.get_by_id(debt_id)
        if debt is None:
            raise ValueError("Долг не найден")
        
        # Рассчитываем баланс
        balance = await self.payment_repo.calculate_balance(
            debt_id=debt_id,
            principal_amount=debt.principal_amount
        )
        
        return balance

