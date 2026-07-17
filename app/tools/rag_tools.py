"""RAG retrieval tool backed by uploaded PDF documents."""

from contextvars import ContextVar

from langchain_core.tools import tool

from app.rag.vector_store import search_documents as vector_search
from app.services.document_registry import get_document_registry

_active_document_ids: ContextVar[list[str] | None] = ContextVar("active_document_ids", default=None)
_rag_sources: ContextVar[list[dict]] = ContextVar("rag_sources", default=[])


def set_active_document_ids(document_ids: list[str] | None) -> None:
    _active_document_ids.set(document_ids)


def reset_rag_sources() -> None:
    _rag_sources.set([])


def get_collected_rag_sources() -> list[dict]:
    return list(_rag_sources.get())


def _append_source(document_id: str, filename: str, page: int | None, excerpt: str) -> None:
    sources = _rag_sources.get()
    sources.append(
        {
            "document_id": document_id,
            "filename": filename,
            "page": page,
            "excerpt": excerpt,
        }
    )
    _rag_sources.set(sources)


@tool
def search_uploaded_documents(query: str, document_id: str | None = None, top_k: int = 4) -> str:
    """检索用户已上传的 PDF 文档内容。适合基于本地论文、讲义或笔记回答问题。"""
    query = query.strip()
    if not query:
        return "检索问题不能为空。"
    if not 1 <= top_k <= 8:
        return "top_k 需在 1 到 8 之间。"

    registry = get_document_registry()
    ready_documents = [item for item in registry.list_documents() if item.status == "ready"]
    if not ready_documents:
        return "当前知识库中没有已处理完成的 PDF 文档，请先上传文档。"

    scoped_ids = _active_document_ids.get()
    if document_id:
        target_ids = [document_id]
    elif scoped_ids:
        target_ids = scoped_ids
    else:
        target_ids = [item.id for item in ready_documents]

    hits: list[str] = []
    for current_id in target_ids:
        record = registry.get_document(current_id)
        if record is None or record.status != "ready":
            continue
        documents = vector_search(query, document_id=current_id, top_k=top_k)
        for rank, doc in enumerate(documents, start=1):
            excerpt = doc.page_content.strip()
            if len(excerpt) > 500:
                excerpt = excerpt[:500] + "..."
            page = doc.metadata.get("page")
            _append_source(current_id, record.original_filename, page, excerpt)
            hits.append(
                "\n".join(
                    [
                        f"[{record.original_filename} | 第 {page} 页 | 片段 {rank}]",
                        excerpt,
                    ]
                )
            )

    if not hits:
        return "未在已上传文档中找到相关内容，请尝试换个问法或上传更多资料。"
    return "文档检索结果：\n\n" + "\n\n".join(hits)
