"""Upload, ingest, and query uploaded PDF documents."""

import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.rag.pdf_processor import extract_and_chunk_pdf
from app.rag.vector_store import add_document_chunks, delete_document_vectors
from app.services.document_registry import DocumentRecord, get_document_registry


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name.strip()
    if not cleaned.lower().endswith(".pdf"):
        raise ValueError("仅支持上传 PDF 文件。")
    return cleaned.replace(" ", "_")


async def save_uploaded_pdf(upload: UploadFile) -> DocumentRecord:
    settings = get_settings()
    registry = get_document_registry()
    original_filename = upload.filename or "document.pdf"
    stored_filename = _safe_filename(original_filename)
    record = registry.create_processing_record(original_filename, stored_filename)

    document_dir = settings.uploads_dir / record.id
    document_dir.mkdir(parents=True, exist_ok=True)
    destination = document_dir / stored_filename

    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
        ingest_pdf(record.id, destination, stored_filename)
    except Exception as error:
        registry.mark_failed(record.id, str(error))
        raise

    updated = registry.get_document(record.id)
    if updated is None:
        raise RuntimeError("文档记录写入失败。")
    return updated


def ingest_pdf(document_id: str, file_path: Path, filename: str) -> DocumentRecord:
    registry = get_document_registry()
    try:
        delete_document_vectors(document_id)
        extraction = extract_and_chunk_pdf(str(file_path), document_id, filename)
        chunk_count = add_document_chunks(extraction.chunks)
        return registry.mark_ready(document_id, extraction.page_count, chunk_count)
    except Exception as error:
        registry.mark_failed(document_id, str(error))
        raise


def list_documents() -> list[DocumentRecord]:
    return get_document_registry().list_documents()


def get_document(document_id: str) -> DocumentRecord | None:
    return get_document_registry().get_document(document_id)
