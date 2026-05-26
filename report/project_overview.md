# SynHub 项目工作总结

## 一、项目简介

SynHub 是一个芯片综合（Synthesis）领域知识库系统，目标是将团队经验沉淀为 AI 工具底座，服务于芯片低功耗设计、UPF 实现、CLP 检查等方向。

**架构定位**：双线路设计

| 线路 | 前端 | 知识库 | 状态 |
|------|------|--------|------|
| Mify 线 | Mify 聊天 + 飞书机器人 | Mify 平台自带知识库 | 已有，直接使用 |
| 自建线 | Claude Code（MCP） | 自建 RAG（Mify API） | 本项目核心 |

---

## 二、已完成的工作

### 2.1 检索引擎：RAG-Fusion 检索策略（`core/mify_client.py`）

**问题背景**：93 篇低功耗领域文档存储在 Mify 平台上，但原始检索存在严重缺陷——大量 CLP error code 无法命中，中文查询无法匹配英文 embedding。

**解决方案**：实现了基于 RAG-Fusion 的多变体检索策略，核心改动在 `core/mify_client.py`（~280 行）。

**具体实现**：

1. **查询扩展（`_build_queries`）**：将单条查询扩展为多个变体
   - 短缩写展开（如 `ISO` → `isolation cell`，`PSW` → `power switch`）
   - 文档标题桥接（纯大写缩写匹配文档标题）
   - 部分缩写展开（查询中嵌入的缩写子串替换）
   - 中英文桥接（如 `功耗` → `power`）

2. **并行检索**：使用 `ThreadPoolExecutor` 并行调用 Mify API 检索所有变体

3. **RRF 融合排序（`_rrf_fuse`）**：Reciprocal Rank Fusion，公式 `score(d) = Σ 1/(k + rank_i(d))`，合并多变体结果，确保被多个变体命中的文档排名更靠前

4. **API 修复**：补全了 Mify retrieve API 的 `retrieval_model` 配置（含 hybrid_search、reranking、embedding 参数），解决了之前返回空结果的问题

**配置参数**（`config/settings.py`）：
- `MIFY_RRF_K=60`：RRF 常数
- `MIFY_NUM_VARIANTS=5`：最大查询变体数
- `MIFY_RETRIEVE_WORKERS=3`：并行线程数

**测试覆盖**：16 个单元测试（`tests/test_mify_client.py`），覆盖 RRF 融合、查询变体生成、并行检索、错误隔离、去重、top_k 截断。

**效果**：`"UPF"` 查询从原来召回 1 篇提升到 3 篇不同文档。

---

### 2.2 MCP Server：Claude Code 知识库接入（`adapters/mcp_server.py`）

基于 FastMCP 实现了 Claude Code 的 MCP Server（~75 行），支持 stdio 和 SSE 双模式传输。

**暴露的工具**：

| 工具 | 功能 |
|------|------|
| `search_synthesis_knowledge(query, top_k)` | 搜索芯片综合知识库，返回文档片段 + 来源链接 |
| `list_knowledge_categories()` | 列出知识库中所有文档 |

**传输模式**：
- **stdio**：个人本地使用，`python scripts/serve_mcp.py`
- **SSE**：团队共享，`python scripts/serve_mcp.py --transport sse --port 8003`

Claude Code 配置后可直接通过 MCP 协议查询知识库，用户提问时自动调用检索并返回结果。

---

### 2.3 评测体系：知识库答案质量检测（`tests/`）

**创建了完整的评测框架**，包含问题集、评测工具和评测报告。

#### 问题集

| 文件 | 题数 | 说明 |
|------|------|------|
| `eval_questions.md` | 98 题 | 通用评测（精准查询 30 + 多文档综合 25 + 语义近似 20 组 + 隐含关联 15 + 边界测试 8） |
| `eval_questions_v2.md` | 98 题 | 通用评测 v2（含难度标注） |
| `eval_questions_lp.md` | 30 题 | 低功耗领域专项（CLP 规则 10 + UPF 实现 8 + LP Cell 5 + 流程配置 4 + 案例分析 3） |

#### 评测工具

| 文件 | 说明 |
|------|------|
| `tests/answer_evaluator.py` | 通用评测工具（~900 行），4 维评分 |
| `tests/check_answers.py` | 低功耗领域专用检测工具 |

