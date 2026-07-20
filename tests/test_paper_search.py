from datetime import datetime, timezone

import pytest

from app.schemas.papers import PaperSearchParams
from app.services.paper_search import _build_arxiv_query, search_arxiv


class FakeAuthor:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeArxivResult:
    title = "  Retrieval   Augmented Generation  "
    authors = [FakeAuthor("Ada Lovelace"), FakeAuthor("Alan Turing")]
    summary = "  A paper about retrieval.  "
    published = datetime(2024, 5, 1, tzinfo=timezone.utc)
    updated = datetime(2024, 5, 2, tzinfo=timezone.utc)
    primary_category = "cs.CL"
    categories = ["cs.CL", "cs.IR"]
    entry_id = "https://arxiv.org/abs/2405.00001"
    pdf_url = "https://arxiv.org/pdf/2405.00001"

    def get_short_id(self) -> str:
        return "2405.00001"


class FakeArxivClient:
    def results(self, _search):
        return [FakeArxivResult()]


def test_build_arxiv_query_with_category() -> None:
    query = _build_arxiv_query(PaperSearchParams(query="RAG", category="cs.CL"))
    assert query == "all:RAG AND cat:cs.CL"


def test_build_arxiv_query_rejects_invalid_category() -> None:
    with pytest.raises(ValueError, match="分类格式"):
        _build_arxiv_query(PaperSearchParams(query="RAG", category="invalid category"))


def test_search_arxiv_normalizes_a_provider_result() -> None:
    response = search_arxiv(PaperSearchParams(query="RAG", max_results=1), FakeArxivClient())
    assert response.provider == "arxiv"
    assert response.papers[0].arxiv_id == "2405.00001"
    assert response.papers[0].authors == ["Ada Lovelace", "Alan Turing"]
    assert response.papers[0].title == "Retrieval Augmented Generation"


def test_search_arxiv_filters_by_year() -> None:
    response = search_arxiv(
        PaperSearchParams(query="RAG", start_year=2025, max_results=1), FakeArxivClient()
    )
    assert response.papers == []
