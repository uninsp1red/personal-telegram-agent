FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY . .
RUN pip install uv 
RUN uv sync
CMD ["uv", "run", "app/bot/main.py"]