#### 评分维度（满分 100，>= 60 通过）

| 维度 | 满分 | 评价内容 |
|------|------|----------|
| **召回率** | 30 | 检索结果是否命中了预期文档所属的分类 |
| **精确率** | 30 | top-K 结果中有多少比例属于预期分类 |
| **检索分** | 20 | RRF 融合质量（融合成功性、分布合理性、排名一致性、结果数量） |
| **内容分** | 20 | 检索结果的原始 embedding score 平均值（语义相似度） |

#### 评测结果（30 题低功耗专项）

| 指标 | 值 |
|------|-----|
| 通过率 | **50.0%**（15/30） |
| 标杆题（>=90） | 1 道（Q22：PSW control/ack port hier 层级对比，90 分） |
| 各维度平均分 | 召回 15.2/30 · 精确 13.6/30 · 检索 16.7/20 · 内容 12.0/20 |

**按类型通过率**：

| 类型 | 通过率 | 平均分 |
|------|--------|--------|
| 案例分析类 | 100% (3/3) | 71.0 |
| UPF 实现类 | 50% (4/8) | 57.6 |
| 流程与配置类 | 50% (2/4) | 59.8 |
| CLP 规则类 | 40% (4/10) | 51.3 |
| LP Cell 类 | 40% (2/5) | 59.6 |

**主要失分题**：
- Q7（CROSSING_OFF_TO_ON_AON）：27 分 — AON 相关文档完全未命中
- Q9（LSH_REDUNDANT）：18 分 — level shifter 冗余文档未命中
- Q11（UPF gen flow）：14 分 — power switch 参数文档未命中

#### 评分维度说明

评测工具（`answer_evaluator.py`）对每题从 4 个维度独立打分，满分 100，>= 60 通过：

| 维度 | 满分 | 评什么 | 计算方式 |
|------|------|--------|----------|
| **召回率** | 30 | 该命中的分类有没有出现 | `命中分类数 / 预期分类数 × 30`。例如预期 2 个分类但只命中 1 个 → 15 分 |
| **精确率** | 30 | 结果中有多少比例是相关的 | `属于预期分类的文档数 / 总检索数 × 30`。例如 top-5 中 3 篇属于预期分类 → 18 分 |
| **检索分** | 20 | RRF 融合排序的质量 | 4 个子项各 5 分：融合是否成功、分数分布是否合理、排名是否一致、结果数量是否充足 |
| **内容分** | 20 | 查询与文档的语义相似度 | 取所有结果的 `score` 平均值，映射到 0~20 分。平均 score >= 0.7 → 20 分，0.5~0.7 → 12~16 分，< 0.3 → 6 分以下 |

**举例**：Q22（PSW control/ack port 对比）得分 90 分 = 召回 25 + 精确 30 + 检索 15 + 内容 20。精确满分说明 top-5 结果全部属于预期分类，内容满分说明语义相似度很高。

---

### 2.4 Mify 平台知识库对接

- 调通了 Mify 的 retrieve API（`https://service.mify.mioffice.cn/api/v1/datasets/{id}/retrieve`）
- 发现并修复了 `retrieval_model` 字段缺失导致检索返回空结果的 bug
- 当前对接了 93 篇低功耗领域文档

---

## 三、项目架构现状

```
SynHub/
├── core/mify_client.py          # RAG-Fusion 检索引擎（核心）
├── adapters/mcp_server.py       # Claude Code MCP Server
├── config/settings.py           # 配置（API Key、RRF 参数等）
├── tests/
│   ├── eval_questions.md        # 通用评测问题集（98 题）
│   ├── eval_questions_v2.md     # 通用评测问题集 v2
│   ├── eval_questions_lp.md     # 低功耗专项评测（30 题）
│   ├── answer_evaluator.py      # 通用评测工具
│   ├── check_answers.py         # 低功耗专项检测工具
│   ├── test_mify_client.py      # 单元测试
│   └── eval_answers_report.md   # 评测报告
├── conclusion/2026-05-18.md     # 工作日志
└── plan.md                      # 项目实施方案 v2
```

---

## 四、能力边界：Mify 平台提供了什么，我们少做了什么

### 4.1 Mify 平台已集成的能力

