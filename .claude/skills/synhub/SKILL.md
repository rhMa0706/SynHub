---
name: synhub
description: SynHub 芯片综合知识库 - 一键接入 + 自动检索 + 规范化回答。当用户搜索芯片综合文档(SDC/memory/低功耗)、问 UPF/CLP/clock gating/error code/约束/时序等技术问题、想接入或诊断知识库时使用。
when_to_use: |
  用户问内部综合文档时触发(如"clock gating 怎么做"、"CROSSING_OFF_TO_ON_AON 怎么修"、"UPF power domain 流程");
  接入/诊断/卸载/更新知识库时触发(如"接入 SynHub"、"知识库连不上"、"卸载知识库");
  搜索 SDC/memory/低功耗领域文档时触发。
argument-hint: "[query]"
allowed-tools: Bash(python *) Read Glob AskUserQuestion
---

# SynHub 知识库

接入芯片综合知识库,通过 MCP 工具检索 SDC / memory / 低功耗领域文档。

## 文档地图(按需查阅)

| 场景 | 看哪个 |
|---|---|
| 第一次装 / 同事接入 | [README.md](./README.md) → [docs/onboarding.md](./docs/onboarding.md) |
| 装好后不能用 / 报错 | [docs/troubleshooting.md](./docs/troubleshooting.md) |
| 想调参 / 团队共享 / 高级路由 | [docs/advanced.md](./docs/advanced.md) |
| 想看具体怎么提问 | [examples/usage.md](./examples/usage.md) |

## 何时跑哪个脚本

| 用户意图 | 命令 |
|---|---|
| 接入知识库 | `python <skill-path>/scripts/setup.py` |
| 知识库不工作了 | `python <skill-path>/scripts/doctor.py`(会真打一次 Mify 接口) |
| 升级 SynHub 仓库 | `python <skill-path>/scripts/update.py` |
| 卸载 | `python <skill-path>/scripts/uninstall.py [--remove-repo]` |
| 一键反馈本次回答 | `python <skill-path>/scripts/feedback.py --question ... --answer ... --tool-calls ... --reason ...` |

> `<skill-path>` = `.claude/skills/synhub/`(项目级)或 `~/.claude/skills/synhub/`(全局)。

## 可用 MCP 工具(接入后自动可调)

### `search_synthesis_knowledge(query, top_k=5, dataset_id="")`

搜索知识库,返回最相关的文档片段。

| 参数 | 说明 |
|------|------|
| `query` | 搜索问题(支持中英文、错误码、缩写) |
| `top_k` | 返回结果数,默认 5,复杂调研可调到 10-15 |
| `dataset_id` | 可选,指定知识库 ID 跳过自动路由 |

**返回字段**:`document_name` / `content` / `doc_url` / `score` / `rrf_score`。
**没有"章节"字段**,标注来源时只用 `[document_name]` + `doc_url`,禁止伪造章节名。

### `list_knowledge_categories(dataset_id="")`

列出当前能召回的文档名(去重)。⚠️ 是关键词聚合的**近似列表**,不是 Mify 全量目录。

### `submit_feedback(question, answer, tool_calls, reason="")`

提交反馈到多维表格。当用户对回答不满意或需要改进时使用。

| 参数 | 说明 |
|------|------|
| `question` | 用户的原始问题 |
| `answer` | Claude 给出的回答 |
| `tool_calls` | 本次回答用到的检索 query / 文档 / 思考过程 |
| `reason` | 用户填写的不满意原因(可选) |

## 知识库范围与自动路由

3 个知识库,按查询关键词自动路由:

| 领域 | dataset_id | 触发关键词(部分) |
|------|------|------|
| SDC | `b26e181e-fc6c-4371-8a11-3e19580afd85` | sdc, constraint, timing, clock, false_path, 约束 |
| memory | `fa43ebb5-0333-4e8f-9351-33952daafaec` | memory, sram, mick, vclint, broadway, 触发器 |
| 低功耗 | `99d29d7f-bd5a-491d-b34f-3cb1cef5eac7` | upf, clp, isolation, level_shifter, 功耗, 隔离 |

不传 `dataset_id` 时:命中某领域则只搜该库,跨域(差距 ≤ 1)则并搜,不命中则搜全部 + RRF 融合。

## 回答规范(调用 MCP 后必须遵循)

### 1. 基于检索结果,不编造
- 答案必须以本次检索返回的文档片段为依据,不要用通用知识脑补未命中内容。
- 检索**完全未命中**时,先诚实声明:
  > ⚠️ 知识库未命中相关内容。以下基于通用知识回答,仅供参考,请以实际文档为准。

  然后再用 LLM 自身知识作答,清楚标注"以下非知识库内容"。

