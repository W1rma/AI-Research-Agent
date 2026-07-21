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

## 测试

```powershell
python -m pytest
```

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
