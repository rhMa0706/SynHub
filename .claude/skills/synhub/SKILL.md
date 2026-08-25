---
name: synhub
description: SynHub 芯片综合知识库 - 凡是与芯片综合/SDC/memory/STA/低功耗/UPF/CLP/clock gating/error code/约束/时序/FSDB/netlist/STC/lec/IR drop 等任何相关的技术问题,本 skill 一旦加载,必须先调用 mcp__synhub__search_synthesis_knowledge 检索,基于检索结果作答,绝不允许直接用通用知识回答。即使你"知道"答案也必须先检索一次。
when_to_use: |
  ⚠️ 强制规则(必读):本 skill 一旦加载,以下话题的任何问题都必须先调 search_synthesis_knowledge,绝不能跳过检索:
    SDC、约束、constraint、timing、clock、CTS、false_path、multicycle、input_delay、output_delay
    memory、SRAM、ROM、DRAM、register、flip_flop、latch、wrapper、mick、vclint、broadway、spyglass
    STA、PT、PrimeTime、ICC2、Innovus、setup、hold、slack
    低功耗、UPF、CLP、power、isolation、level_shifter、power_domain、power_switch、AON、retention
    FSDB、netlist、STC、LEC、formality、IR drop、EM、DRC、LVS
    任何 EDA 工具的 error code / warning code(如 PTE-XXX、UPF-XXX、CROSSING-XXX 等)
  以及:
    用户明确说"接入/诊断/卸载/更新 SynHub 知识库"的运维场景
    用户输入"反馈"、"feedback"、"/feedback"、"反馈:XXX" 时触发反馈流程
  ⚠️ 即使你已经"知道"答案,也必须先打一次检索,确认知识库是否有更准确的内部资料。
  ⚠️ 检索"完全未命中"时,必须明确告诉用户"知识库未命中",不要伪装成基于知识库回答。
argument-hint: "[query]"
allowed-tools: Bash(python *) Read Glob AskUserQuestion
---

# SynHub 知识库

接入芯片综合知识库,通过 MCP 工具检索 SDC / memory / 低功耗领域文档。

## ⚠️ 第一条规则:先检索,再回答

**本 skill 加载后,凡是上述领域的问题,生成第一句回答之前必须调用过 `mcp__synhub__search_synthesis_knowledge`。**
- 跳过检索直接答 = 违反 skill 约束。
- 即使你确信答案 = 仍然必须检索(知识库可能有内部规范覆盖你的通用知识)。
- 用户没说"用知识库" = 不影响,你看到上述话题就该自己去检索。
- 第一次检索 0 命中 = 至少换 1-2 次关键词再重试(中英文、缩写展开、相关同义词),仍 0 命中才能声明未命中。

## 标准输出模板(每次基于知识库回答按此结构,顺序不可变)

### 模板 A — 检索有命中

```
【结论】
<一两句直接答,不复述问题>

【依据】
- <要点 1> [document_name_1]
- <要点 2> [document_name_2]

【置信度】高 / 中 / 低
- 高:检索结果直接覆盖问题,证据充分
- 中:部分覆盖,需要少量推断
- 低:仅边缘相关,建议进一步确认

【参考文档】
- document_name_1 — doc_url_1
- document_name_2 — doc_url_2

---
💬 这个回答有问题?
- 回复"反馈"一键提交给维护者
- 或回复"反馈:<原因>"附上原因
```

### 模板 B — 检索完全未命中(换 1-2 次关键词后仍 0 条)

```
⚠️ 知识库未命中相关内容(已尝试 query: <关键词1>、<关键词2>)。

以下基于通用知识回答,仅供参考,请以实际文档为准:

<通用知识回答>

💡 建议尝试英文关键词或更具体的术语(例如 <建议词>)再问一次。

---
💬 知识库该补这块内容?
- 回复"反馈"告诉维护者哪个领域需要补文档
```

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

当前接入 16 个知识库,按查询关键词自动路由(完整关键词见 `config/settings.py:DOMAIN_MAP`):

| 领域 | dataset_id | 触发关键词(部分) |
|------|------|------|
| SDC 知识库 | `b26e181e-fc6c-4371-8a11-3e19580afd85` | sdc, constraint, input_delay, output_delay, false_path, multicycle |
| SDC Part2 | `dce185be-b1c9-4a86-bd4d-7e6d43346255` | sdc, constraint, input_delay, output_delay, false_path, multicycle |
| 时序分析 | `bb4d9587-8010-46b1-b8cf-8798b0c6a0eb` | timing, sta, primetime, pt, slack, setup |
| Memory Part1 | `fa43ebb5-0333-4e8f-9351-33952daafaec` | memory, mem, sram, rom, dram, register |
| Memory Part2 | `52dfe94f-507e-4cff-a172-6d86d90bc582` | memory, mem, sram, rom, dram, register |
| 低功耗领域 | `99d29d7f-bd5a-491d-b34f-3cb1cef5eac7` | low_power, upf, clp, power, isolation, level_shifter |
| 低功耗 Part 2 | `e7c1e746-e1d0-4bb3-b378-d36e6fe08291` | low_power, upf, clp, power, isolation, level_shifter |
| DFT | `5c906757-2747-4718-9522-bd17852035ab` | dft, atpg, scan, scan_chain, bist, mbist |
| PPA | `39a13266-3e70-43bb-9e38-32c7ff6e5eea` | ppa, qor, area, power, performance, utilization |
| LEC | `fb33c54a-42ea-45ae-8b1a-668d6c71d8c4` | lec, formality, conformal, equivalence, 等价性检查, 逻辑等价 |
| Signoff | `acc7250a-026f-437f-86bc-28c45f2b383f` | signoff, sign_off, sign-off, release, 交付检查, 签核 |
| 穿线 | `82a67a2c-f83c-41be-9fa8-d8646bdad631` | 穿线, feedthrough, feed_through, port_punch, 打洞, 穿孔 |
| 综合策略 | `2fb30098-e238-4daa-992c-d7b9d735e87c` | synthesis, genus, dc, design_compiler, 综合, 综合策略 |
| 项目经验 | `86fdcf82-e017-4069-bcbc-b38565f3ba46` | 项目经验, 项目总结, 经验, 案例, case_study, lessons |
| 交付 | `a7851884-20e8-47f8-a46f-2492de614646` | 交付, delivery, release, netlist, gds, handoff |
| 复盘 | `e4821655-d759-41ce-ad6d-7d09ee6de943` | 复盘, review, retro, retrospective, postmortem, 问题复盘 |

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
