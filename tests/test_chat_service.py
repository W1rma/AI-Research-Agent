import json
from datetime import date

from langchain_core.messages import AIMessage, ToolMessage

from app.schemas.web import WebResult
from app.services.chat_service import (
    _build_source_notice,
    _extract_paper_sources,
    _extract_tool_calls,
    _extract_web_sources,
)


def _paper(arxiv_id: str) -> dict:
    return {
        "source_type": "paper",
        "provider": "arxiv",
        "arxiv_id": arxiv_id,
        "title": f"Paper {arxiv_id}",
        "authors": ["Ada Lovelace"],
        "abstract": "A test paper.",
        "published_at": date(2024, 1, 1).isoformat(),
        "updated_at": date(2024, 1, 1).isoformat(),
        "primary_category": "cs.CL",
        "categories": ["cs.CL"],
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
    }


def test_paper_sources_uses_the_latest_successful_search() -> None:
    messages = [
        ToolMessage(
            name="search_arxiv_papers",
            tool_call_id="first",
            content=json.dumps({"papers": [_paper("2501.00001")] }),
        ),
        ToolMessage(
            name="search_arxiv_papers",
            tool_call_id="second",
            content=json.dumps({"papers": [_paper("2401.00001"), _paper("2401.00002")] }),
        ),
    ]

    papers = _extract_paper_sources(messages)

    assert [paper.arxiv_id for paper in papers] == ["2401.00001", "2401.00002"]


def test_arxiv_tool_log_is_a_summary_not_the_full_payload() -> None:
    messages = [
        AIMessage(
            content="",
            tool_calls=[{"name": "search_arxiv_papers", "args": {"query": "RAG"}, "id": "call-1"}],
        ),
        ToolMessage(
            name="search_arxiv_papers",
            tool_call_id="call-1",
            content=json.dumps({"papers": [_paper("2401.00001")] }),
        ),
    ]

    logs = _extract_tool_calls(messages)

    assert logs[0].result == "arXiv 返回 1 篇候选论文，完整信息见 paper_sources。"


def test_web_sources_use_the_latest_successful_search() -> None:
    messages = [
        ToolMessage(
            name="search_public_web",
            tool_call_id="first",
            content=json.dumps({"results": [{"title": "Old", "url": "https://old.example"}]}),
        ),
        ToolMessage(
            name="search_public_web",
            tool_call_id="second",
            content=json.dumps(
                {"results": [{"title": "Current", "url": "https://current.example"}]}
            ),
        ),
    ]

    results = _extract_web_sources(messages)

    assert [result.title for result in results] == ["Current"]


def test_source_notice_keeps_web_and_paper_categories_distinct() -> None:
    notice = _build_source_notice(
        [],
        [
            _extract_paper_sources(
                [
                    ToolMessage(
                        name="search_arxiv_papers",
                        tool_call_id="paper",
                        content=json.dumps({"papers": [_paper("2401.00001")]}),
                    )
                ]
            )[0]
        ],
        [WebResult(title="FastAPI", url="https://fastapi.tiangolo.com/")],
    )

    assert "arXiv 论文" in notice
    assert "公开网页" in notice
    assert "FastAPI" in notice
