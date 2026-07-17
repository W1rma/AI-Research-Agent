from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="文档唯一 ID")
    filename: str = Field(..., description="服务端保存的文件名")
    original_filename: str = Field(..., description="用户上传时的原始文件名")
    status: str = Field(..., description="processing / ready / failed")
    page_count: int | None = Field(default=None, description="PDF 页数")
    chunk_count: int = Field(default=0, description="切分后的文本块数量")
    error: str | None = Field(default=None, description="处理失败时的错误信息")


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    original_filename: str
    status: str
    page_count: int | None = None
    chunk_count: int = 0
    uploaded_at: str
    error: str | None = None
