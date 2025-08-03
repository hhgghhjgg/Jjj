# =================================================================
#               bot.py - The Main Controller
#
# این فایل نقطه شروع و کنترلر اصلی ربات نقش‌آفرینی ماست.
# مسئولیت‌های اصلی:
#   - ارتباط با API تلگرام
#   - مدیریت ورودی‌های کاربر (دستورات و دکمه‌ها)
#   - فراخوانی متدها از کلاس Player برای تغییر وضعیت بازیکن
#   - نمایش اطلاعات و منوها به کاربر
#   - راه‌اندازی وب‌سرور Flask برای هاستینگ در Render
# =================================================================

import os
import threading
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- وارد کردن ماژول‌های سفارشی پروژه ---
# Player: کلاس اصلی برای مدیریت وضعیت هر بازیکن
# gamedata: تمام داده‌های ثابت بازی (نقشه، کوئست‌ها، رتبه‌ها و...)
from player import Player
from gamedata import game_world, CULTIVATION_PATHS

# --- مقداردهی اولیه ---

# توکن ربات از متغیرهای محیطی خوانده می‌شود تا امنیت حفظ شود
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# این دیکشنری، وضعیت تمام بازیکنان آنلاین را نگه می‌دارد
# کلید: user_id | مقدار: یک شیء کامل از کلاس Player
players = {}

# --- طراحی کیبوردهای شیشه‌ای (Inline Keyboards) ---

