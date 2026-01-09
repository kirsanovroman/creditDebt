"""
Unit-тесты для PlannerService.
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from services.planner_service import PlannerService, PaymentPlanItem
from models.debt import Debt
from datetime import datetime, timezone


@pytest.fixture
def planner_service():
    """Фикстура для создания PlannerService с моком PaymentService."""
    service = PlannerService()
    service.payment_service = MagicMock()
    service.payment_service.calculate_balance = AsyncMock(return_value=Decimal('10000'))
    return service


@pytest.mark.asyncio
async def test_calculate_plan_empty_when_no_monthly_payment(planner_service):
    """Тест: план пустой, если нет monthly_payment."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('10000'), currency='RUB',
        monthly_payment=None, due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('10000'))
    assert plan == []


@pytest.mark.asyncio
async def test_calculate_plan_empty_when_no_due_day(planner_service):
    """Тест: план пустой, если нет due_day."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('10000'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=None, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('10000'))
    assert plan == []


@pytest.mark.asyncio
async def test_calculate_plan_empty_when_closed(planner_service):
    """Тест: план пустой для закрытого долга."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('10000'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='closed',
        closed_at=datetime.now(timezone.utc), close_note='Закрыт',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('10000'))
    assert plan == []


@pytest.mark.asyncio
async def test_calculate_plan_empty_when_balance_zero(planner_service):
    """Тест: план пустой, если баланс <= 0."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('10000'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('0'))
    assert plan == []


@pytest.mark.asyncio
async def test_calculate_plan_max_payments(planner_service):
    """Тест: план генерируется с ограничением на максимальное количество платежей."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('100000'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('100000'))
    # План должен содержать платежи (максимум 100 из-за ограничения в коде)
    assert len(plan) > 0
    assert len(plan) <= 100  # Проверяем, что не превышает лимит генерации
    assert all(isinstance(item, PaymentPlanItem) for item in plan)
    assert all(item.amount == Decimal('1000') for item in plan)


@pytest.mark.asyncio
async def test_calculate_plan_final_payment(planner_service):
    """Тест: последний платёж является 'добивающим' (остаток <= monthly_payment)."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('2500'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('2500'))
    assert len(plan) == 3
    assert plan[0].amount == Decimal('1000')
    assert plan[0].is_final is False
    assert plan[1].amount == Decimal('1000')
    assert plan[1].is_final is False
    assert plan[2].amount == Decimal('500')
    assert plan[2].is_final is True  # "Добивающий" платёж


@pytest.mark.asyncio
async def test_calculate_plan_exact_multiple(planner_service):
    """Тест: план для суммы, кратной monthly_payment."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('3000'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('3000'))
    assert len(plan) == 3
    assert all(item.amount == Decimal('1000') for item in plan)
    assert plan[2].is_final is True  # Последний платёж


def test_get_due_date_in_month_february_normal_year(planner_service):
    """Тест: due_day=31 в феврале обычного года (28 дней)."""
    result = planner_service._get_due_date_in_month(2023, 2, 31)
    assert result == date(2023, 2, 28)


def test_get_due_date_in_month_february_leap_year(planner_service):
    """Тест: due_day=31 в феврале високосного года (29 дней)."""
    result = planner_service._get_due_date_in_month(2024, 2, 31)
    assert result == date(2024, 2, 29)


def test_get_due_date_in_month_30_day_month(planner_service):
    """Тест: due_day=31 в месяце с 30 днями (апрель, июнь, сентябрь, ноябрь)."""
    result_april = planner_service._get_due_date_in_month(2024, 4, 31)
    assert result_april == date(2024, 4, 30)
    
    result_june = planner_service._get_due_date_in_month(2024, 6, 31)
    assert result_june == date(2024, 6, 30)
    
    result_september = planner_service._get_due_date_in_month(2024, 9, 31)
    assert result_september == date(2024, 9, 30)
    
    result_november = planner_service._get_due_date_in_month(2024, 11, 31)
    assert result_november == date(2024, 11, 30)


def test_get_due_date_in_month_29_in_february_normal(planner_service):
    """Тест: due_day=29 в феврале обычного года."""
    result = planner_service._get_due_date_in_month(2023, 2, 29)
    assert result == date(2023, 2, 28)


def test_get_due_date_in_month_29_in_february_leap(planner_service):
    """Тест: due_day=29 в феврале високосного года."""
    result = planner_service._get_due_date_in_month(2024, 2, 29)
    assert result == date(2024, 2, 29)


def test_get_due_date_in_month_30_in_february(planner_service):
    """Тест: due_day=30 в феврале (обычный и високосный)."""
    result_normal = planner_service._get_due_date_in_month(2023, 2, 30)
    assert result_normal == date(2023, 2, 28)
    
    result_leap = planner_service._get_due_date_in_month(2024, 2, 30)
    assert result_leap == date(2024, 2, 29)


def test_get_next_due_date_today_equals_due_date(planner_service):
    """Тест: today == due_date -> возвращает текущий месяц."""
    current_date = date(2024, 3, 15)
    result = planner_service._get_next_due_date(current_date, 15)
    assert result == date(2024, 3, 15)


def test_get_next_due_date_today_before_due_date(planner_service):
    """Тест: today < due_date -> возвращает текущий месяц."""
    current_date = date(2024, 3, 10)
    result = planner_service._get_next_due_date(current_date, 15)
    assert result == date(2024, 3, 15)


def test_get_next_due_date_today_after_due_date(planner_service):
    """Тест: today > due_date -> возвращает следующий месяц."""
    current_date = date(2024, 3, 20)
    result = planner_service._get_next_due_date(current_date, 15)
    assert result == date(2024, 4, 15)


def test_get_next_due_date_december_wrap(planner_service):
    """Тест: переход через декабрь в январь следующего года."""
    current_date = date(2024, 12, 20)
    result = planner_service._get_next_due_date(current_date, 15)
    assert result == date(2025, 1, 15)


def test_get_next_due_date_31_in_february_next_month(planner_service):
    """Тест: due_day=31, следующий месяц - февраль (28/29 дней)."""
    current_date = date(2024, 1, 31)
    result = planner_service._get_next_due_date(current_date, 31)
    assert result == date(2024, 2, 29)  # 2024 - високосный год


def test_get_next_due_date_31_in_january(planner_service):
    """Тест: due_day=31 в январе возвращает 31 января."""
    current_date = date(2024, 1, 10)
    result = planner_service._get_next_due_date(current_date, 31)
    assert result == date(2024, 1, 31)


@pytest.mark.asyncio
async def test_calculate_plan_single_payment(planner_service):
    """Тест: план с одним платежом (остаток меньше monthly_payment)."""
    debt = Debt(
        id=1, debtor_user_id=1, creditor_user_id=None,
        principal_amount=Decimal('500'), currency='RUB',
        monthly_payment=Decimal('1000'), due_day=15, status='active',
        closed_at=None, close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    plan = await planner_service.calculate_payment_plan(debt, Decimal('500'))
    assert len(plan) == 1
    assert plan[0].amount == Decimal('500')
    assert plan[0].is_final is True

