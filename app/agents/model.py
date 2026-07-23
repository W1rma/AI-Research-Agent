from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def create_chat_model() -> ChatOpenAI:
    """Create the shared DeepSeek-compatible chat model."""
    settings = get_settings()
    if settings.deepseek_api_key is None:
        raise ValueError(
            "未配置 DEEPSEEK_API_KEY，请在项目根目录的 .env 中填写后重试。"
        )
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        temperature=0.2,
        max_tokens=1_200,
    )
