from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5_000, description="用户的问题")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="模型生成的回答")
