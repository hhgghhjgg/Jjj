# file: main.py
import logging
import nest_asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import database
import handlers

nest_asyncio.apply()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main() -> None:
    database.init_db()
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    print("ربات سیستمی در حال اجراست...")
    application.run_polling()

if __name__ == '__main__':
    main()
