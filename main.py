import logging
from telegram.ext import Application
from handlers import get_conversation_handler
from db import init_db

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8383492223:AAH_MiAu-9Yfwy2WJNLF8fEwNeXzlx6J6N8"  # 🔑 replace with your bot token

def main():
    # 1. Initialize application
    application = Application.builder().token(TOKEN).build()

    # 2. Add conversation handler
    application.add_handler(get_conversation_handler())

    # 3. Attach DB pool asynchronously (accepts 'app' argument)
    async def attach_db(app: Application):
        pool = await init_db()
        app.bot_data["db_pool"] = pool

    application.post_init = attach_db  # run after bot initialization

    # 4. Run bot (handles its own asyncio loop)
    logger.info("Bot started...")
    application.run_polling()


if __name__ == "__main__":
    main()
