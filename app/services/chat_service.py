from openai import AsyncOpenAI

from app.core.config import get_settings

SYSTEM_PROMPT = """你是 AI 科研学习助手。请用中文清晰回答问题。
当问题涉及事实但你不能确定时，要明确说明不确定性，不要编造来源。"""


async def generate_reply(message: str) -> str:
    """调用 DeepSeek 的 OpenAI 兼容 Chat Completions API。"""
    settings = get_settings()
    if settings.deepseek_api_key is None:
        raise ValueError("未配置 DEEPSEEK_API_KEY，请在项目根目录的 .env 中填写后重试。")

    client = AsyncOpenAI(
        api_key=settings.deepseek_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
    )
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0.3,
        max_tokens=1_000,
    )

    answer = response.choices[0].message.content
    return answer or "模型没有返回可显示的内容，请重试。"
