# file: keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_keyboard(user_id: int) -> InlineKeyboardMarkup:
    keyboard = []
    
    # دکمه‌های حرکت
    move_buttons = [
        InlineKeyboardButton("↑ شمال", callback_data="move_north"),
        InlineKeyboardButton("↓ جنوب", callback_data="move_south"),
        InlineKeyboardButton("→ شرق", callback_data="move_east"),
        InlineKeyboardButton("← غرب", callback_data="move_west"),
    ]
    keyboard.append(move_buttons)
    
    # دکمه‌های اقدام
    action_buttons = [
        InlineKeyboardButton("📊 وضعیت", callback_data="status"),
        InlineKeyboardButton("📜 مأموریت‌ها", callback_data="quests"),
        InlineKeyboardButton("🎒 موجودی", callback_data="inventory")
    ]
    keyboard.append(action_buttons)
    
    return InlineKeyboardMarkup(keyboard)
