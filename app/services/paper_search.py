"""Provider-agnostic paper-search service; arXiv is the first provider."""

import re

import arxiv

from app.schemas.papers import PaperResult, PaperSearchParams, PaperSearchResponse


class PaperSearchError(RuntimeError):
    """Raised when a remote paper provider cannot complete a search."""


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _build_arxiv_query(params: PaperSearchParams) -> str:
    terms = [f"all:{params.query.strip()}"]
    if params.category:
        category = params.category.strip()
        if not re.fullmatch(r"[a-zA-Z-]+\.[a-zA-Z-]+", category):
            raise ValueError("arXiv 分类格式应类似 cs.CL 或 stat.ML。")
        terms.append(f"cat:{category}")
    return " AND ".join(terms)


def _to_paper_result(result: arxiv.Result) -> PaperResult:
    return PaperResult(
        arxiv_id=result.get_short_id(),
        title=_normalize_text(result.title),
        authors=[author.name for author in result.authors],
        abstract=_normalize_text(result.summary),
        published_at=result.published.date(),
        updated_at=result.updated.date(),
        primary_category=getattr(result, "primary_category", None),
        categories=list(getattr(result, "categories", []) or []),
        url=result.entry_id,
        pdf_url=result.pdf_url,
    )


def search_arxiv(params: PaperSearchParams, client: arxiv.Client | None = None) -> PaperSearchResponse:
    """Search arXiv and apply year filtering after the provider returns results."""
    if not params.query.strip():
        raise ValueError("检索关键词不能为空。")
    if params.start_year and params.end_year and params.start_year > params.end_year:
        raise ValueError("start_year 不能晚于 end_year。")

    sort_criterion = (
        arxiv.SortCriterion.Relevance
        if params.sort_by == "relevance"
        else arxiv.SortCriterion.SubmittedDate
    )
    search = arxiv.Search(
        query=_build_arxiv_query(params),
        max_results=params.max_results * 3 if (params.start_year or params.end_year) else params.max_results,
        sort_by=sort_criterion,
    )
    active_client = client or arxiv.Client(page_size=params.max_results, delay_seconds=1, num_retries=2)

    try:
        candidates = active_client.results(search)
        papers: list[PaperResult] = []
        seen_ids: set[str] = set()
        for result in candidates:
            paper = _to_paper_result(result)
            if params.start_year and paper.published_at.year < params.start_year:
                continue
            if params.end_year and paper.published_at.year > params.end_year:
                continue
            if paper.arxiv_id in seen_ids:
                continue
            seen_ids.add(paper.arxiv_id)
            papers.append(paper)
            if len(papers) == params.max_results:
                break
    except Exception as error:
        raise PaperSearchError("arXiv 检索失败，请稍后重试。") from error

    return PaperSearchResponse(query=params.query.strip(), papers=papers)
