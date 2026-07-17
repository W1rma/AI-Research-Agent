"""Persistent Chroma vector store for uploaded PDF chunks."""

from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "research_documents"


@lru_cache
def get_vector_store() -> Chroma:
    settings = get_settings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(settings.vector_store_dir),
        embedding_function=get_embeddings(),
    )


def add_document_chunks(chunks: list[Document]) -> int:
    store = get_vector_store()
    store.add_documents(chunks)
    return len(chunks)


def search_documents(query: str, document_id: str | None = None, top_k: int | None = None) -> list[Document]:
    settings = get_settings()
    store = get_vector_store()
    kwargs: dict = {"k": top_k or settings.rag_top_k}
    if document_id:
        kwargs["filter"] = {"document_id": document_id}
    return store.similarity_search(query, **kwargs)


def delete_document_vectors(document_id: str) -> None:
    store = get_vector_store()
    collection = store._collection
    existing = collection.get(where={"document_id": document_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
