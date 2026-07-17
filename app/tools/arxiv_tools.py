"""arXiv paper search tool."""

import arxiv
from langchain_core.tools import tool


@tool
def search_arxiv_papers(query: str, max_results: int = 5) -> str:
    """在 arXiv 上检索学术论文。适合查找论文标题、作者、摘要和 arXiv 链接。"""
    query = query.strip()
    if not query:
        return "检索关键词不能为空。"
    if not 1 <= max_results <= 10:
        return "max_results 需在 1 到 10 之间。"

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers: list[str] = []
    for index, result in enumerate(client.results(search), start=1):
        authors = ", ".join(author.name for author in result.authors[:5])
        summary = result.summary.replace("\n", " ").strip()
        if len(summary) > 280:
            summary = summary[:280] + "..."
        papers.append(
            "\n".join(
                [
                    f"{index}. {result.title}",
                    f"   作者: {authors}",
                    f"   发布日期: {result.published.date()}",
                    f"   链接: {result.entry_id}",
                    f"   摘要: {summary}",
                ]
            )
        )

    if not papers:
        return f"未在 arXiv 找到与「{query}」相关的论文。"
    return "arXiv 检索结果：\n" + "\n\n".join(papers)
