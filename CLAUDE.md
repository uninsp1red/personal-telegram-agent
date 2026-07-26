# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A personal Telegram bot ("personal-agent") for task management, written in Python 3.12 with **aiogram 3.x** (async), **SQLAlchemy 2.0 async** over **PostgreSQL** (asyncpg), and **Alembic** migrations. User-facing bot text is in Russian. Dependencies are managed with **uv** (`uv.lock`).

The database schema (`docs/shema.md`) anticipates more than is implemented: receipt/spending tracking and an AI conversation agent (`conversation_history`) and scheduled reminders (`message_schedule`) have tables but no code yet. `docker-compose.yml` also declares a Celery `worker` service and Redis, but `app/worker` does not exist. Treat these as planned, not present.

## Commands

```bash
uv sync                                   # install dependencies into .venv
uv run app/bot/main.py                    # run the bot (long-polling); imports are absolute (app.*), so run from repo root

uv run alembic revision --autogenerate -m "message"   # create a migration from model changes
uv run alembic upgrade head               # apply migrations
uv run alembic downgrade -1               # roll back one

docker compose up --build                 # bot + postgres (worker/redis services are aspirational)
```

There are no tests, linters, or formatters configured.

## Environment

Loaded from `.env` via `python-dotenv` (git-ignored). Required:

- `BOT_TOKEN` — Telegram bot token (`app/bot/main.py`)
- `DATABASE_URL` — **async** URL for the running bot, must use the asyncpg driver, e.g. `postgresql+asyncpg://...` (`app/models/session.py`)
- `DATABASE_URL_SYNC` — **sync** URL for Alembic, uses psycopg2, e.g. `postgresql+psycopg2://...` (`migrations/env.py`)
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` — used by docker-compose's postgres service

Note the two separate DB URLs: the app runs async (asyncpg) while Alembic runs sync (psycopg2). `alembic.ini`'s `sqlalchemy.url` is a placeholder — `migrations/env.py` overrides it with `DATABASE_URL_SYNC` at runtime.

## Architecture

- `app/bot/main.py` — entrypoint: builds `Bot`/`Dispatcher`, includes the router, `dp.start_polling`.
- `app/bot/handlers.py` — one `Router` with command handlers (`/start`, `/help`, `/add`, `/list`, `/complete`, `/delete`). Each handler opens a DB session via `async with get_db()` and calls a crud function.
- `app/models/session.py` — the async engine, `AsyncSessionLocal` sessionmaker, and the `get_db()` async context manager used by handlers.
- `app/models/crud.py` — all query logic (`get_or_create_user`, `add_task`, `get_tasks`, `complete_task`, `delete_task`). Handlers hold no SQL.
- `app/models/models.py` — declarative models. `Base` here is the metadata target for Alembic (`migrations/env.py` imports it).

Flow: handler → `get_db()` session → crud function → model. Every command first resolves the Telegram user via `get_or_create_user`, so users are lazily created on first interaction.

## Conventions

- `crud.py`/`handlers.py` must use the actual `Task` column names from `models.py`: `task_id` (PK), `task_name`, `status` (a string, `"done"` marks completion — not a boolean). There is no `Task.id`, `Task.title`, or `Task.is_completed`.
- Command arguments use the aiogram 3.x API: add a `command: CommandObject` parameter to the handler and read `command.args` (which is `None` when absent). Do not use the removed 2.x `message.get_args()`.
- When changing models, generate and apply an Alembic migration rather than editing the DB directly.