SynHub 的自建线本质上是一个**薄代理层**——核心检索能力由 Mify 平台提供，我们只做上层适配。以下是 Mify 已经完整交付的基础设施：

| 能力层 | Mify 提供的内容 | SynHub 是否需要自建 |
|--------|-----------------|-------------------|
| **文档管理** | 飞书文档自动同步、版本管理、权限控制、文档预览/编辑 | 不需要 |
| **文档解析** | 飞书文档 HTML → 纯文本/Markdown 转换、表格解析、代码块提取 | 不需要 |
| **文本分块** | 按语义段落自动分块，支持自定义分块大小 | 不需要 |
| **Embedding 生成** | 内置 `text-embedding-3-small`（Azure OpenAI），自动对分块生成向量 | 不需要 |
| **向量存储** | 内置向量数据库，自动持久化、索引、增量更新 | 不需要 |
| **混合检索** | hybrid_search（向量 + 关键词混合检索） | 不需要 |
| **Reranking** | 内置 `gte-rerank-v2`（通义），对初检结果重排序 | 不需要 |
| **检索 API** | 标准 REST API（`/retrieve` 端点），返回带分数的结果 | 不需要 |
| **知识库管理** | Web UI 管理文档、查看统计、调整检索参数 | 不需要 |
| **多端接入** | Mify 聊天界面、飞书机器人 | 不需要（Mify 线直接用） |

**总结**：完整的 RAG 系统需要 6 层基础设施（文档管理 → 解析 → 分块 → Embedding → 向量存储 → 检索），Mify 平台全部覆盖。SynHub 的自建线只做第 7 层——**检索策略适配 + MCP 接入**。

### 4.2 相比完整 RAG 系统，我们少做了什么

对照 `plan.md` 中的完整架构，以下模块因 Mify 的存在而**可以不做**：

#### 可以完全跳过的模块

| plan.md 中的模块 | 对应文件 | 原因 |
|------------------|---------|------|
| Embedding 封装 | `core/embeddings.py` | Mify 内置 `text-embedding-3-small`，无需自建 |
| 向量存储封装 | `core/vector_store.py` | Mify 内置向量数据库，无需 ChromaDB |
| 文档导入管线 | `core/ingestion.py` | Mify 飞书文档自动同步，无需解析/分块/向量化 |
| LLM 调用封装 | `core/llm_client.py` | Claude Code 本身是 LLM，MCP 检索结果直接作为上下文注入 |
| RAG 查询引擎 | `core/query_engine.py` | Claude Code 自己完成"检索 + 生成"，无需单独的 query_engine |
| MCP Server 的 SSE 模式 | `adapters/mcp_server.py` 的 SSE 部分 | Mify 线已有飞书机器人，SSE 共享可后续按需补充 |

#### 仍然需要自建的部分

| 模块 | 为什么不能省 | 当前状态 |
|------|-------------|---------|
| **查询扩展**（`_build_queries`） | Mify API 不做查询变体生成，原始查询对缩写/中文命中率差 | 已完成 |
| **RRF 融合**（`_rrf_fuse`） | Mify API 单次查询返回单次结果，无多变体融合能力 | 已完成 |
| **MCP Server** | Mify 平台不提供 MCP 协议接入，Claude Code 需要 MCP 桥接 | 已完成 |
| **评测体系** | Mify 平台无内置评测功能，检索质量需要自建检测 | 已完成 |
| **中英文桥接** | Mify embedding 对纯中文查询命中率低，需要预处理 | 已完成 |

### 4.3 Mify 平台的局限性（我们补了什么）

Mify 虽然提供了完整的 RAG 基础设施，但在实际使用中暴露了几个问题，SynHub 通过自建层进行了弥补：

| 问题 | 表现 | SynHub 的解决方案 |
|------|------|------------------|
| 查询扩展缺失 | 单条查询对缩写（ISO、PSW）、中英混合查询命中率极低 | `_build_queries` 生成 5 种变体 |
| 无多变体融合 | API 单次调用只用一条查询，无法利用变体间的互补信息 | RRF 融合排序 |
| API 必传字段不明确 | `retrieval_model` 字段缺失时静默返回空结果，无错误提示 | 在 payload 中补全配置 |
| 评测能力为零 | 平台无内置检索质量评测，无法量化回答好坏 | 自建 4 维评测框架（召回/精确/RRF/语义） |
| 前端适配有限 | 只有 Mify 聊天和飞书机器人，不支持 MCP 协议 | MCP Server 桥接 Claude Code |

