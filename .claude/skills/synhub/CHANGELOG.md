# Changelog

## v1.2.0 — 2026-09-18

检索质量闭环 + 用户体验修复。

### 新增

- **错误码检索增强** — `_tech_id_re` 新增 `[A-Z]+-\d{2,4}` 分支覆盖 PTE-060 / UITE-529 / SEL-001 形态，配合数字补零命中团队文档标题惯例；新增策略 2.6 问答意图扩展，检出错误码+意图时追加 `<token> 描述/根因分析/怎么fix/Name` 四条 RRF 变体；`errcode_variants` 截断保护确保错误码变体不被低价值变体挤掉。v3 通过率 88.7% → 92.5%
- **MCP tool description 错误码判定硬约束** — `search_synthesis_knowledge` docstring 增加 ~40 行判定规则，未命中时强制声明、严禁基于共现脚本片段编造定义
- **RRF 评分重写** — 从 4 个定性项改为 4 个定量项（排名集中度 / 分数下降梯度 / 尾部分离度 / 分数熵），每项有明确计算公式和阈值
- **kb-feedback 用户名采集** — `feedback.py` 新增 `--user` 参数，Bitable 字段从 7 列扩为 8 列（新增 `user` 列）；分类卡从 1 问题扩为 2 问题（反馈分类 + 用户名）；选项数适配 AskUserQuestion 2–4 限制
- **`.mcp.json` 注入 16 库 `MIFY_DATASET_IDS`** — MCP server 启动时直接用

### 修复

- **飞书文档 URL 归一化** — 新增 `_normalize_doc_url`，Mify 签名链接自动替换为 `mi.feishu.cn/docx/<token>` 原始链接，解决用户浏览器打不开问题

---

## v1.1.0 — 2026-08-25

16 库全景接入 + retriever 并列结构切分。

### 新增

- **DOMAIN_MAP 3→16 库全量接入** — 覆盖 SDC / 时序 / Memory / 低功耗 / DFT / PPA / LEC / Signoff / 穿线等全部 16 个知识库
- **短关键词词边界修复** — `_kw_hit()` 对 ≤4 char 纯 ASCII 关键词强制词边界，修复 `ff/pd/rc/mc` 一族子串误伤
- **`update.py` 全同步** — 从单纯 `git pull` 进化为 `.env` / `.mcp.json` / `SKILL.md` 三处同步，新用户装完自动补齐 16 库
- **并列结构切分策略** — 策略 1.7 `_split_conjunction()`，对"A 和 B 分别…"类复合 query 拆为两条子 query + 原句参与 RRF 融合。v3 通过率 81.1% → 88.7%
- **kb-feedback 分类卡** — 空原因时弹 5 类分类卡，选中的 label 包成 `[标签]` 拼进 reason
- **datasets.json** — DOMAIN_MAP 序列化数据文件，供 `update.py` 消费
- **colleague-guide.md** — 同事接入指南（凭证走占位符，真值飞书私聊）

### 修复

- **Windows GBK 控制台 emoji 崩溃** — `update.py` 顶部加 `sys.stdout.reconfigure(encoding='utf-8')`
- **SDC/Memory/低功耗 alias 指向修正** — `_KB_ALIAS_TO_ID` 重新指向 Part 2 库（飞书批量导入的库），老库以 `-legacy` 保留
- **GitHub Push Protection 拦 secret** — colleague-guide.md 凭证替换为 `<向维护者索取>` 占位符

---

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
