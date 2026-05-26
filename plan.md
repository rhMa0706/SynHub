# SynHub — 芯片综合知识库系统实施方案（v2）

## 一、项目目标

搭建一个芯片综合（Synthesis）领域知识库，作为团队经验沉淀的 AI 工具底座。

**架构设计（v2）**：三端分成两条独立线路：

| 线路 | 前端 | 知识库 | 说明 |
|------|------|--------|------|
| **Mify 线** | Mify 聊天 + 飞书机器人 | Mify 平台自带知识库 | 零开发，直接用平台能力 |
| **自建线** | Claude Code（MCP） | 自建 RAG（ChromaDB + BGE） | 本项目核心开发内容 |

**约束**：不自建模型，使用已有 LLM API；对大模型新手落地性强。

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mify 平台（自带知识库）                    │
│                                                                 │
│    ┌──────────────┐              ┌──────────────┐               │
│    │  Mify 聊天   │              │ 飞书机器人    │               │
│    │  (直接用)    │              │ (查 Mify KB) │               │
│    └──────────────┘              └──────────────┘               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────── 绿区（办公网）───────────────────────────────────┐
│                                                                 │
│  开发环境：代码编写、文档撰写、测试                               │
│                                                                 │
│  ┌───────────────────────────────────────┐                     │
│  │  SynHub 绿区副本（只读）               │                     │
│  │                                       │                     │
│  │  ChromaDB ← 仅绿区内容                │                     │
│  │  MCP Server (stdio) → Claude Code     │                     │
│  └───────────────────────────────────────┘                     │
│                                                                 │
│  绿区知识：技术文档、流程规范、培训资料、工具手册                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                 打包 → 安全传输工具 → 红区安装
                       │
┌─────────────── 红区（涉密网）───────────────────────────────────┐
│                                                                 │
│  生产环境：完整知识库                                            │
│                                                                 │
│  ┌───────────────────────────────────────┐                     │
│  │  SynHub 红区主库（完整）               │                     │
│  │                                       │                     │
│  │  ChromaDB ← 红区内容 + 绿区同步内容   │                     │
│  │  MCP Server (stdio + SSE)             │                     │
│  │    → 红区 Claude Code（本地/共享）     │                     │
│  └───────────────────────────────────────┘                     │
│                                                                 │
│  红区独有：RTL 代码、网表、约束、时序报告、综合脚本               │
│  绿区同步：通用技术文档、最佳实践                                 │
└─────────────────────────────────────────────────────────────────┘
```

**关键约束**：
- 红区数据**无法**转绿区（单向隔离）
- 绿区数据**可以**转红区
- 开发在绿区，数据库主库在红区
- 绿区保留只读副本（仅绿区内容），供绿区人员开发调试

**为什么分两条线**：
- Mify 平台自带知识库 + 聊天能力，飞书机器人也能调用，无需重复造轮子
- 自建 RAG 专注服务 Claude Code，承载 Mify 平台不方便放的内容（红区/绿区方案、敏感经验、深度技术细节）
- 两条线独立演进，互不干扰

---

## 三、技术栈选型

| 组件 | 方案 | 选型理由 |
|------|------|----------|
| 语言 | **Python 3.11+** | 生态最丰富，大模型相关库几乎都是 Python 优先 |
| 向量数据库 | **ChromaDB** | `pip install chromadb`，零配置，API 极简，数据持久化本地，适合原型和中小规模 |
| Embedding 模型 | **BAAI/bge-base-zh-v1.5**（sentence-transformers） | 本地运行，约 400MB，无需 GPU，中英双语效果好，芯片领域大量中英混合术语适配性佳 |
| LLM | **mimo-v2.5 pro**（通过 Mify 代理 `http://model.mify.ai.srv/anthropic`） | 已有环境配置，换模型名即可 |
| Web 框架 | **FastAPI** | 异步、自带 Swagger 文档、部署简单 |
| 文档处理 | **unstructured** + **pypdf** | 支持 PDF / Word / Markdown / TXT，芯片文档常见格式 |
| MCP Server | **mcp** Python SDK（FastMCP） | Anthropic 官方 SDK，支持 stdio + SSE 双模式传输 |

