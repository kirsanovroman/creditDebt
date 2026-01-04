"""
Сервис для расчёта плана погашения долга.
"""
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from calendar import monthrange
from models.debt import Debt
from services.payment_service import PaymentService


class PaymentPlanItem:
    """Элемент плана погашения."""
    
    def __init__(self, payment_date: date, amount: Decimal, is_final: bool = False):
        self.payment_date = payment_date
        self.amount = amount
        self.is_final = is_final  # True для "добивающего" платежа


class PlannerService:
    """Сервис для расчёта плана погашения."""
    
    def __init__(self):
        self.payment_service = PaymentService()
    
    def _get_due_date_in_month(self, year: int, month: int, due_day: int) -> date:
        """
        Получает дату платежа в указанном месяце.
        Если due_day отсутствует в месяце (29-31), использует последний день месяца.
        
        Args:
            year: Год
            month: Месяц (1-12)
            due_day: День платежа (1-31)
        
        Returns:
            Дата платежа
        """
        _, last_day = monthrange(year, month)
        actual_day = min(due_day, last_day)
        return date(year, month, actual_day)
    
    def _get_next_due_date(self, current_date: date, due_day: int) -> date:
        """
        Определяет следующую дату платежа.
        Если today <= due_date текущего месяца → текущий месяц,
        иначе → следующий месяц.
        
        Args:
            current_date: Текущая дата
            due_day: День платежа (1-31)
        
        Returns:
            Следующая дата платежа
        """
        due_date_current_month = self._get_due_date_in_month(
            current_date.year,
            current_date.month,
            due_day
        )
        
        if current_date <= due_date_current_month:
            return due_date_current_month
        
        # Следующий месяц
        if current_date.month == 12:
            next_year = current_date.year + 1
            next_month = 1
        else:
            next_year = current_date.year
            next_month = current_date.month + 1
        
        return self._get_due_date_in_month(next_year, next_month, due_day)
    
    async def calculate_payment_plan(
        self,
        debt: Debt,
        current_balance: Optional[Decimal] = None
    ) -> List[PaymentPlanItem]:
        """
        Рассчитывает план погашения долга.
        
        Args:
            debt: Долг
            current_balance: Текущий баланс (опционально, будет рассчитан, если не указан)
        
        Returns:
            Список элементов плана погашения
        """
        # Если нет monthly_payment или due_day, план пустой
        if debt.monthly_payment is None or debt.due_day is None:
            return []
        
        # Рассчитываем баланс, если не указан
        if current_balance is None:
            current_balance = await self.payment_service.calculate_balance(debt.id)
        
        # Если баланс <= 0, план пустой
        if current_balance <= 0:
            return []
        
        # Если долг закрыт, план пустой
        if debt.status == 'closed':
            return []
        
        plan = []
        today = date.today()
        current_date = today
        remaining_balance = current_balance
        monthly_payment = debt.monthly_payment
        due_day = debt.due_day
        max_payments = 100  # Достаточно большой лимит для генерации плана
        
        # Генерируем план погашения
        for _ in range(max_payments):
            if remaining_balance <= 0:
                break
            
            # Определяем дату платежа
            if len(plan) == 0:
                # Первая дата - следующая дата платежа
                payment_date = self._get_next_due_date(current_date, due_day)
            else:
                # Следующие даты - следующий месяц
                prev_date = plan[-1].payment_date
                if prev_date.month == 12:
                    next_year = prev_date.year + 1
                    next_month = 1
                else:
                    next_year = prev_date.year
                    next_month = prev_date.month + 1
                
                payment_date = self._get_due_date_in_month(next_year, next_month, due_day)
            
            # Определяем сумму платежа
            if remaining_balance <= monthly_payment:
                # "Добивающий" платёж
                amount = remaining_balance
                plan.append(PaymentPlanItem(payment_date, amount, is_final=True))
                break
            else:
                amount = monthly_payment
                plan.append(PaymentPlanItem(payment_date, amount, is_final=False))
            
            remaining_balance -= amount
        
        return plan
    
    async def get_payment_plan_for_debt(self, debt_id: int) -> List[PaymentPlanItem]:
        """
        Получает план погашения для долга.
        
        Args:
            debt_id: ID долга
        
        Returns:
            Список элементов плана погашения
        
        Raises:
            ValueError: Если долг не найден
        """
        from repositories.debt_repository import DebtRepository
        
        debt_repo = DebtRepository()
        debt = await debt_repo.get_by_id(debt_id)
        
        if debt is None:
            raise ValueError("Долг не найден")
        
        return await self.calculate_payment_plan(debt)

