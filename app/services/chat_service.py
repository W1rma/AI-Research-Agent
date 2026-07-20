"""Service layer between the HTTP API and the LangGraph agent."""

import json
from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.graph import get_research_agent
from app.schemas.chat import SourceCitation, ToolCallLog
from app.schemas.papers import PaperResult
from app.services.session_service import build_request_messages, store_turn
from app.services.tool_log_service import append_tool_log


@dataclass
class AgentReply:
    answer: str
    plan: str
    tools_used: list[str]
    sources: list[SourceCitation] = field(default_factory=list)
    paper_sources: list[PaperResult] = field(default_factory=list)
    tool_calls: list[ToolCallLog] = field(default_factory=list)
    session_id: str | None = None


def _extract_tool_calls(messages: list) -> list[ToolCallLog]:
    pending_args: dict[str, dict] = {}
    logs: list[ToolCallLog] = []
    for item in messages:
        if isinstance(item, AIMessage) and item.tool_calls:
            for call in item.tool_calls:
                pending_args[call["id"]] = {"name": call["name"], "args": call.get("args", {})}
        elif isinstance(item, ToolMessage):
            meta = pending_args.get(item.tool_call_id, {"name": item.name or "unknown", "args": {}})
            logs.append(
                ToolCallLog(
                    name=meta["name"],
                    args=meta["args"],
                    result=_summarize_tool_result(meta["name"], item.content),
                )
            )
    return logs


def _summarize_tool_result(tool_name: str, content: object) -> str:
    """Keep API tool logs useful without duplicating large structured payloads."""
    if tool_name != "search_arxiv_papers":
        return str(content)

    try:
        payload = json.loads(str(content))
    except json.JSONDecodeError:
        # Provider and validation errors are already concise, so retain them verbatim.
        return str(content)

    papers = payload.get("papers")
    if not isinstance(papers, list):
        return str(content)
    return f"arXiv 返回 {len(papers)} 篇候选论文，完整信息见 paper_sources。"


def _extract_rag_sources(messages: list) -> list[dict]:
    """Read citations from the RAG tool payload instead of process-local state."""
    sources: list[dict] = []
    for item in messages:
        if not isinstance(item, ToolMessage) or item.name != "search_uploaded_documents":
            continue
        try:
            payload = json.loads(str(item.content))
        except json.JSONDecodeError:
            continue
        sources.extend(payload.get("sources", []))
    return sources


def _extract_paper_sources(messages: list) -> list[PaperResult]:
    """Return candidates from the latest successful paper-search call in this turn.

    An agent can refine a query and call arXiv more than once.  Returning every
    intermediate response makes ``paper_sources`` ambiguous and can expose
    papers that the final answer did not use.
    """
    latest_papers: list[PaperResult] | None = None
    for item in messages:
        if not isinstance(item, ToolMessage) or item.name != "search_arxiv_papers":
            continue
        try:
            payload = json.loads(str(item.content))
        except json.JSONDecodeError:
            continue
        raw_papers = payload.get("papers")
        if not isinstance(raw_papers, list):
            continue
        try:
            latest_papers = [PaperResult.model_validate(raw_paper) for raw_paper in raw_papers]
        except (TypeError, ValueError):
            continue
    return latest_papers or []


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
                score=item.get("score"),
                highlights=item.get("highlights", []),
            )
        )
    return citations


async def generate_reply(
    message: str,
    session_id: str | None = None,
    document_ids: list[str] | None = None,
) -> AgentReply:
    """Run a complete turn, then persist only the user-facing final answer."""
    active_session_id, request_messages = build_request_messages(session_id, message)
    graph_input = {"messages": request_messages}
    if document_ids:
        # The graph prompt exposes the currently selected IDs for the model to pass to the tool.
        graph_input["selected_document_ids"] = document_ids
    result = await get_research_agent().ainvoke(graph_input, config={"recursion_limit": 12})
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
    sources = _dedupe_sources(_extract_rag_sources(messages))
    paper_sources = _extract_paper_sources(messages)

    store_turn(active_session_id, message, answer)
    for log in tool_calls:
        append_tool_log(active_session_id, log.name, log.args, log.result)
    return AgentReply(
        answer=answer,
        plan=result.get("plan", "未生成计划。"),
        tools_used=tools_used,
        sources=sources,
        paper_sources=paper_sources,
        tool_calls=tool_calls,
        session_id=active_session_id,
    )
