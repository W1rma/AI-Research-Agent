# 多 Agent 架构

第四周第一步将原来的单 Agent 工具循环拆分为 Supervisor、四个专业 Agent 和 Synthesis Agent。

```text
用户请求
   |
Supervisor Agent
   |-- Knowledge Agent  -> search_uploaded_documents
   |-- Literature Agent -> search_arxiv_papers
   |-- Web Agent        -> search_public_web
   `-- Learning Agent   -> calculate / date / study plan
   |
Synthesis Agent
   |
统一回答 + 结构化来源
```

## 各 Agent 职责

- `knowledge`：只处理已上传 PDF、本地论文、讲义和笔记。
- `literature`：只处理 arXiv 论文、预印本和学术论文检索。
- `web`：只处理最新信息、官方文档和公开网页。
- `learning`：处理学习计划、知识解释、日期和计算等学习任务。
- `synthesis`：不调用工具，只汇总专业 Agent 的结果并处理来源差异。

专业 Agent 使用独立工具白名单。新增工具时，应先判断它属于哪个专业 Agent，再加入
`app/agents/specialists.py` 的 `SPECIALIST_TOOLS`，不要默认暴露给所有 Agent。

## 路由机制

Supervisor 优先使用模型的结构化输出生成 `routes` 和 `reason`。如果当前模型不支持结构化路由，
系统会使用确定性的关键词规则作为回退，不会让整个 Chat 请求失败。

混合请求可以选择多个 Agent。例如：

```text
比较我上传的 RAG 论文与最新官方资料，并给出学习建议。
```

预期路由至少包含 `knowledge`、`web` 和 `learning`。各 Agent 顺序执行，最后由 Synthesis Agent
生成一个统一回答。

## Chat 响应新增字段

- `agents_used`：本轮安排的专业 Agent，按执行顺序返回。
- `routing_reason`：Supervisor 的路由原因。
- `tools_used`：各专业 Agent 实际调用的工具。
- `sources`、`paper_sources`、`web_sources`：继续表示三类结构化来源。

这两个新增字段是向后兼容的；原有 `/api/v1/chat` 路径和请求体不变。

## 扩展新 Agent

1. 在 `SpecialistName` 中加入新名称。
2. 为它编写职责明确的 System Prompt。
3. 在 `SPECIALIST_TOOLS` 中配置最小工具权限。
4. 将节点加入主图的路由映射。
5. 增加单一路由、混合路由和工具权限测试。
