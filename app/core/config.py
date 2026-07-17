from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Centralized, typed configuration loaded from the project .env file."""

    deepseek_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"
    app_env: str = "development"
    debug: bool = True

    # Remote embeddings are opt-in. Do not reuse a chat-model key implicitly.
    embedding_api_key: SecretStr | None = None
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"

    uploads_dir: Path = PROJECT_ROOT / "data" / "uploads"
    vector_store_dir: Path = PROJECT_ROOT / "data" / "vector_store"
    documents_registry_path: Path = PROJECT_ROOT / "data" / "documents.json"
    sessions_db_path: Path = PROJECT_ROOT / "data" / "sessions.sqlite3"
    tool_logs_path: Path = PROJECT_ROOT / "data" / "tool_logs.jsonl"

    pdf_chunk_size: int = 800
    pdf_chunk_overlap: int = 120
    max_upload_size_mb: int = 20
    pdf_enable_ocr: bool = False
    tesseract_cmd: str | None = None
    ocr_min_text_characters: int = 20

    rag_top_k: int = 4
    rag_candidate_k: int = 24
    session_history_limit: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_data_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        self.documents_registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.sessions_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.tool_logs_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_data_dirs()
    return settings
