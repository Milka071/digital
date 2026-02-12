from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from datetime import datetime

from database.setup import async_session
from database.models import User, Schedule, ClassGroup

router = Router()

WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

@router.message(Command("schedule"))
async def get_schedule(message: Message):
    async with async_session() as session:
        # Get user
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Сначала выбери класс! (Функция выбора класса будет позже)")
            return

        # Simple logic: get today's schedule
        today = datetime.now().weekday()
        
        # if Sunday (6), show Monday (0)
        target_day = 0 if today == 6 else today
        
        lessons = (await session.execute(
            select(Schedule).where(
                Schedule.class_group_id == user.class_group_id,
                Schedule.day_of_week == target_day
            ).order_by(Schedule.lesson_number)
        )).scalars().all()
        
        if not lessons:
            await message.answer(f"На {WEEKDAYS[target_day]} расписания нет.")
            return

        text = [f"📅 <b>Расписание на {WEEKDAYS[target_day]}</b>\n"]
        for lesson in lessons:
            text.append(f"{lesson.lesson_number}. {lesson.subject_name}")
            
        await message.answer("\n".join(text))

@router.message(Command("schedule_day"))
async def get_schedule_day(message: Message):
    """Get schedule for specific day"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /schedule_day [день 0-6]\n0=Понедельник, 1=Вторник, ..., 6=Воскресенье")
        return
    
    try:
        target_day = int(args[1])
        if target_day < 0 or target_day > 6:
            raise ValueError()
    except ValueError:
        await message.answer("День должен быть числом от 0 до 6 (0=Понедельник, 6=Воскресенье)")
        return
    
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Сначала выбери класс! Используйте /join_class [название]")
            return
        
        lessons = (await session.execute(
            select(Schedule).where(
                Schedule.class_group_id == user.class_group_id,
                Schedule.day_of_week == target_day
            ).order_by(Schedule.lesson_number)
        )).scalars().all()
        
        if not lessons:
            await message.answer(f"На {WEEKDAYS[target_day]} расписания нет.")
            return

        text = [f"📅 <b>Расписание на {WEEKDAYS[target_day]}</b>\n"]
        for lesson in lessons:
            text.append(f"{lesson.lesson_number}. {lesson.subject_name}")
            
        await message.answer("\n".join(text))
