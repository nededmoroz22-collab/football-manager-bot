import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")

from .db import init_db_pool
from .handlers import router

async def on_startup(bot: Bot, dp: Dispatcher):
    await init_db_pool()
    # можно добавить другие init действия

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    # Startup
    await on_startup(bot, dp)
    print("Bot started (polling).")
    try:
        await dp.start_polling(bot, allowed_updates=[])
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())