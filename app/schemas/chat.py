from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5_000, description="用户的问题")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="模型生成的回答")
    plan: str = Field(..., description="Agent 为本次任务生成的内部执行计划")
    tools_used: list[str] = Field(default_factory=list, description="本次执行实际调用的工具")
