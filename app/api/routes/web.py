import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.web import WebSearchParams, WebSearchResponse
from app.services.web_search import WebSearchError, search_web

router = APIRouter(prefix="/web", tags=["web search"])


@router.get("/search", response_model=WebSearchResponse, status_code=status.HTTP_200_OK)
async def search_public_web(
    query: Annotated[str, Query(min_length=1, max_length=200)],
    max_results: Annotated[int, Query(ge=1, le=10)] = 5,
    region: Annotated[Literal["wt-wt", "cn-zh", "us-en"], Query()] = "wt-wt",
) -> WebSearchResponse:
    """Search public web sources independently of the Agent."""
    try:
        params = WebSearchParams(query=query, max_results=max_results, region=region)
        return await asyncio.to_thread(search_web, params)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except WebSearchError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
