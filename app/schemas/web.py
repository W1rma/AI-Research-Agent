from typing import Literal

from pydantic import BaseModel, Field


class WebSearchParams(BaseModel):
    """Validated input shared by the HTTP route and the Agent tool."""

    query: str = Field(..., min_length=1, max_length=200, description="网页检索关键词")
    max_results: int = Field(default=5, ge=1, le=10, description="最多返回的网页数量")
    region: Literal["wt-wt", "cn-zh", "us-en"] = Field(
        default="wt-wt",
        description="搜索区域：全球、中文或英文",
    )


class WebResult(BaseModel):
    """A normalized public-web result, deliberately distinct from a paper."""

    source_type: Literal["web"] = "web"
    provider: Literal["ddgs"] = "ddgs"
    title: str
    url: str
    snippet: str = ""
    published_at: str | None = None


class WebSearchResponse(BaseModel):
    provider: Literal["ddgs"] = "ddgs"
    query: str
    results: list[WebResult] = Field(default_factory=list)
