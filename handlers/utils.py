"""
Вспомогательные функции для handlers.
"""
from decimal import Decimal
from datetime import date
from typing import Optional
from models.debt import Debt
from services.payment_service import PaymentService
from services.planner_service import PaymentPlanItem


async def format_debt_info(debt: Debt, balance: Optional[Decimal] = None) -> str:
    """
    Форматирует информацию о долге для отображения.
    
    Args:
        debt: Долг
        balance: Текущий баланс (опционально)
    
    Returns:
        Отформатированная строка
    """
    status_emoji = "🔒" if debt.status == 'closed' else "🟢"
    status_text = "Закрыт" if debt.status == 'closed' else "Активен"
    
    text = f"{status_emoji} <b>Долг #{debt.id}</b>\n"
    text += f"Статус: {status_text}\n"
    text += f"Сумма долга: {debt.principal_amount:,.2f} {debt.currency}\n"
    
    if balance is not None:
        if balance < 0:
            text += f"Переплата: {abs(balance):,.2f} {debt.currency}\n"
        else:
            text += f"Остаток: {balance:,.2f} {debt.currency}\n"
    
    if debt.monthly_payment:
        text += f"Ежемесячный платёж: {debt.monthly_payment:,.2f} {debt.currency}\n"
    
    if debt.due_day:
        text += f"День платежа: {debt.due_day}\n"
    
    if debt.close_note:
        text += f"\nПримечание: {debt.close_note}\n"
    
    return text


async def format_payment_plan(plan_items: list[PaymentPlanItem]) -> str:
    """
    Форматирует план погашения для отображения.
    
    Args:
        plan_items: Список элементов плана
    
    Returns:
        Отформатированная строка
    """
    if not plan_items:
        return "План погашения не задан или долг погашен."
    
    text = "<b>План погашения:</b>\n\n"
    for i, item in enumerate(plan_items, 1):
        final_mark = " (финальный)" if item.is_final else ""
        text += f"{i}. {item.payment_date.strftime('%d.%m.%Y')} — {item.amount:,.2f}{final_mark}\n"
    
    return text


def parse_decimal(text: str) -> Optional[Decimal]:
    """
    Парсит строку в Decimal.
    
    Args:
        text: Строка для парсинга
    
    Returns:
        Decimal или None, если не удалось распарсить
    """
    try:
        # Заменяем запятую на точку
        text = text.replace(',', '.')
        return Decimal(text)
    except (ValueError, Exception):
        return None


def parse_date(text: str) -> Optional[date]:
    """
    Парсит строку в date (форматы: DD.MM.YYYY, YYYY-MM-DD).
    
    Args:
        text: Строка для парсинга
    
    Returns:
        date или None, если не удалось распарсить
    """
    try:
        # Пробуем DD.MM.YYYY
        if '.' in text:
            parts = text.split('.')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                return date(year, month, day)
        
        # Пробуем YYYY-MM-DD
        if '-' in text:
            return date.fromisoformat(text)
        
        return None
    except (ValueError, Exception):
        return None


def format_debt_list_item(debt: Debt, index: int, is_debtor: bool) -> str:
    """
    Форматирует элемент списка долгов.
    
    Args:
        debt: Долг
        index: Индекс в списке
        is_debtor: True, если пользователь является должником
    
    Returns:
        Отформатированная строка
    """
    role = "Должник" if is_debtor else "Кредитор"
    status = "🔒 Закрыт" if debt.status == 'closed' else "🟢 Активен"
    
    text = f"{index}. <b>Долг #{debt.id}</b> ({role})\n"
    text += f"   {status} | {debt.principal_amount:,.2f} {debt.currency}\n"
    
    return text

