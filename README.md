# AI Research Agent

面向学生科研学习场景的 AI Agent。当前阶段实现了 FastAPI 接口、DeepSeek 模型调用、LangGraph 任务规划、本地工具调用，以及 PDF RAG 知识库。

## 当前能力

### 第一周

- `GET /health`：检查服务是否正常启动。
- `POST /api/v1/chat`：运行 Research Agent，返回最终回答、内部计划摘要和实际调用的工具。
- Agent 工作流：`规划 → 模型决策 → 工具调用（可选）→ 最终回答`。
- 内置工具：安全算术计算、中国当前日期、基础学习计划生成。

### 第二周（RAG 与 PDF 知识库）

- `POST /api/v1/documents/upload`：上传 PDF，保存到 `data/uploads/`，并完成文本提取、切分、向量化入库。
- `GET /api/v1/documents`：列出已上传文档及处理状态。
- `GET /api/v1/documents/{document_id}`：查询单个文档状态。
- `search_uploaded_documents` 工具：Agent 基于已上传 PDF 检索并回答，响应中包含引用来源片段。
- `search_arxiv_papers` 工具：检索 arXiv 论文标题、作者、摘要与链接。
- 会话记忆：聊天接口支持 `session_id` 多轮对话。
- 工具调用日志：写入 `data/tool_logs.jsonl`，并在聊天响应中返回 `tool_calls`。

## 本地启动

1. 复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。(不一定使用 DeepSeek API，其他 OpenAI 兼容模型亦可)
2. 可选：配置 `EMBEDDING_API_KEY` 使用远程 Embedding API；留空则使用 Chroma 内置本地向量模型。
3. 激活虚拟环境后安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. 启动开发服务：

   ```powershell
   python -m uvicorn main:app --reload
   ```

5. 在浏览器打开 `http://127.0.0.1:8000/docs` 测试接口。

## 推荐使用流程

1. 调用 `POST /api/v1/documents/upload` 上传 PDF，确认返回 `status: ready`。
2. 调用 `POST /api/v1/chat`，在 `message` 中提问，可选传入：
   - `session_id`：延续多轮会话
   - `document_ids`：限定 RAG 检索范围
3. 查看响应中的 `answer`、`sources`（引用片段）和 `tool_calls`（工具调用日志）。

## 测试

```powershell
python -m pytest
```

## 数据目录

运行时自动创建（已在 `.gitignore` 中忽略）：

- `data/uploads/`：原始 PDF 文件
- `data/vector_store/`：Chroma 向量库
- `data/documents.json`：文档元数据
- `data/tool_logs.jsonl`：工具调用日志

## 下一步

- 增加会话持久化（SQLite / Redis）。
- 支持扫描版 PDF OCR。
- 增加混合检索（BM25 + 向量）与引用高亮。
