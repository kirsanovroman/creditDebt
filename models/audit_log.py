"""
Модель записи аудита.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json


@dataclass
class AuditLog:
    """Модель записи аудита."""
    id: int
    entity_type: str  # 'debt', 'payment', 'invite'
    entity_id: int
    action: str  # 'create', 'update', 'delete', 'close'
    actor_user_id: int
    occurred_at: datetime
    before: Optional[dict]
    after: Optional[dict]
    
    @classmethod
    def from_row(cls, row) -> "AuditLog":
        """Создаёт экземпляр AuditLog из строки БД."""
        before = row['before']
        after = row['after']
        
        # JSONB может быть dict или str, приводим к dict
        if isinstance(before, str):
            before = json.loads(before) if before else None
        if isinstance(after, str):
            after = json.loads(after) if after else None
        
        return cls(
            id=row['id'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            action=row['action'],
            actor_user_id=row['actor_user_id'],
            occurred_at=row['occurred_at'],
            before=before,
            after=after
        )

