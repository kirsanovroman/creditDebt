"""
Утилиты для создания клавиатур.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню."""
    keyboard = [
        [InlineKeyboardButton("📋 Мои долги", callback_data="debts:list")],
        [InlineKeyboardButton("➕ Создать долг", callback_data="debt:create")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру с кнопкой Отмена."""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)


def get_debt_list_keyboard(debt_id: int, is_debtor: bool, debt_name: str = None) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для элемента списка долгов.
    
    Args:
        debt_id: ID долга
        is_debtor: True, если пользователь является должником
        debt_name: Название долга (опционально, для отображения в кнопке)
    """
    # Формируем текст кнопки с названием долга
    if debt_name:
        # Ограничиваем длину названия для кнопки (Telegram ограничение ~64 символа)
        # Оставляем место для эмодзи и текста "Просмотр"
        max_name_length = 40
        if len(debt_name) > max_name_length:
            debt_name_display = debt_name[:max_name_length - 3] + "..."
        else:
            debt_name_display = debt_name
        button_text = f"👁️ {debt_name_display}"
    else:
        button_text = "👁️ Просмотр"
    
    keyboard = [[InlineKeyboardButton(button_text, callback_data=f"debt:{debt_id}")]]
    return InlineKeyboardMarkup(keyboard)


def get_debt_detail_keyboard(debt_id: int, is_debtor: bool, is_closed: bool) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для деталей долга.
    
    Args:
        debt_id: ID долга
        is_debtor: True, если пользователь является должником
        is_closed: True, если долг закрыт
    """
    keyboard = []
    
    if is_debtor and not is_closed:
        # Только должник может редактировать активные долги
        keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"debt:edit:{debt_id}")])
        keyboard.append([InlineKeyboardButton("💰 Добавить платёж", callback_data=f"payment:add:{debt_id}")])
        keyboard.append([InlineKeyboardButton("👥 Пригласить кредитора", callback_data=f"invite:create:{debt_id}")])
        keyboard.append([InlineKeyboardButton("🔒 Закрыть долг", callback_data=f"debt:close:{debt_id}")])
    
    keyboard.append([InlineKeyboardButton("📄 Платежи", callback_data=f"payments:list:{debt_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад к списку", callback_data="debts:list")])
    
    return InlineKeyboardMarkup(keyboard)


def get_payments_list_keyboard(debt_id: int, payment_ids: list[int], is_debtor: bool, is_closed: bool) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру списка платежей.
    
    Args:
        debt_id: ID долга
        payment_ids: Список ID платежей
        is_debtor: True, если пользователь является должником
        is_closed: True, если долг закрыт
    """
    keyboard = []
    
    if is_debtor and not is_closed:
        keyboard.append([InlineKeyboardButton("➕ Добавить платёж", callback_data=f"payment:add:{debt_id}")])
    
    keyboard.append([InlineKeyboardButton("◀️ К долгу", callback_data=f"debt:{debt_id}")])
    
    return InlineKeyboardMarkup(keyboard)


def get_payment_delete_keyboard(payment_id: int, debt_id: int) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для подтверждения удаления платежа."""
    keyboard = [
        [InlineKeyboardButton("✅ Удалить", callback_data=f"payment:delete:confirm:{payment_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"payments:list:{debt_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_debt_close_keyboard(debt_id: int) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру для подтверждения закрытия долга."""
    keyboard = [
        [InlineKeyboardButton("✅ Закрыть", callback_data=f"debt:close:confirm:{debt_id}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"debt:{debt_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