### 2. 标注来源
- 每个结论后用 `[document_name]` 标注出处,`doc_url` 放在文末参考链接。
- 多来源用分号:`[doc_A; doc_B]`。
- 只能用检索结果中实际返回的 `document_name`,**禁止伪造章节名**(返回字段里没有章节)。

### 3. 先结论后依据
- 第一段直接给答案,不复述问题、不铺垫。
- 之后再列检索到的关键原文片段作为支撑。

### 4. 给出置信度
末尾标:
- **高**:检索结果直接覆盖问题,证据充分
- **中**:部分覆盖,需要少量推断
- **低**:仅边缘相关,建议进一步确认

### 5. 低召回时建议换关键词
检索结果少于 2 条或相关性明显偏低时,主动建议:
> 💡 当前检索召回较低,建议尝试英文关键词(如 `clock gating` 而非"时钟门控")或更具体的术语再问一次。

### 6. 在回答末尾加反馈入口

每次基于知识库的回答末尾,**必须**附加以下内容:

```
---
💬 **这个回答有问题?**
- 回复"反馈"一键提交
- 或回复"反馈:<原因>"告诉我哪里不对
```

### 7. 交互式反馈收集

当用户回复"反馈"时,使用 AskUserQuestion 工具询问用户具体原因:

```python
AskUserQuestion(
  questions=[{
    "question": "请问哪里不对?请选择或填写原因:",
    "header": "反馈原因",
    "options": [
      {"label": "答案不准确", "description": "回答内容与实际不符"},
      {"label": "缺少关键信息", "description": "回答不够完整，缺少重要内容"},
      {"label": "答非所问", "description": "回答没有解决我的问题"},
      {"label": "其他原因", "description": "请在下方填写具体原因"}
    ],
    "multiSelect": false
  }]
)
```

收集到原因后,调用 `submit_feedback` 工具提交。

## 一键反馈触发规则(关键)

当用户在对话里输入以下任一形式时,立即触发反馈:

- 单独的"反馈"、"feedback"、"不对"、"答非所问"、"这个不准"
- 形如"反馈:XXX"、"反馈,XXX"、"feedback: XXX"(冒号/逗号后是用户填的原因)
- "@反馈"、"/feedback"

**触发后,你(Claude)必须做以下事**:

1. **检查用户是否已提供原因**:
   - 如果用户输入的是"反馈:XXX"或"反馈,XXX"(冒号/逗号后有内容),直接使用该内容作为原因
   - 如果用户只输入了"反馈"、"feedback"等(没有原因),使用 AskUserQuestion 工具询问用户具体原因

2. **从对话上下文里抽取以下信息**(无需问用户,自己整理):
   - `question`:用户最近一次对知识库的实质性提问(不是"反馈"这个词本身)
   - `answer`:你针对那个问题给出的完整回答原文
   - `tool_calls`:你为了回答那个问题调用的工具+参数+关键检索结果摘要,例如:
     ```
     search_synthesis_knowledge(query="CROSSING_OFF_TO_ON_AON", top_k=5)
     检索到文档: doc_A, doc_B
     文档片段(节选): ...
     ```
   - `reason`:用户提供的原因(从"反馈:XXX"中提取,或通过 AskUserQuestion 收集)

3. **调用 submit_feedback 工具**(用 MCP 工具):

   ```python
   submit_feedback(
     question="<上面抽取的 question>",
     answer="<上面抽取的 answer>",
     tool_calls="<上面抽取的 tool_calls>",
     reason="<上面抽取的 reason>"
   )
   ```

4. **告诉用户结果**:
   - 成功 → "✅ 反馈已提交,谢谢!维护者已收到。"
   - 失败 → 把错误信息贴出来,提示用户截图发给维护者。

**绝对不要**:
- 不要让用户手动复述他们的问题或你的回答(那就不是"一键"了)
- 不要在反馈里编造内容,只用对话里实际出现过的
- 不要把上下文里其他无关的对话也塞进 question/answer

## 配置项参考

完整列表见 [docs/advanced.md](./docs/advanced.md)。常用:

| 环境变量 | 默认 | 说明 |
|------|------|------|
| `MIFY_API_KEY` | — | Mify Key(找 rhMa0706 申请) |
| `MIFY_DATASET_IDS` | — | dataset_id,逗号分隔 |
| `MIFY_TOP_K` | 5 | 返回结果数 |
| `MIFY_RRF_K` | 40 | RRF 融合常数 |
| `MIFY_NUM_VARIANTS` | 5 | 查询变体上限 |
| `MCP_TRANSPORT` | stdio | `stdio` / `sse` |
