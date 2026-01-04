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
    
    text = f"{status_emoji} <b>{debt.name}</b>\n"
    text += f"ID: {debt.id} | Статус: {status_text}\n"
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


async def format_payment_plan(
    plan_items: list[PaymentPlanItem],
    max_length: Optional[int] = None
) -> str:
    """
    Форматирует план погашения для отображения.
    
    Если max_length задан и план не влезает, показывает первые 5 платежей,
    пропускает средние и показывает последний.
    
    Args:
        plan_items: Список элементов плана
        max_length: Максимальная длина текста (опционально)
    
    Returns:
        Отформатированная строка
    """
    if not plan_items:
        return "План погашения не задан или долг погашен."
    
    header = "<b>План погашения:</b>\n\n"
    
    # Константы для форматирования с пропуском
    SHOW_FIRST = 5  # Показывать первые N платежей
    SHOW_LAST = 1   # Показывать последний N платежей
    
    def format_item(item: PaymentPlanItem, index: int) -> str:
        """Форматирует один элемент плана."""
        final_mark = " (финальный)" if item.is_final else ""
        return f"{index}. {item.payment_date.strftime('%d.%m.%Y')} — {item.amount:,.2f}{final_mark}\n"
    
    # Форматируем все платежи
    all_lines = []
    for i, item in enumerate(plan_items, 1):
        all_lines.append(format_item(item, i))
    
    full_text = header + "".join(all_lines)
    
    # Если лимит не задан или текст влезает - возвращаем всё
    if max_length is None or len(full_text) <= max_length:
        return full_text
    
    # Если платежей мало - показываем все, даже если немного не влезает
    if len(plan_items) <= SHOW_FIRST + SHOW_LAST:
        return full_text
    
    # Форматируем начало (первые SHOW_FIRST платежей)
    start_lines = []
    for i in range(SHOW_FIRST):
        start_lines.append(format_item(plan_items[i], i + 1))
    
    # Форматируем конец (последние SHOW_LAST платежей)
    skipped_count = len(plan_items) - SHOW_FIRST - SHOW_LAST
    end_lines = []
    for i in range(SHOW_LAST):
        idx = len(plan_items) - SHOW_LAST + i
        end_lines.append(format_item(plan_items[idx], idx + 1))
    
    # Собираем результат с пропуском
    result = header + "".join(start_lines)
    result += f"... (пропущено {skipped_count} платежей) ...\n"
    result += "".join(end_lines)
    
    # Если даже сокращённый вариант не влезает - показываем только начало
    if len(result) > max_length:
        # Показываем только первые платежи, сколько влезет
        result_lines = [header]
        current_length = len(header)
        
        for i in range(len(plan_items)):
            line = format_item(plan_items[i], i + 1)
            if current_length + len(line) > max_length:
                break
            result_lines.append(line)
            current_length += len(line)
        
        result = "".join(result_lines)
    
    return result


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
    
    text = f"{index}. <b>{debt.name}</b> ({role})\n"
    text += f"   ID: {debt.id} | {status} | {debt.principal_amount:,.2f} {debt.currency}\n"
    
    return text

