import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.setup import async_session
from database.models import User, ClassGroup

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    logging.info(f"Received /start from user {message.from_user.id}: {message.from_user.full_name}")
    
    try:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
            user = result.scalar_one_or_none()

            if not user:
                new_user = User(
                    telegram_id=message.from_user.id,
                    full_name=message.from_user.full_name
                )
                session.add(new_user)
                await session.commit()
                
                # Create main menu
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📋 Команды")],
                        [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="📖 Домашка")],
                        [KeyboardButton(text="🏫 Мой класс"), KeyboardButton(text="⚙️ Управление")]
                    ],
                    resize_keyboard=True
                )
                
                await message.answer(
                    "🎉 <b>Добро пожаловать в Школьного Бота!</b>\n\n"
                    "Я помогу тебе с расписанием и домашними заданиями.\n"
                    "Нажми '📋 Команды' или используй /help чтобы увидеть все возможности.",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # Create main menu for existing users
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📋 Команды")],
                        [KeyboardButton(text="📚 Расписание"), KeyboardButton(text="📖 Домашка")],
                        [KeyboardButton(text="🏫 Мой класс"), KeyboardButton(text="⚙️ Управление")]
                    ],
                    resize_keyboard=True
                )
                
                await message.answer(
                    f"👋 <b>С возвращением, {message.from_user.full_name}!</b>\n\n"
                    "Выбери действие из меню или введи /help",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
    except Exception as e:
        logging.error(f"Error in /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(Command("help"))
async def help_command(message: Message):
    """Show help message with all available commands"""
    help_text = """
📚 <b>Справочник команд Школьного Бота:</b>

🔹 <b>🎯 Основные команды:</b>
/start - Регистрация в боте
/help - Показать эту справку
/schedule - Расписание на сегодня
/schedule_day [день] - Расписание на конкретный день (0=Пн, 6=Вс)
/hw - Показать домашние задания

🔹 <b>🏫 Классы:</b>
/join_class [название] - Присоединиться к классу
/create_class [название] - Создать новый класс

🔹 <b>⚙️ Управление расписанием:</b>
/add_schedule [день] [урок] [предмет] - Добавить урок
/remove_schedule [день] [урок] - Удалить урок

🔹 <b>📖 Управление ДЗ:</b>
/add_hw [предмет] [задание] - Добавить домашнее задание
/remove_hw [предмет] - Удалить домашнее задание

🔹 <b>📅 Дни недели (цифры):</b>
0 - Понедельник
1 - Вторник  
2 - Среда
3 - Четверг
4 - Пятница
5 - Суббота
6 - Воскресенье

💡 <b>Подсказка:</b> Используй кнопки в главном меню для быстрого доступа!
    """
    
    await message.answer(help_text, parse_mode="HTML")

@router.message(F.text == "📋 Команды")
async def commands_button(message: Message):
    await help_command(message)

@router.message(F.text == "📚 Расписание")
async def schedule_button(message: Message):
    """Handle schedule button"""
    try:
        async with async_session() as session:
            user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
            
            if not user or not user.class_group_id:
                await message.answer("Сначала выбери класс! Используйте /join_class [название] или кнопку '🏫 Мой класс'")
                return

            from datetime import datetime
            
            today = datetime.now().weekday()
            target_day = 0 if today == 6 else today
            
            from database.models import Schedule
            
            lessons = (await session.execute(
                select(Schedule).where(
                    Schedule.class_group_id == user.class_group_id,
                    Schedule.day_of_week == target_day
                ).order_by(Schedule.lesson_number)
            )).scalars().all()
            
            if not lessons:
                await message.answer(f"На сегодня расписания нет.")
                return

            WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            text = [f"📅 <b>Расписание на {WEEKDAYS[target_day]}</b>\n"]
            for lesson in lessons:
                text.append(f"{lesson.lesson_number}. {lesson.subject_name}")
                
            await message.answer("\n".join(text), parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in schedule_button: {e}")
        await message.answer("Произошла ошибка при загрузке расписания.")

@router.message(F.text == "📖 Домашка")
async def homework_button(message: Message):
    """Handle homework button"""
    try:
        async with async_session() as session:
            user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
            
            if not user or not user.class_group_id:
                await message.answer("Сначала выбери класс! Используйте /join_class [название] или кнопку '🏫 Мой класс'")
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
                
            await message.answer("\n".join(text), parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in homework_button: {e}")
        await message.answer("Произошла ошибка при загрузке домашних заданий.")

@router.message(F.text == "🏫 Мой класс")
async def my_class_button(message: Message):
    """Handle my class button"""
    try:
        async with async_session() as session:
            user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
            
            if not user:
                await message.answer("Сначала зарегистрируйтесь командой /start")
                return
            
            if not user.class_group_id:
                # Show available classes
                classes = (await session.execute(select(ClassGroup))).scalars().all()
                if classes:
                    text = ["🏫 <b>Доступные классы:</b>\n"]
                    for cls in classes:
                        text.append(f"• {cls.name}")
                    text.append("\nИспользуй /join_class [название] чтобы присоединиться")
                    await message.answer("\n".join(text), parse_mode="HTML")
                else:
                    await message.answer("Классы еще не созданы. Используй /create_class [название] для создания класса.")
                return
            
            # Show current class info
            class_group = (await session.execute(
                select(ClassGroup).where(ClassGroup.id == user.class_group_id)
            )).scalar_one_or_none()
            
            await message.answer(
                f"🏫 <b>Твой класс: {class_group.name if class_group else 'Неизвестен'}</b>\n\n"
                f"👤 Роль: {user.role}\n\n"
                f"Используй /join_class [название] чтобы сменить класс",
                parse_mode="HTML"
            )
    except Exception as e:
        logging.error(f"Error in my_class_button: {e}")
        await message.answer("Произошла ошибка при загрузке информации о классе.")

@router.message(F.text == "⚙️ Управление")
async def management_button(message: Message):
    """Handle management button"""
    management_text = """
⚙️ <b>Управление:</b>

📅 <b>Расписание:</b>
• /add_schedule [день] [урок] [предмет]
• /remove_schedule [день] [урок]

📚 <b>Домашние задания:</b>  
• /add_hw [предмет] [задание]
• /remove_hw [предмет]

🏫 <b>Классы:</b>
• /create_class [название]
• /join_class [название]

📅 <b>Дни недели:</b>
0 - Понедельник, 1 - Вторник, ..., 6 - Воскресенье
    """
    
    await message.answer(management_text, parse_mode="HTML")

@router.message(Command("join_class"))
async def join_class(message: Message):
    """Join a class by class name"""
    if not message.text:
        await message.answer("Ошибка: пустое сообщение")
        return
        
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /join_class [название_класса]")
        return
    
    class_name = args[1].strip()
    
    try:
        async with async_session() as session:
            # Find class
            class_group = (await session.execute(
                select(ClassGroup).where(ClassGroup.name == class_name)
            )).scalar_one_or_none()
            
            if not class_group:
                await message.answer(f"Класс '{class_name}' не найден. Доступные классы:")
                
                # Show available classes
                classes = (await session.execute(select(ClassGroup))).scalars().all()
                if classes:
                    class_list = "\n".join(f"• {cls.name}" for cls in classes)
                    await message.answer(class_list)
                else:
                    await message.answer("Классы еще не созданы.")
                return
            
            # Update user's class
            user = (await session.execute(select(User).where(User.telegram_id == message.from_user.id))).scalar_one_or_none()
            if user:
                user.class_group_id = class_group.id
                await session.commit()
                await message.answer(f"✅ Ты присоединился к классу '{class_name}'!")
            else:
                await message.answer("Сначала зарегистрируйтесь командой /start")
    except Exception as e:
        logging.error(f"Error in join_class: {e}")
        await message.answer("Произошла ошибка при присоединении к классу.")

@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_({"📋 Команды", "📚 Расписание", "📖 Домашка", "🏫 Мой класс", "⚙️ Управление"}))
async def handle_other_messages(message: Message):
    """Handle messages that don't match specific handlers"""
    logging.info(f"Unhandled message: {message.text}")
    await message.answer("Используйте кнопки меню или команду /help для справки")
