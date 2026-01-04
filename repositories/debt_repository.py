"""
Репозиторий для работы с долгами.
"""
from typing import Optional, List
from datetime import datetime
from datetime import timezone
from decimal import Decimal
import asyncpg
from models.debt import Debt
from repositories.base import BaseRepository
from database import Database


class DebtRepository(BaseRepository):
    """Репозиторий для работы с долгами."""
    
    async def create(
        self,
        debtor_user_id: int,
        creditor_user_id: Optional[int],
        name: str,
        principal_amount: Decimal,
        currency: str,
        monthly_payment: Optional[Decimal],
        due_day: Optional[int],
        conn: Optional[asyncpg.Connection] = None
    ) -> Debt:
        """
        Создаёт новый долг.
        
        Args:
            debtor_user_id: ID должника
            creditor_user_id: ID кредитора (опционально)
            name: Название долга
            principal_amount: Основная сумма долга
            currency: Валюта
            monthly_payment: Ежемесячный платёж (опционально)
            due_day: День месяца для платежа (опционально)
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Debt: Созданный долг
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO debts (
                    debtor_user_id, creditor_user_id, name, principal_amount, currency,
                    monthly_payment, due_day, status, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', $8, $8)
                RETURNING id, debtor_user_id, creditor_user_id, name, principal_amount,
                          currency, monthly_payment, due_day, status, closed_at,
                          close_note, created_at, updated_at
                """,
                debtor_user_id,
                creditor_user_id,
                name,
                principal_amount,
                currency,
                monthly_payment,
                due_day,
                datetime.now(timezone.utc)
            )
            
            return Debt.from_row(row)
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_id(
        self,
        debt_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Debt]:
        """
        Получает долг по ID.
        
        Args:
            debt_id: ID долга
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Debt или None, если долг не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                SELECT id, debtor_user_id, creditor_user_id, name, principal_amount,
                       currency, monthly_payment, due_day, status, closed_at,
                       close_note, created_at, updated_at
                FROM debts
                WHERE id = $1
                """,
                debt_id
            )
            
            if row:
                return Debt.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_debtor(
        self,
        debtor_user_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> List[Debt]:
        """
        Получает все долги должника.
        
        Args:
            debtor_user_id: ID должника
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Список долгов
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            rows = await conn.fetch(
                """
                SELECT id, debtor_user_id, creditor_user_id, name, principal_amount,
                       currency, monthly_payment, due_day, status, closed_at,
                       close_note, created_at, updated_at
                FROM debts
                WHERE debtor_user_id = $1
                ORDER BY created_at DESC
                """,
                debtor_user_id
            )
            
            return [Debt.from_row(row) for row in rows]
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_creditor(
        self,
        creditor_user_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> List[Debt]:
        """
        Получает все долги кредитора.
        
        Args:
            creditor_user_id: ID кредитора
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Список долгов
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            rows = await conn.fetch(
                """
                SELECT id, debtor_user_id, creditor_user_id, name, principal_amount,
                       currency, monthly_payment, due_day, status, closed_at,
                       close_note, created_at, updated_at
                FROM debts
                WHERE creditor_user_id = $1
                ORDER BY created_at DESC
                """,
                creditor_user_id
            )
            
            return [Debt.from_row(row) for row in rows]
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def update(
        self,
        debt_id: int,
        creditor_user_id: Optional[int] = None,
        monthly_payment: Optional[Decimal] = None,
        due_day: Optional[int] = None,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Debt]:
        """
        Обновляет долг.
        
        Args:
            debt_id: ID долга
            creditor_user_id: ID кредитора (опционально)
            monthly_payment: Ежемесячный платёж (опционально)
            due_day: День месяца для платежа (опционально)
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Обновлённый Debt или None, если долг не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            # Формируем SET часть запроса динамически
            updates = []
            values = []
            param_num = 1
            
            if creditor_user_id is not None:
                updates.append(f"creditor_user_id = ${param_num}")
                values.append(creditor_user_id)
                param_num += 1
            
            if monthly_payment is not None:
                updates.append(f"monthly_payment = ${param_num}")
                values.append(monthly_payment)
                param_num += 1
            
            if due_day is not None:
                updates.append(f"due_day = ${param_num}")
                values.append(due_day)
                param_num += 1
            
            if not updates:
                # Нет изменений
                return await self.get_by_id(debt_id, conn)
            
            values.append(debt_id)
            
            query = f"""
                UPDATE debts
                SET {', '.join(updates)}, updated_at = NOW()
                WHERE id = ${param_num}
                RETURNING id, debtor_user_id, creditor_user_id, name, principal_amount,
                          currency, monthly_payment, due_day, status, closed_at,
                          close_note, created_at, updated_at
            """
            
            row = await conn.fetchrow(query, *values)
            
            if row:
                return Debt.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def check_access(
        self,
        debt_id: int,
        user_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> bool:
        """
        Проверяет, есть ли у пользователя доступ к долгу.
        
        Args:
            debt_id: ID долга
            user_id: ID пользователя
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            True, если пользователь является должником или кредитором
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                SELECT 1
                FROM debts
                WHERE id = $1
                  AND (debtor_user_id = $2 OR creditor_user_id = $2)
                """,
                debt_id,
                user_id
            )
            
            return row is not None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def close_debt(
        self,
        debt_id: int,
        close_note: Optional[str] = None,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Debt]:
        """
        Закрывает долг (устанавливает status='closed' и closed_at).
        
        Args:
            debt_id: ID долга
            close_note: Примечание при закрытии (опционально)
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Обновлённый Debt или None, если долг не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                UPDATE debts
                SET status = 'closed', closed_at = $1, close_note = $2, updated_at = $1
                WHERE id = $3 AND status = 'active'
                RETURNING id, debtor_user_id, creditor_user_id, name, principal_amount,
                          currency, monthly_payment, due_day, status, closed_at,
                          close_note, created_at, updated_at
                """,
                datetime.now(timezone.utc),
                close_note,
                debt_id
            )
            
            if row:
                return Debt.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)

