"""Service layer between the HTTP API and the LangGraph agent."""

from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agent.graph import get_research_agent
from app.schemas.chat import SourceCitation, ToolCallLog
from app.services.session_service import build_request_messages, store_turn
from app.services.tool_log_service import append_tool_log
from app.tools.rag_tools import get_collected_rag_sources, reset_rag_sources, set_active_document_ids


@dataclass
class AgentReply:
    answer: str
    plan: str
    tools_used: list[str]
    sources: list[SourceCitation] = field(default_factory=list)
    tool_calls: list[ToolCallLog] = field(default_factory=list)
    session_id: str | None = None


def _extract_tool_calls(messages: list) -> list[ToolCallLog]:
    pending_args: dict[str, dict] = {}
    logs: list[ToolCallLog] = []

    for item in messages:
        if isinstance(item, AIMessage) and item.tool_calls:
            for call in item.tool_calls:
                pending_args[call["id"]] = {
                    "name": call["name"],
                    "args": call.get("args", {}),
                }
        if isinstance(item, ToolMessage):
            meta = pending_args.get(item.tool_call_id, {"name": item.name or "unknown", "args": {}})
            logs.append(
                ToolCallLog(
                    name=meta["name"],
                    args=meta["args"],
                    result=str(item.content),
                )
            )
    return logs


def _dedupe_sources(raw_sources: list[dict]) -> list[SourceCitation]:
    seen: set[tuple[str, int | None, str]] = set()
    citations: list[SourceCitation] = []
    for item in raw_sources:
        key = (item["document_id"], item.get("page"), item["excerpt"][:120])
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            SourceCitation(
                document_id=item["document_id"],
                filename=item["filename"],
                page=item.get("page"),
                excerpt=item["excerpt"],
            )
        )
    return citations


async def generate_reply(
    message: str,
    session_id: str | None = None,
    document_ids: list[str] | None = None,
) -> AgentReply:
    """Run one complete Agent turn and extract data suitable for the API response."""
    reset_rag_sources()
    set_active_document_ids(document_ids)
    active_session_id, request_messages = build_request_messages(session_id, message)

    graph = get_research_agent()
    result = await graph.ainvoke(
        {"messages": request_messages},
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
    tools_used = [item.name for item in messages if isinstance(item, ToolMessage) and item.name]
    tool_calls = _extract_tool_calls(messages)
    sources = _dedupe_sources(get_collected_rag_sources())

    store_turn(active_session_id, message, answer)
    for log in tool_calls:
        append_tool_log(active_session_id, log.name, log.args, log.result)

    return AgentReply(
        answer=answer,
        plan=result.get("plan", "未生成计划。"),
        tools_used=tools_used,
        sources=sources,
        tool_calls=tool_calls,
        session_id=active_session_id,
    )
