"""
Репозиторий для работы с платежами.
"""
from typing import Optional, List
from datetime import datetime, date
from datetime import timezone
from decimal import Decimal
import asyncpg
from models.payment import Payment
from repositories.base import BaseRepository
from database import Database


class PaymentRepository(BaseRepository):
    """Репозиторий для работы с платежами."""
    
    async def create(
        self,
        debt_id: int,
        amount: Decimal,
        payment_date: date,
        conn: Optional[asyncpg.Connection] = None
    ) -> Payment:
        """
        Создаёт новый платёж.
        
        Args:
            debt_id: ID долга
            amount: Сумма платежа
            payment_date: Дата платежа
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Payment: Созданный платёж
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO payments (debt_id, amount, payment_date, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $4)
                RETURNING id, debt_id, amount, payment_date, deleted_at, created_at, updated_at
                """,
                debt_id,
                amount,
                payment_date,
                datetime.now(timezone.utc)
            )
            
            return Payment.from_row(row)
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_id(
        self,
        payment_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Payment]:
        """
        Получает платёж по ID.
        
        Args:
            payment_id: ID платежа
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Payment или None, если платёж не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                SELECT id, debt_id, amount, payment_date, deleted_at, created_at, updated_at
                FROM payments
                WHERE id = $1
                """,
                payment_id
            )
            
            if row:
                return Payment.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def get_by_debt_id(
        self,
        debt_id: int,
        include_deleted: bool = False,
        conn: Optional[asyncpg.Connection] = None
    ) -> List[Payment]:
        """
        Получает все платежи по долгу.
        
        Args:
            debt_id: ID долга
            include_deleted: Включать ли удалённые платежи
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Список платежей, отсортированных по дате (DESC)
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            if include_deleted:
                query = """
                    SELECT id, debt_id, amount, payment_date, deleted_at, created_at, updated_at
                    FROM payments
                    WHERE debt_id = $1
                    ORDER BY payment_date DESC, created_at DESC
                """
                rows = await conn.fetch(query, debt_id)
            else:
                query = """
                    SELECT id, debt_id, amount, payment_date, deleted_at, created_at, updated_at
                    FROM payments
                    WHERE debt_id = $1 AND deleted_at IS NULL
                    ORDER BY payment_date DESC, created_at DESC
                """
                rows = await conn.fetch(query, debt_id)
            
            return [Payment.from_row(row) for row in rows]
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def soft_delete(
        self,
        payment_id: int,
        conn: Optional[asyncpg.Connection] = None
    ) -> Optional[Payment]:
        """
        Мягко удаляет платёж (устанавливает deleted_at).
        
        Args:
            payment_id: ID платежа
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Обновлённый Payment или None, если платёж не найден
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            row = await conn.fetchrow(
                """
                UPDATE payments
                SET deleted_at = $1, updated_at = $1
                WHERE id = $2 AND deleted_at IS NULL
                RETURNING id, debt_id, amount, payment_date, deleted_at, created_at, updated_at
                """,
                datetime.now(timezone.utc),
                payment_id
            )
            
            if row:
                return Payment.from_row(row)
            return None
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)
    
    async def calculate_balance(
        self,
        debt_id: int,
        principal_amount: Decimal,
        conn: Optional[asyncpg.Connection] = None
    ) -> Decimal:
        """
        Рассчитывает остаток долга (principal_amount - сумма активных платежей).
        
        Args:
            debt_id: ID долга
            principal_amount: Основная сумма долга
            conn: Подключение к БД (опционально, для транзакций)
        
        Returns:
            Остаток долга (может быть отрицательным при переплате)
        """
        own_connection = conn is None
        if own_connection:
            pool = await Database.get_pool()
            conn = await pool.acquire()
        
        try:
            total_payments = await conn.fetchval(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE debt_id = $1 AND deleted_at IS NULL
                """,
                debt_id
            )
            
            if total_payments is None:
                total_payments = Decimal('0')
            else:
                total_payments = Decimal(str(total_payments))
            
            balance = principal_amount - total_payments
            return balance
        
        finally:
            if own_connection:
                pool = await Database.get_pool()
                await pool.release(conn)

