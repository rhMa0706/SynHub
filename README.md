# SynHub

芯片综合（Synthesis）领域知识库 MCP Server，基于 RAG-Fusion 检索策略，为 Claude Code 提供芯片低功耗设计、UPF 实现、CLP 检查等方向的知识检索能力。

## 架构

```
Claude Code  ←─ MCP 协议 ─→  SynHub Server  ←─ REST API ─→  Mify 知识库
 (LLM + 交互)     (stdio/SSE)    (检索策略层)       (Embedding + 向量检索)
```

SynHub 是**检索策略层**，不做完整 RAG。核心能力：

- **查询扩展**：缩写展开、中英文桥接、文档标题匹配
- **RAG-Fusion**：多变体并行检索 + Reciprocal Rank Fusion 融合排序
- **MCP Server**：stdio / SSE 双模式，接入 Claude Code

## 快速开始

### 1. 安装依赖

```bash
pip install mcp python-dotenv
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 Mify API Key 和知识库 ID
```

### 3. 启动服务

```bash
# stdio 模式（Claude Code 默认）
python adapters/mcp_server.py

# SSE 模式（团队共享）
MCP_TRANSPORT=sse python adapters/mcp_server.py
```

### 4. 接入 Claude Code

在项目根目录的 `.mcp.json` 中配置：

```json
{
  "mcpServers": {
    "synhub": {
      "command": "python",
      "args": ["adapters/mcp_server.py"]
    }
  }
}
```

SSE 模式：

```json
{
  "mcpServers": {
    "synhub": {
      "transport": "sse",
      "url": "http://localhost:8003/sse"
    }
  }
}
```

## MCP Tools

| 工具 | 说明 |
|------|------|
| `search_synthesis_knowledge(query, top_k, dataset_id)` | 搜索芯片综合知识库，返回文档片段 + 来源链接 |
| `list_knowledge_categories(dataset_id)` | 列出知识库中所有文档 |

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MIFY_API_KEY` | — | Mify 平台 API Key |
| `MIFY_DATASET_IDS` | — | 知识库 ID，多个逗号分隔 |
| `MIFY_TOP_K` | 5 | 每次检索返回结果数 |
| `MIFY_RRF_K` | 60 | RRF 融合常数 |
| `MIFY_NUM_VARIANTS` | 5 | 最大查询变体数 |
| `MIFY_RETRIEVE_WORKERS` | 3 | 并行检索线程数 |
| `MCP_TRANSPORT` | stdio | 传输模式：`stdio` 或 `sse` |
| `MCP_HOST` | 0.0.0.0 | SSE 绑定地址 |
| `MCP_PORT` | 8003 | SSE 端口 |

## 项目结构

```
SynHub/
├── core/mify_client.py       # RAG-Fusion 检索引擎
├── adapters/mcp_server.py    # MCP Server
├── config/settings.py        # 配置加载
├── tests/
│   ├── test_mify_client.py   # 单元测试
│   ├── test_sse.py           # SSE 连接测试
│   ├── answer_evaluator.py   # 检索质量评测工具
│   └── eval_questions*.md    # 评测问题集
└── report/                   # 项目报告
```

## 测试

```bash
# 单元测试
pytest tests/test_mify_client.py

# SSE 连接测试
MCP_TRANSPORT=sse python adapters/mcp_server.py &
python tests/test_sse.py
```

## License

Internal use only.
