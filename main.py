#!/usr/bin/env python3
"""
Точка входа для Telegram-бота Debt Tracker.
"""
import asyncio
import logging
import signal
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from config import config
from database import Database
from handlers.start import start_command
from handlers.help import help_callback
from handlers.debts import (
    debts_list_callback,
    debt_detail_callback,
    debt_close_callback,
    cancel_callback
)
from handlers.payments import (
    payments_list_callback,
    payment_add_start,
    payment_add_amount,
    payment_add_date,
    payment_delete_callback
)
from handlers.create_debt import (
    debt_create_start,
    debt_create_name,
    debt_create_amount,
    debt_create_monthly_payment,
    debt_create_due_day,
    DEBT_NAME,
    DEBT_AMOUNT,
    DEBT_MONTHLY_PAYMENT,
    DEBT_DUE_DAY
)
from handlers.edit_debt import (
    debt_edit_start,
    debt_edit_monthly_payment,
    debt_edit_due_day,
    EDIT_MONTHLY_PAYMENT,
    EDIT_DUE_DAY
)
from handlers.invites import (
    invite_create_callback,
    invite_accept_command
)


# Состояния для ConversationHandler
PAYMENT_AMOUNT, PAYMENT_DATE = range(2)
# DEBT_NAME, DEBT_AMOUNT, DEBT_MONTHLY_PAYMENT, DEBT_DUE_DAY импортируются из handlers.create_debt
# EDIT_MONTHLY_PAYMENT, EDIT_DUE_DAY импортируются из handlers.edit_debt


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Уменьшаем уровень логирования для некоторых библиотек
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ошибки на уровне приложения.
    
    Логирует ошибку с полной информацией и отправляет пользователю понятное сообщение.
    """
    error = context.error
    logger.error(
        f"Error handling update: {type(error).__name__}: {error}",
        exc_info=error,
        extra={
            'update_id': update.update_id if isinstance(update, Update) else None,
            'user_id': update.effective_user.id if isinstance(update, Update) and update.effective_user else None,
        }
    )
    
    # Отправляем сообщение пользователю только если это Update с сообщением
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте ещё раз или обратитесь к администратору."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}", exc_info=e)


async def post_init(application: Application) -> None:
    """Инициализация после запуска бота."""
    # Инициализируем подключение к БД
    config.validate()
    await Database.create_pool()
    logger.info("Database pool created")


async def post_shutdown(application: Application) -> None:
    """
    Очистка ресурсов при остановке бота (graceful shutdown).
    
    Закрывает пул подключений к БД и другие ресурсы.
    """
    logger.info("Shutting down application...")
    try:
        await Database.close_pool()
        logger.info("Database pool closed successfully")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}", exc_info=e)
    logger.info("Application shutdown complete")


def main() -> None:
    """
    Запускает бота.
    
    Настраивает обработчики, регистрирует их в приложении и запускает polling.
    Поддерживает graceful shutdown при получении сигналов SIGINT/SIGTERM.
    """
    # Создаём приложение
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()
    
    # Настройка graceful shutdown для обработки сигналов
    def signal_handler(signum, frame):
        """Обработчик сигналов для graceful shutdown."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        # Останавливаем polling, что вызовет post_shutdown
        if application.running:
            application.stop()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Обработчик команды /start
    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start с учётом параметров."""
        args = context.args
        if args and args[0].startswith('invite_'):
            await invite_accept_command(update, context)
        else:
            await start_command(update, context)
    
    application.add_handler(CommandHandler("start", start_handler))
    
    # Обработчик команды /help
    application.add_handler(CommandHandler("help", help_callback))
    
    # ConversationHandler для создания долга
    debt_create_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(debt_create_start, pattern="^debt:create$")],
        states={
            DEBT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_create_name)],
            DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_create_amount)],
            DEBT_MONTHLY_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_create_monthly_payment)],
            DEBT_DUE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_create_due_day)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$"), CommandHandler("start", start_handler), CommandHandler("help", help_callback)],
        name="debt_create",
    )
    application.add_handler(debt_create_conv)
    
    # ConversationHandler для добавления платежа
    payment_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(payment_add_start, pattern="^payment:add:")],
        states={
            PAYMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_add_amount)],
            PAYMENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_add_date)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$")],
        name="payment_add",
    )
    application.add_handler(payment_add_conv)
    
    # ConversationHandler для редактирования долга
    debt_edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(debt_edit_start, pattern="^debt:edit:")],
        states={
            EDIT_MONTHLY_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_edit_monthly_payment)],
            EDIT_DUE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, debt_edit_due_day)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$"), CommandHandler("start", start_handler), CommandHandler("help", help_callback)],
        name="debt_edit",
    )
    application.add_handler(debt_edit_conv)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(debts_list_callback, pattern="^debts:list$"))
    application.add_handler(CallbackQueryHandler(debt_detail_callback, pattern="^debt:[0-9]+$"))
    application.add_handler(CallbackQueryHandler(debt_close_callback, pattern="^debt:close"))
    application.add_handler(CallbackQueryHandler(payments_list_callback, pattern="^payments:list:"))
    application.add_handler(CallbackQueryHandler(payment_delete_callback, pattern="^payment:delete"))
    application.add_handler(CallbackQueryHandler(invite_create_callback, pattern="^invite:create:"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(start_command, pattern="^start$"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel$"))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

