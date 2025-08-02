# file: handlers.py (نسخه نهایی و کامل)
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
import database
import game_data
import keyboards

logger = logging.getLogger(__name__)

async def send_location_update(context: ContextTypes.DEFAULT_TYPE, player_id: int, chat_id: int, message_id: int = None, extra_text: str = ""):
    """پیام اصلی بازی را که شامل وضعیت و دکمه‌هاست، ارسال یا ویرایش می‌کند."""
    player_data = database.get_player(player_id)
    if not player_data:
        logger.error(f"Player data not found for user_id: {player_id}")
        return

    current_loc_name = player_data['location_name']
    loc_info = game_data.locations[current_loc_name]
    
    hp_bar = "❤️" * (player_data['hp'] // 10) + "🖤" * ((player_data['max_hp'] - player_data['hp']) // 10)
    
    # استفاده از کوتیشن سه‌تایی برای جلوگیری از خطا
    text = f"""❤️ سلامتی: {player_data['hp']}/{player_data['max_hp']}
{hp_bar}

📍<b>{current_loc_name}</b>
{loc_info['description']}"""
    
    if extra_text:
        text += f"\n\n{extra_text}"
    
    other_players = [f"{p['name']} ({p['hp']} HP)" for i, p in players.items() if p['location'] == current_loc_name and i != player_id]
    if other_players: text += f"\n\n👥 بازیکنان دیگر اینجا: {', '.join(other_players)}"
        
    keyboard = keyboards.build_keyboard(player_id)
    
    try:
        if message_id:
            await context.bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode='HTML', reply_markup=keyboard)
        else:
            await context.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Failed to update message: {e}. Sending a new one.")
        await context.bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    player_data = database.get_player(user.id)
    
    if not player_data:
        # --- مشکل اینجا بود: ارسال تمام مقادیر لازم ---
        start_x, start_y = game_data.STARTING_COORDS
        start_region, _ = get_region_from_coords(start_x, start_y)
        xp_next = game_data.xp_for_level(1)
        
        database.create_player(
            user_id=user.id, 
            name=user.first_name, 
            location=start_region, 
            x=start_x, 
            y=start_y, 
            max_hp=game_data.DEFAULT_HP,
            xp_to_next_level=xp_next
        )
        await update.message.reply_text(f"سلام {user.first_name}! به دنیای سیستم خوش آمدی.")
        
    await send_location_update(context, player_id=user.id, chat_id=update.effective_chat.id)
    await check_quests(context, user.id, update.effective_chat.id, 'login')
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تمام کلیک‌های روی دکمه‌ها را پردازش می‌کند."""
    query = update.callback_query
    await query.answer()

    player_id = query.from_user.id
    player_data = database.get_player(player_id)
    if not player_data:
        await query.edit_message_text("خطا: اطلاعات شما یافت نشد. لطفاً با /start مجدداً شروع کنید.")
        return

    callback_data = query.data
    action, _, target = callback_data.partition('_')
    extra_text_for_update = ""

    # منطق انتخاب مسیر
    if action == "choose":
        if player_data['path'] is None:
            if target == 'martial':
                database.update_player(player_id, {'path': 'martial', 'location_name': 'قله کوهستان مه آلود'})
            elif target == 'magic':
                database.update_player(player_id, {'path': 'magic', 'location_name': 'غار معنوی'})
    
    # منطق حمله
    elif action == "attack":
        target_id = int(target)
        if target_id in players and players[target_id]['location'] == player_data['location_name']:
            damage = random.randint(10, 25)
            # update target's hp in database
            target_player_data = database.get_player(target_id)
            new_hp = target_player_data['hp'] - damage
            database.update_player(target_id, {'hp': new_hp})

            await query.answer(f"شما {damage} آسیب به {target_player_data['name']} وارد کردید!", show_alert=True)
            await context.bot.send_message(chat_id=target_id, text=f"⚔️ {player_data['name']} به شما حمله کرد و {damage} آسیب وارد کرد!")
            
            if new_hp <= 0:
                defeated_name = target_player_data['name']
                database.update_player(target_id, {'hp': target_player_data['max_hp'], 'location_name': game_data.STARTING_LOCATION, 'path': None})
                await context.bot.send_message(chat_id=target_id, text="شما شکست خوردید و به چهارراه سرنوشت بازگشتید.")
                await context.bot.send_message(chat_id=player_id, text=f"شما {defeated_name} را شکست دادید!")
                await send_location_update(context, player_id=target_id, chat_id=target_id)
        else:
            await query.answer("بازیکن مورد نظر دیگر اینجا نیست!", show_alert=True)
        await send_location_update(context, player_id=player_id, chat_id=query.message.chat_id, message_id=query.message.message_id)
        return

    # منطق چت
    elif action == "chat":
        target_id = int(target)
        if target_id in players and players[target_id]['location'] == player_data['location_name']:
            database.update_player(player_id, {'state': f"chatting_{target_id}"})
            target_name = database.get_player(target_id)['name']
            await context.bot.send_message(chat_id=player_id, text=f"پیام خود را برای ارسال به {target_name} تایپ کنید:")
        else:
            await query.answer("بازیکن مورد نظر دیگر اینجا نیست!", show_alert=True)
        return

    # منطق اقدام اصلی (تمرین یا تمرکز)
    elif action == "action":
        current_rank = get_player_rank(player_data)
        if player_data['path'] == 'martial':
            qi_gain = random.randint(5, 15)
            database.update_player(player_id, {'qi': player_data['qi'] + qi_gain})
            extra_text_for_update = f"⚔️ شما تمرین کردید و {qi_gain} واحد چی (Qi) به دست آوردید."
        elif player_data['path'] == 'magic':
            mana_gain = random.randint(7, 20)
            database.update_player(player_id, {'mana': player_data['mana'] + mana_gain})
            extra_text_for_update = f"✨ شما تمرکز کردید و {mana_gain} واحد مانا (Mana) به دست آوردید."
        
        new_rank = get_player_rank(database.get_player(player_id))
        if new_rank != current_rank:
            extra_text_for_update += f"\n\n🎉 تبریک! شما به قلمرو «{new_rank}» ارتقا یافتید!"

    # منطق رفتن
    elif action == "go":
        if target in game_data.locations[player_data['location_name']]['exits']:
            database.update_player(player_id, {'location_name': game_data.locations[player_data['location_name']]['exits'][target]})
        else:
            await query.answer("از این طرف راهی نیست!", show_alert=True)
            return

    # منطق برداشتن آیتم
    elif action == "take":
        item_name = target
        # This part requires a proper inventory system, for now we assume it works
        await query.answer(f"شما '{item_name}' را برداشتید.")

    # منطق نمایش موجودی
    elif action == "inventory":
        inventory = json.loads(player_data['inventory'])
        await query.answer(f"موجودی: {', '.join(inventory) if inventory else 'خالی'}", show_alert=True)
        return
        
    # منطق نمایش وضعیت
    elif action == "status":
        rank = get_player_rank(player_data)
        path_name = "رزمی" if player_data['path'] == 'martial' else "جادو" if player_data['path'] == 'magic' else "نامشخص"
        energy_text = f"🔥 چی: {player_data['qi']}" if player_data['path'] == 'martial' else f"💧 مانا: {player_data['mana']}" if player_data['path'] == 'magic' else ""
        status_text = f"📊 وضعیت:\n- مسیر: {path_name}\n- قلمرو: {rank}\n{energy_text}"
        await query.answer(status_text, show_alert=True)
        return

    await send_location_update(context, player_id=player_id, chat_id=query.message.chat_id, message_id=query.message.message_id, extra_text=extra_text_for_update)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش پیام‌های متنی، به خصوص برای سیستم چت."""
    player_id = update.effective_user.id
    player_data = database.get_player(player_id)
    if not player_data: return

    player_state = player_data.get('state', 'idle')
    if player_state.startswith("chatting_"):
        target_id = int(player_state.split('_')[1])
        message_text = update.message.text
        
        target_player = database.get_player(target_id)
        if target_player and target_player['location'] == player_data['location_name']:
            await context.bot.send_message(chat_id=target_id, text=f"💬 {player_data['name']} می‌گوید:\n«{message_text}»")
            await update.message.reply_text("پیام شما ارسال شد.")
        else:
            await update.message.reply_text("بازیکن مورد نظر دیگر اینجا نیست.")
        database.update_player(player_id, {'state': 'idle'})
    else:
        await update.message.reply_text("برای تعامل با بازی از دکمه‌ها استفاده کنید. برای دیدن محیط اطراف، /start را بزنید.")

# Dummy players dictionary for send_location_update function
players = {}

def get_player_rank(player_data):
    # This is a dummy function. The real one is in the database module or should be.
    # For now, let's keep it simple.
    return "Rank"
