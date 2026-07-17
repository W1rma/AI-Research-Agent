from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5_000, description="用户的问题")
    session_id: str | None = Field(default=None, description="可选会话 ID，用于多轮记忆")
    document_ids: list[str] | None = Field(
        default=None,
        description="可选文档 ID 列表，限制 RAG 检索范围",
    )


class SourceCitation(BaseModel):
    document_id: str = Field(..., description="来源文档 ID")
    filename: str = Field(..., description="来源文件名")
    page: int | None = Field(default=None, description="页码")
    excerpt: str = Field(..., description="引用片段")


class ToolCallLog(BaseModel):
    name: str = Field(..., description="工具名称")
    args: dict = Field(default_factory=dict, description="工具调用参数")
    result: str = Field(..., description="工具返回结果摘要")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="模型生成的回答")
    plan: str = Field(..., description="Agent 为本次任务生成的内部执行计划")
    tools_used: list[str] = Field(default_factory=list, description="本次执行实际调用的工具")
    sources: list[SourceCitation] = Field(default_factory=list, description="RAG 引用来源")
    tool_calls: list[ToolCallLog] = Field(default_factory=list, description="工具调用日志")
    session_id: str | None = Field(default=None, description="本次会话 ID")