> **关于 BGE Embedding 的说明**：BGE（BAAI General Embedding）是北京智源研究院开源的文本向量化模型，作用是把文字翻译成一组数字（向量），用于计算两段文字的语义相似度。例如"clock gating 优化"和"时钟门控功耗降低"虽然用词不同，但 BGE 会把它们映射到相近的向量，从而被向量数据库识别为相关内容。BGE 是"翻译官"，负责找相关的文档；LLM（mimo-v2.5 pro）是"专家"，负责读文档后写回答。选本地 BGE 而非云端 API，原因是团队无 OpenAI API Key，且本地模型离线可用、无调用费用。BGE 只是一个 400MB 的轻量模型，与"自建大模型"是不同概念。

> **关于向量数据库的说明**：向量数据库和 SQL 数据库解决不同的问题。SQL 擅长精确匹配（"找出所有 DC 脚本"），向量数据库擅长语义检索（"找出和 clock gating 最相关的知识"，即使文档里写的是"时钟门控"）。ChromaDB 选型理由：① `pip install chromadb` 零配置，不需要 Docker；② 3 行代码即可使用，对新手最友好；③ 团队级知识库（几千到几万条文档）性能完全够用；④ 未来规模增长可平滑迁移到 Milvus 等更强大的方案。

---

## 四、项目目录结构

