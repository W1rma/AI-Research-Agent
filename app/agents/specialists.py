from collections.abc import Sequence

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.state import SpecialistName, SpecialistState
from app.tools.arxiv_tools import search_arxiv_papers
from app.tools.rag_tools import search_uploaded_documents
from app.tools.research_tools import calculate, generate_study_plan, get_current_date
from app.tools.web_search_tools import search_public_web

SPECIALIST_TOOLS: dict[SpecialistName, list[BaseTool]] = {
    "knowledge": [search_uploaded_documents],
    "literature": [search_arxiv_papers],
    "web": [search_public_web],
    "learning": [calculate, get_current_date, generate_study_plan],
}

SPECIALIST_PROMPTS: dict[SpecialistName, str] = {
    "knowledge": (
        "你是 Knowledge Agent，只分析用户上传的 PDF、讲义和本地知识库。"
        "需要文档事实时必须调用 search_uploaded_documents，并保留文件名与页码证据。"
        "如果知识库没有证据，要明确说明，不得使用外部常识补写文档结论。"
        "你的输出是给 Synthesis Agent 的专业分析，不要假装已经完成最终汇总。"
    ),
    "literature": (
        "你是 Literature Agent，只负责 arXiv 论文检索与学术资料分析。"
        "需要论文时调用 search_arxiv_papers；用户指定单一年份时，同时传 start_year 和 end_year；"
        "max_results 应与用户要求的数量一致。区分预印本与已经同行评审的结论。"
        "输出论文题目、arXiv ID、相关性和简短阅读建议，供 Synthesis Agent 汇总。"
    ),
    "web": (
        "你是 Web Agent，只负责最新动态、官方文档和一般公开网页资料。"
        "需要联网事实时调用 search_public_web，并保留标题、URL 和摘要。"
        "优先采用官方或一手来源；公开网页不能被描述为同行评审论文。"
        "你的输出是给 Synthesis Agent 的检索结果，不是最终回答。"
    ),
    "learning": (
        "你是 Learning Agent，负责知识解释、数学计算、学习计划和复习安排。"
        "需要计算、当前日期或学习计划时使用对应工具。"
        "不要虚构本地文档、论文或网页来源；涉及这些来源时交由其他专业 Agent。"
        "给出清楚、适合学生继续学习的分析，供 Synthesis Agent 汇总。"
    ),
}


def build_specialist_graph(model, name: SpecialistName, tools: Sequence[BaseTool]):
    """Build an isolated ReAct loop whose tool permissions are specialist-scoped."""
    scoped_tools = list(tools)
    model_with_tools = model.bind_tools(scoped_tools)

    async def specialist_node(state: SpecialistState) -> dict:
        scope_instruction = ""
        if name == "knowledge" and state.get("selected_document_ids"):
            selected_ids = ", ".join(state["selected_document_ids"])
            scope_instruction = (
                f"\n本次仅允许检索这些 document_ids：{selected_ids}。"
                "调用 search_uploaded_documents 时必须传入 document_ids。"
            )
        conversation = list(state["messages"])
        if conversation and not isinstance(conversation[-1], (HumanMessage, ToolMessage)):
            conversation.append(
                HumanMessage(
                    content=f"内部委派：请由 {name} Agent 针对用户最新请求完成本专业分析。"
                )
            )
        response = await model_with_tools.ainvoke(
            [SystemMessage(content=SPECIALIST_PROMPTS[name] + scope_instruction), *conversation]
        )
        return {"messages": [response]}

    workflow = StateGraph(SpecialistState)
    workflow.add_node("agent", specialist_node)
    workflow.add_node("tools", ToolNode(scoped_tools, handle_tool_errors=True))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")
    return workflow.compile()
