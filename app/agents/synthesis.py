from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import MultiAgentState

SYNTHESIS_PROMPT = """你是 Synthesis Agent，负责把各专业 Agent 的分析整理成最终中文回答。

要求：
1. 直接回答用户问题，不展示内部思维过程，也不要声称自己调用了未出现的工具。
2. 不同专业 Agent 的结果冲突时，说明差异与不确定性。
3. 本地资料写作“本地知识库”，arXiv 结果写作“arXiv 论文”，网页结果写作“公开网页”。
4. 公开网页不是同行评审论文；没有证据时明确说明。
5. 引用本地 PDF 时尽量带文件名和页码；引用论文时带 arXiv ID；引用网页时带标题或 URL。
6. 回答保持结构清楚、简洁，并给出适合学生继续学习的下一步。
"""


async def synthesize_response(model, state: MultiAgentState) -> dict:
    response = await model.ainvoke(
        [
            SystemMessage(content=SYNTHESIS_PROMPT),
            *state["messages"],
            HumanMessage(content="请基于以上专业 Agent 结果生成最终回答。"),
        ]
    )
    return {"messages": [response]}
