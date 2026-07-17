from app.rag.pdf_processor import extract_and_chunk_pdf
from app.rag.vector_store import highlight_terms
from app.services.document_registry import DocumentRegistry
from app.services.session_service import SQLiteSessionStore
from app.tools.arxiv_tools import search_arxiv_papers

MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 55>>stream
BT /F1 24 Tf 100 700 Td (Transformer test) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000263 00000 n
0000000370 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
444
%%EOF"""


def test_extract_and_chunk_pdf(tmp_path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(MINIMAL_PDF)
    result = extract_and_chunk_pdf(str(pdf_path), "doc-1", "sample.pdf")
    assert result.page_count == 1
    assert result.chunks[0].metadata["document_id"] == "doc-1"
    assert result.chunks[0].metadata["extraction_method"] == "text"


def test_document_registry_create_and_mark_ready(tmp_path) -> None:
    registry = DocumentRegistry(tmp_path / "documents.json")
    record = registry.create_processing_record("paper.pdf", "paper.pdf")
    updated = registry.mark_ready(record.id, page_count=3, chunk_count=10)
    assert updated.status == "ready"
    assert updated.page_count == 3


def test_sqlite_session_store_persists_history(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "sessions.sqlite3", history_limit=4)
    store.append_turn("session-1", "第一轮问题", "第一轮回答")
    restored_store = SQLiteSessionStore(tmp_path / "sessions.sqlite3", history_limit=4)
    messages = restored_store.get_messages("session-1")
    assert [str(message.content) for message in messages] == ["第一轮问题", "第一轮回答"]


def test_highlight_terms_marks_matching_excerpt() -> None:
    excerpt, highlights = highlight_terms("RAG combines retrieval and generation.", "What is RAG?")
    assert "【rag】" in excerpt.lower()
    assert "rag" in highlights


def test_search_arxiv_papers_rejects_empty_query() -> None:
    assert search_arxiv_papers.invoke({"query": "  "}) == "检索关键词不能为空。"
