# SynHub Skill

> Claude Code skill — 一键接入芯片综合知识库,在对话里直接问"clock gating 怎么做"。

**版本**:v1.0.0
**适用**:芯片综合 / 后端实现工程师
**平台**:Windows / macOS / Linux
**前置**:Python ≥ 3.10、git、Claude Code

## 这是什么

SynHub 是芯片综合领域的内部知识库,通过 MCP 协议接入 Claude Code,覆盖:

- **SDC**:时序约束、clock、uncertainty、latency、false_path
- **memory**:SRAM/ROM/DRAM、Spyglass、Broadway
- **低功耗**:UPF、CLP、isolation、level shifter、power domain

装上这个 skill 后,你在 Claude Code 里直接用自然语言提问,Claude 会自动检索知识库、引用文档原文、标注来源。

## ⚠️ 装好 skill ≠ 能直接用

Claude Code 的 skill 机制只会自动加载 `SKILL.md` 和回答规范,**不会自动执行 `setup.py`**。装好 skill 后,你**仍然要手动跑接入脚本**,把 SynHub 仓库克隆下来、写 `.mcp.json`、填 API Key。

完整流程:

| 步骤 | 谁做 | 自动? |
|---|---|---|
| 1. 装 skill 到 `~/.claude/skills/synhub/` | 平台 | ✅ |
| 2. 找 rhMa0706 申请 Mify API Key | 你 | ❌ |
| 3. 在项目根目录跑 `python ~/.claude/skills/synhub/scripts/setup.py` | 你(或让 Claude 帮跑) | ❌ |
| 4. 编辑 `SynHub/.env` 填入 Key 和 dataset_id | 你 | ❌ |
| 5. 跑 `python ~/.claude/skills/synhub/scripts/doctor.py` 诊断 | 你 | ❌ |
| 6. **重启 Claude Code** | 你 | ❌ |

只有第 1 步是平台自动的,后 5 步必须手动完成。

## 最快的接入方式

**让 Claude 帮你跑**——装好 skill 之后,在 Claude Code 里直接说:

> 接入 SynHub 知识库

Claude 会读 SKILL.md,自动调 `setup.py` + 引导你填 `.env` + 调 `doctor.py` 验证。你只需要:

1. 提前找 **rhMa0706** 申请 Mify API Key
2. 在 Claude 引导你填 `.env` 时,把 Key 和 [3 个 dataset_id](./docs/onboarding.md#第-2-步确认要接入的-dataset_id) 填进去
3. 重启 Claude Code

之后在对话里问:
> 知识库里有哪些文档?

Claude 会自动调 `list_knowledge_categories` 工具并返回文档列表。

## 不想让 Claude 代跑?手动版

```bash
# 1. 接入(克隆 + 装包 + 写 .mcp.json)
python ~/.claude/skills/synhub/scripts/setup.py

# 2. 编辑 SynHub/.env 填入真实 Key 和 dataset_id

# 3. 诊断(真打一次 Mify 接口)
python ~/.claude/skills/synhub/scripts/doctor.py

# 4. 重启 Claude Code
```

完整指南见 **[docs/onboarding.md](./docs/onboarding.md)**。

## 装进哪儿

| 位置 | 效果 |
|---|---|
| `<项目>/.claude/skills/synhub/` | 仅在这个项目里加载 |
| `~/.claude/skills/synhub/` | 全局加载,所有项目可见 |

> 注意:即使 skill 全局装,**MCP server 配置(`.mcp.json`)仍然是项目级的**——每个想用知识库的项目都要跑一次 `setup.py`。SynHub 仓库本身可以用 `--target-dir` 让多项目共用。

## 提供的脚本

| 脚本 | 用途 |
|---|---|
| `scripts/setup.py` | 一键接入:克隆 + 装包 + 写 `.env` 模板 + 写 `.mcp.json` + 校验 |
| `scripts/doctor.py` | 诊断:环境/依赖/配置/真打 Mify 接口,任一失败给修复建议 |
| `scripts/update.py` | 升级 SynHub 仓库(`git pull --ff-only`) |
| `scripts/uninstall.py` | 从 `.mcp.json` 移除 synhub,可选删除仓库 |
| `scripts/feedback.py` | 一键反馈:把当前问题/回答/检索过程发到维护者飞书群(由 Claude 代调,同事不用手敲) |

## 一键反馈

每次知识库回答末尾,Claude 会附加一行:

> 💬 这个回答有问题?回复"反馈"或"反馈:<原因>"一键提交给维护者。

不满意的时候,**直接回复"反馈"**(或"反馈:答非所问"之类带原因的形式),Claude 会:
1. 自动从对话里抓取你的问题、它给的回答、它调的检索工具
2. 打包成飞书消息卡片发到维护者群
3. 告诉你"已提交"

不需要复制粘贴,不需要打开任何外部工具。

## 文档导航

| 文档 | 内容 |
|---|---|
| [docs/onboarding.md](./docs/onboarding.md) | 同事首次接入完整指南(找谁要 Key、dataset_id 列表、6 步流程) |
| [docs/troubleshooting.md](./docs/troubleshooting.md) | 排错手册(按症状定位:安装/配置/运行) |
| [docs/advanced.md](./docs/advanced.md) | 高级用法(自动路由、查询扩展、SSE 共享、参数调优) |
| [examples/usage.md](./examples/usage.md) | 7 个真实场景的提问示例 |
| [SKILL.md](./SKILL.md) | Skill 主入口(Claude Code 自动加载,定义触发条件 + 回答规范) |
| [CHANGELOG.md](./CHANGELOG.md) | 版本历史 |

## 我装了之后能问什么样的问题

详见 [examples/usage.md](./examples/usage.md)。一句话:**任何你以前会去飞书里搜内部综合文档的问题**,装了 skill 后直接问 Claude 即可——Claude 会帮你找文档、提取关键信息、标注来源。

## 反馈 / Bug / 加文档

联系 **rhMa0706(马若涵)**,飞书或 GitHub Issues:<https://github.com/rhMa0706/SynHub/issues>

## 许可

内部使用。请勿外传 API Key 和文档内容。
