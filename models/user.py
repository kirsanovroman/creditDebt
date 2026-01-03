"""
Модель пользователя.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя."""
    id: int
    tg_user_id: int
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> "User":
        """Создаёт экземпляр User из строки БД."""
        return cls(
            id=row['id'],
            tg_user_id=row['tg_user_id'],
            created_at=row['created_at']
        )

