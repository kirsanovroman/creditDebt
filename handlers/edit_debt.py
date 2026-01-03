"""
Handler для редактирования долга.
"""
from typing import Optional
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import get_cancel_keyboard
from handlers.utils import parse_decimal
from services.debt_service import DebtService
from repositories.user_repository import UserRepository

# Константы состояний для редактирования долга
# Эти константы должны совпадать с теми, что используются в main.py
EDIT_MONTHLY_PAYMENT = 3
EDIT_DUE_DAY = 4


async def debt_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс редактирования долга."""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Извлекаем debt_id из callback_data (формат: "debt:edit:123")
    callback_data = query.data if query else ""
    try:
        debt_id = int(callback_data.split(':')[2])
    except (IndexError, ValueError):
        if query:
            await query.answer("Ошибка: неверный ID долга", show_alert=True)
        return -1
    
    user = update.effective_user
    if user is None:
        return -1
    
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    
    # Проверяем доступ и получаем долг
    if not await debt_service.check_access(debt_id, db_user.id):
        if query:
            await query.answer("Нет доступа к этому долгу", show_alert=True)
        return -1
    
    debt = await debt_service.get_debt_by_id(debt_id)
    if debt is None:
        if query:
            await query.answer("Долг не найден", show_alert=True)
        return -1
    
    # Проверяем, что долг не закрыт
    if debt.status == 'closed':
        if query:
            await query.answer("Нельзя редактировать закрытый долг", show_alert=True)
        return -1
    
    # Сохраняем debt_id в контексте
    context.user_data['debt_edit_debt_id'] = debt_id
    context.user_data['debt_edit'] = {}
    
    # Показываем текущие значения и запрашиваем новое значение monthly_payment
    current_monthly = f"{debt.monthly_payment:,.2f}" if debt.monthly_payment else "не задан"
    text = (
        "✏️ <b>Редактирование долга</b>\n\n"
        f"Текущий ежемесячный платёж: {current_monthly}\n\n"
        "Введите новый ежемесячный платёж (например: 5000 или 5000.50)\n"
        "или отправьте \"-\" чтобы оставить без изменений:"
    )
    keyboard = get_cancel_keyboard()
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
    
    return EDIT_MONTHLY_PAYMENT


async def debt_edit_monthly_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод нового ежемесячного платежа."""
    text = update.message.text if update.message else ""
    
    if text.strip() == '-':
        context.user_data['debt_edit']['monthly_payment'] = None
    else:
        monthly_payment = parse_decimal(text)
        if monthly_payment is None or monthly_payment <= 0:
            await update.message.reply_text(
                "❌ Неверный формат суммы. Введите число больше нуля или \"-\" для пропуска:",
                reply_markup=get_cancel_keyboard()
            )
            return EDIT_MONTHLY_PAYMENT
        
        context.user_data['debt_edit']['monthly_payment'] = float(monthly_payment)
    
    # Получаем долг для отображения текущего due_day
    debt_id = context.user_data.get('debt_edit_debt_id')
    if not debt_id:
        await update.message.reply_text("❌ Ошибка: потерян ID долга. Начните заново.")
        return -1
    
    user = update.effective_user
    if user is None:
        return -1
    
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    debt = await debt_service.get_debt_by_id(debt_id)
    if debt is None:
        await update.message.reply_text("❌ Долг не найден.")
        return -1
    
    current_due_day = str(debt.due_day) if debt.due_day else "не задан"
    
    await update.message.reply_text(
        f"Текущий день платежа: {current_due_day}\n\n"
        "Введите новый день платежа (1-31)\n"
        "или отправьте \"-\" чтобы оставить без изменений:",
        reply_markup=get_cancel_keyboard()
    )
    
    return EDIT_DUE_DAY


async def debt_edit_due_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод нового дня платежа и сохраняет изменения."""
    text = update.message.text if update.message else ""
    
    if text.strip() == '-':
        due_day = None
    else:
        try:
            due_day = int(text.strip())
            if due_day < 1 or due_day > 31:
                await update.message.reply_text(
                    "❌ День должен быть от 1 до 31. Введите число или \"-\" для пропуска:",
                    reply_markup=get_cancel_keyboard()
                )
                return EDIT_DUE_DAY
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат. Введите число от 1 до 31 или \"-\" для пропуска:",
                reply_markup=get_cancel_keyboard()
            )
            return EDIT_DUE_DAY
    
    debt_id = context.user_data.get('debt_edit_debt_id')
    if not debt_id:
        await update.message.reply_text("❌ Ошибка: потерян ID долга. Начните заново.")
        return -1
    
    user = update.effective_user
    if user is None:
        return -1
    
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    
    # Получаем данные для обновления
    edit_data = context.user_data.get('debt_edit', {})
    monthly_payment = None
    if 'monthly_payment' in edit_data and edit_data['monthly_payment'] is not None:
        monthly_payment = Decimal(str(edit_data['monthly_payment']))
    
    try:
        # Обновляем долг
        updated_debt = await debt_service.update_debt_conditions(
            debt_id=debt_id,
            user_id=db_user.id,
            monthly_payment=monthly_payment,
            due_day=due_day
        )
        
        # Очищаем данные
        context.user_data.pop('debt_edit_debt_id', None)
        context.user_data.pop('debt_edit', None)
        
        # Форматируем сообщение об успехе
        monthly_payment_text = f"{updated_debt.monthly_payment:,.2f}" if updated_debt.monthly_payment else "не задан"
        due_day_text = str(updated_debt.due_day) if updated_debt.due_day else "не задан"
        
        text = (
            f"✅ Долг #{debt_id} успешно обновлён!\n\n"
            f"Ежемесячный платёж: {monthly_payment_text}\n"
            f"День платежа: {due_day_text}"
        )
        
        # Кнопка для возврата к деталям долга
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ К долгу", callback_data=f"debt:{debt_id}")]
        ])
        
        await update.message.reply_text(text, reply_markup=keyboard)
        
        return -1
    
    except PermissionError:
        await update.message.reply_text("❌ Только должник может редактировать долг.", reply_markup=get_cancel_keyboard())
        return -1
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}", reply_markup=get_cancel_keyboard())
        return -1
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}", reply_markup=get_cancel_keyboard())
        return -1

