"""
Handlers для работы с платежами.
"""
import logging
from datetime import date
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)
from handlers.keyboards import get_payments_list_keyboard, get_payment_delete_keyboard, get_cancel_keyboard
from handlers.utils import parse_decimal, parse_date
from services.payment_service import PaymentService
from services.debt_service import DebtService
from repositories.user_repository import UserRepository

# Константы состояний для ConversationHandler
PAYMENT_AMOUNT = 0
PAYMENT_DATE = 1


async def payments_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос списка платежей."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    if user is None:
        return
    
    # Извлекаем debt_id из callback_data
    callback_data = query.data if query else ""
    try:
        debt_id = int(callback_data.split(':')[2])
    except (IndexError, ValueError):
        await query.answer("Ошибка: неверный ID долга", show_alert=True)
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    payment_service = PaymentService()
    
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
    
    # Получаем платежи
    payments = await payment_service.get_payments_by_debt(debt_id, include_deleted=False)
    
    text = f"<b>📄 Платежи по долгу #{debt_id}</b>\n\n"
    
    if not payments:
        text += "Платежей пока нет."
    else:
        for i, payment in enumerate(payments, 1):
            text += f"{i}. {payment.payment_date.strftime('%d.%m.%Y')} — {payment.amount:,.2f} {debt.currency}\n"
    
    keyboard = get_payments_list_keyboard(debt_id, [p.id for p in payments], is_debtor, is_closed)
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')


async def payment_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс добавления платежа."""
    query = update.callback_query
    
    logger.info(f"payment_add_start called: query={query is not None}, callback_data={query.data if query else None}")
    
    user = update.effective_user
    if user is None:
        logger.warning("payment_add_start: user is None")
        if query:
            await query.answer("Ошибка: не удалось определить пользователя", show_alert=True)
        return -1
    
    # Извлекаем debt_id из callback_data
    if not query:
        logger.error("payment_add_start: query is None")
        return -1
    
    callback_data = query.data
    try:
        debt_id = int(callback_data.split(':')[2])
        logger.info(f"payment_add_start: debt_id={debt_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"payment_add_start: error parsing debt_id from '{callback_data}': {e}")
        await query.answer("Ошибка: неверный ID долга", show_alert=True)
        return -1
    
    # Проверяем доступ и права перед началом процесса
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_service = DebtService()
    if not await debt_service.check_access(debt_id, db_user.id):
        if query:
            await query.answer("Нет доступа к этому долгу", show_alert=True)
        return -1
    
    # Проверяем, что пользователь является должником (только должник может добавлять платежи)
    debt = await debt_service.get_debt_by_id(debt_id)
    if debt is None:
        if query:
            await query.answer("Долг не найден", show_alert=True)
        return -1
    
    if debt.debtor_user_id != db_user.id:
        if query:
            await query.answer("Только должник может добавлять платежи", show_alert=True)
        return -1
    
    # Проверяем, что долг не закрыт
    if debt.status == 'closed':
        if query:
            await query.answer("Нельзя добавлять платежи к закрытому долгу", show_alert=True)
        return -1
    
    # Все проверки пройдены - отвечаем на callback
    await query.answer()
    logger.info(f"payment_add_start: all checks passed, starting conversation for debt_id={debt_id}")
    
    # Сохраняем debt_id в контексте
    context.user_data['payment_add_debt_id'] = debt_id
    context.user_data['payment_add_step'] = 'amount'
    
    text = (
        "💰 <b>Добавление платежа</b>\n\n"
        "Введите сумму платежа (например: 1000 или 1000.50):"
    )
    keyboard = get_cancel_keyboard()
    
    if query and query.message:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        logger.info(f"payment_add_start: message edited for debt_id={debt_id}")
    elif update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='HTML')
        logger.info(f"payment_add_start: message sent for debt_id={debt_id}")
    else:
        logger.error(f"payment_add_start: no message to edit/send for debt_id={debt_id}")
    
    return PAYMENT_AMOUNT


async def payment_add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод суммы платежа."""
    text = update.message.text if update.message else ""
    
    amount = parse_decimal(text)
    if amount is None or amount <= 0:
        await update.message.reply_text(
            "❌ Неверный формат суммы. Введите число больше нуля (например: 1000):",
            reply_markup=get_cancel_keyboard()
        )
        return PAYMENT_AMOUNT
    
    context.user_data['payment_add_amount'] = float(amount)
    context.user_data['payment_add_step'] = 'date'
    
    await update.message.reply_text(
        "Введите дату платежа (формат: DD.MM.YYYY, например: 15.01.2024):",
        reply_markup=get_cancel_keyboard()
    )
    
    return PAYMENT_DATE


