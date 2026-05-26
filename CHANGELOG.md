# Changelog

## 2026-05-18

### 知识库召回率问题发现

- 测试了 SynHub MCP 知识库检索，发现 93 篇文档中大部分查询返回空结果
- 定位原因：
  1. `mify_client.py` 的 `_build_queries` 只展开 <=5 字符的短缩写，大量 CLP 错误码无法命中
  2. `retrieve` 有 early-break 逻辑——第一个查询变体返回结果就停止，不融合其他变体
  3. 中文查询无法匹配英文 embedding

### 实现 RAG-Fusion 检索策略

**核心改动：** `core/mify_client.py`

- 新增 `_rrf_fuse()` — Reciprocal Rank Fusion 融合函数，公式 `score(d) = Σ 1/(k + rank_i(d))`
- 新增 `_fetch_one_variant()` — 单次 API 调用封装，供线程池并行调用
- 重写 `retrieve()` — 移除 early-break，改为并行检索所有查询变体 → RRF 融合排序
- 扩展 `_build_queries()` — 新增两个策略：
  - 部分缩写展开：对查询中嵌入的缩写做子串替换（如 "ISO cell sizing" → "isolation cell cell sizing"）
  - 中英文桥接：对含中文的查询生成英文同义词变体（如 "功耗" → "power"）
- 新增 `_CN_BRIDGE` 字典：中文芯片术语到英文的映射

**配置改动：** `config/settings.py`

- `MIFY_RRF_K=60` — RRF 常数
- `MIFY_NUM_VARIANTS=5` — 最大查询变体数
- `MIFY_RETRIEVE_WORKERS=3` — 并行线程数

**测试：** `tests/test_mify_client.py`

- 16 个测试全部通过（RRF 融合、查询变体生成、并行检索、错误隔离、去重、top_k 截断）

### 效果验证

- `"UPF"` 查询：生成 5 个变体，召回 3 篇不同文档（之前只召回 1 篇）
- MCP server 需要重启才能使用新逻辑
