from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from app.models.session import get_db
from app.models.crud import get_or_create_user, add_task, get_tasks, complete_task, delete_task

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    async with get_db() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)
    await message.answer("Привет! Я бот для управления задачами.")

@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "Вот список доступных команд:\n"
        "/start - начать работу с ботом\n"
        "/help - показать это сообщение\n"
        "/add <название> - добавить новую задачу\n"
        "/list - показать все задачи\n"
        "/complete <id> - отметить задачу выполненной\n"
        "/delete <id> - удалить задачу\n"
    )
    await message.answer(help_text)

@router.message(Command("add"))
async def add_command(message: Message):
    task_title = message.get_args()
    if not task_title:
        await message.answer("Укажите название задачи: /add купить молоко")
        return

    async with get_db() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        task = await add_task(session, user.id, task_title)

    await message.answer(f"✅ Задача добавлена: {task.title}")

@router.message(Command("list"))
async def list_command(message: Message):
    async with get_db() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        tasks = await get_tasks(session, user.id)

    if not tasks:
        await message.answer("Задач нет. Добавьте первую: /add название")
        return

    lines = ["Ваши задачи:\n"]
    for task in tasks:
        status = "✅" if task.is_completed else "⬜"
        lines.append(f"{status} {task.id}. {task.title}")

    await message.answer("\n".join(lines))

@router.message(Command("complete"))
async def complete_command(message: Message):
    task_id_str = message.get_args()
    if not task_id_str or not task_id_str.isdigit():
        await message.answer("Укажите ID задачи: /complete 3")
        return

    async with get_db() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        task = await complete_task(session, int(task_id_str), user.id)

    if task:
        await message.answer(f"✅ Задача {task.id} выполнена: {task.title}")
    else:
        await message.answer(f"Задача {task_id_str} не найдена.")

@router.message(Command("delete"))
async def delete_command(message: Message):
    task_id_str = message.get_args()
    if not task_id_str or not task_id_str.isdigit():
        await message.answer("Укажите ID задачи: /delete 3")
        return

    async with get_db() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        success = await delete_task(session, int(task_id_str), user.id)

    if success:
        await message.answer(f"🗑 Задача {task_id_str} удалена.")
    else:
        await message.answer(f"Задача {task_id_str} не найдена.")