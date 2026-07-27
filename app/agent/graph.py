from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langchain_cerebras import ChatCerebras
import os
from datetime import datetime
from zoneinfo import ZoneInfo

SYSTEM_PROMPT = (
    "Ты — личный ассистент в Telegram. Помогаешь вести задачи и учитывать траты. Отвечай кратко, по-русски."
)

checkpointer = InMemorySaver()


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def build_graph(tools: list, tz: str = "UTC"):
    llm = ChatCerebras(model="gemma-4-31b", api_key=os.getenv("CEREBRAS_API_KEY"))  
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: AgentState) -> AgentState:
        now_local = datetime.now(ZoneInfo(tz))
        prompt = (
            f"{SYSTEM_PROMPT}\n"
            f"Часовой пояс пользователя: {tz}. Текущее локальное время: {now_local:%Y-%m-%d %H:%M}. "
            f"Время в напоминаниях указывай в этом локальном времени. Если пояс UTC "
            f"(не задан) и пользователь просит напоминание — сначала уточни город/часовой "
            f"пояс и сохрани через set_timezone."
        )
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition) 
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=checkpointer)
