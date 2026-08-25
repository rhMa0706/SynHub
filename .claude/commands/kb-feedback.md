---
description: 一键反馈本次 SynHub 知识库回答给维护者(rhMa0706)。对刚才的提问/回答不满意时直接 /kb-feedback 即可,会弹分类卡让用户选。也可直接 /kb-feedback <原因> 跳过卡片。
argument-hint: [可选:直接填原因跳过分类卡]
allowed-tools: Bash(python *) AskUserQuestion
---

# /kb-feedback — 一键反馈刚才的知识库回答

用户用 `/kb-feedback` 触发这条命令时,你要把**本轮对话中刚刚发生的那次问答**通过本地脚本 `feedback.py` 提交给维护者。脚本会同时发飞书群消息 + 写多维表格(双通道,任一成功即视为成功)。

**不要调用 MCP `mcp__synhub__submit_feedback`** —— 那条路径只写 Bitable,在权限未到位前一定失败,且即使成功也不发群消息。

## 参数

`$ARGUMENTS` 可能为空,也可能是用户填的自由原因(走快捷通道,跳过分类卡)。

## 执行步骤

1. **不要再问"是哪一次问答"** —— 默认就是用户发起 `/kb-feedback` 之前最近一次实质性的 用户问题 → 助手回答。如果当前会话里压根没有这样一对(比如用户一上来就 `/kb-feedback`),才回复一句"还没有可反馈的回答,先问个问题再 /kb-feedback"并停下。

2. **从对话历史中抽取三个字段**:
   - `question`:用户上一条实质性提问的原文(不要包含 `/kb-feedback` 这条本身)。
   - `answer`:你针对那条提问给出的回答正文(完整保留,不要二次概括)。
   - `tool_calls`:那次回答过程中调用的检索工具及关键参数(例如 `search_synthesis_knowledge(query=..., top_k=...)` 命中的 `document_name` 列表、score)。如果那次回答没用任何工具,如实写"未使用知识库检索工具,基于对话上下文直接回答"。

3. **`reason` 字段(关键 — 走分类卡 + 可选自由文本)**:

   **3a. 如果 `$ARGUMENTS` 非空** —— 用户走的是快捷通道,直接把 `$ARGUMENTS` 作为 `reason`,**不要弹分类卡**,跳到第 4 步。

   **3b. 如果 `$ARGUMENTS` 为空** —— 用 `AskUserQuestion` 工具弹一次分类卡,**只问一个问题**:

   ```
   AskUserQuestion(
     questions=[{
       "question": "这个回答的主要问题是?",
       "header": "反馈分类",
       "multiSelect": false,
       "options": [
         {"label": "知识库未覆盖", "description": "Claude 说未命中或基于通用知识答 — 该补文档"},
         {"label": "答非所问", "description": "没回答用户实际问的点"},
         {"label": "引用文档不对", "description": "标注的 [document_name] 跟内容不匹配"},
         {"label": "内容错误", "description": "答了但事实/参数/规则错"},
         {"label": "信息不完整", "description": "答对但漏关键信息(前提/例外/步骤)"}
       ]
     }]
   )
   ```

   - 用户选完后,把选中的 label 包成 `[分类标签]` 拼到 `reason` 里,例如选了"内容错误" → `reason = "[内容错误]"`。
   - 用户走"Other"自定义文本 → 直接把那段文本作为 `reason`(不加方括号,因为不是预定义分类)。
   - 用户取消(没选任何选项) → 把 `reason` 留空字符串提交,继续后续步骤,**不要追问第二次**。

4. **定位 feedback.py**:按下面顺序找,用第一个存在的:
   1. `.claude/skills/synhub/scripts/feedback.py`(项目级 skill)
   2. `~/.claude/skills/synhub/scripts/feedback.py`(用户级 skill,Windows 上是 `C:\Users\<user>\.claude\skills\synhub\scripts\feedback.py`)

   找不到就告诉用户:"没找到 feedback.py,先跑接入流程或检查 skill 是否安装"并停下。

5. **直接调用 Bash 跑脚本**(把四个字段安全转义后传进去,`reason` 即使空字符串也要传):
   ```
   python <feedback.py 路径> --question "<question>" --answer "<answer>" --tool-calls "<tool_calls>" --reason "<reason>"
   ```
   - 在 PowerShell / Bash 里都用双引号包字段,字段内的双引号转义为 `\"`,换行用真实换行(脚本会按 argv 接收完整字符串)。
   - 如果字段太长(>2000 字符),不要自己截断,脚本里有 `MAX_FIELD_LEN` 自动处理。

6. **解析脚本输出**:
   - stdout 末尾出现 `✅ 反馈已发送给 SynHub 维护者,谢谢!` → 回一句简短确认即可,例如"✅ 已反馈给维护者,谢谢"。
   - 出现 `❌ 飞书配置未初始化` 或其他失败信息 → 把脚本最后 5-10 行原文贴出来给用户,让他知道是哪一环挂(凭证缺失/网络/Bitable 权限),并提示可以把这段日志发给 rhMa0706。

## 不要做的事

- 不要重新生成或润色 `answer` —— 反馈的就是**当时那个原版回答**,改了就失真。
- 不要把 `/kb-feedback` 这条用户消息本身当成 `question`。
- 不要追问"你确定要提交吗" / "原因是什么" —— 用户输 `/kb-feedback` 就是确认动作。
- 不要在没有可反馈对象时硬造一份提交。
- 不要回退到 `mcp__synhub__submit_feedback`,即使 `feedback.py` 失败 —— MCP 那条路径漏发飞书群消息,且 Bitable 权限未到位时同样会挂,回退没意义。
