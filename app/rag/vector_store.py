"""Persistent Chroma store with hybrid (vector + BM25) retrieval."""

import re
from dataclasses import dataclass
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "research_documents"


@dataclass(frozen=True)
class RetrievedChunk:
    document: Document
    score: float


def _tokenize(text: str) -> list[str]:
    """Use words plus CJK bigrams so lexical search also works for Chinese PDFs."""
    normalized = text.lower()
    words = re.findall(r"[a-z0-9_]+", normalized)
    cjk_characters = re.findall(r"[\u4e00-\u9fff]", normalized)
    bigrams = ["".join(cjk_characters[index : index + 2]) for index in range(len(cjk_characters) - 1)]
    return [*words, *bigrams, *cjk_characters]


def highlight_terms(text: str, query: str, limit: int = 3) -> tuple[str, list[str]]:
    """Return a display-ready excerpt and the matching terms used for highlighting."""
    terms = []
    for term in _tokenize(query):
        if len(term) > 1 and term not in terms:
            terms.append(term)
        if len(terms) == limit:
            break
    highlighted = text
    found: list[str] = []
    for term in sorted(terms, key=len, reverse=True):
        if term in highlighted.lower():
            highlighted = re.sub(re.escape(term), lambda match: f"【{match.group(0)}】", highlighted, flags=re.IGNORECASE)
            found.append(term)
    return highlighted, found


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
    ids = [f"{chunk.metadata['document_id']}:{chunk.metadata['chunk_index']}" for chunk in chunks]
    store.add_documents(chunks, ids=ids)
    return len(chunks)


def _where_filter(document_ids: list[str] | None) -> dict | None:
    if not document_ids:
        return None
    if len(document_ids) == 1:
        return {"document_id": document_ids[0]}
    return {"document_id": {"$in": document_ids}}


def hybrid_search_documents(
    query: str,
    document_ids: list[str] | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Fuse semantic and lexical rankings with reciprocal-rank fusion."""
    settings = get_settings()
    store = get_vector_store()
    limit = top_k or settings.rag_top_k
    candidate_k = max(limit * 3, settings.rag_candidate_k)
    where = _where_filter(document_ids)

    vector_hits = store.similarity_search_with_relevance_scores(query, k=candidate_k, filter=where)
    raw = store._collection.get(where=where, include=["documents", "metadatas"])
    lexical_documents = [
        Document(page_content=text, metadata=metadata or {})
        for text, metadata in zip(raw.get("documents", []), raw.get("metadatas", []), strict=False)
        if text
    ]

    ranked_lexical: list[Document] = []
    if lexical_documents:
        corpus = [_tokenize(document.page_content) or [""] for document in lexical_documents]
        scores = BM25Okapi(corpus).get_scores(_tokenize(query) or [""])
        ranked_lexical = [
            document
            for _, document in sorted(zip(scores, lexical_documents, strict=True), key=lambda item: item[0], reverse=True)
            if _ > 0
        ]

    scores_by_id: dict[str, float] = {}
    documents_by_id: dict[str, Document] = {}
    for rank, (document, _) in enumerate(vector_hits, start=1):
        chunk_id = f"{document.metadata.get('document_id')}:{document.metadata.get('chunk_index')}"
        documents_by_id[chunk_id] = document
        scores_by_id[chunk_id] = scores_by_id.get(chunk_id, 0) + 1 / (60 + rank)
    for rank, document in enumerate(ranked_lexical, start=1):
        chunk_id = f"{document.metadata.get('document_id')}:{document.metadata.get('chunk_index')}"
        documents_by_id[chunk_id] = document
        scores_by_id[chunk_id] = scores_by_id.get(chunk_id, 0) + 1 / (60 + rank)

    ordered = sorted(scores_by_id, key=scores_by_id.get, reverse=True)[:limit]
    return [RetrievedChunk(document=documents_by_id[chunk_id], score=scores_by_id[chunk_id]) for chunk_id in ordered]


def search_documents(query: str, document_id: str | None = None, top_k: int | None = None) -> list[Document]:
    """Compatibility wrapper for code that only needs documents, not scores."""
    ids = [document_id] if document_id else None
    return [item.document for item in hybrid_search_documents(query, ids, top_k)]


def delete_document_vectors(document_id: str) -> None:
    store = get_vector_store()
    collection = store._collection
    existing = collection.get(where={"document_id": document_id})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
