from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User, Task

async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalars().first()
    if user:
        return user

    new_user = User(telegram_id=telegram_id, username=username)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user

async def add_task(session: AsyncSession, user_id: int, title: str) -> Task:
    task = Task(user_id=user_id, title=title)
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def get_tasks(session: AsyncSession, user_id: int) -> list[Task]:
    result = await session.execute(
        select(Task).where(Task.user_id == user_id)
    )
    return result.scalars().all()

async def complete_task(session: AsyncSession, task_id: int, user_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if task:
        task.is_completed = True
        await session.commit()
    return task

async def delete_task(session: AsyncSession, task_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if task:
        await session.delete(task)
        await session.commit()
        return True
    return False