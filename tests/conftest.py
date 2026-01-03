"""
Конфигурация pytest и общие фикстуры.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timezone
from models.debt import Debt


@pytest.fixture
def sample_debt():
    """Фикстура для создания тестового долга."""
    return Debt(
        id=1,
        debtor_user_id=1,
        creditor_user_id=None,
        principal_amount=Decimal('10000'),
        currency='RUB',
        monthly_payment=Decimal('1000'),
        due_day=15,
        status='active',
        closed_at=None,
        close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def closed_debt():
    """Фикстура для создания закрытого долга."""
    return Debt(
        id=2,
        debtor_user_id=1,
        creditor_user_id=None,
        principal_amount=Decimal('5000'),
        currency='RUB',
        monthly_payment=Decimal('500'),
        due_day=20,
        status='closed',
        closed_at=datetime.now(timezone.utc),
        close_note='Тестовое закрытие',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