### 4.4 如果从零搭建完整 RAG，需要额外投入的工作量

假设没有 Mify 平台，要实现 `plan.md` 中的完整自建 RAG，还需要：

| 工作项 | 估计工时 | 说明 |
|--------|---------|------|
| ChromaDB 向量数据库部署 + 持久化 | 2-3 天 | 安装、配置、数据目录管理 |
| BGE Embedding 模型部署 | 1-2 天 | 模型下载、推理服务、batch 处理 |
| 文档解析管线 | 3-5 天 | PDF/Word/Markdown 解析、分块策略调优 |
| LLM 调用封装 + Prompt 工程 | 2-3 天 | System prompt、上下文注入、回答格式化 |
| RAG 查询引擎 | 2-3 天 | 检索 → 过滤 → 上下文拼接 → LLM 生成 |
| 文档更新/增量导入机制 | 1-2 天 | MD5 去重、增量更新、版本管理 |
| **合计** | **11-18 天** | 这些工作因 Mify 的存在而完全省略 |

**实际节省的开发成本**：SynHub 自建线的代码量约 **1200 行**（mify_client ~280 + mcp_server ~75 + 评测工具 ~1680），而完整 RAG 系统预估需要 **3000-4000 行**。Mify 平台让我们用约 1/3 的工作量获得了等效的检索能力。

### 4.5 当前架构的本质

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                       │
│  （LLM + 用户交互 + 回答生成）                        │
│                                                     │
│  用户提问 → MCP 调用 → SynHub 检索 → 返回文档片段    │
│                                                     │
│  Claude Code 自己完成"理解问题 + 阅读文档 + 生成回答" │
└─────────────────────────────────────────────────────┘
                         │ MCP 协议
                         ▼
┌─────────────────────────────────────────────────────┐
│              SynHub MCP Server                       │
│  （薄代理层：查询扩展 + RRF 融合 + 结果格式化）       │
│                                                     │
│  职责：把"查什么"变成"查得准"                         │
└─────────────────────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────┐
│              Mify 平台知识库                          │
│  （文档管理 + Embedding + 向量检索 + Reranking）      │
│                                                     │
│  职责：存储知识 + 返回相关文档片段                     │
└─────────────────────────────────────────────────────┘
```

SynHub 的定位是**检索策略层**，不是 RAG 系统。它解决的核心问题是"Mify 平台检索不够准"，而非"从零搭建 RAG"。

---

## 五、参数传递与 Score 处理机制

### 5.1 参数流图：从 Mify API 到 Claude Code

```
Claude Code 用户提问
    │
    │  MCP 调用: search_synthesis_knowledge(query="...", top_k=5)
    │
    ▼
adapters/mcp_server.py
    │  透传 query, top_k → core.mify_client.retrieve()
    │
    ▼
core/mify_client.py
    │
    ├─ ① _build_queries(query)  ─── 本地处理，不调 API
    │     输出: 最多 MIFY_NUM_VARIANTS(5) 个查询变体
    │     策略: 原始查询 + 缩写展开 + 文档标题桥接 + 部分展开 + 中英桥接
    │
    ├─ ② _fetch_one_variant() × N  ─── 并行调 Mify API
    │     请求 payload:
    │       query:              变体查询文本
    │       top_k:              每个变体返回的文档数（= 用户传入的 top_k）
    │       retrieval_model:    ← 硬编码在代码中，不可配置
    │           search_method: "hybrid_search"
    │           reranking_enable: True
    │           reranking_model: "gte-rerank-v2_mi_sys"
    │           embedding_model: "text-embedding-3-small_mi_sys"
    │           score_threshold_enabled: False   ← 不在服务端过滤
    │           weights: 70% 关键词 + 30% 向量（Mify 默认）
    │
    ├─ ③ _rrf_fuse(variant_results, k=60, top_k)
    │     合并所有变体结果，RRF 融合排序（不过滤 score）
    │     输出: top_k 条结果，每条带 rrf_score + 原始 score
    │
    └─ ④ 返回给 MCP Server → 格式化后返回 Claude Code
