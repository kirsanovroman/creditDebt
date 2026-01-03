"""
Модель приглашения.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Invite:
    """Модель приглашения."""
    id: int
    debt_id: int
    token: UUID
    expires_at: datetime
    used_at: Optional[datetime]
    created_at: datetime
    
    @classmethod
    def from_row(cls, row) -> "Invite":
        """Создаёт экземпляр Invite из строки БД."""
        return cls(
            id=row['id'],
            debt_id=row['debt_id'],
            token=UUID(str(row['token'])),
            expires_at=row['expires_at'],
            used_at=row['used_at'],
            created_at=row['created_at']
        )
    
    def is_expired(self) -> bool:
        """Проверяет, истёк ли срок действия токена."""
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_used(self) -> bool:
        """Проверяет, использован ли токен."""
        return self.used_at is not None
    
    def is_valid(self) -> bool:
        """Проверяет, валиден ли токен (не использован и не истёк)."""
        return not self.is_used() and not self.is_expired()

