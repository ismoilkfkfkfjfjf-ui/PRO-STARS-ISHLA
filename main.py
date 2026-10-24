import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, PORT
import database as db
from handlers import user, withdraw, admin
from keep_alive import start_web_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN topilmadi! Iltimos, .env faylini tekshiring.")
        return

    # Initialize SQLite database (WAL mode for blazing speed)
    logging.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    await db.init_db()

    # Bot & Dispatcher setup
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers (order: admin -> withdraw -> user)
    dp.include_router(admin.router)
    dp.include_router(withdraw.router)
    dp.include_router(user.router)

    # Start healthcheck server for Render 24/7 web service
    try:
        await start_web_server(PORT)
    except Exception as e:
        logging.warning(f"Web serverni ishga tushirishda ogohlantirish: {e}")

    bot_info = await bot.get_me()
    logging.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} (ID: {bot_info.id})")

    # Start polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
