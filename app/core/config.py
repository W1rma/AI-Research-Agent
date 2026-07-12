from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """集中读取 .env；变量名与 .env.example 保持一致。"""

    deepseek_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    app_env: str = "development"
    debug: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """缓存配置，避免每次请求重复读取文件。"""
    return Settings()
