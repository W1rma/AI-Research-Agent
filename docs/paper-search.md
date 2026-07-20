# 论文检索基础层

当前论文检索提供者为 arXiv。实现分为三个层次：

```text
FastAPI /api/v1/papers/search
              │
       paper_search.py
              │
        arXiv Python API

LangGraph Agent ──> search_arxiv_papers 工具 ──> 同一 service
```

## 独立接口测试

启动服务后，在 Swagger 页面或浏览器访问：

```text
http://127.0.0.1:8000/api/v1/papers/search?query=RAG&max_results=3&category=cs.CL
```

响应中的每篇论文都标记为：

```json
{
  "source_type": "paper",
  "provider": "arxiv"
}
```

## Agent 测试

向 `POST /api/v1/chat` 发送：

```json
{
  "message": "帮我找 3 篇 2024 年 RAG 评估方向的 arXiv 论文，并给出阅读建议。"
}
```

预期：`tools_used` 包含 `search_arxiv_papers`，且 `paper_sources` 返回论文的标题、作者、摘要、日期和 PDF 链接。`sources` 字段仍仅表示本地 PDF 的 RAG 引用。

## 响应字段约定

- `sources`：仅本地 PDF 知识库（RAG）的引用。
- `paper_sources`：本轮 **最后一次成功** arXiv 检索返回的候选论文。它是可追溯的检索结果，不承诺与模型在自然语言回答中最终推荐的论文逐字一一对应。
- `tool_calls`：用于调试和审计的工具调用摘要。对 arXiv 搜索只保留候选数量，完整的论文数据只在 `paper_sources` 返回，避免摘要被重复传输。

当用户限定单一年份时，Agent 会同时传入 `start_year` 和 `end_year`；例如“2024 年的 RAG 论文”会被限制为 2024 年，而不是“2024 年以后”。
