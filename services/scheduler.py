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
    Checks for upcoming lessons and homework reminders.
    This runs every 5 minutes.
    """
    now = datetime.now()
    current_time_str = now.strftime("%H:%M") 
    weekday = now.weekday() # 0-6

    # Simple reminder times - you can customize these
    REMINDER_TIMES = ["08:00", "12:00", "15:00"]  # Morning, lunch, evening
    
    if current_time_str in REMINDER_TIMES:
        async with async_session() as session:
            classes = (await session.execute(select(ClassGroup))).scalars().all()
            
            for class_group in classes:
                # Get all users in this class
                users = (await session.execute(
                    select(User).where(User.class_group_id == class_group.id)
                )).scalars().all()
                
                if not users:
                    continue
                
                # Send homework reminder
                homeworks = (await session.execute(
                    select(Homework).where(
                        Homework.class_group_id == class_group.id
                    ).order_by(Homework.date_assigned.desc())
                )).scalars().all()
                
                if homeworks:
                    hw_text = ["📚 <b>Напоминание о домашних заданиях:</b>\n"]
                    for hw in homeworks[:3]:  # Limit to 3 recent homeworks
                        hw_text.append(f"📖 {hw.subject_name}: {hw.content}")
                    
                    # Send to all users in the class
                    for user in users:
                        try:
                            await bot.send_message(
                                user.telegram_id,
                                "\n".join(hw_text),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logging.error(f"Failed to send reminder to {user.telegram_id}: {e}")

    logging.info(f"Scheduler check: {current_time_str}")

def start_scheduler(bot: Bot):
    scheduler.add_job(check_lessons, "interval", minutes=5, kwargs={"bot": bot})
    scheduler.start()
