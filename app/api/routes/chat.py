from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_reply

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """向当前配置的大模型发送科研学习问题。"""
    try:
        answer = await generate_reply(request.message)
    except ValueError as error:
        # 这是本地配置问题，例如尚未填写所用模型的api-key。
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    return ChatResponse(answer=answer)
