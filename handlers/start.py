"""
Handler для команды /start.
"""
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu_keyboard
from repositories.user_repository import UserRepository


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start.
    Показывает главное меню и создаёт/получает пользователя.
    """
    # Пул уже создан в post_init
    
    user_repo = UserRepository()
    user = update.effective_user
    
    if user is None:
        msg = update.message or (update.callback_query.message if update.callback_query else None)
        if msg:
            await msg.reply_text("Ошибка: не удалось определить пользователя.")
        return
    
    # Создаём или получаем пользователя
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    text = (
        "👋 Добро пожаловать в <b>Debt Tracker</b>!\n\n"
        "Я помогу вам вести учёт задолженностей.\n\n"
        "Выберите действие:"
    )
    
    if update.message:
        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='HTML'
        )
        await update.callback_query.answer()

