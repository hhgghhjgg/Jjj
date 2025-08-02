import logging
import nest_asyncio
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import database
import handlers

# اعمال پچ برای اجرا در محیط‌هایی مانند کولب
nest_asyncio.apply()

# تنظیمات اولیه لاگ برای نمایش خطاها
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

def main() -> None:
    """راه‌اندازی و اجرای ربات."""
    
    # ۱. اول از همه، پایگاه داده را راه‌اندازی کن
    database.init_db()
    
    # ۲. توکن را از متغیرهای محیطی بخوان
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # بررسی وجود توکن
    if not TOKEN:
        print("خطا: توکن تلگرام در متغیرهای محیطی یافت نشد.")
        return

    # ۳. ربات را بساز
    application = Application.builder().token(TOKEN).build()

    # ۴. پردازشگرها را از فایل handlers.py ثبت کن
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_handler))
    
    # ۵. ربات را اجرا کن
    print("ربات با موفقیت در حال اجراست...")
    application.run_polling()

if __name__ == '__main__':
    main()