```
SynHub/
├── pyproject.toml                 # 项目依赖
├── .env.example                   # 环境变量模板
├── .gitignore
│
├── config/
│   └── settings.py                # 全局配置（从 .env 加载）
│
├── core/                          # ===== 核心 RAG 引擎 =====
│   ├── __init__.py
│   ├── embeddings.py              # BGE Embedding 封装
│   ├── vector_store.py            # ChromaDB 操作封装
│   ├── llm_client.py              # mimo-v2.5 pro 调用封装
│   ├── query_engine.py            # RAG 查询主逻辑（检索 + 生成）
│   └── ingestion.py               # 文档导入管线（解析 + 分块 + 向量化）
│
├── adapters/                      # ===== 前端适配器 =====
│   ├── __init__.py
│   └── mcp_server.py              # Claude Code MCP Server（stdio + SSE）
│
├── knowledge/                     # ===== 知识库内容 =====
│   ├── raw/                       # 原始文档（PDF/Word/PPT）
│   ├── processed/                 # 处理后的 Markdown
│   ├── zone_bridge/               # 红区/绿区打通方案
│   │   ├── zone_overview.md       # 红绿区概述
│   │   ├── data_flow.md           # 数据流转规程
│   │   ├── transfer_tools.md      # 跨区传输工具
│   │   ├── access_guide.md        # 跨区访问指南
│   │   ├── sync_strategy.md       # 知识同步策略
│   │   └── checklist.md           # 跨区操作检查清单
│   └── scripts/                   # 芯片综合脚本示例
│       ├── dc_scripts/
│       ├── genus_scripts/
│       ├── constraints/
│       └── timing_examples/
│
├── scripts/                       # ===== 运维脚本 =====
│   ├── ingest.py                  # 执行文档导入
│   └── serve_mcp.py               # 启动 MCP Server
│
├── tests/
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 五、核心模块设计

### 5.1 配置管理 (`config/settings.py`)

从 `.env` 文件加载环境变量，统一管理所有配置项：

```
LLM_BASE_URL        → Mify 代理地址 (http://model.mify.ai.srv/anthropic)
LLM_API_KEY         → Mify 认证 token
LLM_MODEL           → mimo-v2.5 pro（具体模型名需确认）
EMBEDDING_MODEL     → BAAI/bge-base-zh-v1.5
CHROMA_PERSIST_DIR  → ./data/chroma_db
CHUNK_SIZE          → 文本分块大小（默认 500 字符）
CHUNK_OVERLAP       → 分块重叠（默认 50 字符）
TOP_K               → 检索返回文档数（默认 5）
```

### 5.2 Embedding 模块 (`core/embeddings.py`)

使用 `sentence-transformers` 加载 `BAAI/bge-base-zh-v1.5`：

- `get_embedding(text) → list[float]`：单条文本向量化
- `get_embeddings(texts) → list[list[float]]`：批量向量化（batch_size=32）
- 首次运行自动下载模型到本地缓存，后续加载秒级
- 使用 `normalize_embeddings=True`，配合余弦相似度检索

### 5.3 向量存储 (`core/vector_store.py`)

基于 ChromaDB，封装以下接口：

- `add_documents(texts, metadatas, ids)`：批量添加文档（含 embedding 生成）
- `query(query_text, top_k) → dict`：向量检索，返回文档 + metadata + 距离
- `get_stats() → dict`：返回文档总数、分类列表等统计信息
- `delete_by_source(source)`：按来源删除文档（用于更新）
- 持久化路径：`./data/chroma_db`

### 5.4 LLM 客户端 (`core/llm_client.py`)

使用 `anthropic` SDK，通过 Mify 代理调用 **mimo-v2.5 pro**：

- `ask_with_context(query, context_docs) → str`
- System prompt 角色设定为"芯片综合领域专家"
- 将检索到的文档作为参考资料注入 prompt
- 如果参考资料不足，要求模型如实说明

### 5.5 查询引擎 (`core/query_engine.py`)

RAG 查询的完整流程：

```
用户问题
  ↓
① 向量检索（ChromaDB，返回 Top-K 文档）
  ↓
② 相似度过滤（cosine distance < 阈值才保留）
  ↓
③ 构造上下文（将相关文档拼接为参考资料）
  ↓
④ 调用 LLM 生成回答（参考资料 + 用户问题 → mimo-v2.5 pro）
  ↓
⑤ 返回回答 + 引用来源
```

返回格式：
```json
{
  "answer": "关于 clock gating 的回答...",
  "sources": [
    {"title": "clock_gating_best_practice", "file": "knowledge/scripts/xxx.md", "category": "04-时序优化", "zone": "green"}
  ]
}
```

### 5.6 文档导入管线 (`core/ingestion.py`)

处理流程：解析文档 → 文本分块 → 生成 embedding → 存入 ChromaDB

- 支持格式：PDF、Word (.docx)、Markdown、TXT
- 分块策略：按 500 字符切分，50 字符重叠，尝试在句号/换行处断开
- 每个文档块附带 metadata：`{source, category, title, chunk_index, zone}`
  - `zone` 字段标记文档所属区域：`red`（红区）/ `green`（绿区）/ `bridge`（跨区）/ 空（通用）
- 使用 MD5 哈希生成唯一 ID，支持增量更新（不重复导入）

---

## 六、MCP Server 设计（核心交付物）

### 6.1 双模式传输

MCP Server 支持两种传输模式，覆盖个人开发和团队共享：

| 模式 | 传输方式 | 适用场景 | 启动命令 |
|------|----------|----------|----------|
| **stdio** | 标准输入输出 | 个人本地使用 | `python scripts/serve_mcp.py` |
| **SSE** | HTTP Server-Sent Events | 团队共享 | `python scripts/serve_mcp.py --transport sse --port 8003` |

### 6.2 暴露的工具

| 工具名 | 参数 | 说明 |
|--------|------|------|
| `search_synthesis_knowledge` | `query: str, top_k: int = 5` | 搜索芯片综合知识库 |
| `list_knowledge_categories` | 无 | 列出所有文档分类 |
| `get_zone_bridge_info` | `topic: str` | 查询红区/绿区打通方案 |

### 6.3 暴露的资源

| 资源 URI | 说明 |
|----------|------|
| `synhub://stats` | 知识库统计信息（文档总数等） |

### 6.4 团队共享方案

**阶段 1：本地模式（起步）**

每个团队成员 clone 仓库，本地运行：

```bash
# 每个成员执行
git clone <repo>
cd SynHub
python -m venv .venv && .venv\Scripts\activate
pip install -e .
cp .env.example .env  # 填入 token
python scripts/ingest.py  # 导入文档
```

Claude Code 配置（`~/.claude/settings.json`）：
```json
{
  "mcpServers": {
    "synhub": {
      "command": "python",
      "args": ["C:\\path\\to\\SynHub\\scripts\\serve_mcp.py"],
      "env": {
        "LLM_BASE_URL": "http://model.mify.ai.srv/anthropic",
        "LLM_API_KEY": "your-token"
      }
    }
  }
}
```

**阶段 2：SSE 共享模式**

部署在内网服务器，团队成员通过 URL 连接：

```bash
# 服务器上启动
python scripts/serve_mcp.py --transport sse --port 8003
```

团队成员 Claude Code 配置：
```json
{
  "mcpServers": {
    "synhub": {
      "url": "http://internal-server:8003/sse"
    }
  }
}
```

这样团队成员无需 clone 仓库、无需安装依赖，连接 URL 即可用。

---

## 七、红区/绿区打通方案设计

### 7.1 背景

| 区域 | 网络 | 典型内容 | 数据流向 |
|------|------|----------|----------|
| **红区** | 内网/涉密网 | RTL 代码、网表、约束、时序报告、综合脚本 | 只进不出 |
| **绿区** | 办公网 | 技术文档、流程规范、培训资料、工具手册 | 可以进红区 |

**关键约束**：红区数据无法转绿区，绿区数据可以转红区。自建数据库主库在红区，开发在绿区。

### 7.2 两套部署的内容差异

| 部署位置 | 知识库内容 | 用途 |
|----------|------------|------|
| **红区主库** | 红区独有数据 + 绿区同步过来的通用文档 | 红区人员完整查询 |
| **绿区副本** | 仅绿区内容（通用文档、最佳实践） | 绿区人员开发调试 |

### 7.3 知识同步方向

```
绿区文档（通用技术知识）
  ↓ 绿区可以转红区
红区主库（自动导入绿区内容）
  ↓
红区人员可查询完整知识库

红区经验（脱敏后）
  ✗ 红区数据无法转绿区
  → 红区独有内容只在红区可用
  → 绿区人员无法直接查询红区内容
```

### 7.4 部署流程

```
绿区开发完成
  ↓
打包（代码 + 绿区知识文档）
  ↓
安全传输工具（加密 U 盘 / 数据摆渡 / 安全传输平台）
  ↓
红区接收 → 安装部署 → 导入绿区文档到红区主库
```

### 7.5 自建知识库中需要包含的内容

```
knowledge/zone_bridge/
├── zone_overview.md         # 红绿区网络拓扑、划分原则
├── data_flow.md             # 数据流转方向（绿→红允许，红→绿禁止）
├── transfer_tools.md        # 跨区传输工具（加密 U 盘、数据摆渡、安全传输平台）
├── deploy_guide.md          # 绿区打包 → 红区部署操作指南
├── sync_strategy.md         # 绿区文档如何同步到红区主库
└── checklist.md             # 跨区操作检查清单
```

### 7.6 限制与应对

| 限制 | 影响 | 应对方案 |
|------|------|----------|
| 红区数据不能到绿区 | 绿区人员无法查询红区经验 | 红区经验只能在红区查询；如需共享，需人工脱敏后以通用文档形式放入绿区 |
| 开发和部署分离 | 调试周期长 | 绿区副本用绿区内容验证流程，红区部署后验证完整功能 |
| 打包传输有延迟 | 知识更新不及时 | 建立定期同步机制（如每周一次打包传输） |

---

## 八、知识库内容设计

### 8.1 知识分类体系

```
├── 01-综合基础/        综合流程、DC vs Genus 对比、报告解读
├── 02-TCL脚本/         DC/Genus 常用命令、脚本模板
├── 03-时序约束/        SDC 语法、时钟定义、I/O 约束、多周期/虚假路径
├── 04-时序优化/        critical path 优化、clock gating、timing-driven 综合
├── 05-面积优化/        资源共享、FSM 编码选择、面积报告分析
├── 06-功耗优化/        多阈值电压、功耗报告、低功耗设计
├── 07-DFX/            DFT 插入、BIST 配置、Scan chain
├── 08-后端接口/        综合到布局布线、Netlist 格式、DEF/LEF
├── 09-常见问题/        DRC 修复、LVS 问题、综合失败排查
├── 10-实战案例/        具体模块综合案例、时序收敛经验
└── 11-红区绿区/        跨区打通方案、数据流转规程、安全操作
```

### 8.2 文档格式规范

每个知识文档使用统一的 Markdown 格式（含 frontmatter）：

```markdown
---
category: 04-时序优化
tags: [clock-gating, power, optimization]
tool: [DC, Genus]
zone: green          # red / green / bridge / 空（通用）
author: 张三
date: 2025-01-15
---

# Clock Gating 最佳实践

## 概述
时钟门控是降低动态功耗的关键技术...

## DC 实现方式
```tcl
set_clock_gating_style -sequential_cell latch ...
compile_ultra
```

## 常见问题
1. 门控单元插入后 timing 违例怎么办?
...

## 参考
- DC User Guide Chapter 8
```

### 8.3 知识贡献流程

1. 团队成员在 `knowledge/raw/` 下添加文档（PDF / Word / Markdown 均可）
2. 运行 `python scripts/ingest.py` 执行导入
3. 导入脚本自动：解析 → 分块 → 生成 embedding → 存入 ChromaDB
4. 建议定期（每周/每月）更新知识库

---

## 九、部署策略

### 9.1 绿区：开发环境

绿区是开发环境，搭建本地副本（仅绿区内容），用于开发调试：

```bash
# 1. 创建虚拟环境
cd SynHub
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. 安装依赖
pip install chromadb sentence-transformers anthropic httpx \
    fastapi uvicorn unstructured pypdf mcp pydantic python-dotenv

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env 填入 LLM_API_KEY

# 4. 导入绿区知识文档
python scripts/ingest.py

# 5. 启动 MCP Server（stdio 模式）
python scripts/serve_mcp.py
```

绿区副本只能查询绿区内容（通用文档、最佳实践），无法查询红区独有数据。

### 9.2 红区：生产部署

红区是生产环境，部署完整知识库（红区内容 + 绿区同步内容）：

```bash
# 在红区服务器上
python scripts/ingest.py --source red    # 导入红区文档
python scripts/ingest.py --source green  # 导入从绿区同步来的文档

# 启动 MCP Server（SSE 模式，供红区团队共享）
python scripts/serve_mcp.py --transport sse --port 8003
```

### 9.3 绿区 → 红区同步（Git Bundle）

使用 `git bundle` 将整个仓库（含历史）打包成一个文件，通过安全传输工具搬到红区。

**完整流程**：

```
绿区开发者
  │
  │ ① 写代码/文档，git commit + push（绿区 Git）
  │
  │ ② 打包发布
  │     git bundle create synhub.bundle --all
  │
  │ ③ 通过安全传输工具把 synhub.bundle 搬到红区
  │
红区管理员
  │
  │ ④ 接收并部署
  │     git clone synhub.bundle SynHub
  │     pip install -e .
  │     python scripts/ingest.py
  │     python scripts/serve_mcp.py --transport sse --port 8003
  │
团队成员
  │
  │ ⑤ 配置 Claude Code 连接
  │     "url": "http://红区服务器:8003/sse"
```

**绿区打包**：
```bash
cd SynHub
git bundle create synhub.bundle --all
# 生成 synhub.bundle 文件，通过安全传输工具搬运到红区
```

**红区首次接收**：
```bash
git clone synhub.bundle SynHub
cd SynHub
python -m venv .venv && .venv\Scripts\activate
pip install -e .
cp .env.example .env   # 填入红区 token
python scripts/ingest.py
python scripts/serve_mcp.py --transport sse --port 8003
```

**红区后续更新**（绿区有新提交时）：
```bash
# 绿区重新打包
git bundle create synhub.bundle --all

# 传输到红区后，红区拉取更新
cd SynHub
git fetch synhub.bundle
git merge origin/main
pip install -e .        # 如有新依赖
python scripts/ingest.py  # 重新导入文档
# 重启 MCP Server
```

**哪些进 Git，哪些不进**：

| 内容 | 进 Git？ | 原因 |
|------|----------|------|
| Python 代码 | 是 | 团队共享，版本管理 |
| 知识文档（Markdown） | 是 | 团队共享，版本管理 |
| `.env.example` | 是 | 配置模板，无密钥 |
| `data/chroma_db/` | 否 | 二进制数据，体积大，每环境独立生成 |
| `.env` | 否 | 含 API 密钥，不能暴露 |

### 9.4 部署方式对比

| 环境 | 用途 | 知识库内容 | 服务模式 |
|------|------|------------|----------|
| **绿区本地** | 个人开发调试 | 仅绿区内容 | stdio |
| **红区本地** | 红区个人使用 | 完整内容 | stdio |
| **红区服务器** | 团队共享 | 完整内容 | SSE |

---

## 十、实施路线图

### 阶段 1：MVP — 自建 RAG + MCP（1-2 周）

**目标**：通过 Claude Code MCP 查询芯片综合知识库

1. 创建项目骨架（目录、依赖、配置）
2. 实现核心模块：embeddings → vector_store → llm_client → ingestion → query_engine
3. 实现 MCP Server（先 stdio 模式）
4. 导入红区/绿区文档 + 芯片综合示例文档
5. 配置 Claude Code，验证查询功能

**验收标准**：在 Claude Code 中输入"搜索 SynHub 里关于 clock gating 的知识"，能返回基于知识库的正确回答。

### 阶段 2：Mify + 飞书接入（1 周）

1. 在 Mify 平台搭建知识库，导入文档
2. 配置飞书机器人调用 Mify 知识库
3. 测试两端问答效果

### 阶段 3：团队 MCP 共享（1 周）

1. 实现 MCP Server SSE 传输模式
2. 部署到内网服务器
3. 团队成员配置 Claude Code 连接

### 阶段 4-5：持续优化

- 红区知识同步流程完善
- 检索质量优化（分块策略、Reranker）
- 查询日志与反馈收集
- Docker 部署

---

## 十一、风险与注意事项

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| 红区数据导出受限 | 知识同步受阻 | 手动脱敏导出 + 安全传输工具，建立标准化流程 |
| 芯片文档中代码块/表格解析 | 分块质量差 | `unstructured` 解析后人工检查，必要时手动转 Markdown |
| BGE 模型首次加载慢 | 首次查询体验差 | 预热脚本，或在服务启动时自动加载模型 |
| ChromaDB 单机性能 | 文档量极大时变慢 | 初期足够，后续可迁移到 Milvus/Qdrant |
| 中英混合术语检索 | 语义匹配不准 | BGE 中英双语能力强，可通过增加术语同义词扩展 |
| 知识时效性 | 工具版本更新快 | 建立文档更新机制，定期重新导入 |
| SSE 模式并发 | 多人同时查询 | FastAPI 异步处理，ChromaDB 读操作无锁 |

---

## 十二、关键文件清单（实施顺序）

| 顺序 | 文件 | 作用 |
|------|------|------|
| 1 | `pyproject.toml` | 项目依赖管理 |
| 2 | `.env.example` | 环境变量模板 |
| 3 | `config/settings.py` | 全局配置 |
| 4 | `core/embeddings.py` | BGE Embedding 封装 |
| 5 | `core/vector_store.py` | ChromaDB 向量存储 |
| 6 | `core/llm_client.py` | mimo-v2.5 pro 调用封装 |
| 7 | `core/ingestion.py` | 文档导入管线 |
| 8 | `core/query_engine.py` | RAG 查询主逻辑 |
| 9 | `adapters/mcp_server.py` | MCP Server（stdio + SSE） |
| 10 | `scripts/ingest.py` | 文档导入脚本 |
| 11 | `scripts/serve_mcp.py` | MCP Server 启动脚本 |
| 12 | `scripts/package.sh` | 绿区 → 红区打包脚本 |
| 13 | `knowledge/zone_bridge/*.md` | 红区/绿区打通文档 |

---

## 十三、待确认事项

- **mimo-v2.5 pro 模型名称**：Mify 代理中的具体模型 ID 是什么？
- **Mify 平台知识库接入飞书**：飞书机器人调用 Mify 知识库的具体 API 方式？
- **安全传输工具**：绿区到红区的具体传输工具是什么？（加密 U 盘 / 数据摆渡 / 安全传输平台）
