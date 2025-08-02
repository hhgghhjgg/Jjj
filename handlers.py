# file: handlers.py
import logging
import json
from telegram import Update
from telegram.ext import ContextTypes
import database
import game_data
import keyboards

logger = logging.getLogger(__name__)

# --- توابع کمکی سیستم ---
async def send_system_notification(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str):
    """یک نوتیفیکیشن با فرمت سیستمی ارسال می‌کند."""
    await context.bot.send_message(chat_id=chat_id, text=f"
    
[System] 🔷\n{message}")

async def grant_xp(context: ContextTypes.DEFAULT_TYPE, player_id: int, chat_id: int, xp_amount: int):
    """به بازیکن XP می‌دهد و سطح او را بررسی می‌کند."""
    player = database.get_player(player_id)
    new_xp = player['xp'] + xp_amount
    database.update_player(player_id, {'xp': new_xp})
    await send_system_notification(context, chat_id, f"شما {xp_amount} امتیاز تجربه (XP) کسب کردید.")
    
    # بررسی برای ارتقاء سطح
    if new_xp >= player['xp_to_next_level']:
        new_level = player['level'] + 1
        xp_over = new_xp - player['xp_to_next_level']
        next_level_xp_req = game_data.xp_for_level(new_level)
        new_stat_points = player['stat_points'] + 5 # پاداش 5 امتیاز آمار برای هر سطح
        
        database.update_player(player_id, {
            'level': new_level,
            'xp': xp_over,
            'xp_to_next_level': next_level_xp_req,
            'stat_points': new_stat_points,
            'hp': player['max_hp'] # سلامتی را پر می‌کند
        })
        await send_system_notification(context, chat_id, f"🎉 **سطح شما افزایش یافت!** 🎉\nشما به سطح {new_level} رسیدید.\nشما 5 امتیاز آمار برای تخصیص دریافت کردید.")

async def check_quests(context: ContextTypes.DEFAULT_TYPE, player_id: int, chat_id: int, event_type: str, value=None):
    """وضعیت مأموریت‌ها را بر اساس یک رویداد بررسی می‌کند."""
    player = database.get_player(player_id)
    for q_name, q_data in game_data.QUESTS.items():
        # بررسی برای فعال کردن مأموریت‌های جدید
        if q_data['trigger']['type'] == 'level' and player['level'] >= q_data['trigger']['value']:
            if not database.get_active_quest(player_id, q_name):
                database.add_quest(player_id, q_name)
                await send_system_notification(context, chat_id, f"📜 مأموریت جدید دریافت شد: **{q_data['title']}**\n{q_data['description']}")
        
        # بررسی برای تکمیل مأموریت‌های فعال
        active_quest = database.get_active_quest(player_id, q_name)
        if active_quest:
            objective = q_data['objective']
            if objective['type'] == 'reach_coord' and event_type == 'move':
                if (player['coord_x'], player['coord_y']) == objective['coords']:
                    database.complete_quest(player_id, q_name)
                    await send_system_notification(context, chat_id, f"✅ مأموریت **{q_data['title']}** با موفقیت انجام شد!")
                    await grant_xp(context, player_id, chat_id, q_data['reward']['xp'])


# --- توابع اصلی ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    player_data = database.get_player(user.id)
    
    if not player_data:
        start_x, start_y = game_data.STARTING_COORDS
        start_region, _ = get_region_from_coords(start_x, start_y) # این تابع باید از کد قبلی کپی شود
        database.create_player(user.id, user.first_name, start_region, start_x, start_y, game_data.DEFAULT_HP, game_data.xp_for_level(1))
        await update.message.reply_text(f"سلام {user.first_name}! به دنیای سیستم خوش آمدی.")
        
    await send_location_update(context, player_id=user.id, chat_id=update.effective_chat.id)
    await check_quests(context, user.id, update.effective_chat.id, 'login')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    player_id = query.from_user.id
    player_data = database.get_player(player_id)
    if not player_data: return

    callback_data = query.data
    action, _, target = callback_data.partition('_')
    
    if action == "move":
        x, y = player_data['coord_x'], player_data['coord_y']
        if target == 'north' and y < game_data.WORLD_HEIGHT - 1: y += 1
        elif target == 'south' and y > 0: y -= 1
        elif target == 'east' and x < game_data.WORLD_WIDTH - 1: x += 1
        elif target == 'west' and x > 0: x -= 1
        database.update_player(player_id, {'coord_x': x, 'coord_y': y})
        await check_quests(context, player_id, query.message.chat_id, 'move')

    elif action == "status":
        p = player_data
        status_text = (
            f"📊 **وضعیت {p['name']}**\n"
            f"سطح: {p['level']} ({p['xp']}/{p['xp_to_next_level']} XP)\n"
            f"❤️ سلامتی: {p['hp']}/{p['max_hp']}\n\n"
            f"⚔️ قدرت: {p['strength']}\n"
            f"🏃 چابکی: {p['agility']}\n"
            f"🧠 هوش: {p['intelligence']}\n\n"
            f"✨ امتیازات قابل تخصیص: {p['stat_points']}"
        )
        await query.answer(status_text, show_alert=True)
        return
        
    # ... (منطق سایر دکمه‌ها)

    await send_location_update(context, player_id=player_id, chat_id=query.message.chat_id, message_id=query.message.message_id)

# ... (توابع send_location_update و get_region_from_coords باید از کد قبلی کپی شوند)
async def get_region_from_coords(x, y):
    for region_name, region_data in game_data.regions.items():
        min_x, max_x, min_y, max_y = region_data['bounds']
        if min_x <= x <= max_x and min_y <= y <= max_y:
            return region_name, region_data
    return "سرزمین‌های ناشناخته", {'base_description': 'شما در منطقه‌ای ناشناخته و عجیب قرار دارید.'}

async def send_location_update(context: ContextTypes.DEFAULT_TYPE, player_id: int, chat_id: int, message_id: int = None):
    player_data = database.get_player(player_id)
    x, y = player_data['coord_x'], player_data['coord_y']
    region_name, region_data = await get_region_from_coords(x, y)
    
    if (x, y) in region_data.get('special_locations', {}):
        description = region_data['special_locations'][(x, y)]
    else:
        description = region_data['base_description']
        
    if player_data['location_name'] != region_name:
        database.update_player(player_id, {'location_name': region_name})

    text = f"📍<b>{region_name} ({x}, {y})</b>\n{description}"
    keyboard_markup = keyboards.build_keyboard(player_id)
    
    try:
        if message_id:
            await context.bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode='HTML', reply_markup=keyboard_markup)
        else:
            await context.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard_markup)
    except Exception as e:
        logger.warning(f"Failed to update message: {e}")
        await context.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard_markup)
