"""
Handler для помощи.
"""
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu_keyboard


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает запрос помощи."""
    query = update.callback_query
    
    if query:
        await query.answer()
    
    text = (
        "<b>ℹ️ Помощь</b>\n\n"
        "<b>Основные функции:</b>\n"
        "• Создание и управление долгами\n"
        "• Учёт платежей\n"
        "• План погашения\n"
        "• Приглашение кредиторов\n\n"
        "<b>Права доступа:</b>\n"
        "• Должник может изменять долг и добавлять платежи\n"
        "• Кредитор имеет доступ только на чтение\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n\n"
        "Все действия выполняются через кнопки меню."
    )
    
    if query and query.message:
        await query.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
    elif update.message:
        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )

