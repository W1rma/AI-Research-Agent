from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class PaperSearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="论文检索关键词")
    max_results: int = Field(default=5, ge=1, le=20, description="最多返回的论文数")
    category: str | None = Field(default=None, max_length=50, description="可选 arXiv 分类，如 cs.CL")
    start_year: int | None = Field(default=None, ge=1991, le=2100, description="可选起始年份")
    end_year: int | None = Field(default=None, ge=1991, le=2100, description="可选结束年份")
    sort_by: Literal["relevance", "submitted_date"] = Field(default="relevance")


class PaperResult(BaseModel):
    source_type: Literal["paper"] = "paper"
    provider: Literal["arxiv"] = "arxiv"
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published_at: date
    updated_at: date
    primary_category: str | None = None
    categories: list[str] = Field(default_factory=list)
    url: str
    pdf_url: str


class PaperSearchResponse(BaseModel):
    provider: Literal["arxiv"] = "arxiv"
    query: str
    papers: list[PaperResult] = Field(default_factory=list)
