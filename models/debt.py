"""
Модель долга.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal


@dataclass
class Debt:
    """Модель долга."""
    id: int
    debtor_user_id: int
    creditor_user_id: Optional[int]
    name: str  # Название долга
    principal_amount: Decimal
    currency: str
    monthly_payment: Optional[Decimal]
    due_day: Optional[int]
    status: str  # 'active' или 'closed'
    closed_at: Optional[datetime]
    close_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row) -> "Debt":
        """Создаёт экземпляр Debt из строки БД."""
        return cls(
            id=row['id'],
            debtor_user_id=row['debtor_user_id'],
            creditor_user_id=row['creditor_user_id'],
            name=row.get('name', f"Долг #{row['id']}"),  # Для обратной совместимости
            principal_amount=row['principal_amount'],
            currency=row['currency'],
            monthly_payment=row['monthly_payment'],
            due_day=row['due_day'],
            status=row['status'],
            closed_at=row['closed_at'],
            close_note=row['close_note'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

