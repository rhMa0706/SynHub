# 高级用法

装好默认配置后还能怎么用得更深入。

## 调用工具时的参数

### `search_synthesis_knowledge(query, top_k=5, dataset_id="")`

| 参数 | 何时调 |
|---|---|
| `top_k` | 复杂问题需要更多上下文 → 调到 10/15;简单问题想要精准答案 → 保持 5 |
| `dataset_id` | 你**确定**问题归属哪个领域,绕过自动路由提速;或者自动路由跑偏时手动指定 |

**例子**:在对话里告诉 Claude:

> 用 top_k=10 搜一下 power switch 的所有相关资料
>
> 只在低功耗库(`99d29d7f-bd5a-491d-b34f-3cb1cef5eac7`)里搜 retention

Claude 会把参数透传给工具。

### 自动路由怎么决定搜哪个库

不传 `dataset_id` 时,SynHub 看你的查询里有没有领域关键词:

| 库 | 触发关键词(部分) |
|---|---|
| SDC | sdc, constraint, timing, clock, cts, uncertainty, latency, input_delay, output_delay, false_path, multicycle, set_max, 驱动, 约束 |
| memory | memory, sram, rom, dram, register, ff, latch, mick, vclint, broadway, bw, 锁存器, 触发器, 存储器 |
| 低功耗 | low_power, upf, clp, power, isolation, level_shifter, power_domain, aon, retention, iso, lsh, pd, psw, 功耗, 隔离 |

匹配数差距 ≤ 1 的库都会被搜(解决"Mick clp"这种跨域查询)。完全不命中则搜全部 + RRF 融合。

## 查询扩展机制(影响怎么写问题)

每次查询会自动生成 ≤5 个变体并 RRF 融合,你不需要做什么,但理解机制能帮你写更好的查询:

| 策略 | 例子 |
|---|---|
| 缩写展开 | `ISO` → `isolation cell` |
| 中英桥接 | `时序` → `timing`、`低功耗` → `low_power` |
| 错误码桥接 | `1801_REF_OBJ_NOT_FOUND` → 自动找匹配的文档标题 |
| 短语提取 | `clock relation table 和 Maxwell` → `clock relation table`、`clock table` |
| 多关键词拆分 | `mem2reg MCP2 MCP3` → 各自独立检索后合并 |

**实操建议**:
- 错误码直接贴原文(`1801_REF_OBJ_NOT_FOUND` 比 `怎么修1801错误` 强)
- 中文术语不需要先翻译,系统会自动桥接
- 多关键词组合提问时,空格分隔(不要用顿号、逗号)

## 调试单次检索

在 SynHub 仓库目录下:

```bash
python -c "from core.mify_client import search; print(search('clock gating', top_k=3))"
```

会打印每个结果的 `rrf_score`、`score`、`document_name`、`content`、`doc_url`,方便判断检索质量。

## SSE 模式(团队共享一个 server)

默认 stdio 模式:每个用户本地起一个 MCP server。如果团队想集中维护、共用一份 `.env`,可以改 SSE 模式。

### 服务端(管理员)

在某台常驻机器上:

```bash
cd SynHub
MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 MCP_PORT=8003 python adapters/mcp_server.py
```

或者写到 `.env`:
```ini
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8003
```

> ⚠️ `mcp_server.py` 里 `transport_security` 写死了允许的 host(127.0.0.1 / localhost / 一个内网 IP)。要让其他同事访问,改 `adapters/mcp_server.py` 第 20-22 行的白名单。

### 客户端(同事)

`.mcp.json` 改成:

```json
{
  "mcpServers": {
    "synhub": {
      "transport": "sse",
      "url": "http://<服务端 IP>:8003/sse"
    }
  }
}
```

不需要本地装 SynHub 仓库、不需要 `.env`。

### 何时该用 SSE

- ✅ 团队共用一份 Key,集中管理
- ✅ 不希望每个同事都本地装环境
- ❌ 服务端单点故障,挂了大家都用不了
- ❌ 需要管理员手动维护服务

个人用 / 小团队 → stdio。规模化部署 → SSE。

## 改检索参数调质量

`.env` 里:

| 参数 | 默认 | 调大效果 | 调小效果 |
|---|---|---|---|
| `MIFY_TOP_K` | 5 | 更多上下文,但 token 消耗高 | 答案更精准但可能漏信息 |
| `MIFY_RRF_K` | 40 | 长尾结果权重接近,排名更平均 | 头部结果更主导 |
| `MIFY_NUM_VARIANTS` | 5 | 召回率高,但延迟大、token 多 | 快但可能漏关键变体 |
| `MIFY_RETRIEVE_WORKERS` | 3 | 变体并发高,延迟低 | 节省 Mify QPS |

改完重启 Claude Code 才生效(.env 是进程启动时读取的)。

## 多项目复用同一份 SynHub 仓库

每个项目跑 setup.py 默认会在该项目目录下克隆一份 `SynHub`,占空间。可以让多个项目共用同一份:

```bash
# 在每个项目根分别跑
python <skill-path>/scripts/setup.py --target-dir /shared/path/to/repos
```

`.mcp.json` 里的 `args` 会指向 `/shared/path/to/repos/SynHub/adapters/mcp_server.py`,多项目共享。
