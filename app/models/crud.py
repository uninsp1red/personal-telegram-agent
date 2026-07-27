from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models.models import User, Task, Receipt, Spending, ConversationHistory, MessageSchedule
from datetime import datetime


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


async def get_user_timezone(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User.timezone).where(User.id == user_id))
    return result.scalar_one_or_none() or "UTC"


async def set_user_timezone(session: AsyncSession, user_id: int, timezone: str) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(timezone=timezone)
    )
    await session.commit()

async def add_task(session: AsyncSession, user_id: int, title: str) -> Task:
    task = Task(user_id=user_id, task_name=title)
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
        select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if task:
        task.status = "done"
        await session.commit()
    return task

async def delete_task(session: AsyncSession, task_id: int, user_id: int) -> bool:
    result = await session.execute(
        select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
    )
    task = result.scalars().first()
    if task:
        await session.delete(task)
        await session.commit()
        return True
    return False

async def create_receipt(session: AsyncSession, user_id: int, raw_text: str) -> Receipt:
    receipt = Receipt(user_id=user_id, raw_text=raw_text)
    session.add(receipt)
    await session.commit()
    await session.refresh(receipt)
    return receipt

async def add_spending(
    session: AsyncSession,
    user_id: int,
    name: str,
    category: str,
    amount: float,
    receipt_id: int | None = None,
) -> Spending:
    spending = Spending(
        user_id=user_id,
        receipt_id=receipt_id,
        spending_name=name,
        spending_category=category,
        amount=amount,
    )
    session.add(spending)
    await session.commit()
    await session.refresh(spending)
    return spending

async def save_messages_batch(
    session: AsyncSession,
    user_id: int,
    messages: list[tuple[str, str, list[float] | None]],
) -> list[ConversationHistory]:
    """Одним коммитом сохраняет несколько сообщений. messages — (role, content, embedding)."""
    rows = [
        ConversationHistory(user_id=user_id, role=role, content=content, embedding=embedding)
        for role, content, embedding in messages
    ]
    session.add_all(rows)
    await session.commit()
    return rows

async def search_history(
    session: AsyncSession, user_id: int, query_embedding: list[float], limit: int = 5,
) -> list[ConversationHistory]:
    result = await session.execute(
        select(ConversationHistory)
        .where(
            ConversationHistory.user_id == user_id,
            ConversationHistory.embedding.is_not(None),
        )
        .order_by(ConversationHistory.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())

async def create_schedule(
    session: AsyncSession, user_id: int, title: str, time_to_send: datetime, task_id: int | None = None,
) -> MessageSchedule:
    schedule = MessageSchedule(
        user_id=user_id, task_id=task_id, title=title, time_to_send=time_to_send, status="pending",
    )
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return schedule

async def get_due_schedules(session: AsyncSession, before: datetime) -> list[MessageSchedule]:
    result = await session.execute(
        select(MessageSchedule)
        .options(selectinload(MessageSchedule.user))
        .where(
            MessageSchedule.status == "pending", MessageSchedule.time_to_send <= before,
        )
    )
    return list(result.scalars().all())

async def mark_sent(session: AsyncSession, schedule_id: int) -> None:
    await session.execute(
        update(MessageSchedule).where(MessageSchedule.id == schedule_id).values(status="sent")
    )
    await session.commit()


async def get_user_schedules(
    session: AsyncSession, user_id: int, status: str = "pending",
) -> list[MessageSchedule]:
    result = await session.execute(
        select(MessageSchedule)
        .where(MessageSchedule.user_id == user_id, MessageSchedule.status == status)
        .order_by(MessageSchedule.time_to_send)
    )
    return list(result.scalars().all())


async def cancel_schedule(session: AsyncSession, schedule_id: int, user_id: int) -> bool:
    result = await session.execute(
        update(MessageSchedule)
        .where(
            MessageSchedule.id == schedule_id,
            MessageSchedule.user_id == user_id,
            MessageSchedule.status == "pending",
        )
        .values(status="cancelled")
    )
    await session.commit()
    return result.rowcount > 0