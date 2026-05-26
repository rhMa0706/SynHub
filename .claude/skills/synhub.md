# SynHub 知识库使用指南

SynHub 是芯片综合领域知识库 MCP Server，为 Claude Code 提供低功耗设计、UPF、CLP 等方向的文档检索能力。

## 架构

```
Claude Code  ←─ MCP 协议 ─→  SynHub Server  ←─ REST API ─→  Mify 知识库
 (LLM + 交互)     (stdio/SSE)    (检索策略层)       (Embedding + 向量检索)
```

## 快速接入（3 步）

### 第 1 步：克隆仓库

```bash
git clone https://github.com/rhMa0706/SynHub.git
cd SynHub
pip install mcp python-dotenv
```

### 第 2 步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入：

```
MIFY_API_KEY=你的-api-key
MIFY_DATASET_IDS=知识库id1,知识库id2
```

### 第 3 步：接入 Claude Code

在你的项目根目录创建或编辑 `.mcp.json`：

```json
{
  "mcpServers": {
    "synhub": {
      "command": "python",
      "args": ["C:\\path\\to\\SynHub\\adapters\\mcp_server.py"]
    }
  }
}
```

重启 Claude Code 即可使用。

## 可用工具

| 工具 | 用法示例 |
|------|----------|
| `search_synthesis_knowledge` | 搜索 "clock gating 最佳实践"、"UPF power domain"、"CLP error LSH" |
| `list_knowledge_categories` | 列出知识库中所有文档 |

## 传输模式切换

在 `.env` 中配置：

```
# stdio 模式（默认，适合个人）
MCP_TRANSPORT=stdio

# SSE 模式（适合团队共享）
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8003
```

SSE 模式下 `.mcp.json` 改为：

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

## 常见问题

**Q: 搜索返回"未找到相关内容"？**
A: 尝试用英文关键词，或换一种表述。知识库以英文 embedding 为主，中文查询会自动桥接但效果有限。

**Q: 如何添加新知识库？**
A: 在 Mify 平台创建数据集后，把 ID 加到 `.env` 的 `MIFY_DATASET_IDS`（逗号分隔）。

**Q: 如何验证连接正常？**
A: 运行 `python tests/test_sse.py`（需先启动 SSE 模式）。
