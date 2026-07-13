"""Service layer between the HTTP API and the LangGraph agent."""

from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.graph import get_research_agent


@dataclass
class AgentReply:
    answer: str
    plan: str
    tools_used: list[str]


async def generate_reply(message: str) -> AgentReply:
    """Run one complete Agent turn and extract data suitable for the API response."""
    graph = get_research_agent()
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config={"recursion_limit": 12},
    )
    messages = result["messages"]
    answer = next(
        (
            str(item.content)
            for item in reversed(messages)
            if isinstance(item, AIMessage) and not item.tool_calls
        ),
        "Agent 没有返回最终回答，请重试。",
    )
    tools_used = [item.name for item in messages if isinstance(item, ToolMessage)]
    return AgentReply(answer=answer, plan=result.get("plan", "未生成计划。"), tools_used=tools_used)
