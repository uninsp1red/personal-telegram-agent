import os
import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.worker.celery_app import celery_app
from app.models import crud


logger = logging.getLogger(__name__)

@celery_app.task
def check_reminders():
    asyncio.run(_check_reminders())

async def _check_reminders():
    # Свой engine на каждый прогон: celery запускает задачу через asyncio.run()
    # (новый event loop каждый раз), поэтому общий engine из app.models.session
    # переиспользовать нельзя — asyncpg-коннекты привязаны к своему event loop.
    engine = create_async_engine(os.environ["DATABASE_URL"])
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    bot = Bot(token=os.environ["BOT_TOKEN"])
    try:
        async with Session() as session:
            due = await crud.get_due_schedules(session, before=datetime.now(timezone.utc))
            for schedule in due:
                try:
                    await bot.send_message(schedule.user.telegram_id, f"🔔 {schedule.title}")
                    await crud.mark_sent(session, schedule.id)
                except Exception:
                    logger.exception("failed to send reminder id=%s", schedule.id)
    finally:
        await bot.session.close()
        await engine.dispose()
