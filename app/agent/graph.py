from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_cerebras import ChatCerebras

SYSTEM_PROMPT = (
    "Ты — личный ассистент в Telegram. Помогаешь вести задачи и учитывать траты. Отвечай кратко, по-русски."
)

# Краткосрочная память диалога живёт здесь (в процессе), отдельная на каждого
# пользователя по thread_id. Долгосрочная память — это эмбеддинги в БД.
checkpointer = InMemorySaver()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def build_graph(tools: list):
    llm = ChatCerebras(model="gemma-4-31b")  # Cerebras-hosted Gemma 4 31B
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: AgentState) -> AgentState:
        # Системный промпт не храним в состоянии — подставляем на каждый вызов LLM.
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)  # tool_calls? -> tools, иначе -> END
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
