from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """集中读取 .env；变量名与 .env.example 保持一致。"""

    deepseek_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    app_env: str = "development"
    debug: bool = True

    # 可选：OpenAI 兼容 Embedding API（未配置时使用 Chroma 内置本地向量模型）
    embedding_api_key: SecretStr | None = None
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"

    uploads_dir: Path = PROJECT_ROOT / "data" / "uploads"
    vector_store_dir: Path = PROJECT_ROOT / "data" / "vector_store"
    documents_registry_path: Path = PROJECT_ROOT / "data" / "documents.json"
    tool_logs_path: Path = PROJECT_ROOT / "data" / "tool_logs.jsonl"

    pdf_chunk_size: int = 800
    pdf_chunk_overlap: int = 120
    rag_top_k: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_data_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.documents_registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.tool_logs_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """缓存配置，避免每次请求重复读取文件。"""
    settings = Settings()
    settings.ensure_data_dirs()
    return settings
