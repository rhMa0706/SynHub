"""
SynHub 知识库一键接入脚本（stdio 模式）
用法: python setup.py
"""
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/rhMa0706/SynHub.git"


def ensure_deps():
    try:
        import mcp  # noqa: F401
        import dotenv  # noqa: F401
    except ImportError:
        print("安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp", "python-dotenv"])


def clone_repo(work_dir: Path):
    synhub_dir = work_dir / "SynHub"
    if synhub_dir.exists():
        print(f"SynHub 目录已存在: {synhub_dir}")
        return synhub_dir

    print(f"克隆仓库到 {work_dir}...")
    subprocess.check_call(["git", "clone", REPO_URL], cwd=str(work_dir))
    return synhub_dir


def setup_env(synhub_dir: Path):
    env_file = synhub_dir / ".env"
    example_file = synhub_dir / ".env.example"

    if env_file.exists():
        print(".env 已存在，跳过")
        return

    if example_file.exists():
        import shutil
        shutil.copy(example_file, env_file)
        print("已从 .env.example 创建 .env")
    else:
        env_file.write_text(
            "MIFY_API_KEY=\nMIFY_DATASET_IDS=\nMIFY_TOP_K=5\nMCP_TRANSPORT=stdio\n",
            encoding="utf-8",
        )
        print("已创建 .env")

    print("\n请编辑 SynHub/.env，填入你的 MIFY_API_KEY 和 MIFY_DATASET_IDS")


def get_project_root():
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() or (parent / ".mcp.json").exists():
            return parent
    return cwd


def write_mcp_config(project_root: Path, synhub_dir: Path):
    import json

    mcp_file = project_root / ".mcp.json"
    server_path = str(synhub_dir / "adapters" / "mcp_server.py").replace("\\", "\\\\")

    if mcp_file.exists():
        with open(mcp_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    if "synhub" in config["mcpServers"]:
        print(".mcp.json 中已有 synhub 配置，跳过")
        return

    config["mcpServers"]["synhub"] = {
        "command": "python",
        "args": [str(synhub_dir / "adapters" / "mcp_server.py")],
    }

    with open(mcp_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"已写入 {mcp_file}")


def test_connection(synhub_dir: Path):
    print("\n测试连接...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", "from core.mify_client import retrieve; r = retrieve('clock gating', top_k=2); print(f'OK: {len(r)} results')"],
            cwd=str(synhub_dir),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            print(result.stdout.strip())
            return True
        else:
            print(f"测试失败: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"测试失败: {e}")
        return False


def main():
    print("=== SynHub 知识库一键接入 ===\n")

    ensure_deps()

    work_dir = Path.cwd()
    synhub_dir = clone_repo(work_dir)
    setup_env(synhub_dir)

    project_root = get_project_root()
    print(f"\n项目目录: {project_root}")
    write_mcp_config(project_root, synhub_dir)

    print()
    if test_connection(synhub_dir):
        print("\n接入完成! 重启 Claude Code 后即可使用知识库。")
    else:
        print("\n接入配置已写入，但连接测试失败。")
        print("请检查 SynHub/.env 中的 MIFY_API_KEY 和 MIFY_DATASET_IDS")


if __name__ == "__main__":
    main()
