"""LangGraph tool adapter for public-web search."""

import json

from langchain_core.tools import tool

from app.schemas.web import WebSearchParams
from app.services.web_search import WebSearchError, search_web


@tool
def search_public_web(
    query: str,
    max_results: int = 5,
    region: str = "wt-wt",
) -> str:
    """检索公开网页资料，适合时效性信息、官方文档和非论文背景资料。"""
    try:
        response = search_web(
            WebSearchParams(query=query, max_results=max_results, region=region)
        )
    except ValueError as error:
        return f"网页检索参数无效：{error}"
    except WebSearchError as error:
        return str(error)
    return json.dumps(response.model_dump(mode="json"), ensure_ascii=False)
