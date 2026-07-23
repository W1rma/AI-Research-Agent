from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agents.state import MultiAgentState, SpecialistName

_VALID_ROUTES: tuple[SpecialistName, ...] = (
    "knowledge",
    "literature",
    "web",
    "learning",
)

SUPERVISOR_PROMPT = """你是 Research Agent 的主管 Agent，只负责路由，不回答用户问题。
根据用户的最新请求，选择一个或多个专业 Agent：
- knowledge：已上传 PDF、本地论文、讲义、笔记和 RAG 知识库。
- literature：arXiv 论文、预印本、学术论文检索与论文推荐。
- web：最新动态、官方文档、产品资料、新闻和一般公开网页。
- learning：学习计划、知识解释、数学计算以及不需要外部检索的一般学习问题。

混合问题可以选择多个 Agent，但不要选择与任务无关的 Agent。routes 按执行顺序返回。
如果请求限定了 document_ids，通常应包含 knowledge。
"""


class RoutingDecision(BaseModel):
    routes: list[SpecialistName] = Field(min_length=1, max_length=4)
    reason: str = Field(min_length=1, max_length=300)


def _latest_user_text(state: MultiAgentState) -> str:
    latest = next(
        (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
        None,
    )
    if latest is None:
        return ""
    return latest.content if isinstance(latest.content, str) else str(latest.content)


def normalize_routes(
    routes: list[str] | None,
    fallback: list[SpecialistName] | None = None,
) -> list[SpecialistName]:
    """Filter unknown and duplicate routes while preserving execution order."""
    normalized: list[SpecialistName] = []
    for route in routes or []:
        if route in _VALID_ROUTES and route not in normalized:
            normalized.append(route)  # type: ignore[arg-type]
    return normalized or fallback or ["learning"]


def fallback_routes(
    question: str,
    selected_document_ids: list[str] | None = None,
) -> list[SpecialistName]:
    """Deterministic fallback when structured LLM routing is unavailable."""
    lowered = question.casefold()
    routes: list[SpecialistName] = []

    knowledge_terms = ("上传", "本地", "知识库", "讲义", "笔记", "pdf", "document")
    literature_terms = (
        "arxiv",
        "预印本",
        "学术论文",
        "论文检索",
        "找论文",
        "推荐论文",
        "research paper",
    )
    web_terms = (
        "最新",
        "新闻",
        "官网",
        "官方文档",
        "公开网页",
        "联网",
        "current",
        "latest",
        "official",
        "news",
        "web",
    )
    learning_terms = ("学习计划", "复习计划", "解释", "计算", "总结", "怎么学")

    if selected_document_ids or any(term in lowered for term in knowledge_terms):
        routes.append("knowledge")
    if any(term in lowered for term in literature_terms):
        routes.append("literature")
    if any(term in lowered for term in web_terms):
        routes.append("web")
    if any(term in lowered for term in learning_terms):
        routes.append("learning")
    return routes or ["learning"]


async def route_request(model, state: MultiAgentState) -> dict:
    """Use the supervisor model, with a deterministic fallback for portability."""
    question = _latest_user_text(state)
    fallback = fallback_routes(question, state.get("selected_document_ids"))
    try:
        router = model.with_structured_output(RoutingDecision)
        decision = await router.ainvoke(
            [
                SystemMessage(content=SUPERVISOR_PROMPT),
                *state["messages"][-6:],
            ]
        )
        routes = normalize_routes(decision.routes, fallback)
        if state.get("selected_document_ids") and "knowledge" not in routes:
            routes.insert(0, "knowledge")
        reason = decision.reason.strip()
    except Exception:
        routes = fallback
        reason = "结构化路由不可用，已根据问题关键词执行安全回退路由。"

    route_labels = " → ".join(routes)
    return {
        "routes": routes,
        "route_index": 0,
        "routing_reason": reason,
        "plan": f"Supervisor 路由：{route_labels}。{reason}",
    }
