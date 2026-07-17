from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.documents import DocumentSummary, DocumentUploadResponse
from app.services.document_registry import DocumentRecord
from app.services.document_service import get_document, list_documents, save_uploaded_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_summary(record: DocumentRecord) -> DocumentSummary:
    return DocumentSummary(
        document_id=record.id,
        filename=record.filename,
        original_filename=record.original_filename,
        status=record.status,
        page_count=record.page_count,
        chunk_count=record.chunk_count,
        uploaded_at=record.uploaded_at,
        error=record.error,
    )


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """上传 PDF，保存原文件并完成文本提取、切分与向量化入库。"""
    if file.content_type not in {"application/pdf", "application/x-pdf", "binary/octet-stream", None}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 PDF 文件。")

    try:
        record = await save_uploaded_pdf(file)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败：{error}",
        ) from error

    return DocumentUploadResponse(
        document_id=record.id,
        filename=record.filename,
        original_filename=record.original_filename,
        status=record.status,
        page_count=record.page_count,
        chunk_count=record.chunk_count,
        error=record.error,
    )


@router.get("", response_model=list[DocumentSummary])
async def get_documents() -> list[DocumentSummary]:
    """列出已上传文档及处理状态。"""
    return [_to_summary(record) for record in list_documents()]


@router.get("/{document_id}", response_model=DocumentSummary)
async def get_document_detail(document_id: str) -> DocumentSummary:
    """查询单个文档的处理状态。"""
    record = get_document(document_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文档不存在。")
    return _to_summary(record)
