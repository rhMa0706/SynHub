# 接入指南(给同事)

从零到能在 Claude Code 里问"clock gating 怎么做"——全部步骤。

## 谁应该装这个 skill

- 做芯片综合 / 后端实现的工程师
- 想在 Claude Code 里直接搜内部知识库(SDC、memory、低功耗)的人
- 用 AI 写代码时希望答案有团队文档背书的人

## 前置要求

| 项 | 版本/说明 | 检查命令 |
|---|---|---|
| Python | ≥ 3.10 | `python --version` |
| git | 任意现代版本 | `git --version` |
| Claude Code | 最新版 | `claude --version` |
| 网络 | 能访问 `service.mify.mioffice.cn` | `curl -I https://service.mify.mioffice.cn` |

公司外网 / 无 VPN 状态下访问不了 Mify,需要先连内网。

## 第 1 步:拿 API Key

**找 rhMa0706(马若涵)申请**,告诉他你的飞书工号。Key 形如:

```
dataset-XXXXXXXXXXXXXXXXXXXXX
```

> ⚠️ Key 是个人凭证,**不要提交到 git、不要发群里**。如果泄露,马上联系签发人吊销。

## 第 2 步:确认要接入的 dataset_id

当前公开的 3 个知识库(全部接入即可,不冲突):

| 领域 | dataset_id | 覆盖内容 |
|---|---|---|
| SDC | `b26e181e-fc6c-4371-8a11-3e19580afd85` | 时序约束、clock、uncertainty、latency、input/output_delay、false_path |
| memory | `fa43ebb5-0333-4e8f-9351-33952daafaec` | SRAM/ROM/DRAM、寄存器、Spyglass(mick/vclint/vprune)、Broadway/BW |
| 低功耗 | `99d29d7f-bd5a-491d-b34f-3cb1cef5eac7` | UPF、CLP、isolation、level shifter、power domain/switch、AON、retention |

**默认 3 个全填**(用逗号分隔)。SynHub 会按你的提问内容自动路由到对应知识库,不命中则搜全部。

## 第 3 步:跑一键接入脚本

在你**目标项目的根目录**(就是平时启动 Claude Code 的目录),运行:

```bash
# Windows
python C:\path\to\skill\scripts\setup.py

# macOS / Linux
python ~/.claude/skills/synhub/scripts/setup.py
```

脚本会自动:
1. 检查 Python 版本和 git
2. 装包(`mcp` / `python-dotenv` / `httpx`)
3. 在当前目录克隆 `SynHub` 仓库
4. 生成 `SynHub/.env` 模板
5. 在你项目的 `.mcp.json` 里追加 synhub 配置(不会覆盖已有的其他 server)

> 想克隆到别的位置?用 `--target-dir`:
> ```bash
> python <skill-path>/scripts/setup.py --target-dir D:/repos
> ```

## 第 4 步:填 `.env`

打开 `<目标目录>/SynHub/.env`,把第 1、2 步拿到的值填进去:

```ini
MIFY_API_KEY=dataset-你的Key
MIFY_DATASET_IDS=b26e181e-fc6c-4371-8a11-3e19580afd85,fa43ebb5-0333-4e8f-9351-33952daafaec,99d29d7f-bd5a-491d-b34f-3cb1cef5eac7
```

其他字段保留默认值即可。

## 第 5 步:诊断

跑诊断脚本验证全部环节正常(包括真打一次 Mify 接口):

```bash
python <skill-path>/scripts/doctor.py
```

期望输出:

```
✅ Python 版本: 3.12.0
✅ git 可用: /usr/bin/git
✅ 依赖包(mcp / dotenv / httpx): 已安装
✅ SynHub 仓库: /path/to/SynHub
✅ .env 配置: KEY=dataset-64... DATASETS=3
✅ .mcp.json 包含 synhub: /path/to/.mcp.json
✅ Mify 接口连通(真打): OK: 1 result(s)

🎉 全部通过! 重启 Claude Code 即可使用知识库。
```

任一项 ❌ 时,脚本会给具体修复建议。详细排错见 [troubleshooting.md](./troubleshooting.md)。

## 第 6 步:重启 Claude Code 并验证

完全退出 Claude Code 再重新进入(只关窗口可能不够)。然后在对话里问:

> 知识库里有哪些文档?

Claude 应该自动调 `list_knowledge_categories` 工具并返回文档列表。

或者直接问个具体问题:

> CLP error CROSSING_OFF_TO_ON_AON 怎么修?

Claude 会调 `search_synthesis_knowledge`,基于检索到的文档回答,并按 skill 的回答规范标注来源和置信度。

## 装好之后能干什么

详见 [examples/usage.md](../examples/usage.md) 和 [advanced.md](./advanced.md)。

## 常见问题速查

- **API Key 怎么轮换?** 找 rhMa0706 重新签发,改 `.env` 后重启 Claude Code。
- **多个项目都想用怎么办?** 每个项目根都跑一次 `setup.py`,会写各自的 `.mcp.json`(`SynHub` 仓库可以共用)。
- **想在所有项目自动加载这个 skill?** 把整个 `synhub/` 目录拷到 `~/.claude/skills/`(全局 skill)。MCP server 还是要每个项目配。
- **想要团队共享而不是每人本地装?** 见 [advanced.md](./advanced.md) 的 SSE 模式。
