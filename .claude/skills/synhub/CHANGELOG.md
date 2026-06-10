# Changelog

## v1.0.0 — 2026-06-04

首个对外发布版本。

### 新增

- **一键接入脚本** `scripts/setup.py`
  - 检查 Python ≥ 3.10、git
  - 自动装 `mcp` / `python-dotenv` / `httpx`
  - 克隆 SynHub 仓库(支持 `--target-dir`)
  - 生成完整 `.env` 模板(含 RAG-Fusion / LLM 配置)
  - 在项目 `.mcp.json` 追加 synhub 配置(不覆盖已有 server)
  - 跨平台:Windows / macOS / Linux
- **诊断脚本** `scripts/doctor.py`
  - 7 项检查:Python 版本 / git / 依赖 / 仓库 / `.env` / `.mcp.json` / **真打 Mify 接口**
  - 任一失败给出具体修复建议
- **更新脚本** `scripts/update.py` — `git pull --ff-only` SynHub 仓库
- **卸载脚本** `scripts/uninstall.py` — 从 `.mcp.json` 移除 synhub,可选删除仓库
- **文档**
  - `README.md` 平台展示页
  - `docs/onboarding.md` 同事首次接入完整指南
  - `docs/troubleshooting.md` 排错手册
  - `docs/advanced.md` 高级用法(自动路由、SSE 共享、参数调优)
  - `examples/usage.md` 7 个真实提问场景
- **回答规范**(`SKILL.md`)
  - 基于检索结果,不编造;未命中时诚实声明
  - 用 `[document_name]` 标注来源,禁止伪造章节名
  - 先结论后依据
  - 给出置信度(高/中/低)
  - 低召回时建议换关键词

- **一键反馈** `scripts/feedback.py`
  - 同事在对话里打"反馈"或"反馈:原因",Claude 自动抽取问题/回答/检索过程并 POST 到维护者飞书群机器人
  - 飞书消息卡片格式,含提问/回答/检索 query/用户填写原因/系统信息
  - 长内容自动截断,失败时输出 JSON 让用户手贴

### 已知限制

- `list_knowledge_categories` 返回的是关键词聚合的近似列表,不是 Mify 全量目录
- SSE 模式的 `transport_security` 白名单需要管理员手动改 `adapters/mcp_server.py`
- 不支持自动检测 SynHub 仓库版本,升级要手动跑 `update.py`
- 反馈脚本里的 webhook URL 需要 skill 维护者填实际地址(默认是 REPLACE_ME 占位符)

## 路线图

- [ ] `setup.py` 自动检测项目根并提示;支持非交互模式(CI 友好)
- [ ] `doctor.py` 输出 JSON 格式,方便接入监控
- [ ] 一键导出诊断包(脱敏后)用于报 bug
- [ ] 支持 dataset_id 元信息查询(`describe_dataset` 工具)
