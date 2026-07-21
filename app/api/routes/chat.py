from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_reply

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest) -> ChatResponse:
    """运行 Research Agent，并返回回答、计划、工具日志与引用来源。"""
    try:
        result = await generate_reply(
            message=request.message,
            session_id=request.session_id,
            document_ids=request.document_ids,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error

    return ChatResponse(
        answer=result.answer,
        plan=result.plan,
        tools_used=result.tools_used,
        sources=result.sources,
        paper_sources=result.paper_sources,
        web_sources=result.web_sources,
        tool_calls=result.tool_calls,
        session_id=result.session_id,
    )
