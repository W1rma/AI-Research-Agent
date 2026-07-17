from app.rag.pdf_processor import extract_and_chunk_pdf
from app.services.document_registry import DocumentRegistry
from app.services.session_service import build_request_messages, create_session_id, store_turn
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
    assert len(result.chunks) >= 1
    assert result.chunks[0].metadata["document_id"] == "doc-1"


def test_document_registry_create_and_mark_ready(tmp_path) -> None:
    registry = DocumentRegistry(tmp_path / "documents.json")
    record = registry.create_processing_record("paper.pdf", "paper.pdf")
    assert record.status == "processing"

    updated = registry.mark_ready(record.id, page_count=3, chunk_count=10)
    assert updated.status == "ready"
    assert updated.page_count == 3
    assert updated.chunk_count == 10


def test_session_service_keeps_history() -> None:
    session_id = create_session_id()
    _, first_messages = build_request_messages(session_id, "第一轮问题")
    assert len(first_messages) == 1

    store_turn(session_id, "第一轮问题", "第一轮回答")
    _, second_messages = build_request_messages(session_id, "第二轮问题")
    assert len(second_messages) == 3


def test_search_arxiv_papers_rejects_empty_query() -> None:
    assert search_arxiv_papers.invoke({"query": "  "}) == "检索关键词不能为空。"
