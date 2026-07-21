# 来源路由与联网资料搜索

第三周第二步将 Agent 的外部信息划分为三类，避免将本地文档、论文和普通网页混为同一种证据。

```text
用户问题
   ├─ 已上传 PDF、讲义、笔记 ──> search_uploaded_documents ──> sources
   ├─ 论文、预印本、学术资料 ──> search_arxiv_papers ────────> paper_sources
   └─ 最新动态、官方文档、公开资料 -> search_public_web ───────> web_sources
```

## 公开网页搜索

- 独立接口：`GET /api/v1/web/search`
- 关键词：`query`
- 结果数量：`max_results`，范围 1–10，默认 5
- 区域：`region`，可选 `wt-wt`（全球）、`cn-zh`（中文）或 `us-en`（英文）
- 提供者：`ddgs`。该实现不需要单独的 API Key，但公开搜索服务可能受网络环境和上游限流影响。

示例：

```text
http://127.0.0.1:8000/api/v1/web/search?query=FastAPI%20official%20documentation&max_results=3
```

## Chat 响应约定

- `sources`：仅本地 PDF RAG 引用，`source_type` 为 `local_document`。
- `paper_sources`：仅最后一次成功 arXiv 检索返回的候选论文，`source_type` 为 `paper`。
- `web_sources`：仅最后一次成功公开网页检索返回的网页，`source_type` 为 `web`。
- `answer`：若任意来源工具实际运行，服务端会在结尾补充“来源说明”，标出本地知识库、arXiv 论文或公开网页类别。

网页结果适合时效性信息和官方资料；它们不是同行评审论文，Agent 不应将其表述为学术结论。
