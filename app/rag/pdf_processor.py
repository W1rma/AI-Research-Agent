"""Extract and chunk text from PDF files."""

from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import get_settings


@dataclass
class PdfExtractionResult:
    page_count: int
    chunks: list[Document]


def extract_and_chunk_pdf(file_path: str, document_id: str, filename: str) -> PdfExtractionResult:
    """Read a PDF, attach page metadata, and split into retrieval chunks."""
    settings = get_settings()
    reader = PdfReader(file_path)
    raw_documents: list[Document] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        raw_documents.append(
            Document(
                page_content=text,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "page": page_index,
                },
            )
        )

    if not raw_documents:
        raise ValueError("未能从 PDF 中提取到可用文本，请确认文件不是扫描版或加密文档。")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.pdf_chunk_size,
        chunk_overlap=settings.pdf_chunk_overlap,
        separators=["\n\n", "\n", "。", "；", " ", ""],
    )
    chunks = splitter.split_documents(raw_documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    return PdfExtractionResult(page_count=len(reader.pages), chunks=chunks)
