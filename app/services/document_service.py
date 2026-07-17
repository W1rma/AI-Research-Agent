"""Safe upload, ingest, and query operations for uploaded PDF documents."""

import asyncio
import shutil
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.rag.pdf_processor import extract_and_chunk_pdf
from app.rag.vector_store import add_document_chunks, delete_document_vectors
from app.services.document_registry import DocumentRecord, get_document_registry


def _safe_filename(name: str) -> str:
    cleaned = Path(name).name.strip().replace(" ", "_")
    if not cleaned.lower().endswith(".pdf"):
        raise ValueError("仅支持上传 PDF 文件。")
    if not cleaned:
        raise ValueError("文件名不能为空。")
    return cleaned


async def _save_pdf_stream(upload: UploadFile, destination: Path, max_bytes: int) -> None:
    total_size = 0
    header = b""
    try:
        with destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                if len(header) < 1024:
                    header += chunk[: 1024 - len(header)]
                total_size += len(chunk)
                if total_size > max_bytes:
                    raise ValueError(f"PDF 大小不能超过 {max_bytes // 1024 // 1024} MB。")
                output.write(chunk)
    finally:
        await upload.close()
    if not header.lstrip().startswith(b"%PDF-"):
        raise ValueError("上传内容不是有效的 PDF 文件。")


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
        await _save_pdf_stream(upload, destination, settings.max_upload_size_mb * 1024 * 1024)
        await asyncio.to_thread(ingest_pdf, record.id, destination, stored_filename)
    except Exception as error:
        registry.mark_failed(record.id, str(error))
        shutil.rmtree(document_dir, ignore_errors=True)
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
