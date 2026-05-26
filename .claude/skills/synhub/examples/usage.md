# SynHub 使用示例

## 在 Claude Code 中使用

接入 SynHub 后，你可以直接用自然语言提问，Claude Code 会自动调用知识库检索。

### 搜索示例

**用户**: "clock gating 怎么做？"
**Claude Code**: 调用 `search_synthesis_knowledge(query="clock gating")`
**返回**: 相关文档片段 + 来源链接

**用户**: "UPF power domain 创建步骤"
**Claude Code**: 调用 `search_synthesis_knowledge(query="UPF power domain creation")`
**返回**: UPF 相关文档

**用户**: "CLP error CROSSING_OFF_TO_ON_AON 怎么修"
**Claude Code**: 调用 `search_synthesis_knowledge(query="CROSSING_OFF_TO_ON_AON CLP error")`
**返回**: CLP 错误码相关文档

### 列出知识库文档

**用户**: "知识库里有哪些文档？"
**Claude Code**: 调用 `list_knowledge_categories()`
**返回**: 文档列表

## 直接调用 MCP Server

### stdio 模式

```bash
python adapters/mcp_server.py
```

### SSE 模式

```bash
# 启动服务
MCP_TRANSPORT=sse python adapters/mcp_server.py

# 测试连接
python tests/test_sse.py
```

## .mcp.json 配置示例

### 个人使用（stdio）

```json
{
  "mcpServers": {
    "synhub": {
      "command": "python",
      "args": ["C:\\Users\\你的用户名\\SynHub\\adapters\\mcp_server.py"]
    }
  }
}
```

### 团队共享（SSE）

```json
{
  "mcpServers": {
    "synhub": {
      "transport": "sse",
      "url": "http://192.168.1.100:8003/sse"
    }
  }
}
```
