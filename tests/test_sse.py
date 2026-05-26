"""快速测试 SSE 模式的 MCP server。"""
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


async def main():
    print("连接 SSE server http://localhost:8003/sse ...")
    async with sse_client("http://localhost:8003/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("连接成功!\n")

            # 列出 tools
            tools = await session.list_tools()
            print(f"可用 tools ({len(tools.tools)}):")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            # 调用 search
            print("\n调用 search_synthesis_knowledge(query='clock gating') ...")
            result = await session.call_tool(
                "search_synthesis_knowledge", {"query": "clock gating", "top_k": 2}
            )
            print(f"\n返回结果:\n{result.content[0].text[:500]}")


if __name__ == "__main__":
    asyncio.run(main())
