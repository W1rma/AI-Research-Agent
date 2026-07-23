from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agents.model import create_chat_model
from app.agents.specialists import SPECIALIST_TOOLS, build_specialist_graph
from app.agents.state import MultiAgentState, SpecialistName
from app.agents.supervisor import route_request
from app.agents.synthesis import synthesize_response

_SPECIALIST_NODES: tuple[SpecialistName, ...] = (
    "knowledge",
    "literature",
    "web",
    "learning",
)


def _next_node(state: MultiAgentState) -> str:
    index = state.get("route_index", 0)
    routes = state.get("routes", [])
    return routes[index] if index < len(routes) else "synthesis"


def _specialist_runner(name: SpecialistName, graph):
    async def run(state: MultiAgentState) -> dict:
        original_count = len(state["messages"])
        specialist_input = {"messages": state["messages"]}
        if state.get("selected_document_ids"):
            specialist_input["selected_document_ids"] = state["selected_document_ids"]
        result = await graph.ainvoke(
            specialist_input,
            config={"recursion_limit": 8},
        )
        return {
            "messages": result["messages"][original_count:],
            "route_index": state["route_index"] + 1,
        }

    run.__name__ = f"run_{name}_agent"
    return run


@lru_cache
def get_research_agent():
    """Build the supervisor-led multi-agent graph once per server process."""
    model = create_chat_model()
    specialist_graphs = {
        name: build_specialist_graph(model, name, tools)
        for name, tools in SPECIALIST_TOOLS.items()
    }

    async def supervisor_node(state: MultiAgentState) -> dict:
        return await route_request(model, state)

    async def synthesis_node(state: MultiAgentState) -> dict:
        return await synthesize_response(model, state)

    workflow = StateGraph(MultiAgentState)
    workflow.add_node("supervisor", supervisor_node)
    for name in _SPECIALIST_NODES:
        workflow.add_node(name, _specialist_runner(name, specialist_graphs[name]))
    workflow.add_node("synthesis", synthesis_node)

    route_map = {name: name for name in _SPECIALIST_NODES}
    route_map["synthesis"] = "synthesis"

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges("supervisor", _next_node, route_map)
    for name in _SPECIALIST_NODES:
        workflow.add_conditional_edges(name, _next_node, route_map)
    workflow.add_edge("synthesis", END)
    return workflow.compile()
