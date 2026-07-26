from langchain_core.tools import tool
from app.models import crud
from app.models.session import get_db
from app.services.embeddings import embed_with_retry


def make_agent_tools(user_id: int, receipt_id: int | None = None):
    """Фабрика тулов: user_id приходит из контекста бота, LLM его не видит и не выбирает."""

    @tool
    async def add_task(title: str) -> str:
        """Добавляет пользователю новую задачу по названию. Используй, когда
        пользователь просит запомнить дело или добавить в список задач."""
        async with get_db() as session:
            task = await crud.add_task(session, user_id=user_id, title=title)
        return f"Задача «{task.task_name}» добавлена (id={task.task_id})"

    @tool
    async def get_tasks(status: str = "pending") -> str:
        """Возвращает список задач пользователя. status — 'pending' (невыполненные,
        по умолчанию), 'done' (выполненные) или 'all' (все задачи)."""
        async with get_db() as session:
            tasks = await crud.get_tasks(session, user_id=user_id)
        if status != "all":
            tasks = [t for t in tasks if t.status == status]
        if not tasks:
            return "Задач нет."
        return "\n".join(f"[{t.task_id}] {t.task_name} — {t.status}" for t in tasks)

    @tool
    async def complete_task(task_id: int) -> str:
        """Отмечает задачу выполненной по её id. Id узнаётся заранее через get_tasks —
        не выдумывай id сам."""
        async with get_db() as session:
            task = await crud.complete_task(session, task_id=task_id, user_id=user_id)
        if task is None:
            return f"Задача с id={task_id} не найдена."
        return f"Задача «{task.task_name}» отмечена выполненной"

    @tool
    async def delete_task(task_id: int) -> str:
        """Удаляет задачу по её id. Необратимо — используй только если пользователь
        явно попросил удалить, а не просто выполнить."""
        async with get_db() as session:
            ok = await crud.delete_task(session, task_id=task_id, user_id=user_id)
        if not ok:
            return f"Задача с id={task_id} не найдена."
        return f"Задача с id={task_id} удалена"

    @tool
    async def save_spending(name: str, category: str, amount: float) -> str:
        """Сохраняет одну трату. Если распознаёшь несколько позиций в чеке —
        вызови этот тул отдельно на каждую позицию. Если пользователь просто
        написал "потратил 300 на такси" без чека — вызови один раз.
        category — одна из: продукты, транспорт, кафе, одежда, развлечения, другое."""
        async with get_db() as session:
            spending = await crud.add_spending(
                session, user_id=user_id, receipt_id=receipt_id,
                name=name, category=category, amount=amount,
            )
        return f"Записано: {spending.spending_name} — {spending.amount} ₽"

    @tool
    async def recall_history(query: str) -> str:
        """Ищет в истории переписки сообщения, семантически похожие на запрос.
        Используй, когда пользователь ссылается на давний разговор, который не
        поместился в последние сообщения текущего диалога — например
        "а что я говорил про отпуск" или "напомни что мы решили насчёт машины"."""
        vectors = await embed_with_retry([query], input_type="query")  # query, не document!

        async with get_db() as session:
            messages = await crud.search_history(
                session, user_id=user_id, query_embedding=vectors[0], limit=5,
            )

        if not messages:
            return "Ничего похожего в истории не нашлось."

        return "\n".join(
            f"[{m.created_at:%d.%m %H:%M}] {m.role}: {m.content}" for m in messages
        )

    return [add_task, get_tasks, complete_task, delete_task, save_spending, recall_history]