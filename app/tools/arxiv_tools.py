"""LangGraph tool adapter for the arXiv paper-search service."""

import json

from langchain_core.tools import tool

from app.schemas.papers import PaperSearchParams
from app.services.paper_search import PaperSearchError, search_arxiv


@tool
def search_arxiv_papers(
    query: str,
    max_results: int = 5,
    category: str | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    sort_by: str = "relevance",
) -> str:
    """在 arXiv 检索论文，返回标题、作者、摘要、日期和 PDF 链接。"""
    if not query.strip():
        return "检索关键词不能为空。"
    try:
        response = search_arxiv(
            PaperSearchParams(
                query=query,
                max_results=max_results,
                category=category,
                start_year=start_year,
                end_year=end_year,
                sort_by=sort_by,
            )
        )
    except ValueError as error:
        return f"论文检索参数无效：{error}"
    except PaperSearchError as error:
        return str(error)
    return json.dumps(response.model_dump(mode="json"), ensure_ascii=False)