```

### 5.2 哪些参数最终传到了 Claude Code

Claude Code 通过 MCP 工具调用拿到的结果**不包含任何原始配置参数**，只包含检索结果本身：

| 返回字段 | 来源 | 含义 |
|----------|------|------|
| `content` | Mify API | 文档片段原文 |
| `score` | Mify API | embedding 语义相似度分数（0~1） |
| `rrf_score` | SynHub 计算 | RRF 融合分数（越高越相关） |
| `document_name` | Mify API | 飞书文档标题 |
| `doc_url` | Mify API | 飞书文档链接 |

Claude Code **看不到**也**不需要关心**以下底层参数：

| 参数 | 当前值 | 谁在用 | Claude Code 是否感知 |
|------|--------|--------|---------------------|
| `top_k` | 5（MCP 工具默认值） | MCP 工具入参 → Mify API | 只影响返回条数，不直接暴露 |
| `MIFY_RRF_K` | 60 | `_rrf_fuse()` 内部 | 不感知 |
| `MIFY_NUM_VARIANTS` | 5 | `_build_queries()` 内部 | 不感知 |
| `MIFY_RETRIEVE_WORKERS` | 3 | 并行线程池大小 | 不感知 |
| `score_threshold_enabled` | False | 发给 Mify API 的请求参数 | 不感知 |
| `reranking_enable` | True | 发给 Mify API 的请求参数 | 不感知 |
| 向量/关键词权重 | 70:30 | 发给 Mify API 的请求参数 | 不感知 |

### 5.3 Score 阈值：Mify 的行为与我们的处理

#### Mify API 的 Score 机制

Mify API 返回的 `score` 是 embedding 语义相似度分数（0~1），**每条结果都带**。API 侧有一个 `score_threshold_enabled` 开关：

| 设置 | Mify 行为 |
|------|----------|
| `score_threshold_enabled: True` | 服务端按阈值过滤，低于阈值的结果**直接丢弃不返回** |
| `score_threshold_enabled: False` | **不过滤**，所有结果按相关度排序后全部返回 |

当前我们设为 `False`。

#### 我们有没有做 Score 过滤

**没有。** `_rrf_fuse()` 的逻辑是所有结果都参与 RRF 融合排序，没有任何 score 过滤：

```python
# mify_client.py — _rrf_fuse()
for results in variant_results:
    for rank, r in enumerate(results):
        # 直接全部参与融合，没有检查 r["score"]
        doc_scores[doc_id] += 1.0 / (k + rank)
```

所有结果（无论 score 多低）都会被返回给 Claude Code，排序完全由 RRF 分数决定。

#### 为什么不做 Score 过滤

| 原因 | 说明 |
|------|------|
| RRF 融合天然排序 | 低分文档在 RRF 融合后排到后面，Claude Code 自然不会重点引用 |
| 避免误杀 | 芯片领域术语多，有些文档 score 偏低但内容高度相关（如缩写匹配），硬阈值会误杀 |
| Claude Code 自行判断 | Claude Code 作为 LLM 有能力判断哪些文档真正有用，比硬阈值更灵活 |
| 评测验证 | 评测工具中用 `score >= 0.5` 作为"相关"的判断标准，实际评测中大部分命中题的 score 在 0.15~0.95 之间，差异很大 |

#### 如果未来要加 Score 过滤

有两种方式：

| 方式 | 位置 | 优点 | 缺点 |
|------|------|------|------|
| **服务端过滤** | 改 `score_threshold_enabled: True` + 设阈值 | 减少返回数据量，降低带宽 | 会丢弃低分但可能相关的文档 |
| **客户端过滤** | 在 `_rrf_fuse()` 里加 `if r["score"] >= threshold` | 可自定义阈值，灵活 | 增加代码复杂度 |

当前两种都没做，检索结果**零过滤**全部传给 Claude Code。

---

## 六、待完成事项

### 6.1 检索质量优化

- 部分 CLP error code 文档检索不到（如 LSH_REDUNDANT、CROSSING_OFF_TO_ON_AON），需要在 Mify 上检查这些文档的 embedding 质量
- `_ABBREV_MAP` 和 `_CN_BRIDGE` 可以补充更多低功耗领域的缩写和中英映射
- 考虑引入 Reranker 进一步提升排序质量

### 6.2 知识库内容扩充

- 当前 93 篇文档偏向低功耗领域，通用综合话题（时序约束、面积优化、DFT、后端接口等）覆盖不足
- 需要扩充到 plan.md 中设计的 11 个分类

### 6.3 流程与工程化

- 评测脚本集成到 CI，每次知识库更新后自动跑评测
- 红区/绿区打包传输流程的自动化（git bundle + 安全传输）
- Docker 部署方案

### 6.4 前端扩展

- 飞书机器人接入 Mify 知识库（Mify 线）
- SSE 模式团队共享部署

### 6.5 内测反馈机制

#### 目标

建立"使用 → 采集 → 分析 → 迭代"的闭环，让每次内测使用都能反哺知识库质量。

#### 方案一：MCP Server 层加日志（最快落地）

在 `adapters/mcp_server.py` 的 `search_synthesis_knowledge` 中加日志，记录每次查询的输入和检索结果：

```python
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "query": query,
    "top_k": top_k,
    "results": [
        {"doc": r["document_name"], "score": r["score"], "rrf": r["rrf_score"]}
        for r in results
    ],
}
# 追加写入 feedback_log.jsonl
```

- **优点**：改动量极小（几行代码），不影响现有逻辑
- **缺点**：只有检索结果，没有 Claude Code 最终生成的回答，无法判断回答质量

#### 方案二：Claude Code hooks 自动记录问答对（完整链路）

利用 Claude Code 的 hooks 机制，在每次 MCP 工具调用后自动捕获完整的问答链路：

```
用户提问 → MCP 检索结果 → Claude Code 生成回答
         ↓ 记录这三段
    feedback_log.jsonl
