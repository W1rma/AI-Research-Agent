from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """确认服务是否已启动；不返回密钥。"""
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.app_env,
        "model": settings.llm_model,
    }
