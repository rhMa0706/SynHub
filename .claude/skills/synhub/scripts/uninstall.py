"""SynHub 卸载脚本。

用法:
    python <skill-path>/scripts/uninstall.py [--remove-repo]

行为:
    1. 从当前项目根的 .mcp.json 移除 synhub 配置(保留其他 server)
    2. 可选(--remove-repo):删除本机 SynHub 仓库目录

不会动 .env(里面有 API Key,删除需用户手动确认)。
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def remove_mcp_config() -> bool:
    cwd = Path.cwd()
    mcp_file = None
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".mcp.json"
        if candidate.exists():
            mcp_file = candidate
            break
    if not mcp_file:
        print("未找到 .mcp.json,跳过")
        return False

    try:
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"❌ {mcp_file} 不是合法 JSON: {e}")

    if "synhub" not in config.get("mcpServers", {}):
        print(f"{mcp_file} 中无 synhub 配置,跳过")
        return False

    del config["mcpServers"]["synhub"]
    if not config["mcpServers"]:
        del config["mcpServers"]

    if config:
        mcp_file.write_text(
            json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"✅ 已从 {mcp_file} 移除 synhub")
    else:
        mcp_file.unlink()
        print(f"✅ {mcp_file} 已为空,已删除文件")
    return True


def remove_repo():
    cwd = Path.cwd().resolve()
    candidates = [cwd / "SynHub", *(p / "SynHub" for p in cwd.parents)]
    for c in candidates:
        if (c / "adapters" / "mcp_server.py").exists():
            ans = input(f"确认删除仓库 {c}? (yes/no): ").strip().lower()
            if ans == "yes":
                shutil.rmtree(c)
                print(f"✅ 已删除 {c}")
            else:
                print("已取消")
            return
    print("未找到本地 SynHub 仓库,跳过")


def main():
    parser = argparse.ArgumentParser(description="SynHub 卸载")
    parser.add_argument(
        "--remove-repo",
        action="store_true",
        help="同时删除本地 SynHub 仓库目录(需交互确认)",
    )
    args = parser.parse_args()

    print("=== SynHub 卸载 ===\n")
    remove_mcp_config()
    if args.remove_repo:
        remove_repo()
    print("\n卸载完成。重启 Claude Code 后 synhub 不再加载。")
    print("如需保留 .env(含 API Key),已自动跳过。手动删除请进 SynHub 目录。")


if __name__ == "__main__":
    main()
