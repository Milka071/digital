from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database.setup import async_session
from database.models import User, Schedule, ClassGroup

router = Router()

# Simple text-based schedule adder for MVP
# Format: /add_schedule [day_num 0-6] [lesson_num] [subject]
# Example: /add_schedule 0 1 Algebra
@router.message(Command("add_schedule"))
async def add_schedule(message: Message):
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.answer("Использование: /add_schedule [день 0-6] [урок №] [предмет]")
        return
    
    try:
        day = int(args[1])
        lesson_num = int(args[2])
        subject = args[3]
    except ValueError:
        await message.answer("День и номер урока должны быть числами.")
        return

    async with async_session() as session:
        # Check permissions (simplified: anyone registered as headman or just first user for now)
        # For MVP, assuming the user has class_group_id
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Ты не привязан к классу.")
            return

        # Create or update schedule
        # Check if exists
        existing_sub = (await session.execute(
            select(Schedule).where(
                Schedule.class_group_id == user.class_group_id,
                Schedule.day_of_week == day,
                Schedule.lesson_number == lesson_num
            )
        )).scalar_one_or_none()

        if existing_sub:
            existing_sub.subject_name = subject
        else:
            new_sch = Schedule(
                class_group_id=user.class_group_id,
                day_of_week=day,
                lesson_number=lesson_num,
                subject_name=subject
            )
            session.add(new_sch)
        
        await session.commit()
        await message.answer(f"✅ Урок добавлен: День {day}, Урок {lesson_num} - {subject}")

@router.message(Command("add_hw"))
async def add_homework(message: Message):
    # Format: /add_hw [subject] [text]
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /add_hw [предмет] [задание]")
        return
    
    subject = args[1]
    content = args[2]

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Ты не привязан к классу.")
            return

        # Simplified: Just create a new homework entry for "today" or "next lesson"
        # For this MVP, we just store it. Logic to find "next lesson" is needed but complex.
        # We will assume it's for the next occurrence of this subject.
        
        from database.models import Homework
        from datetime import datetime
        
        new_hw = Homework(
            class_group_id=user.class_group_id,
            subject_name=subject,
            content=content,
            date_assigned=datetime.now().isoformat()
        )
        session.add(new_hw)
        await session.commit()
        await message.answer(f"✅ ДЗ по {subject} добавлено: {content}")

@router.message(Command("hw"))
async def view_homework(message: Message):
    """View all homework for the user's class"""
    if not message.from_user:
        await message.answer("Ошибка: не удалось определить пользователя")
        return
        
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Ты не привязан к классу.")
            return

        from database.models import Homework
        
        homeworks = (await session.execute(
            select(Homework).where(
                Homework.class_group_id == user.class_group_id
            ).order_by(Homework.date_assigned.desc())
        )).scalars().all()
        
        if not homeworks:
            await message.answer("Домашних заданий нет.")
            return

        text = ["📚 <b>Домашние задания:</b>\n"]
        for hw in homeworks:
            text.append(f"📖 <b>{hw.subject_name}</b> ({hw.date_assigned})")
            text.append(f"   {hw.content}")
            text.append("")
            
        await message.answer("\n".join(text))

@router.message(Command("create_class"))
async def create_class(message: Message):
    """Create a new class"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /create_class [название_класса]")
        return
    
    class_name = args[1].strip()
    
    async with async_session() as session:
        # Check if class already exists
        existing_class = (await session.execute(
            select(ClassGroup).where(ClassGroup.name == class_name)
        )).scalar_one_or_none()
        
        if existing_class:
            await message.answer(f"Класс '{class_name}' уже существует.")
            return
        
        # Create new class
        new_class = ClassGroup(name=class_name)
        session.add(new_class)
        await session.commit()
        await message.answer(f"✅ Класс '{class_name}' создан! Теперь можно присоединиться командой /join_class {class_name}")

@router.message(Command("remove_schedule"))
async def remove_schedule(message: Message):
    """Remove a lesson from schedule"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /remove_schedule [день 0-6] [урок №]")
        return
    
    try:
        day = int(args[1])
        lesson_num = int(args[2])
    except ValueError:
        await message.answer("День и номер урока должны быть числами.")
        return

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Ты не привязан к классу.")
            return

        # Find and delete the schedule
        schedule_item = (await session.execute(
            select(Schedule).where(
                Schedule.class_group_id == user.class_group_id,
                Schedule.day_of_week == day,
                Schedule.lesson_number == lesson_num
            )
        )).scalar_one_or_none()

        if not schedule_item:
            await message.answer(f"Урок на день {day}, номер {lesson_num} не найден.")
            return

        await session.delete(schedule_item)
        await session.commit()
        await message.answer(f"✅ Урок удален: День {day}, Урок {lesson_num}")

@router.message(Command("remove_hw"))
async def remove_homework(message: Message):
    """Remove homework by subject"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /remove_hw [предмет]")
        return
    
    subject = args[1]

    async with async_session() as session:
        user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
        
        if not user or not user.class_group_id:
            await message.answer("Ты не привязан к классу.")
            return

        from database.models import Homework
        
        # Find and delete homework
        homework = (await session.execute(
            select(Homework).where(
                Homework.class_group_id == user.class_group_id,
                Homework.subject_name == subject
            )
        )).scalar_one_or_none()

        if not homework:
            await message.answer(f"Домашнее задание по предмету '{subject}' не найдено.")
            return

        await session.delete(homework)
        await session.commit()
        await message.answer(f"✅ Домашнее задание по '{subject}' удалено.")
