"""Small JSON registry for document metadata with atomic writes."""

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from app.core.config import get_settings

DocumentStatus = Literal["processing", "ready", "failed"]


class DocumentRecord(BaseModel):
    id: str
    filename: str
    original_filename: str
    status: DocumentStatus
    page_count: int | None = None
    chunk_count: int = 0
    uploaded_at: str
    error: str | None = None


class DocumentRegistry:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()

    def _read_all(self) -> dict[str, DocumentRecord]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return {key: DocumentRecord.model_validate(value) for key, value in raw.items()}

    def _write_all(self, records: dict[str, DocumentRecord]) -> None:
        payload = {key: value.model_dump() for key, value in records.items()}
        temporary_path = self._path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary_path.replace(self._path)

    def list_documents(self) -> list[DocumentRecord]:
        with self._lock:
            return sorted(self._read_all().values(), key=lambda item: item.uploaded_at, reverse=True)

    def get_document(self, document_id: str) -> DocumentRecord | None:
        with self._lock:
            return self._read_all().get(document_id)

    def create_processing_record(self, original_filename: str, stored_filename: str) -> DocumentRecord:
        record = DocumentRecord(
            id=str(uuid4()),
            filename=stored_filename,
            original_filename=original_filename,
            status="processing",
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            records = self._read_all()
            records[record.id] = record
            self._write_all(records)
        return record

    def mark_ready(self, document_id: str, page_count: int, chunk_count: int) -> DocumentRecord:
        with self._lock:
            records = self._read_all()
            record = records[document_id]
            record.status = "ready"
            record.page_count = page_count
            record.chunk_count = chunk_count
            record.error = None
            records[document_id] = record
            self._write_all(records)
            return record

    def mark_failed(self, document_id: str, error: str) -> DocumentRecord:
        with self._lock:
            records = self._read_all()
            record = records[document_id]
            record.status = "failed"
            record.error = error
            records[document_id] = record
            self._write_all(records)
            return record


@lru_cache
def get_document_registry() -> DocumentRegistry:
    return DocumentRegistry(get_settings().documents_registry_path)
