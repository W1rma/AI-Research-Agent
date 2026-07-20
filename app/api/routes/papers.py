import asyncio
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.papers import PaperSearchParams, PaperSearchResponse
from app.services.paper_search import PaperSearchError, search_arxiv

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search", response_model=PaperSearchResponse, status_code=status.HTTP_200_OK)
async def search_papers(
    query: Annotated[str, Query(min_length=1, max_length=200)],
    max_results: Annotated[int, Query(ge=1, le=20)] = 5,
    category: Annotated[str | None, Query(max_length=50)] = None,
    start_year: Annotated[int | None, Query(ge=1991, le=2100)] = None,
    end_year: Annotated[int | None, Query(ge=1991, le=2100)] = None,
    sort_by: Annotated[str, Query(pattern="^(relevance|submitted_date)$")] = "relevance",
) -> PaperSearchResponse:
    """Search arXiv independently of the Agent, useful for API-level testing."""
    try:
        params = PaperSearchParams(
            query=query,
            max_results=max_results,
            category=category,
            start_year=start_year,
            end_year=end_year,
            sort_by=sort_by,
        )
        return await asyncio.to_thread(search_arxiv, params)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except PaperSearchError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
