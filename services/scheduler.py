import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy import select
from datetime import datetime

from database.setup import async_session
from database.models import User, ClassGroup, Schedule, Homework

scheduler = AsyncIOScheduler()

async def check_lessons(bot: Bot):
    """
    Checks if any lesson has just ended and sends notifications.
    This runs every minute.
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M") # e.g. "09:15"
    weekday = now.weekday() # 0-6

    # Mock schedule calls logic for MVP
    # Ideally this is stored in DB per ClassGroup
    # "09:15" -> End of 1st lesson
    # "10:10" -> End of 2nd lesson
    # For demo purposes, we will hardcode or use a simplified check
    
    # In a real app, we iterate all ClassGroups and check their schedule_config
    # For this MVP, let's pretend every class ends at X:15
    
    # Let's say we want to debug, so we iterate all classes
    async with async_session() as session:
        classes = (await session.execute(select(ClassGroup))).scalars().all()
        
        for class_group in classes:
            # Here we need to parse class_group.schedule_calls to see if NOW == end_of_lesson
            # But since that field is text JSON, let's assume a simplified static map for MVP
            
            # Example logic: Find what lesson is NEXT for this class
            # We need to know WHICH lesson just ended.
            
            # TODO: Implement robust time checking
            pass

    # Note: Implementing the full time-check logic requires robust data.
    # We will set up the skeleton.
    logging.info(f"Tick: {current_time_str}")

def start_scheduler(bot: Bot):
    scheduler.add_job(check_lessons, "interval", minutes=1, kwargs={"bot": bot})
    scheduler.start()
