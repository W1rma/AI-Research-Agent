"""FastAPI application factory and route registration."""

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.papers import router as papers_router
from app.api.routes.web import router as web_router
from app.core.config import get_settings

get_settings()

app = FastAPI(
    title="AI Research Agent API",
    description="面向科研学习的 AI Agent 后端接口。",
    version="0.2.0",
)

app.include_router(health_router)
app.include_router(chat_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(papers_router, prefix="/api/v1")
app.include_router(web_router, prefix="/api/v1")
