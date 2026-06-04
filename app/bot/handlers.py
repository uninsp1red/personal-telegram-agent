from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.models.session import get_db
from app.models.crud import get_or_create_user

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    async for session in get_db():
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        break
    await message.answer("Привет! Я бот для управления задачами.")

@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "Вот список доступных команд:\n"
        "/start - начать работу с ботом\n"
        "/help - показать это сообщение\n"
        "/add - добавить новую задачу\n"
        "/list - показать все задачи\n"
        "/delete - удалить задачу\n"
    )
    await message.answer(help_text)