"""Public-web search service backed by the keyless DDGS meta-search client."""

from typing import Any, Protocol

from app.schemas.web import WebResult, WebSearchParams, WebSearchResponse


class WebSearchError(RuntimeError):
    """Raised when the public search provider cannot return a response."""


class WebSearchClient(Protocol):
    def text(self, query: str, **kwargs: Any) -> list[dict[str, Any]]: ...


def _normalize_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _to_web_result(raw_result: dict[str, Any]) -> WebResult | None:
    title = _normalize_text(raw_result.get("title"))
    url = _normalize_text(raw_result.get("href") or raw_result.get("url"))
    if not title or not url.startswith(("https://", "http://")):
        return None
    return WebResult(
        title=title,
        url=url,
        snippet=_normalize_text(raw_result.get("body") or raw_result.get("snippet")),
        published_at=_normalize_text(raw_result.get("date")) or None,
    )


def search_web(
    params: WebSearchParams, client: WebSearchClient | None = None
) -> WebSearchResponse:
    """Search the public web and normalize provider-specific result keys."""
    query = params.query.strip()
    if not query:
        raise ValueError("网页检索关键词不能为空。")

    try:
        if client is None:
            from ddgs import DDGS

            client = DDGS(timeout=10)
        raw_results = client.text(
            query,
            region=params.region,
            safesearch="moderate",
            max_results=params.max_results,
        )
    except Exception as error:
        raise WebSearchError("公开网页检索失败，请稍后重试。") from error

    results: list[WebResult] = []
    seen_urls: set[str] = set()
    for raw_result in raw_results or []:
        if not isinstance(raw_result, dict):
            continue
        result = _to_web_result(raw_result)
        if result is None or result.url in seen_urls:
            continue
        seen_urls.add(result.url)
        results.append(result)
        if len(results) == params.max_results:
            break
    return WebSearchResponse(query=query, results=results)
