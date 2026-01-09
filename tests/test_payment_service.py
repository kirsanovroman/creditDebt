# -*- coding: utf-8 -*-
"""
Tests for PaymentService.
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from services.payment_service import PaymentService
from models.debt import Debt
from models.payment import Payment


@pytest.fixture
def payment_service():
    """Create PaymentService instance."""
    return PaymentService()


@pytest.fixture
def sample_debt():
    """Create sample debt for testing."""
    from datetime import datetime, timezone
    return Debt(
        id=1,
        debtor_user_id=100,
        creditor_user_id=200,
        name="Test Debt",
        principal_amount=Decimal("10000.00"),
        currency="RUB",
        monthly_payment=Decimal("1000.00"),
        due_day=15,
        status="active",
        closed_at=None,
        close_note=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def sample_payment():
    """Create sample payment for testing."""
    from datetime import datetime, timezone
    return Payment(
        id=1,
        debt_id=1,
        amount=Decimal("1000.00"),
        payment_date=date(2024, 1, 15),
        deleted_at=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


class TestAddPayment:
    """Tests for add_payment method."""
    
    @pytest.mark.asyncio
    async def test_add_payment_success(self, payment_service, sample_debt, sample_payment):
        """Test successful payment addition."""
        # Mock dependencies
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        payment_service.payment_repo.create = AsyncMock(return_value=sample_payment)
        payment_service.audit_service.log_create = AsyncMock()
        
        # Mock database pool
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_pool.release = AsyncMock()
        mock_conn.transaction = MagicMock()
        mock_conn.transaction.__aenter__ = AsyncMock()
        mock_conn.transaction.__aexit__ = AsyncMock(return_value=None)
        
        with patch('services.payment_service.Database.get_pool', return_value=mock_pool):
            result = await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("1000.00"),
                payment_date=date(2024, 1, 15),
                user_id=100  # debtor_user_id
            )
        
        assert result == sample_payment
        payment_service.debt_repo.check_access.assert_called_once_with(1, 100)
        payment_service.debt_repo.get_by_id.assert_called_once_with(1)
        payment_service.payment_repo.create.assert_called_once()
        payment_service.audit_service.log_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_payment_no_access(self, payment_service):
        """Test payment addition when user has no access."""
        payment_service.debt_repo.check_access = AsyncMock(return_value=False)
        
        with pytest.raises(PermissionError, match="Нет доступа к этому долгу"):
            await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("1000.00"),
                payment_date=date(2024, 1, 15),
                user_id=999
            )
    
    @pytest.mark.asyncio
    async def test_add_payment_debt_not_found(self, payment_service):
        """Test payment addition when debt doesn't exist."""
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Долг не найден"):
            await payment_service.add_payment(
                debt_id=999,
                amount=Decimal("1000.00"),
                payment_date=date(2024, 1, 15),
                user_id=100
            )
    
    @pytest.mark.asyncio
    async def test_add_payment_closed_debt(self, payment_service, sample_debt):
        """Test payment addition to closed debt."""
        closed_debt = Debt(
            **{**sample_debt.__dict__, 'status': 'closed'}
        )
        
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=closed_debt)
        
        with pytest.raises(ValueError, match="Нельзя добавлять платежи к закрытому долгу"):
            await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("1000.00"),
                payment_date=date(2024, 1, 15),
                user_id=100
            )
    
    @pytest.mark.asyncio
    async def test_add_payment_not_debtor(self, payment_service, sample_debt):
        """Test payment addition when user is not debtor (e.g., creditor)."""
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        
        with pytest.raises(PermissionError, match="Только должник может добавлять платежи"):
            await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("1000.00"),
                payment_date=date(2024, 1, 15),
                user_id=200  # creditor_user_id, not debtor
            )
    
    @pytest.mark.asyncio
    async def test_add_payment_invalid_amount_zero(self, payment_service, sample_debt):
        """Test payment addition with zero amount."""
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        
        with pytest.raises(ValueError, match="Сумма платежа должна быть больше нуля"):
            await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("0.00"),
                payment_date=date(2024, 1, 15),
                user_id=100
            )
    
    @pytest.mark.asyncio
    async def test_add_payment_invalid_amount_negative(self, payment_service, sample_debt):
        """Test payment addition with negative amount."""
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        
        with pytest.raises(ValueError, match="Сумма платежа должна быть больше нуля"):
            await payment_service.add_payment(
                debt_id=1,
                amount=Decimal("-100.00"),
                payment_date=date(2024, 1, 15),
                user_id=100
            )


class TestDeletePayment:
    """Tests for delete_payment method."""
    
    @pytest.mark.asyncio
    async def test_delete_payment_success(self, payment_service, sample_debt, sample_payment):
        """Test successful payment deletion."""
        payment_service.payment_repo.get_by_id = AsyncMock(return_value=sample_payment)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        
        deleted_payment = Payment(
            **{**sample_payment.__dict__, 'deleted_at': date.today()}
        )
        payment_service.payment_repo.soft_delete = AsyncMock(return_value=deleted_payment)
        payment_service.audit_service.log_delete = AsyncMock()
        
        # Mock database pool
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire = AsyncMock(return_value=mock_conn)
        mock_pool.release = AsyncMock()
        mock_conn.transaction = MagicMock()
        mock_conn.transaction.__aenter__ = AsyncMock()
        mock_conn.transaction.__aexit__ = AsyncMock(return_value=None)
        
        with patch('services.payment_service.Database.get_pool', return_value=mock_pool):
            result = await payment_service.delete_payment(
                payment_id=1,
                user_id=100  # debtor_user_id
            )
        
        assert result == deleted_payment
        payment_service.payment_repo.soft_delete.assert_called_once()
        payment_service.audit_service.log_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_payment_not_found(self, payment_service):
        """Test payment deletion when payment doesn't exist."""
        payment_service.payment_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Платёж не найден"):
            await payment_service.delete_payment(
                payment_id=999,
                user_id=100
            )
    
    @pytest.mark.asyncio
    async def test_delete_payment_not_debtor(self, payment_service, sample_debt, sample_payment):
        """Test payment deletion when user is not debtor."""
        payment_service.payment_repo.get_by_id = AsyncMock(return_value=sample_payment)
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        payment_service.debt_repo.check_access = AsyncMock(return_value=True)
        
        with pytest.raises(PermissionError, match="Только должник может удалять платежи"):
            await payment_service.delete_payment(
                payment_id=1,
                user_id=200  # creditor_user_id, not debtor
            )


class TestCalculateBalance:
    """Tests for calculate_balance method."""
    
    @pytest.mark.asyncio
    async def test_calculate_balance_success(self, payment_service, sample_debt):
        """Test successful balance calculation."""
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=sample_debt)
        payment_service.payment_repo.calculate_balance = AsyncMock(return_value=Decimal("5000.00"))
        
        result = await payment_service.calculate_balance(debt_id=1)
        
        assert result == Decimal("5000.00")
        payment_service.debt_repo.get_by_id.assert_called_once_with(1)
        payment_service.payment_repo.calculate_balance.assert_called_once_with(
            debt_id=1,
            principal_amount=sample_debt.principal_amount
        )
    
    @pytest.mark.asyncio
    async def test_calculate_balance_debt_not_found(self, payment_service):
        """Test balance calculation when debt doesn't exist."""
        payment_service.debt_repo.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="Долг не найден"):
            await payment_service.calculate_balance(debt_id=999)
