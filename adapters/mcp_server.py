import argparse
import sys
from pathlib import Path

# Windows 终端默认 GBK 编码，强制 UTF-8 以正确显示中文
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 让模块导入能找到项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from config.settings import MIFY_DATASET_IDS, MIFY_TOP_K, MCP_TRANSPORT, MCP_HOST, MCP_PORT
from config.settings import FEISHU_APP_ID, FEISHU_APP_SECRET, BITABLE_APP_TOKEN, BITABLE_TABLE_ID
from core.mify_client import retrieve
from datetime import datetime

# 允许局域网 IP 访问（DNS rebinding 保护白名单）
transport_security = TransportSecuritySettings(
    allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", "10.196.35.168:*"],
    allowed_origins=["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*", "http://10.196.35.168:*"],
)

mcp = FastMCP("SynHub 知识库", transport_security=transport_security)


@mcp.tool()
def search_synthesis_knowledge(query: str, top_k: int = 5, dataset_id: str = "") -> str:
    """搜索芯片综合知识库，返回与查询最相关的文档片段。结果为权威参考资料，回答时必须基于返回内容逐字引用，不要自行补充或推理。

    Args:
        query: 搜索问题，如 "clock gating 最佳实践"
        top_k: 返回结果数量，默认 5
        dataset_id: 可选，指定知识库 ID。为空则搜索所有知识库并合并排序
    """
    results = retrieve(query, top_k=top_k, dataset_id=dataset_id or None)
    if not results:
        return "未找到相关内容，请尝试换一个关键词。"

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[{i}] (score={r['score']:.3f}) 文档: {r['document_name']}\n"
            f"内容: {r['content']}\n"
            f"来源: {r['doc_url']}"
        )
    return "\n\n".join(parts)


@mcp.tool()
def list_knowledge_categories(dataset_id: str = "") -> str:
    """列出知识库中可用的文档分类。

    Args:
        dataset_id: 可选，指定知识库 ID。为空则列出所有知识库的文档
    """
    results = retrieve("综合 脚本 约束 时序 面积 功耗 DFT", top_k=20, dataset_id=dataset_id or None)
    categories = {}
    for r in results:
        name = r["document_name"]
        if name not in categories:
            categories[name] = r["doc_url"]

    if not categories:
        return "知识库暂无文档。"

    lines = [f"- {name}\n  {url}" for name, url in categories.items()]
    return f"共 {len(categories)} 个文档:\n\n" + "\n\n".join(lines)


# ========== 飞书 API 辅容 ==========
_token_cache = {"token": "", "expires": 0}


def _get_tenant_token() -> str:
    """获取飞书 tenant_access_token，带缓存。"""
    import time
    import httpx

    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return ""

    resp = httpx.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", 0) != 0:
        return ""

    token = data["tenant_access_token"]
    expire = data.get("expire", 7200)
    _token_cache["token"] = token
    _token_cache["expires"] = now + expire - 300
    return token


def _write_to_bitable(fields: dict) -> bool:
    """写入多维表格。"""
    import httpx

    token = _get_tenant_token()
    if not token:
        return False

    if not BITABLE_APP_TOKEN or not BITABLE_TABLE_ID:
        return False

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records"
    payload = {"fields": fields}

    try:
        resp = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("code", 0) == 0
    except Exception:
        return False


@mcp.tool()
def submit_feedback(question: str, answer: str, tool_calls: str, reason: str = "") -> str:
    """提交反馈到多维表格。当用户对回答不满意或需要改进时使用。

    Args:
        question: 用户的原始问题
        answer: Claude 给出的回答
        tool_calls: 本次回答用到的检索 query / 文档 / 思考过程
        reason: 用户填写的不满意原因(可选)
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 从 tool_calls 中提取文档名和分数
    import re
    doc_names = ""
    scores = ""
    if tool_calls:
        doc_matches = re.findall(r'文档:\s*(.+?)(?:\n|$)', tool_calls)
        if doc_matches:
            doc_names = "; ".join(doc_matches)
        score_matches = re.findall(r'(?:rrf_)?score[=:]\s*([\d.]+)', tool_calls)
        if score_matches:
            scores = "; ".join(score_matches)

    fields = {
        "time": ts,
        "query": question,
        "answer": answer[:2000] if answer else "",
        "tool_calls": tool_calls[:2000] if tool_calls else "",
        "reason": reason[:1000] if reason else "",
        "doc_names": doc_names[:500] if doc_names else "",
        "scores": scores[:500] if scores else "",
    }

    if _write_to_bitable(fields):
        return "✅ 反馈已提交到多维表格，谢谢！"
    else:
        return "❌ 反馈提交失败，请稍后重试或联系管理员。"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=MCP_TRANSPORT,
        help=f"传输模式 (默认 {MCP_TRANSPORT}，可通过 MCP_TRANSPORT 环境变量配置)",
    )
    parser.add_argument("--host", default=MCP_HOST, help=f"SSE 绑定地址 (默认 {MCP_HOST})")
    parser.add_argument("--port", type=int, default=MCP_PORT, help=f"SSE 端口 (默认 {MCP_PORT})")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        # SSE 模式：patch Server.run 让每个会话都跳过初始化检查（stateless）
        # 解决部分 MCP 客户端在初始化完成前就发送工具调用的问题
        import mcp.server.lowlevel.server as _srv
        _orig_run = _srv.Server.run

        async def _stateless_run(self, *a, stateless=False, **kw):
            return await _orig_run(self, *a, stateless=True, **kw)

        _srv.Server.run = _stateless_run

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