async def payment_add_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ввод даты платежа и сохраняет платёж."""
    text = update.message.text if update.message else ""
    
    payment_date = parse_date(text)
    if payment_date is None:
        await update.message.reply_text(
            "❌ Неверный формат даты. Введите дату в формате DD.MM.YYYY (например: 15.01.2024):",
            reply_markup=get_cancel_keyboard()
        )
        return PAYMENT_DATE
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    user = update.effective_user
    if user is None:
        return -1
    
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    debt_id = context.user_data.get('payment_add_debt_id')
    amount = Decimal(str(context.user_data.get('payment_add_amount', 0)))
    
    if not debt_id:
        await update.message.reply_text("❌ Ошибка: не найден ID долга.", reply_markup=get_cancel_keyboard())
        return -1
    
    payment_service = PaymentService()
    
    try:
        payment = await payment_service.add_payment(
            debt_id=debt_id,
            amount=amount,
            payment_date=payment_date,
            user_id=db_user.id
        )
        
        # Очищаем данные
        context.user_data.pop('payment_add_debt_id', None)
        context.user_data.pop('payment_add_amount', None)
        context.user_data.pop('payment_add_step', None)
        
        # Показываем сообщение об успехе с кнопкой возврата к долгу
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = f"✅ Платёж добавлен: {payment.amount:,.2f} на {payment_date.strftime('%d.%m.%Y')}"
        
        # Кнопка для возврата к деталям долга
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ К долгу", callback_data=f"debt:{debt_id}")]
        ])
        
        # Отправляем сообщение об успехе
        if update.message:
            try:
                await update.message.reply_text(
                    text,
                    reply_markup=keyboard
                )
                logger.info(f"Payment added successfully: debt_id={debt_id}, amount={payment.amount}")
            except Exception as e:
                logger.error(f"Error sending payment confirmation: {e}", exc_info=True)
                # Пытаемся отправить хотя бы простое сообщение
                try:
                    await update.message.reply_text(f"✅ Платёж добавлен: {payment.amount:,.2f}")
                except:
                    pass
        else:
            logger.warning(f"update.message is None. update type: {type(update)}, update: {update}")
        
        return -1
    
    except PermissionError:
        await update.message.reply_text("❌ Только должник может добавлять платежи.")
        return -1
    except ValueError as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        return -1
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")
        return -1


async def payment_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает удаление платежа."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    if user is None:
        return
    
    # Извлекаем payment_id из callback_data
    callback_data = query.data if query else ""
    try:
        parts = callback_data.split(':')
        if len(parts) == 4 and parts[2] == 'confirm':
            payment_id = int(parts[3])
        else:
            payment_id = int(parts[2])
            await query.answer("Ошибка: используйте кнопку удаления из списка платежей", show_alert=True)
            return
    except (IndexError, ValueError):
        await query.answer("Ошибка: неверный ID платежа", show_alert=True)
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    payment_service = PaymentService()
    
    try:
        payment = await payment_service.delete_payment(payment_id, db_user.id)
        
        debt_id = payment.debt_id
        
        text = f"✅ Платёж удалён."
        keyboard = get_cancel_keyboard()
        
        # Обновляем список платежей
        from handlers.debts import payments_list_callback
        update.callback_query.data = f"payments:list:{debt_id}"
        await payments_list_callback(update, context)
    
    except PermissionError:
        await query.answer("Только должник может удалять платежи", show_alert=True)
    except ValueError as e:
        await query.answer(str(e), show_alert=True)
    except Exception as e:
        await query.answer(f"Ошибка: {str(e)}", show_alert=True)

