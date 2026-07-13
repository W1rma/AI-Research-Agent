# AI Research Agent

面向学生科研学习场景的 AI Agent。当前阶段实现了 FastAPI 接口、DeepSeek 模型调用、LangGraph 任务规划与本地工具调用。

## 当前能力（第一周）

- `GET /health`：检查服务是否正常启动。
- `POST /api/v1/chat`：运行 Research Agent，返回最终回答、内部计划摘要和实际调用的工具。
- Agent 工作流：`规划 → 模型决策 → 工具调用（可选）→ 最终回答`。
- 内置工具：安全算术计算、中国当前日期、基础学习计划生成。

## 本地启动

1. 复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。(不一定使用deepseek api其他AI模型亦可)
2. 激活虚拟环境后安装依赖：

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. 启动开发服务：

   ```powershell
   python -m uvicorn main:app --reload
   ```

4. 在浏览器打开 `http://127.0.0.1:8000/docs` 测试接口。

## 测试

```powershell
python -m pytest
```

## 下一步

- 增加 arXiv 论文检索工具。
- 为 Agent 接入 PDF RAG 知识库工具。
- 增加会话记忆、引用来源和工具调用日志。
