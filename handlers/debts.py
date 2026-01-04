"""
Handlers для работы с долгами.
"""
from typing import Optional
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import (
    get_main_menu_keyboard,
    get_debt_list_keyboard,
    get_debt_detail_keyboard,
    get_debt_close_keyboard,
    get_cancel_keyboard
)
from handlers.utils import format_debt_info, format_payment_plan, format_debt_list_item
from services.debt_service import DebtService
from services.payment_service import PaymentService
from services.planner_service import PlannerService
from repositories.user_repository import UserRepository
from database import Database


async def debts_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос списка долгов."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    if user is None:
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    debts = await debt_service.get_user_debts(db_user.id)
    
    if not debts:
        text = "У вас пока нет долгов.\n\nСоздайте первый долг через меню."
        keyboard = get_main_menu_keyboard()
    else:
        text = "<b>📋 Мои долги:</b>\n\n"
        keyboard_buttons = []
        
        for i, debt in enumerate(debts, 1):
            is_debtor = debt.debtor_user_id == db_user.id
            text += format_debt_list_item(debt, i, is_debtor)
            keyboard_buttons.append(
                get_debt_list_keyboard(debt.id, is_debtor, debt.name).inline_keyboard[0]
            )
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard_buttons.append(
            [InlineKeyboardButton("🏠 Главное меню", callback_data="start")]
        )
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')


async def debt_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос деталей долга."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    if user is None:
        return
    
    # Извлекаем debt_id из callback_data (формат: "debt:123")
    callback_data = query.data if query else ""
    try:
        debt_id = int(callback_data.split(':')[1])
    except (IndexError, ValueError):
        await query.answer("Ошибка: неверный ID долга", show_alert=True)
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    
    # Проверяем доступ
    if not await debt_service.check_access(debt_id, db_user.id):
        await query.answer("Нет доступа к этому долгу", show_alert=True)
        return
    
    debt = await debt_service.get_debt_by_id(debt_id)
    if debt is None:
        await query.answer("Долг не найден", show_alert=True)
        return
    
    is_debtor = debt.debtor_user_id == db_user.id
    is_closed = debt.status == 'closed'
    
    # Рассчитываем баланс и план
    payment_service = PaymentService()
    balance = await payment_service.calculate_balance(debt_id)
    
    planner_service = PlannerService()
    plan_items = await planner_service.calculate_payment_plan(debt, balance)
    
    # Форматируем информацию о долге
    debt_info = await format_debt_info(debt, balance)
    
    # Вычисляем доступную длину для плана
    # Telegram лимит: 4096 символов
    # Запас: 100 символов (на всякий случай)
    # Разделитель: 1 символ (\n)
    TELEGRAM_MESSAGE_LIMIT = 4096
    SAFETY_MARGIN = 100
    available_length = TELEGRAM_MESSAGE_LIMIT - len(debt_info) - SAFETY_MARGIN - 1
    
    # Форматируем план с учётом лимита
    plan_text = await format_payment_plan(plan_items, max_length=available_length)
    
    # Собираем итоговое сообщение
    text = debt_info + "\n" + plan_text
    
    keyboard = get_debt_detail_keyboard(debt_id, is_debtor, is_closed)
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')


async def debt_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос закрытия долга."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    if user is None:
        return
    
    # Извлекаем debt_id из callback_data
    callback_data = query.data if query else ""
    try:
        parts = callback_data.split(':')
        if len(parts) == 4 and parts[2] == 'confirm':
            debt_id = int(parts[3])
        else:
            debt_id = int(parts[2])
    except (IndexError, ValueError):
        await query.answer("Ошибка: неверный ID долга", show_alert=True)
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    
    try:
        # Если это подтверждение (confirm), закрываем долг
        if 'confirm' in callback_data:
            debt = await debt_service.close_debt(debt_id, db_user.id)
            
            text = f"✅ Долг #{debt_id} успешно закрыт."
            keyboard = get_main_menu_keyboard()
            
            if query and query.message:
                await query.message.edit_text(text, reply_markup=keyboard)
            return
        
        # Иначе показываем подтверждение
        debt = await debt_service.get_debt_by_id(debt_id)
        if debt is None:
            await query.answer("Долг не найден", show_alert=True)
            return
        
        text = (
            f"⚠️ Вы уверены, что хотите закрыть долг #{debt_id}?\n\n"
            f"После закрытия долга его нельзя будет изменять."
        )
        keyboard = get_debt_close_keyboard(debt_id)
        
        if query and query.message:
            await query.message.edit_text(text, reply_markup=keyboard)
    
    except PermissionError:
        await query.answer("Только должник может закрыть долг", show_alert=True)
    except ValueError as e:
        await query.answer(str(e), show_alert=True)
    except Exception as e:
        await query.answer(f"Ошибка: {str(e)}", show_alert=True)


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает отмену действия."""
    query = update.callback_query
    if query:
        await query.answer()
    
    text = "❌ Действие отменено."
    keyboard = get_main_menu_keyboard()
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard)
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard)

