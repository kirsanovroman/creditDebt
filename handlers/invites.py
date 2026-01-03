"""
Handlers для работы с приглашениями.
"""
from telegram import Update
from telegram.ext import ContextTypes
from handlers.keyboards import get_main_menu_keyboard
from services.invite_service import InviteService
from services.debt_service import DebtService
from repositories.user_repository import UserRepository
from database import Database


async def invite_create_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает создание приглашения."""
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
    
    # Проверяем доступ перед созданием приглашения
    debt_service = DebtService()
    if not await debt_service.check_access(debt_id, db_user.id):
        await query.answer("Нет доступа к этому долгу", show_alert=True)
        return
    
    invite_service = InviteService()
    
    try:
        invite = await invite_service.create_invite(debt_id, db_user.id)
        
        # Формируем ссылку для приглашения
        bot_username = context.bot.username
        invite_link = f"https://t.me/{bot_username}?start=invite_{invite.token}"
        
        text = (
            f"✅ Приглашение создано!\n\n"
            f"Ссылка для приглашения:\n"
            f"{invite_link}\n\n"
            f"Токен действителен до {invite.expires_at.strftime('%d.%m.%Y %H:%M')}"
        )
        
        if query and query.message:
            await query.message.edit_text(text, reply_markup=get_main_menu_keyboard())
        elif update.message:
            await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
    
    except PermissionError:
        await query.answer("Только должник может создавать приглашения", show_alert=True)
    except ValueError as e:
        await query.answer(str(e), show_alert=True)
    except Exception as e:
        await query.answer(f"Ошибка: {str(e)}", show_alert=True)


async def invite_accept_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает принятие приглашения через команду /start с параметром."""
    user = update.effective_user
    if user is None:
        return
    
    # Парсим параметр из команды /start invite_<token>
    args = context.args
    if not args or not args[0].startswith('invite_'):
        return  # Обычный /start обработается другим handler
    
    token_str = args[0].replace('invite_', '')
    
    try:
        from uuid import UUID
        token = UUID(token_str)
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ссылки приглашения.")
        return
    
    # Пул уже создан в post_init
    user_repo = UserRepository()
    db_user = await user_repo.create_or_get_by_tg_id(user.id)
    
    invite_service = InviteService()
    
    try:
        await invite_service.accept_invite(token, db_user.id)
        
        await update.message.reply_text(
            "✅ Вы успешно приняли приглашение и стали кредитором этого долга!",
            reply_markup=get_main_menu_keyboard()
        )
    
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}", reply_markup=get_main_menu_keyboard())
    except PermissionError as e:
        await update.message.reply_text(f"❌ {str(e)}", reply_markup=get_main_menu_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}", reply_markup=get_main_menu_keyboard())

