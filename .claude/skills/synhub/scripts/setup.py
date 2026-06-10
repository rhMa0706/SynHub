"""SynHub 知识库一键接入脚本(stdio 模式)。

用法:
    python <skill-path>/scripts/setup.py [--target-dir DIR]

行为:
    1. 检查 Python(>=3.10) 和 git
    2. 装包(mcp / python-dotenv / httpx)
    3. 在目标目录克隆 SynHub 仓库(已存在则跳过)
    4. 从 skill 自带 .env 读取 MIFY/LLM 凭证
    5. 在当前项目根的 .mcp.json 写入 synhub 配置（带 env 注入,已有则跳过）
    6. 校验 skill/.env 中关键字段已填

跨平台:Windows / macOS / Linux 均可。
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Windows 默认 GBK 终端无法打印 emoji,统一切到 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_URL = "https://github.com/rhMa0706/SynHub.git"
MIN_PY = (3, 10)

# 注入到 .mcp.json env 字段的变量(MCP server 启动时读)
# .env 里没填的 key 会跳过,使用 config/settings.py 的默认值
MCP_ENV_KEYS = [
    "MIFY_API_KEY",
    "MIFY_DATASET_IDS",
    "MIFY_TOP_K",
    "MIFY_RRF_K",
    "MIFY_NUM_VARIANTS",
    "MIFY_RETRIEVE_WORKERS",
    "MCP_TRANSPORT",
    "MCP_HOST",
    "MCP_PORT",
]


def skill_root() -> Path:
    """skill 根目录:scripts/.. → .claude/skills/synhub/"""
    return Path(__file__).resolve().parent.parent


def read_skill_env() -> dict:
    """从 skill 自带 .env 读全部 KEY=VALUE。"""
    env_file = skill_root() / ".env"
    if not env_file.exists():
        return {}
    result = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def check_python():
    if sys.version_info < MIN_PY:
        sys.exit(
            f"❌ Python {MIN_PY[0]}.{MIN_PY[1]}+ required, "
            f"current: {sys.version_info.major}.{sys.version_info.minor}"
        )


def check_git():
    if shutil.which("git") is None:
        sys.exit("❌ 未找到 git,请先安装 git: https://git-scm.com/downloads")


def ensure_deps():
    missing = []
    for mod in ("mcp", "dotenv", "httpx"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return
    print(f"安装依赖: {', '.join(missing)}...")
    pkg_map = {"mcp": "mcp", "dotenv": "python-dotenv", "httpx": "httpx"}
    pkgs = [pkg_map[m] for m in missing]
    subprocess.check_call([sys.executable, "-m", "pip", "install", *pkgs])


def clone_repo(work_dir: Path) -> Path:
    synhub_dir = work_dir / "SynHub"
    if synhub_dir.exists():
        print(f"SynHub 目录已存在,跳过克隆: {synhub_dir}")
        return synhub_dir
    print(f"克隆仓库到 {synhub_dir}...")
    subprocess.check_call(["git", "clone", REPO_URL], cwd=str(work_dir))
    return synhub_dir


def setup_env(synhub_dir: Path):
    env_file = synhub_dir / ".env"
    example_file = synhub_dir / ".env.example"

    if env_file.exists():
        print(".env 已存在,跳过")
        return

    if example_file.exists():
        shutil.copy(example_file, env_file)
        print(f"已从 .env.example 创建 {env_file}")
    else:
        env_file.write_text(
            "# Mify 知识库检索 API\n"
            "MIFY_API_KEY=\n"
            "MIFY_DATASET_IDS=\n"
            "\n"
            "# 检索参数\n"
            "MIFY_TOP_K=5\n"
            "\n"
            "# RAG-Fusion 参数\n"
            "MIFY_RRF_K=40\n"
            "MIFY_NUM_VARIANTS=5\n"
            "MIFY_RETRIEVE_WORKERS=3\n"
            "\n"
            "# LLM 客户端(通过 Mify 代理调用)\n"
            "LLM_API_KEY=\n"
            "LLM_BASE_URL=https://service.mify.mioffice.cn/v1\n"
            "LLM_MODEL=mimo-v2.5-pro\n"
            "\n"
            "# MCP Transport: stdio | sse\n"
            "MCP_TRANSPORT=stdio\n"
            "MCP_HOST=0.0.0.0\n"
            "MCP_PORT=8003\n",
            encoding="utf-8",
        )
        print(f"已创建 {env_file}")

    print(f"\n⚠️  请编辑 {env_file},填入 MIFY_API_KEY 和 MIFY_DATASET_IDS")
    print("   API Key 申请方式见 docs/onboarding.md")


def get_project_root() -> Path:
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() or (parent / ".mcp.json").exists():
            return parent
    return cwd


def write_mcp_config(project_root: Path, synhub_dir: Path):
    mcp_file = project_root / ".mcp.json"

    if mcp_file.exists():
        try:
            config = json.loads(mcp_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            sys.exit(f"❌ {mcp_file} 不是合法 JSON: {e}")
    else:
        config = {}

    config.setdefault("mcpServers", {})

    if "synhub" in config["mcpServers"]:
        print(f".mcp.json 中已有 synhub 配置,跳过: {mcp_file}")
        return

    server_path = synhub_dir / "adapters" / "mcp_server.py"

    # 从 skill/.env 读凭证,注入到 mcpServers.synhub.env
    # 这样 MCP server 启动时不依赖 SynHub 仓库 .env
    skill_env = read_skill_env()
    env_for_mcp = {k: skill_env[k] for k in MCP_ENV_KEYS if k in skill_env and skill_env[k]}

    server_cfg = {
        "command": sys.executable,
        "args": [str(server_path)],
    }
    if env_for_mcp:
        server_cfg["env"] = env_for_mcp

    config["mcpServers"]["synhub"] = server_cfg

    mcp_file.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"已写入 {mcp_file}")
    if env_for_mcp:
        print(f"   注入了 {len(env_for_mcp)} 个环境变量(从 skill/.env)")
    else:
        print("   ⚠️  skill/.env 没有读到任何变量,MCP server 可能起不来")


def verify_env() -> bool:
    """检查 skill/.env 中关键字段已填(不打外网)。"""
    print("\n校验 skill/.env...")
    env = read_skill_env()
    api_key = env.get("MIFY_API_KEY", "")
    dataset_ids = env.get("MIFY_DATASET_IDS", "")
    if not api_key or api_key.startswith("your-"):
        print("⚠️  MIFY_API_KEY 未配置或仍为占位符")
        return False
    if not dataset_ids or dataset_ids.startswith("your-"):
        print("⚠️  MIFY_DATASET_IDS 未配置或仍为占位符")
        return False
    n = len([x for x in dataset_ids.split(",") if x.strip()])
    print(f"OK: {n} dataset(s) configured")
    return True


def main():
    parser = argparse.ArgumentParser(description="SynHub 知识库一键接入")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path.cwd(),
        help="克隆 SynHub 仓库的父目录(默认:当前目录)",
    )
    args = parser.parse_args()

    print("=== SynHub 知识库一键接入 ===\n")

    check_python()
    check_git()
    ensure_deps()

    target_dir = args.target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    synhub_dir = clone_repo(target_dir)

    project_root = get_project_root()
    print(f"\n当前项目根目录: {project_root}")
    write_mcp_config(project_root, synhub_dir)

    if verify_env():
        print("\n✅ 接入完成! 重启 Claude Code 后即可使用知识库。")
        print(f"   下一步可跑诊断: python {Path(__file__).parent / 'doctor.py'}")
    else:
        print(f"\n⚠️  接入配置已写入,但 skill/.env 还需补全。")
        print(f"   编辑 {skill_root() / '.env'} 后再跑一次 setup")


if __name__ == "__main__":
    main()
