import asyncio
import logging
import sys
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.setup import init_db
from handlers import common, schedule, admin

from services.scheduler import start_scheduler

# Load environment variables
load_dotenv()

# Config
TOKEN = getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Dispatcher
dp = Dispatcher()

async def main() -> None:
    # Initialize Bot instance
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Init DB
    await init_db()
    
    # Register routers
    dp.include_router(common.router)
    dp.include_router(schedule.router)
    dp.include_router(admin.router)

    # Start Scheduler
    start_scheduler(bot)

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
