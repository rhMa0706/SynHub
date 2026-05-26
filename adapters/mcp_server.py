import argparse
import sys
from pathlib import Path

# Windows 终端默认 GBK 编码，强制 UTF-8 以正确显示中文
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# 让模块导入能找到项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP

from config.settings import MIFY_DATASET_IDS, MIFY_TOP_K, MCP_TRANSPORT, MCP_HOST, MCP_PORT
from core.mify_client import retrieve

mcp = FastMCP("SynHub 知识库")


@mcp.tool()
def search_synthesis_knowledge(query: str, top_k: int = 5, dataset_id: str = "") -> str:
    """搜索芯片综合知识库，返回与查询最相关的文档片段。

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
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
