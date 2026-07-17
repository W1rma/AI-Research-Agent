"""RAG retrieval tool backed by uploaded PDF documents."""

import json

from langchain_core.tools import tool

from app.rag.vector_store import highlight_terms, hybrid_search_documents
from app.services.document_registry import get_document_registry


def _result_payload(context: str, sources: list[dict]) -> str:
    """ToolNode may run sync tools in another context, so return citations explicitly."""
    return json.dumps({"context": context, "sources": sources}, ensure_ascii=False)


@tool
def search_uploaded_documents(
    query: str,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    top_k: int = 4,
) -> str:
    """检索用户已上传 PDF 内容。适合回答本地论文、讲义或笔记中的问题。"""
    query = query.strip()
    if not query:
        return "检索问题不能为空。"
    if not 1 <= top_k <= 8:
        return "top_k 需在 1 到 8 之间。"

    registry = get_document_registry()
    ready_documents = [item for item in registry.list_documents() if item.status == "ready"]
    if not ready_documents:
        return "当前知识库中没有已处理完成的 PDF 文档，请先上传文档。"

    if document_ids:
        target_ids = document_ids
    elif document_id:
        target_ids = [document_id]
    else:
        target_ids = [item.id for item in ready_documents]
    ready_ids = {item.id for item in ready_documents}
    target_ids = [item for item in target_ids if item in ready_ids]
    if not target_ids:
        return "指定的文档不存在，或尚未处理完成。"

    results = hybrid_search_documents(query, document_ids=target_ids, top_k=top_k)
    if not results:
        return "未在已上传文档中找到相关内容，请尝试换个问法或上传更多资料。"

    contexts: list[str] = []
    sources: list[dict] = []
    for rank, item in enumerate(results, start=1):
        document = item.document
        metadata = document.metadata
        current_id = str(metadata.get("document_id"))
        record = registry.get_document(current_id)
        if record is None:
            continue
        excerpt = document.page_content.strip()
        if len(excerpt) > 500:
            excerpt = excerpt[:500] + "..."
        highlighted_excerpt, highlights = highlight_terms(excerpt, query)
        page = metadata.get("page")
        sources.append(
            {
                "document_id": current_id,
                "filename": record.original_filename,
                "page": page,
                "excerpt": highlighted_excerpt,
                "score": item.score,
                "highlights": highlights,
            }
        )
        contexts.append(
            "\n".join(
                [
                    f"[{record.original_filename} | 第 {page} 页 | 片段 {rank}]",
                    highlighted_excerpt,
                ]
            )
        )

    if not contexts:
        return "检索结果的文档元数据已失效，请重新上传该文档。"
    return _result_payload("文档检索结果：\n\n" + "\n\n".join(contexts), sources)
