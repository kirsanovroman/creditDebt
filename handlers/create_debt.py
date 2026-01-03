"""
Handler для создания долга.
"""
from typing import Optional
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import get_cancel_keyboard, get_main_menu_keyboard
from handlers.utils import parse_decimal
from services.debt_service import DebtService
from repositories.user_repository import UserRepository

# Импортируем константы состояний из main
DEBT_AMOUNT = 0
DEBT_MONTHLY_PAYMENT = 1
DEBT_DUE_DAY = 2


async def debt_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс создания долга."""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Инициализируем состояние
    context.user_data['debt_create_step'] = 'amount'
    context.user_data['debt_create'] = {}
    
    text = (
        "➕ <b>Создание долга</b>\n\n"
        "Введите сумму долга (например: 10000 или 10000.50):"
    )
    keyboard = get_cancel_keyboard()
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
    
    return DEBT_AMOUNT


async def debt_create_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод суммы долга."""
    text = update.message.text if update.message else ""
    
    amount = parse_decimal(text)
    if amount is None or amount <= 0:
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число больше нуля (например: 10000):",
            reply_markup=get_cancel_keyboard()
        )
        return DEBT_AMOUNT
    
    context.user_data['debt_create']['principal_amount'] = float(amount)
    context.user_data['debt_create_step'] = 'monthly_payment'
    
    await update.message.reply_text(
        "Введите ежемесячный платёж (можно пропустить, отправив \"-\"):",
        reply_markup=get_cancel_keyboard()
    )
    
    return DEBT_MONTHLY_PAYMENT


async def debt_create_monthly_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод ежемесячного платежа."""
    text = update.message.text if update.message else ""
    
    if text.strip() == '-':
        context.user_data['debt_create']['monthly_payment'] = None
        context.user_data['debt_create_step'] = 'due_day'
        await update.message.reply_text(
            "Введите день месяца для платежа (1-31, можно пропустить, отправив \"-\"):",
            reply_markup=get_cancel_keyboard()
        )
        return DEBT_DUE_DAY
    
    monthly_payment = parse_decimal(text)
    if monthly_payment is None or monthly_payment <= 0:
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число больше нуля или \"-\" для пропуска:",
            reply_markup=get_cancel_keyboard()
        )
        return DEBT_MONTHLY_PAYMENT
    
    context.user_data['debt_create']['monthly_payment'] = float(monthly_payment)
    context.user_data['debt_create_step'] = 'due_day'
    
    await update.message.reply_text(
        "Введите день месяца для платежа (1-31, можно пропустить, отправив \"-\"):",
        reply_markup=get_cancel_keyboard()
    )
    
    return DEBT_DUE_DAY


async def debt_create_due_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод дня платежа и создаёт долг."""
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
                return DEBT_DUE_DAY
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат. Введите число от 1 до 31 или \"-\" для пропуска:",
                reply_markup=get_cancel_keyboard()
            )
            return DEBT_DUE_DAY
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    user = update.effective_user
    if user is None:
        return -1
    
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_data = context.user_data.get('debt_create', {})
    
    principal_amount = Decimal(str(debt_data.get('principal_amount', 0)))
    monthly_payment = Decimal(str(debt_data['monthly_payment'])) if debt_data.get('monthly_payment') else None
    
    debt_service = DebtService()
    
    try:
        debt = await debt_service.create_debt(
            debtor_user_id=db_user.id,
            creditor_user_id=None,  # В MVP можно добавить позже
            principal_amount=principal_amount,
            currency='RUB',
            monthly_payment=monthly_payment,
            due_day=due_day,
            actor_user_id=db_user.id
        )
        
        # Очищаем данные
        context.user_data.pop('debt_create', None)
        context.user_data.pop('debt_create_step', None)
        
        # Форматируем сообщение
        monthly_payment_text = f"{debt.monthly_payment:,.2f}" if debt.monthly_payment else "не задан"
        due_day_text = str(debt.due_day) if debt.due_day else "не задан"
        
        text = (
            f"✅ Долг создан!\n\n"
            f"ID: {debt.id}\n"
            f"Сумма: {debt.principal_amount:,.2f} {debt.currency}\n"
            f"Ежемесячный платёж: {monthly_payment_text}\n"
            f"День платежа: {due_day_text}"
        )
        
        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )
        
        return -1
    
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}", reply_markup=get_cancel_keyboard())
        return DEBT_DUE_DAY
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}", reply_markup=get_cancel_keyboard())
        return DEBT_DUE_DAY

