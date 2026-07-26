FROM python:3.12-slim
WORKDIR /app
# OCR needs the Tesseract binary + Russian data (app/services/ocr.py uses lang="rus+eng").
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY pyproject.toml uv.lock ./
COPY . .
RUN uv sync --frozen
# Apply DB migrations, then start the bot. Module form (-m) is required so the
# absolute `app.*` imports resolve; running the script file directly does not
# put the project root on sys.path.
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync python -m app.bot.main"]
