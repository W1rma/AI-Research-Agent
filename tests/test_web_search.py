import pytest

from app.schemas.web import WebSearchParams
from app.services.web_search import WebSearchError, search_web


class FakeWebClient:
    def text(self, query: str, **kwargs):
        assert query == "FastAPI official documentation"
        assert kwargs["max_results"] == 3
        return [
            {
                "title": "  FastAPI  ",
                "href": "https://fastapi.tiangolo.com/",
                "body": "  Modern, fast web framework. ",
            },
            {
                "title": "Duplicate URL",
                "href": "https://fastapi.tiangolo.com/",
                "body": "Ignored duplicate",
            },
            {"title": "Invalid result", "href": "not-a-url"},
        ]


class FailingWebClient:
    def text(self, query: str, **kwargs):
        raise RuntimeError("provider unavailable")


def test_search_web_normalizes_and_deduplicates_results() -> None:
    response = search_web(
        WebSearchParams(query="FastAPI official documentation", max_results=3),
        FakeWebClient(),
    )

    assert response.provider == "ddgs"
    assert len(response.results) == 1
    assert response.results[0].source_type == "web"
    assert response.results[0].title == "FastAPI"


def test_search_web_rejects_blank_query() -> None:
    with pytest.raises(ValueError, match="不能为空"):
        search_web(WebSearchParams(query="   "), FakeWebClient())


def test_search_web_wraps_provider_errors() -> None:
    with pytest.raises(WebSearchError, match="公开网页检索失败"):
        search_web(WebSearchParams(query="FastAPI"), FailingWebClient())
