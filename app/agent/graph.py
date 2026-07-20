"""Flow: START -> planner -> agent -> (tools -> agent)* -> END."""

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.prompts import AGENT_PROMPT, PLANNER_PROMPT
from app.agent.state import ResearchAgentState
from app.core.config import get_settings
from app.tools.research_tools import RESEARCH_TOOLS


def _message_text(message: HumanMessage) -> str:
    return message.content if isinstance(message.content, str) else str(message.content)


def _create_model() -> ChatOpenAI:
    settings = get_settings()
    if settings.deepseek_api_key is None:
        raise ValueError("未配置 DEEPSEEK_API_KEY，请在项目根目录的 .env 中填写后重试。")
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        temperature=0.3,
        max_tokens=1_000,
    )


@lru_cache
def get_research_agent():
    """Build once per server process; restart after changing .env."""
    model = _create_model()
    model_with_tools = model.bind_tools(RESEARCH_TOOLS)

    async def planner_node(state: ResearchAgentState) -> dict[str, str]:
        latest_user_message = next(
            (item for item in reversed(state["messages"]) if isinstance(item, HumanMessage)), None
        )
        question = _message_text(latest_user_message) if latest_user_message else ""
        response = await model.ainvoke(
            [SystemMessage(content=PLANNER_PROMPT), HumanMessage(content=question)]
        )
        return {"plan": str(response.content)}

    async def agent_node(state: ResearchAgentState) -> dict[str, list]:
        selected_ids = state.get("selected_document_ids", [])
        paper_search_instruction = (
            "\n论文检索规则：用户要求某一个具体年份时，同时传入 start_year 和 end_year；"
            "没有新的检索意图时不要重复调用 search_arxiv_papers；max_results 要与用户要求的数量一致。"
        )
        scope_instruction = (
            f"\n本次请求限定检索的文档 ID：{', '.join(selected_ids)}。"
            "调用 search_uploaded_documents 时必须把这些 ID 作为 document_ids 参数传入。"
            if selected_ids
            else ""
        )
        system_message = SystemMessage(
            content=AGENT_PROMPT.format(plan=state["plan"])
            + paper_search_instruction
            + scope_instruction
        )
        response = await model_with_tools.ainvoke([system_message, *state["messages"]])
        return {"messages": [response]}

    workflow = StateGraph(ResearchAgentState)
    workflow.add_node("planner", planner_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(RESEARCH_TOOLS, handle_tool_errors=True))
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "agent")
    workflow.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")
    return workflow.compile()