def create_start_markup():
    """کیبورد برای انتخاب مسیر اولیه بازی."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("مسیر تهذیب 🧘‍♂️", callback_data="choose_tahzib"),
               InlineKeyboardButton("مسیر مانا 🔮", callback_data="choose_mana"))
    return markup

def create_main_markup(player):
    """منوی اصلی و داینامیک بازی را بر اساس وضعیت بازیکن می‌سازد."""
    markup = InlineKeyboardMarkup()

    # اگر بازیکن شرایط صعود به رتبه بعد را داشت، دکمه آن را نشان بده
    if player.can_breakthrough():
        markup.add(InlineKeyboardButton("✨ دستیابی به موفقیت! ✨", callback_data="breakthrough"))

    # دکمه‌های حرکتی
    markup.add(InlineKeyboardButton("⬆️ شمال", callback_data="move_up"))
    markup.add(InlineKeyboardButton("⬅️ غرب", callback_data="move_left"),
               InlineKeyboardButton("➡️ شرق", callback_data="move_right"))
    markup.add(InlineKeyboardButton("⬇️ جنوب", callback_data="move_down"))

    # دکمه‌های اقدامات اصلی
    markup.add(InlineKeyboardButton("تمرین/کسب XP 💪", callback_data="action"),
               InlineKeyboardButton("وضعیت من 📊", callback_data="show_status"))
    markup.add(InlineKeyboardButton("کوئست‌ها 📜", callback_data="show_quests"),
               InlineKeyboardButton("مهارت‌ها ⚡️", callback_data="show_skills"))

    return markup

# --- توابع کمکی ---

def get_location_text(player):
    """متن توضیحات مکان فعلی بازیکن را تولید می‌کند."""
    coords = (player.x, player.y)
    if coords in game_world:
        location = game_world[coords]
        return f"📍 **{location['name']}** (مختصات: {coords})\n\n{location['description']}"
    return "شما در یک مکان ناشناخته هستید."

# --- کنترل‌کننده‌های دستورات (Command Handlers) ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """نقطه ورود اصلی کاربر به ربات."""
    user_id = message.from_user.id
    if user_id in players:
        player = players[user_id]
        bot.send_message(message.chat.id,
                         get_location_text(player),
                         reply_markup=create_main_markup(player),
                         parse_mode='Markdown')
    else:
        welcome_text = (
            "به دنیای تهذیب و مانا خوش آمدید!\n\n"
            "برای شروع ماجراجویی، ابتدا باید مسیر قدرت خود را انتخاب کنید. "
            "این انتخاب، سرنوشت شما را رقم خواهد زد.\n\n"
            "پس از انتخاب، می‌توانید با دستور /setname [name] نام شخصیت خود را تعیین کنید."
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=create_start_markup())

@bot.message_handler(commands=['setname'])
def set_ingame_name(message):
    """دستور برای تغییر نام داخل بازی کاربر."""
    user_id = message.from_user.id
    if user_id in players:
        try:
            # جدا کردن نام از دستور
            new_name = message.text.split(maxsplit=1)[1]
            players[user_id].set_name(new_name)
            bot.reply_to(message, f"✅ نام شما با موفقیت به **{new_name}** تغییر کرد.", parse_mode='Markdown')
        except IndexError:
            bot.reply_to(message, "❌ لطفا نام مورد نظر را بعد از دستور وارد کنید.\nمثال: `/setname آرین`", parse_mode='Markdown')
    else:
        bot.reply_to(message, "شما هنوز بازی را شروع نکرده‌اید! لطفاً ابتدا دستور /start را بزنید.")


# --- کنترل‌کننده اصلی دکمه‌ها (Callback Query Handler) ---

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    user_id = call.from_user.id
    
    # --- پردازش انتخاب مسیر اولیه (برای بازیکنان جدید) ---
    if call.data.startswith("choose_"):
        if user_id in players:
            bot.answer_callback_query(call.id, "شما قبلاً مسیر خود را انتخاب کرده‌اید!", show_alert=True)
            return
        
        path = "تهذیب" if call.data == "choose_tahzib" else "مانا"
        
        # ساخت یک شیء جدید از کلاس Player و ذخیره آن
        new_player = Player(user_id=user_id, telegram_name=call.from_user.first_name, path=path)
        players[user_id] = new_player
        
        bot.answer_callback_query(call.id, f"مسیر {path} با موفقیت انتخاب شد.")
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=get_location_text(new_player),
                              reply_markup=create_main_markup(new_player),
                              parse_mode='Markdown')
        return

    # --- بررسی اینکه آیا بازیکن وجود دارد یا خیر (برای سایر دکمه‌ها) ---
    if user_id not in players:
        bot.answer_callback_query(call.id, "خطا! لطفاً با دستور /start ربات را مجدداً راه‌اندازی کنید.", show_alert=True)
        return

    player = players[user_id]

    # --- پردازش حرکت ---
    if call.data.startswith("move_"):
        direction = call.data.split("_")[1]
        moved = player.move(direction) # فرض می‌کنیم متد move در کلاس Player پیاده‌سازی شده
        
        if moved:
            bot.answer_callback_query(call.id, f"حرکت به سمت {direction}")
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=get_location_text(player),
                                  reply_markup=create_main_markup(player),
                                  parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, "شما نمی‌توانید از این طرف بروید! 🚧", show_alert=True)

    # --- پردازش اقدامات اصلی ---
    elif call.data == "action":
        xp_gain = 25  # مقدار XP دریافتی برای هر تمرین
        player.add_xp(xp_gain)
        bot.answer_callback_query(call.id, f"+{xp_gain} XP")
        # ویرایش پیام برای نمایش دکمه Breakthrough در صورت امکان
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=get_location_text(player),
                              reply_markup=create_main_markup(player),
                              parse_mode='Markdown')

    elif call.data == "breakthrough":
        if player.can_breakthrough():
            result = player.perform_breakthrough() # فرض بر وجود این متد در کلاس Player
            bot.answer_callback_query(call.id, "موفقیت بزرگ!", show_alert=True)
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text=f"🎉 **{result}** 🎉\n\n{get_location_text(player)}",
                                  reply_markup=create_main_markup(player),
                                  parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, "هنوز آماده نیستی!", show_alert=True)

    elif call.data == "show_status":
        bot.answer_callback_query(call.id)
        # نمایش وضعیت کامل در یک پیام جدید برای خوانایی بهتر
        bot.send_message(call.message.chat.id, player.get_status_text(), parse_mode='Markdown')

    # --- بخش‌های مربوط به کوئست و مهارت‌ها (در حال حاضر پیام موقت نمایش می‌دهند) ---
    elif call.data == "show_quests":
        bot.answer_callback_query(call.id, "سیستم کوئست به زودی اضافه خواهد شد!", show_alert=True)
    
    elif call.data == "show_skills":
        bot.answer_callback_query(call.id, "سیستم مهارت‌ها به زودی اضافه خواهد شد!", show_alert=True)


# --- بخش مربوط به هاستینگ در Render (بدون تغییر) ---
# این بخش یک وب سرور سبک ایجاد می‌کند تا ربات در هاست رایگان Render همیشه فعال بماند

app = Flask(__name__)

@app.route('/')
def index():
    return "RPG Bot is alive!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # سرور Flask را در یک نخ (Thread) جداگانه اجرا کن
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # ربات تلگرام را برای همیشه در حال گوش دادن نگه دار
    print("Bot is running...")
    bot.polling(none_stop=True)

