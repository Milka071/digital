from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.setup import async_session
from database.models import User, ClassGroup

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
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
            await message.answer("Привет! Ты зарегистрирован. Теперь выбери свой класс (пока эта функция в разработке).")
        else:
            await message.answer("С возвращением!")

@router.message(Command("join_class"))
async def join_class(message: Message):
    """Join a class by class name"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /join_class [название_класса]")
        return
    
    class_name = args[1].strip()
    
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
