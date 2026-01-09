# -*- coding: utf-8 -*-
"""
Handler for test command /test_creditor.
Allows quickly assigning yourself as creditor for testing purposes.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from repositories.user_repository import UserRepository
from repositories.debt_repository import DebtRepository
from services.debt_service import DebtService
from services.payment_service import PaymentService
from services.planner_service import PlannerService
from services.audit_service import AuditService
from handlers.utils import format_debt_info, format_payment_plan
from handlers.keyboards import get_debt_detail_keyboard
from database import Database

logger = logging.getLogger(__name__)

# Telegram username of user allowed to use this command
ALLOWED_TEST_USERNAME = "kirsanovroman"


async def test_creditor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /test_creditor <debt_id> command.
    
    Assigns current user as creditor for specified debt.
    Available only for user with username = ALLOWED_TEST_USERNAME.
    """
    user = update.effective_user
    if user is None:
        await update.message.reply_text("❌ Ошибка: не удалось определить пользователя.")
        return
    
    # Check access by username
    if not user.username or user.username != ALLOWED_TEST_USERNAME:
        logger.warning(
            f"Attempt to use /test_creditor by user {user.username or 'without username'} (ID: {user.id})"
        )
        await update.message.reply_text(
            "❌ Эта команда доступна только для тестирования и ограничена определёнными пользователями."
        )
        return
    
    # Get debt_id from command arguments
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Использование: /test_creditor <debt_id>\n\n"
            "Пример: /test_creditor 123"
        )
        return
    
    try:
        debt_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Ошибка: debt_id должен быть числом.\n\n"
            "Пример: /test_creditor 123"
        )
        return
    
    # Get or create user in DB
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    debt_repo = DebtRepository()
    audit_service = AuditService()
    
    # Check if debt exists
    debt = await debt_service.get_debt_by_id(debt_id)
    if debt is None:
        await update.message.reply_text(f"❌ Долг #{debt_id} не найден.")
        return
    
    # Check if user is already creditor - if yes, just show creditor view
    if debt.creditor_user_id == db_user.id:
        # User is already creditor - show debt view as creditor
        await show_debt_as_creditor(update, debt_id, debt)
        return
    
    # Save state before change for audit
    debt_before = {
        'debt_id': debt.id,
        'creditor_user_id': debt.creditor_user_id,
    }
    
    # Update debt, assigning user as creditor
    pool = await Database.get_pool()
    conn = await pool.acquire()
    
    try:
        async with conn.transaction():
            # Update debt
            updated_debt = await debt_repo.update(
                debt_id=debt_id,
                creditor_user_id=db_user.id,
                conn=conn
            )
            
            if updated_debt is None:
                raise ValueError("Не удалось обновить долг")
            
            # Log change in audit
            debt_after = {
                'debt_id': updated_debt.id,
                'creditor_user_id': updated_debt.creditor_user_id,
            }
            await audit_service.log_update(
                entity_type='debt',
                entity_id=debt_id,
                actor_user_id=db_user.id,
                before=debt_before,
                after=debt_after,
                conn=conn
            )
            
            logger.info(
                f"Test creditor assigned: user_id={db_user.id}, username={user.username}, "
                f"debt_id={debt_id}"
            )
    
    except Exception as e:
        logger.error(f"Error assigning test creditor: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Произошла ошибка при назначении кредитора: {str(e)}"
        )
        return
    
    finally:
        await pool.release(conn)
    
    # Get updated debt info (now user is creditor)
    updated_debt = await debt_service.get_debt_by_id(debt_id)
    if updated_debt is None:
        await update.message.reply_text(
            f"✅ Вы успешно назначены кредитором долга #{debt_id}!\n\n"
            f"Используйте меню 'Мои долги' для просмотра."
        )
        return
    
    # Send success message
    await update.message.reply_text(
        f"✅ Вы успешно назначены кредитором долга #{debt_id}!\n\n"
        f"📋 <b>Просмотр долга как кредитор:</b>",
        parse_mode='HTML'
    )
    
    # Show debt as creditor
    await show_debt_as_creditor(update, debt_id, updated_debt)


async def show_debt_as_creditor(update: Update, debt_id: int, debt) -> None:
    """
    Shows debt details from creditor perspective.
    
    Args:
        update: Telegram update
        debt_id: ID of the debt
        debt: Debt object
    """
    # Calculate balance and payment plan
    payment_service = PaymentService()
    balance = await payment_service.calculate_balance(debt_id)
    
    planner_service = PlannerService()
    plan_items = await planner_service.calculate_payment_plan(debt, balance)
    
    # Format debt information
    debt_info = await format_debt_info(debt, balance)
    
    # Calculate available length for payment plan
    # Telegram limit: 4096 characters
    # Safety margin: 100 characters
    # Separator: 1 character (\n)
    TELEGRAM_MESSAGE_LIMIT = 4096
    SAFETY_MARGIN = 100
    available_length = TELEGRAM_MESSAGE_LIMIT - len(debt_info) - SAFETY_MARGIN - 1
    
    # Format payment plan with limit
    plan_text = await format_payment_plan(plan_items, max_length=available_length)
    
    # Build final message
    text = debt_info + "\n" + plan_text
    
    # Show debt as creditor (is_debtor=False) - no editing buttons, only view
    is_debtor = False  # Force creditor view
    is_closed = debt.status == 'closed'
    keyboard = get_debt_detail_keyboard(debt_id, is_debtor, is_closed)
    
    # Show debt details with creditor view (no debtor actions available)
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
