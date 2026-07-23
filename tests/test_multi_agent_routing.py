from app.agents.graph import _next_node
from app.agents.specialists import SPECIALIST_TOOLS
from app.agents.supervisor import fallback_routes, normalize_routes


def _tool_names(agent_name: str) -> set[str]:
    return {tool.name for tool in SPECIALIST_TOOLS[agent_name]}


def test_specialists_have_isolated_tool_permissions() -> None:
    assert _tool_names("knowledge") == {"search_uploaded_documents"}
    assert _tool_names("literature") == {"search_arxiv_papers"}
    assert _tool_names("web") == {"search_public_web"}
    assert _tool_names("learning") == {
        "calculate",
        "get_current_date",
        "generate_study_plan",
    }


def test_fallback_routes_local_and_web_hybrid_request() -> None:
    routes = fallback_routes("比较我上传的 PDF 与最新官方资料")

    assert routes == ["knowledge", "web"]


def test_fallback_routes_selected_documents_to_knowledge_agent() -> None:
    routes = fallback_routes("请总结核心方法", selected_document_ids=["doc-1"])

    assert routes == ["knowledge", "learning"]


def test_fallback_routes_paper_search_to_literature_agent() -> None:
    assert fallback_routes("帮我找论文：RAG evaluation") == ["literature"]


def test_normalize_routes_removes_unknown_and_duplicate_values() -> None:
    routes = normalize_routes(["web", "unknown", "web", "learning"])

    assert routes == ["web", "learning"]


def test_next_node_follows_route_order_then_synthesizes() -> None:
    state = {
        "messages": [],
        "routes": ["knowledge", "web"],
        "route_index": 0,
        "routing_reason": "hybrid",
        "plan": "test",
    }
    assert _next_node(state) == "knowledge"

    state["route_index"] = 1
    assert _next_node(state) == "web"

    state["route_index"] = 2
    assert _next_node(state) == "synthesis"
