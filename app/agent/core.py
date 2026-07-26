from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from app.agent.tools import make_agent_tools
from app.agent.graph import build_graph
from app.services.embeddings import embed_with_retry
from app.models import crud
from app.models.session import get_db

# После стольких сообщений короткая память (langgraph) обнуляется в долгую (эмбеддинги в БД).
SHORT_TERM_LIMIT = 10


async def invoke(user_id: int, message: str, receipt_id: int | None = None) -> str:
    tools = make_agent_tools(user_id=user_id, receipt_id=receipt_id)
    graph = build_graph(tools)
    config = {"configurable": {"thread_id": str(user_id)}}

    # Короткая память диалога хранится в langgraph (checkpointer, thread на юзера) —
    # передаём только новое сообщение, историю подставит checkpointer.
    result = await graph.ainvoke({"messages": [HumanMessage(content=message)]}, config=config)
    reply = result["messages"][-1].content

    await _flush_if_full(user_id, graph, config, result["messages"])
    return reply


async def _flush_if_full(user_id: int, graph, config: dict, messages: list) -> None:
    """Когда диалог дорос до SHORT_TERM_LIMIT сообщений — эмбеддим его ОДНИМ
    батч-запросом в долгую память (БД) и обнуляем короткую память langgraph."""
    conv = [
        m for m in messages
        if isinstance(m, (HumanMessage, AIMessage))
        and isinstance(m.content, str) and m.content.strip()
    ]
    if len(conv) < SHORT_TERM_LIMIT:
        return

    vectors = await embed_with_retry([m.content for m in conv], input_type="document")
    entries = [
        ("user" if isinstance(m, HumanMessage) else "assistant", m.content, vec)
        for m, vec in zip(conv, vectors)
    ]
    async with get_db() as session:
        await crud.save_messages_batch(session, user_id, entries)

    # Обнуляем короткую память: удаляем все сообщения из состояния thread'а.
    await graph.aupdate_state(config, {"messages": [RemoveMessage(id=m.id) for m in messages]})
