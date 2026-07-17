"""Embedding helpers for the local Chroma vector store."""

from functools import lru_cache

from chromadb.utils import embedding_functions
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


class ChromaDefaultEmbeddings(Embeddings):
    """Wrap Chroma's built-in ONNX embedding model for LangChain."""

    def __init__(self) -> None:
        self._embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embedding_function(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embedding_function([text])[0]


@lru_cache
def get_embeddings() -> Embeddings:
    settings = get_settings()
    api_key = settings.embedding_api_key or settings.deepseek_api_key
    if api_key is not None:
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=api_key.get_secret_value(),
            base_url=settings.embedding_base_url,
        )
    return ChromaDefaultEmbeddings()
