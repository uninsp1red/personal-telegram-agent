from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import User

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