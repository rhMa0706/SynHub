---
name: synhub-connect
description: 一键接入 SynHub 芯片综合知识库。用户说"接入知识库"、"连接 SynHub"、"用知识库"时触发。
when_to_use: 用户问"接入知识库"、"连接 SynHub"、"用知识库"、"搜索芯片文档"、"低功耗设计资料"时触发
argument-hint: "[query]"
allowed-tools: Bash(python *) Read Write Glob
---

# SynHub 知识库一键接入

SynHub 是芯片综合领域知识库，提供低功耗设计、UPF、CLP 等方向的文档检索。

## 你的任务

当用户调用此 skill 时，执行以下步骤：

### 第 1 步：克隆仓库

在用户的工作目录下克隆仓库（如果还没有的话）：

```bash
git clone https://github.com/rhMa0706/SynHub.git
```

### 第 2 步：安装依赖

```bash
cd SynHub && pip install mcp python-dotenv
```

### 第 3 步：配置环境变量

检查 `SynHub/.env` 是否存在。如果不存在，从 `.env.example` 复制并填入用户的 API Key 和知识库 ID：

```bash
cp .env.example .env
```

提示用户填写：
- `MIFY_API_KEY` — Mify 平台的 API Key
- `MIFY_DATASET_IDS` — 知识库 ID（多个逗号分隔）

### 第 4 步：写入 MCP 配置

检查用户项目根目录是否存在 `.mcp.json`。

**如果不存在**，创建文件写入：

```json
{
  "mcpServers": {
    "synhub": {
      "command": "python",
      "args": ["<克隆路径>/SynHub/adapters/mcp_server.py"]
    }
  }
}
```

**如果已存在**，读取内容，检查是否已有 `synhub` 配置：
- 已有 → 跳过，告知用户配置已就绪
- 没有 → 在 `mcpServers` 中追加 `synhub` 配置

### 第 5 步：验证连接

运行以下命令测试：

```bash
python -c "
from core.mify_client import retrieve
results = retrieve('clock gating', top_k=2)
print(f'Results: {len(results)}')
for r in results:
    print(f'  - {r[\"document_name\"]}')
"
```

- 返回文档 → 告知用户接入成功，重启 Claude Code 即可使用
- 报错 → 根据错误信息排查（API Key、网络等）

### 第 6 步：引导使用

接入成功后，告诉用户：

> 配置完成！重启 Claude Code 后，你可以直接用自然语言提问，例如：
> - "clock gating 怎么做？"
> - "UPF power domain 创建步骤"
> - "CLP error 怎么修"
> - "知识库里有哪些文档？"

## 前置依赖

用户机器需要安装 Python 和以下包：

```bash
pip install mcp python-dotenv
```

如果用户没有安装，先帮他装好再执行上述步骤。

## 注意事项

- 使用 stdio 模式，每个用户本地运行自己的 MCP Server 实例
- 需要克隆完整仓库、配置 API Key
- 无需启动单独的服务端进程，Claude Code 启动时自动拉起
