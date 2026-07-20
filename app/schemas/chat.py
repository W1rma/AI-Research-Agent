from pydantic import BaseModel, ConfigDict, Field

from app.schemas.papers import PaperResult


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "根据我上传的论文，作者使用了什么方法？请给出页码依据。"
                }
            ]
        }
    )

    message: str = Field(..., min_length=1, max_length=5_000, description="用户的问题")
    session_id: str | None = Field(default=None, max_length=128, description="可选会话 ID，用于多轮记忆")
    document_ids: list[str] | None = Field(default=None, description="可选文档 ID 列表，限制 RAG 检索范围")


class SourceCitation(BaseModel):
    document_id: str = Field(..., description="来源文档 ID")
    filename: str = Field(..., description="来源文件名")
    page: int | None = Field(default=None, description="页码")
    excerpt: str = Field(..., description="引用片段；匹配词以【】标记")
    score: float | None = Field(default=None, description="混合检索排序分数")
    highlights: list[str] = Field(default_factory=list, description="命中的检索词")


class ToolCallLog(BaseModel):
    name: str = Field(..., description="工具名称")
    args: dict = Field(default_factory=dict, description="工具调用参数")
    result: str = Field(..., description="工具返回结果摘要")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="模型生成的回答")
    plan: str = Field(..., description="Agent 为本次任务生成的内部执行计划")
    tools_used: list[str] = Field(default_factory=list, description="本次执行实际调用的工具")
    sources: list[SourceCitation] = Field(default_factory=list, description="RAG 引用来源")
    paper_sources: list[PaperResult] = Field(
        default_factory=list,
        description="本轮最后一次成功 arXiv 检索返回的候选论文；不等同于模型最终推荐的全部论文",
    )
    tool_calls: list[ToolCallLog] = Field(default_factory=list, description="工具调用日志")
    session_id: str | None = Field(default=None, description="本次会话 ID")
