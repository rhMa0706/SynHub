# 排错手册

按症状定位。先跑 `python <skill-path>/scripts/doctor.py`,大部分问题它会直接告诉你修复方法。

## 安装阶段

### `python: command not found`

**原因**:Python 未安装,或 `python` 命令名不对(macOS / Linux 上常是 `python3`)。

**修复**:
```bash
# macOS
brew install python@3.12

# Ubuntu/Debian
sudo apt install python3 python3-pip

# Windows
winget install Python.Python.3.12
```

之后用 `python3` 替代 `python` 跑 setup.py。

### `Python 3.10+ required`

**原因**:Python 版本过低。

**修复**:升级 Python。SynHub 用了 `match` 语法、`X | None` 类型注解,3.10 是最低。

### `git: command not found`

**原因**:git 未安装。

**修复**:
- Windows: <https://git-scm.com/downloads>
- macOS: `brew install git` 或装 Xcode Command Line Tools
- Linux: `apt install git` / `yum install git`

### `pip install` 卡住或超时

**原因**:pip 默认源 pypi.org 在国内不稳。

**修复**:换镜像:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mcp python-dotenv httpx
```

或永久配置:
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### `git clone` 失败 (`Could not resolve host: github.com`)

**原因**:网络不通 / 代理未设置。

**修复**:
- 公司网:确认开了 VPN
- 代理:`git config --global http.proxy http://127.0.0.1:7890`(端口按你的代理软件)
- 或手动下载 zip:从 <https://github.com/rhMa0706/SynHub> 下载,解压到目标目录

## 配置阶段

### `.mcp.json 不是合法 JSON`

**原因**:你之前手动改过 `.mcp.json`,语法错误(漏逗号、引号没闭合等)。

**修复**:
```bash
python -c "import json; json.load(open('.mcp.json'))"
```
看错误位置,修好再跑 setup.py。

### `MIFY_API_KEY 未配置或仍为占位符`

**原因**:`.env` 里还是 `your-api-key-here` 之类的占位符。

**修复**:编辑 `SynHub/.env`,填入真实 Key(找 rhMa0706 申请)。

### `MIFY_DATASET_IDS 未配置`

**原因**:同上,或者你只填了一个 ID 但忘了 dataset_id 是 UUID 格式。

**修复**:对照 [onboarding.md](./onboarding.md) 第 2 步,3 个 dataset_id 用逗号分隔填入。

## 运行阶段(重启 Claude Code 后)

### Claude Code 启动后没看到 synhub 工具

**症状**:对话里问"知识库里有哪些文档?",Claude 直接回答"我没有访问知识库的能力"。

**排查顺序**:

1. **确认 `.mcp.json` 在正确位置**:在你启动 Claude Code 的目录里 `cat .mcp.json`,确认有 `mcpServers.synhub`。
2. **确认完全重启**:不是关窗口,是退出整个进程再重新启动。
3. **看 Claude Code 启动日志**:在 Claude Code 里运行 `/mcp`,会列出所有 MCP server 的状态。如果 synhub 显示 ❌,日志里会有原因。

### `/mcp` 显示 synhub 启动失败

常见原因:

| 错误 | 原因 | 修复 |
|---|---|---|
| `ModuleNotFoundError: No module named 'mcp'` | 装包没装到 Claude Code 用的 Python 解释器 | `setup.py` 里 `command` 写的是 `sys.executable`,但如果你重装了 Python,需要重新跑 setup.py |
| `FileNotFoundError: ...mcp_server.py` | SynHub 仓库被删了/移动了 | 重新跑 setup.py |
| `ImportError: cannot import name ... from 'config.settings'` | SynHub 仓库版本太旧 | 跑 `update.py` 拉新版 |

### 调用工具时报 401 / 403

**原因**:`MIFY_API_KEY` 错了或被吊销。

**修复**:找 rhMa0706 重新签发,改 `.env`,**重启 Claude Code**(.env 是进程启动时读取的)。

### 调用工具时报 timeout / connection refused

**原因**:网络不通 Mify 服务。

**修复**:
- 确认 VPN 开着
- 确认能访问 `https://service.mify.mioffice.cn`(浏览器打开看响应)
- 公司防火墙策略可能屏蔽某些出站,联系 IT

### 调用工具时返回 "未找到相关内容"

**这不是错误**,而是知识库里真的没相关文档。先尝试:

1. **换英文关键词**:`时钟门控` → `clock gating`
2. **更具体的术语**:`怎么做约束` → `false_path 怎么写`
3. **用错误码原文**:`1801_REF_OBJ_NOT_FOUND` 这类 ID 直接贴(SynHub 会自动桥接到文档标题)

如果换关键词后还是无结果,可能这部分内容确实没收录,联系 rhMa0706 加文档。

### 检索结果质量差(不相关)

**排查**:
- 检索结果的 `score` 都很低(<0.3) → 知识库里没有强相关文档
- 检索结果指向错误领域 → 自动路由失败,手动加 `dataset_id` 参数(见 [advanced.md](./advanced.md))

### Claude 回答时不引用知识库

**原因**:Claude 没触发 skill 的回答规范。

**修复**:确认 skill 在加载位置:
- 项目级:`<项目>/.claude/skills/synhub/SKILL.md`
- 全局:`~/.claude/skills/synhub/SKILL.md`

在对话里手动唤起:`/synhub` 或直接说"查一下知识库 XXX 怎么做"。

## 卸载/重装

### 想完全卸载

```bash
python <skill-path>/scripts/uninstall.py --remove-repo
```

会:
- 从 `.mcp.json` 移除 synhub
- 交互确认后删除 `SynHub` 仓库
- **不会**删除 `.env`(里面有 Key,需手动)

### 想升级到新版

```bash
python <skill-path>/scripts/update.py
```

会 `git pull --ff-only`。如果有本地修改导致 pull 失败,先 `git stash`。

## 还是搞不定?

收集这些信息找 rhMa0706:
- 操作系统 + Python 版本
- `python <skill-path>/scripts/doctor.py` 的完整输出
- Claude Code 里 `/mcp` 的输出
- 你执行的命令和报错原文
