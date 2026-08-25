# SynHub 知识库 · 接入指南

> 凭证仅限内部使用,请勿外传 API Key 和文档内容。

---

## Step 1 · 解压 skill 包

把收到的 skill 的 zip 包 解压到:

- **macOS / Linux**:`~/.claude/skills/synhub/`
- **Windows**:`C:\Users\<你的用户名>\.claude\skills\synhub\`

解压完目录结构应该是:

```
~/.claude/skills/synhub/
├── SKILL.md
├── .env                   ← 解压后是占位符,Step 2 要填真值
├── scripts/
│   ├── setup.py
│   ├── doctor.py
│   └── feedback.py
└── docs/
```

> ⚠️ 有些解压工具默认隐藏 `.` 开头的文件,记得开"显示隐藏文件"。

---

## Step 2 · 让 Claude Code 帮你配 .env 并跑 setup

打开 Claude Code(任意目录都行,推荐你常用的工程根目录),把下面这段 **完整粘贴** 进去:

````
请帮我配置 SynHub 知识库 skill。

第一步:把下面这段写进 ~/.claude/skills/synhub/.env(覆盖原占位符):

```
MIFY_API_KEY=<向维护者索取>
MIFY_DATASET_IDS=<向维护者索取,或首次跑 setup.py 后由 update.py 自动补齐>
FEISHU_APP_ID=<向维护者索取>
FEISHU_APP_SECRET=<向维护者索取>
FEEDBACK_CHAT_ID=<向维护者索取>
BITABLE_APP_TOKEN=<向维护者索取>
BITABLE_TABLE_ID=<向维护者索取>
```

第二步:跑 `python ~/.claude/skills/synhub/scripts/setup.py`(Windows 改成 `%USERPROFILE%\.claude\skills\synhub\scripts\setup.py`),
它会自动 clone SynHub 仓库到当前目录,并把 MCP 配置写进当前项目的 .mcp.json。

第三步:跑 `python ~/.claude/skills/synhub/scripts/doctor.py`,看到「🎉 全部通过」就 OK。
````

Claude Code 会:

1. 把 7 行真值写进你的 `~/.claude/skills/synhub/.env`
2. 跑 `setup.py`:装依赖 → clone SynHub 仓库 → 写当前项目的 `.mcp.json`
3. 跑 `doctor.py`:检查 Python/git/依赖/.env/.mcp.json,**真打一次 Mify 接口** 验证连通

如果 doctor 报错,把它的输出连同建议一起贴给 Claude Code,它会帮你修。常见错误见 [troubleshooting.md](troubleshooting.md)。

---

## Step 3 · 重启 Claude Code 验证

完全关掉 Claude Code 再打开(MCP 配置只在启动时加载)。

随便问一个 Syn 相关问题,例如:

> 怎么修PTE-60的问题?

如果回答里出现 `mcp__synhub__search_synthesis_knowledge` 工具调用,且引用了具体文档片段,就说明知识库通了。

---

## 反馈机制

回答不满意?直接告诉 Claude Code:

> 这个回答不对,帮我反馈一下

它会自动跑 `feedback.py`,把本次问答和你的不满意原因:

- 发到飞书群(@ 维护者)
- 写入飞书多维表格(给我做后续分析)

不需要你手动配 webhook 或 collect 服务,7 个 key 配齐就两条都通。

---

## FAQ

**Q: 配置的 7 个 key 分别是干嘛的?**

| Key                                      | 用途                              |
| ---------------------------------------- | --------------------------------- |
| `MIFY_API_KEY`                           | Mify 知识库检索 API Key(共享我的) |
| `MIFY_DATASET_IDS`                       | 三个 dataset:综合/log/jira(共享)  |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET`    | 飞书自建应用凭证(共享,反馈用)     |
| `FEEDBACK_CHAT_ID`                       | 反馈群 chat_id                    |
| `BITABLE_APP_TOKEN` / `BITABLE_TABLE_ID` | 反馈写入的多维表格                |

**Q: 我能改成自己的 key 吗?**

可以,但 dataset_ids 是我维护的知识库,你换成自己的就查不到 Syn 资料了。建议照抄。

**Q: setup.py 把 SynHub clone 到哪了?**

默认 clone 到你跑 setup 时的 **当前目录**。如果想换地方,加 `--target-dir <路径>`。

**Q: 卸载怎么办?**

```bash
python ~/.claude/skills/synhub/scripts/uninstall.py
```

会清掉 `.mcp.json` 里的 synhub 配置,但保留你 clone 的 SynHub 目录(避免误删本地修改)。

---

有问题随时在群里 @ 我。
