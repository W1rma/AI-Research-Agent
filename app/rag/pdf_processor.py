"""Extract PDF text and optionally use OCR for scanned pages."""

import io
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import Settings, get_settings


@dataclass
class PdfExtractionResult:
    page_count: int
    chunks: list[Document]


def _ocr_page(pdf_page, settings: Settings) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as error:
        raise ValueError("OCR 依赖未安装，请重新安装 requirements.txt。") from error

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    try:
        pixmap = pdf_page.get_pixmap(matrix=__import__("fitz").Matrix(2, 2), alpha=False)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        return pytesseract.image_to_string(image, lang="chi_sim+eng").strip()
    except pytesseract.TesseractNotFoundError as error:
        raise ValueError("未找到 Tesseract。请安装它，并在 .env 设置 TESSERACT_CMD。") from error


def extract_and_chunk_pdf(file_path: str, document_id: str, filename: str) -> PdfExtractionResult:
    """Read each page, preserve page metadata, then split text into retrieval chunks."""
    settings = get_settings()
    reader = PdfReader(file_path)
    raw_documents: list[Document] = []
    ocr_pdf = None
    try:
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            extraction_method = "text"
            if len(text) < settings.ocr_min_text_characters and settings.pdf_enable_ocr:
                try:
                    import fitz
                except ImportError as error:
                    raise ValueError("OCR 依赖未安装，请重新安装 requirements.txt。") from error
                ocr_pdf = ocr_pdf or fitz.open(file_path)
                ocr_text = _ocr_page(ocr_pdf[page_index - 1], settings)
                if len(ocr_text) > len(text):
                    text = ocr_text
                    extraction_method = "ocr"
            if not text:
                continue
            raw_documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "document_id": document_id,
                        "filename": filename,
                        "page": page_index,
                        "extraction_method": extraction_method,
                    },
                )
            )
    finally:
        if ocr_pdf is not None:
            ocr_pdf.close()

    if not raw_documents:
        raise ValueError(
            "未能从 PDF 提取文本。若这是扫描件，请安装 Tesseract，并设置 PDF_ENABLE_OCR=true。"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.pdf_chunk_size,
        chunk_overlap=settings.pdf_chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""],
    )
    chunks = splitter.split_documents(raw_documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
    return PdfExtractionResult(page_count=len(reader.pages), chunks=chunks)
