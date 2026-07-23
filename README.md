# AI Research Agent

面向学生科研学习场景的 AI Agent。项目基于 FastAPI、LangGraph、Chroma 与 RAG，当前已具备基础 Agent、PDF 知识库问答、会话记忆和工具调用日志能力。

## 当前能力

### 第一周：基础 Agent

- `GET /health`：检查服务是否正常启动。
- `POST /api/v1/chat`：运行 Research Agent，返回最终回答、内部计划和工具调用信息。
- Agent 工作流：`任务规划 → 模型决策 → 工具调用（可选）→ 最终回答`。
- 内置工具：安全算术计算、中国当前日期、学习计划生成。

### 第二周：PDF RAG 知识库

- `POST /api/v1/documents/upload`：上传 PDF，完成文本提取、切分和向量化入库。
- `GET /api/v1/documents` 与 `GET /api/v1/documents/{document_id}`：查看文档处理状态。
- `search_uploaded_documents`：基于已上传 PDF 回答问题，并返回文件名、页码、高亮片段和检索分数。
- 混合检索：向量检索与 BM25 词法检索使用 Reciprocal Rank Fusion 融合排序。
- 会话记忆：聊天历史保存在 `data/sessions.sqlite3`，服务重启后仍可通过 `session_id` 延续。
- 工具日志：调用记录写入 `data/tool_logs.jsonl`。
- 扫描件 OCR：可选功能；开启后使用 Tesseract 对低文本量页面进行识别。

## 本地启动

1. 复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。
2. 激活虚拟环境并安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 启动开发服务：

   ```powershell
   python -m uvicorn main:app --reload
   ```

4. 在浏览器打开 `http://127.0.0.1:8000/docs` 测试接口。

## RAG 验收流程

1. 调用 `POST /api/v1/documents/upload` 上传一篇可复制文本的 PDF，并确认返回 `status: ready`。
2. 调用 `POST /api/v1/chat`：

   ```json
   {
     "message": "根据我上传的论文，作者使用了什么方法？请给出页码依据。"
   }
   ```

3. 确认响应中：
   - `tools_used` 包含 `search_uploaded_documents`；
   - `sources` 包含 `filename`、`page`、带 `【】` 的 `excerpt`；
   - 再次请求时传入上次的 `session_id`，Agent 能延续对话。

## OCR 配置（可选）

默认不启用 OCR。若要解析扫描版 PDF：

1. 在 Windows 安装 Tesseract OCR，并确保安装中文语言包。
2. 在 `.env` 中设置：

   ```env
   PDF_ENABLE_OCR=true
   TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
   ```

3. 重启 FastAPI 服务后再上传扫描版 PDF。

## 测试与验收

项目当前以后端原型为主，尚未构建独立前端。所有功能均可通过自动化测试和 FastAPI Swagger
交互文档复现，不需要编写额外测试脚本。

### 自动化测试

```powershell
python -m pytest
```

测试覆盖基础工具、PDF 处理、文档注册、会话持久化、混合检索、arXiv、公开网页搜索、
来源提取、多 Agent 路由顺序和专业 Agent 工具权限隔离。

### Swagger 接口验收

启动服务后访问 `http://127.0.0.1:8000/docs`，通过 `POST /api/v1/chat` 验证 Supervisor
是否把请求交给了正确的专业 Agent：

| 测试目标 | 示例问题 | `agents_used` | 预期工具 | 预期来源字段 |
| --- | --- | --- | --- | --- |
| Knowledge Agent | 总结我上传的 PDF，并给出页码依据 | `knowledge` | `search_uploaded_documents` | `sources` |
| Literature Agent | 查找 3 篇 RAG 评估方向的 arXiv 论文 | `literature` | `search_arxiv_papers` | `paper_sources` |
| Web Agent | 查找 FastAPI 最新官方文档 | `web` | `search_public_web` | `web_sources` |
| Learning Agent | 制定两周 LangGraph 学习计划 | `learning` | `generate_study_plan` | 无外部来源 |

### Knowledge Agent 完整验证流程

1. 在 Swagger 中调用 `POST /api/v1/documents/upload` 上传一份 PDF，并确认响应状态为
   `ready`。也可以调用 `GET /api/v1/documents` 获取已有文档的 `id`。
2. 调用 `POST /api/v1/chat`：

   ```json
   {
     "message": "总结这篇文档的核心方法，并提供页码依据。",
     "document_ids": ["替换为真实的-document_id"]
   }
   ```

3. 检查响应：
   - `agents_used` 包含 `knowledge`；
   - `tools_used` 包含 `search_uploaded_documents`；
   - `sources` 至少包含一条记录，并带有 `document_id`、`filename`、`page` 和 `excerpt`；
   - `paper_sources` 与 `web_sources` 为空；
   - `answer` 结尾包含本地知识库来源说明。

混合任务可以同时出现多个 `agents_used` 和多个来源字段。例如“比较我上传的论文与最新官方资料”
应至少路由到 Knowledge Agent 与 Web Agent。

## 数据目录

运行时生成的数据均已被 `.gitignore` 忽略：

- `data/uploads/`：原始 PDF。
- `data/vector_store/`：Chroma 向量库。
- `data/documents.json`：文档元数据。
- `data/sessions.sqlite3`：SQLite 会话历史。
- `data/tool_logs.jsonl`：工具调用日志。

## 下一步

- 为 PDF 表格、公式和图片增加更细粒度的解析策略。
- 在前端展示引用片段与高亮位置。
- 继续完善来源可信度策略，并在下一阶段接入更多公开资料源。

## 第三周进度：来源路由与联网资料搜索

- `GET /api/v1/papers/search`：独立检索 arXiv 论文资料。
- `GET /api/v1/web/search`：独立检索公开网页资料，无需额外 API Key。
- Agent 会根据问题路由到本地 PDF 知识库、arXiv 论文或公开网页；混合问题可调用多个来源。
- Chat 响应使用 `sources`、`paper_sources`、`web_sources` 区分三类结果，并在最终回答结尾补充来源说明。

详细约定与测试示例见 `docs/source-routing.md`。

## 第四周进度：多 Agent 架构

- Supervisor Agent 根据问题选择 Knowledge、Literature、Web 或 Learning Agent。
- 每个专业 Agent 只拥有职责范围内的工具权限。
- 混合任务可以依次调用多个专业 Agent，再由 Synthesis Agent 生成统一回答。
- Chat 响应新增 `agents_used` 和 `routing_reason`，用于验证路由过程。

详细架构与扩展方法见 `docs/multi-agent.md`。
