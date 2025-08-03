# =================================================================
#               player.py - The Player Class Model
#
# این فایل کلاس Player را تعریف می‌کند که هسته اصلی مدیریت وضعیت
# هر بازیکن در بازی است. هر شیء از این کلاس، یک بازیکن کامل
# با تمام ویژگی‌ها، آمار، موقعیت و منطق مربوط به خود است.
# =================================================================

# --- وارد کردن داده‌های ثابت بازی ---
# ما به این داده‌ها برای انجام محاسبات داخلی کلاس نیاز داریم
from gamedata import TITLES, CULTIVATION_PATHS, game_world

class Player:
    """
    این کلاس، یک بازیکن در دنیای بازی را با تمام ویژگی‌هایش نشان می‌دهد.
    """
    def __init__(self, user_id: int, telegram_name: str, path: str):
        # --- اطلاعات هویتی ---
        self.user_id = user_id                  # شناسه عددی تلگرام کاربر
        self.telegram_name = telegram_name      # نام کاربر در تلگرام
        self.in_game_name = telegram_name       # نام شخصیت در بازی (قابل تغییر با /setname)

        # --- سیستم پیشرفت (Progression) ---
        self.path = path                        # مسیر انتخابی: "تهذیب" یا "مانا"
        self.rank_index = 0                     # ایندکس رتبه فعلی در لیست رتبه‌ها (شروع از 0)
        self.xp = 0                             # میزان تجربه فعلی

        # --- موقعیت مکانی ---
        self.x = 0                              # مختصات X روی نقشه
        self.y = 0                              # مختصات Y روی نقشه

        # --- آمار و ویژگی‌ها (Attributes/Stats) ---
        self.stats = {
            'strength': 5,      # قدرت
            'agility': 5,       # چابکی
            'stamina': 100,     # استقامت
            'intelligence': 5   # هوش
        }
        self.attribute_points = 0 # امتیازاتی که پس از صعود به رتبه بالاتر برای تخصیص داده می‌شود

        # --- مهارت‌ها و کوئست‌ها ---
        self.learned_skills = []                # لیست مهارت‌های یاد گرفته شده
        self.active_quests = {}                 # دیکشنری کوئست‌های فعال
        self.completed_quests = []              # لیست کوئست‌های تمام شده

    # --- متدهای مربوط به پیشرفت و رتبه ---

    def get_rank_info(self) -> dict:
        """اطلاعات رتبه فعلی بازیکن را از gamedata استخراج می‌کند."""
        try:
            return CULTIVATION_PATHS[self.path][self.rank_index]
        except (KeyError, IndexError):
            # اگر بازیکن به بالاترین رتبه رسیده باشد
            return {"rank_name": "افسانه زنده", "xp_needed": float('inf')}

    def get_title(self) -> str:
        """لقب مناسب بازیکن را بر اساس رتبه او پیدا می‌کند."""
        current_title = "بی‌لقب"
        for rank_req, title in TITLES.items():
            if self.rank_index >= rank_req:
                current_title = title
        return current_title

    def add_xp(self, amount: int):
        """مقدار مشخصی تجربه به بازیکن اضافه می‌کند."""
        self.xp += amount

    def can_breakthrough(self) -> bool:
        """بررسی می‌کند که آیا XP بازیکن برای صعود به رتبه بعدی کافی است یا خیر."""
        rank_info = self.get_rank_info()
        return self.xp >= rank_info['xp_needed']

    def perform_breakthrough(self) -> str:
        """عملیات صعود به رتبه بعدی را انجام می‌دهد."""
        if self.can_breakthrough():
            self.rank_index += 1
            self.xp = 0  # ریست کردن تجربه پس از صعود
            self.attribute_points += 1 # جایزه: یک امتیاز ویژگی
            
            new_rank_info = self.get_rank_info()
            return f"شما با موفقیت به رتبه {new_rank_info['rank_name']} صعود کردید!"
        return "شرایط لازم برای صعود را ندارید."

    # --- متدهای مربوط به اقدامات بازیکن ---

    def set_name(self, new_name: str):
        """نام داخل بازی بازیکن را تغییر می‌دهد."""
        self.in_game_name = new_name

    def move(self, direction: str) -> bool:
        """بازیکن را در جهت مشخص شده حرکت می‌دهد و موفقیت‌آمیز بودن حرکت را برمی‌گرداند."""
        new_x, new_y = self.x, self.y

        if direction == "up": new_y += 1
        elif direction == "down": new_y -= 1
        elif direction == "left": new_x -= 1
        elif direction == "right": new_x += 1

        # بررسی اینکه آیا مختصات جدید در نقشه بازی معتبر است یا خیر
        if (new_x, new_y) in game_world:
            self.x, self.y = new_x, new_y
            return True # حرکت موفقیت‌آمیز بود
        return False # حرکت ناموفق بود

    def get_status_text(self) -> str:
        """یک متن کامل و فرمت‌شده از وضعیت فعلی بازیکن را تولید می‌کند."""
        rank_info = self.get_rank_info()
        status_message = (
            f"👤 **نام:** {self.in_game_name}\n"
            f"🎖 **لقب:** {self.get_title()}\n\n"
            f"⚔️ **مسیر:** {self.path}\n"
            f"💠 **رتبه:** {rank_info['rank_name']}\n"
            f"✨ **تجربه (XP):** {self.xp} / {rank_info['xp_needed']}\n\n"
            f"**----- آمار -----**\n"
            f"💪 **قدرت:** {self.stats['strength']}\n"
            f"🏃‍♂️ **چابکی:** {self.stats['agility']}\n"
            f"❤️ **استقامت:** {self.stats['stamina']}\n"
            f"🧠 **هوش:** {self.stats['intelligence']}\n"
        )
        if self.attribute_points > 0:
            status_message += f"\n**⭐️ شما {self.attribute_points} امتیاز ویژگی برای تخصیص دارید!**"
        
        return status_message

