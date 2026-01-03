"""
Модель платежа.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


@dataclass
class Payment:
    """Модель платежа."""
    id: int
    debt_id: int
    amount: Decimal
    payment_date: date
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row) -> "Payment":
        """Создаёт экземпляр Payment из строки БД."""
        return cls(
            id=row['id'],
            debt_id=row['debt_id'],
            amount=row['amount'],
            payment_date=row['payment_date'],
            deleted_at=row['deleted_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def is_deleted(self) -> bool:
        """Проверяет, удалён ли платёж."""
        return self.deleted_at is not None