```

实现方式：
1. 在 `settings.json` 中配置 hook，MCP 工具调用后触发
2. Hook 脚本把 `query + retrieval results + Claude 回答` 写入日志
3. 定期（每周）人工抽检日志，标记回答质量

- **优点**：能看到完整的 RAG 链路，判断是检索问题还是生成问题
- **缺点**：需要配置 Claude Code hooks，稍复杂

#### 方案三：低分自动标记（自动识别差 case）

在方案一的基础上，加自动标记逻辑筛选可能有问题的查询：

```python
flags = []
if not results:
    flags.append("NO_RESULT")          # 检索为空
elif all(r["score"] < 0.3 for r in results):
    flags.append("LOW_RELEVANCE")      # 所有结果分数都很低
elif results[0]["rrf_score"] < 0.01:
    flags.append("WEAK_MATCH")         # RRF 融合分数很低
```

定期将标记的 case 导出，人工审查后决定：
- 补充 `_ABBREV_MAP` / `_CN_BRIDGE` 词典
- 在 Mify 上检查对应文档的 embedding 质量
- 补充评测问题集

- **优点**：自动筛选，不需要人工翻全部日志
- **缺点**：基于启发式规则，可能有误判

#### 建议落地顺序

| 阶段 | 内容 | 估时 |
|------|------|------|
| **第一步** | 方案一 + 方案三：MCP Server 加日志 + 低分自动标记 | 半天 |
| **第二步** | 写导出脚本，每周将标记 case 导出到飞书表格供 review | 半天 |
| **第三步** | 方案二：Claude Code hooks 捕获完整问答对 | 1 天 |
| **持续** | 人工 review → 反哺 `_ABBREV_MAP` / `_CN_BRIDGE` / 评测集 | 每周 |

先落地方案一 + 方案三，成本最低，能覆盖 80% 的需求。方案二作为后续优化，等内测用户量上来后再加。

### 6.6 Mify 数据库申请

- 以项目名义向 Mify 平台申请正式数据库（当前使用的是临时/个人 token）
- 确认数据集归属、权限管理、团队成员访问方式

---

## 七、关键文件说明

| 文件 | 行数 | 作用 |
|------|------|------|
| `core/mify_client.py` | ~280 | 检索引擎核心：查询扩展 + 并行检索 + RRF 融合 |
| `adapters/mcp_server.py` | ~75 | MCP Server：暴露 search/list 工具给 Claude Code |
| `tests/answer_evaluator.py` | ~900 | 通用评测工具：4 维评分 + 报告生成 |
| `tests/check_answers.py` | ~780 | 低功耗专项检测工具 |
| `config/settings.py` | ~17 | 全局配置加载 |

---

*生成时间：2026-05-20*
