"""SynHub 知识库诊断脚本。

用法:
    python <skill-path>/scripts/doctor.py [--synhub-dir DIR]

行为(全跑一遍,任一失败给出修复建议):
    1. Python 版本(>=3.10)
    2. git 可用
    3. 必要依赖(mcp / dotenv / httpx)
    4. SynHub 仓库存在
    5. skill/.env 关键字段已填
    6. 当前项目 .mcp.json 包含 synhub
    7. **真打一次 Mify 接口**(query='clock', top_k=1) — 验证 API Key、网络、Mify 服务
    8. 反馈链路凭证(.mcp.json 含飞书 4 项) — 验证 submit_feedback 能写多维表格
"""
import argparse
import json
import os
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

MIN_PY = (3, 10)


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_skill_env() -> dict:
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


class Check:
    def __init__(self, name: str):
        self.name = name
        self.ok: bool = False
        self.detail: str = ""
        self.fix: str = ""

    def passed(self, detail: str = ""):
        self.ok = True
        self.detail = detail
        return self

    def failed(self, detail: str, fix: str):
        self.ok = False
        self.detail = detail
        self.fix = fix
        return self


def check_python() -> Check:
    c = Check("Python 版本")
    cur = sys.version_info
    if cur >= MIN_PY:
        return c.passed(f"{cur.major}.{cur.minor}.{cur.micro}")
    return c.failed(
        f"{cur.major}.{cur.minor} < {MIN_PY[0]}.{MIN_PY[1]}",
        f"升级 Python 到 {MIN_PY[0]}.{MIN_PY[1]}+",
    )


def check_git() -> Check:
    c = Check("git 可用")
    if shutil.which("git"):
        return c.passed(shutil.which("git"))
    return c.failed("未找到 git", "安装 git: https://git-scm.com/downloads")


def check_deps() -> Check:
    c = Check("依赖包(mcp / dotenv / httpx)")
    missing = []
    for mod in ("mcp", "dotenv", "httpx"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return c.passed("已安装")
    pkg_map = {"mcp": "mcp", "dotenv": "python-dotenv", "httpx": "httpx"}
    pkgs = " ".join(pkg_map[m] for m in missing)
    return c.failed(
        f"缺少: {', '.join(missing)}",
        f"运行: pip install {pkgs}",
    )


def find_synhub_dir(hint: Path | None) -> Path | None:
    """查找 SynHub 仓库目录。优先用 hint,否则在 cwd 及其父目录里找。"""
    if hint:
        if (hint / "adapters" / "mcp_server.py").exists():
            return hint.resolve()
        return None
    cwd = Path.cwd().resolve()
    candidates = [cwd, cwd / "SynHub", *(p / "SynHub" for p in cwd.parents)]
    for c in candidates:
        if (c / "adapters" / "mcp_server.py").exists():
            return c
    return None


def check_synhub_repo(synhub_dir: Path | None) -> Check:
    c = Check("SynHub 仓库")
    if synhub_dir:
        return c.passed(str(synhub_dir))
    return c.failed(
        "未找到 SynHub 仓库",
        "运行 setup.py,或用 --synhub-dir 指定路径",
    )


def check_env() -> Check:
    c = Check("skill/.env 配置")
    env_file = skill_root() / ".env"
    if not env_file.exists():
        return c.failed(f"{env_file} 不存在", "解压 skill 包到 ~/.claude/skills/synhub/")
    env = read_skill_env()
    api_key = env.get("MIFY_API_KEY", "")
    dataset_ids = env.get("MIFY_DATASET_IDS", "")
    if not api_key or api_key.startswith("your-"):
        return c.failed(
            "MIFY_API_KEY 未填或仍为占位符",
            f"编辑 {env_file},填入 Mify API Key",
        )
    if not dataset_ids or dataset_ids.startswith("your-"):
        return c.failed(
            "MIFY_DATASET_IDS 未填或仍为占位符",
            f"编辑 {env_file},填入 dataset_ids(逗号分隔)",
        )
    n = len([x for x in dataset_ids.split(",") if x.strip()])
    return c.passed(f"KEY={api_key[:10]}... DATASETS={n}")


def check_mcp_config() -> Check:
    c = Check(".mcp.json 包含 synhub")
    cwd = Path.cwd()
    mcp_file = None
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".mcp.json"
        if candidate.exists():
            mcp_file = candidate
            break
    if not mcp_file:
        return c.failed("未找到 .mcp.json", "在项目根运行 setup.py")
    try:
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return c.failed(f"{mcp_file} 不是合法 JSON: {e}", "修复 JSON 语法")
    if "synhub" not in config.get("mcpServers", {}):
        return c.failed(f"{mcp_file} 中无 synhub 配置", "运行 setup.py")
    return c.passed(str(mcp_file))


FEEDBACK_KEYS = ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "BITABLE_APP_TOKEN", "BITABLE_TABLE_ID")


def check_feedback_credentials() -> Check:
    """检查 .mcp.json 中是否注入了反馈链路所需的 4 项飞书凭证。
    submit_feedback 工具依赖 MCP 进程能读到这 4 项,否则会返回失败提示。
    """
    c = Check("反馈链路凭证(.mcp.json 含飞书 4 项)")
    cwd = Path.cwd()
    mcp_file = None
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".mcp.json"
        if candidate.exists():
            mcp_file = candidate
            break
    if not mcp_file:
        return c.failed("未找到 .mcp.json", "在项目根运行 setup.py")
    try:
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return c.failed(f"{mcp_file} 不是合法 JSON: {e}", "修复 JSON 语法")
    synhub_cfg = config.get("mcpServers", {}).get("synhub")
    if not synhub_cfg:
        return c.failed(f"{mcp_file} 中无 synhub 配置", "运行 setup.py")
    mcp_env = synhub_cfg.get("env", {}) or {}
    missing = [k for k in FEEDBACK_KEYS if not mcp_env.get(k)]
    if not missing:
        return c.passed("4 项齐全(可写多维表格)")

    # 看看 skill/.env 里是否有,有的话直接提示重跑 setup
    skill_env = read_skill_env()
    skill_has = [k for k in missing if skill_env.get(k)]
    if skill_has:
        fix = (
            f"skill/.env 已有 {len(skill_has)} 项,重跑 setup.py 自动补齐: "
            f"python {Path(__file__).parent / 'setup.py'}"
        )
    else:
        fix = (
            f"先在 {skill_root() / '.env'} 填入 {', '.join(missing)},"
            f"再重跑 setup.py 注入 .mcp.json"
        )
    return c.failed(f"缺失: {', '.join(missing)}", fix)


def check_mify_api(synhub_dir: Path) -> Check:
    """真打一次 Mify 接口,极轻量(top_k=1, query=clock, num_variants=1)。"""
    c = Check("Mify 接口连通(真打)")
    code = (
        "from core.mify_client import retrieve;"
        "r = retrieve('clock', top_k=1, num_variants=1);"
        "print(f'OK: {len(r)} result(s)')"
    )
    # 把 skill/.env 的变量注入到 subprocess,绕开 SynHub 仓库 .env 依赖
    sub_env = os.environ.copy()
    sub_env.update({k: v for k, v in read_skill_env().items() if v})
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(synhub_dir),
            capture_output=True,
            text=True,
            timeout=30,
            env=sub_env,
        )
        if result.returncode == 0:
            return c.passed(result.stdout.strip())
        err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown"
        fix = "检查 .env 中 MIFY_API_KEY 是否正确,确认网络能访问 service.mify.mioffice.cn"
        if "401" in err or "403" in err:
            fix = "MIFY_API_KEY 无效,联系管理员重新签发"
        elif "timeout" in err.lower() or "connect" in err.lower():
            fix = "网络无法访问 Mify,检查 VPN/代理/防火墙"
        elif "404" in err:
            fix = "MIFY_DATASET_IDS 错误,检查 ID 是否正确"
        return c.failed(err, fix)
    except subprocess.TimeoutExpired:
        return c.failed(
            "请求超时 (>30s)",
            "网络慢或 Mify 服务异常,稍后重试或联系管理员",
        )
    except Exception as e:
        return c.failed(f"调用失败: {e}", "查看 docs/troubleshooting.md")


def main():
    parser = argparse.ArgumentParser(description="SynHub 诊断")
    parser.add_argument("--synhub-dir", type=Path, default=None,
                        help="SynHub 仓库路径(默认自动查找)")
    args = parser.parse_args()

    print("=== SynHub 诊断 ===\n")

    checks: list[Check] = []
    checks.append(check_python())
    checks.append(check_git())
    checks.append(check_deps())

    synhub_dir = find_synhub_dir(args.synhub_dir)
    checks.append(check_synhub_repo(synhub_dir))

    checks.append(check_env())
    if synhub_dir:
        checks.append(check_mcp_config())
        # 只有 .env 通过,才真打接口(否则白打)
        env_check = next((x for x in checks if x.name == "skill/.env 配置"), None)
        if env_check and env_check.ok:
            checks.append(check_mify_api(synhub_dir))
        checks.append(check_feedback_credentials())

    failed = 0
    for c in checks:
        mark = "✅" if c.ok else "❌"
        print(f"{mark} {c.name}: {c.detail}")
        if not c.ok:
            failed += 1
            print(f"   修复建议: {c.fix}")

    print()
    if failed == 0:
        print("🎉 全部通过! 重启 Claude Code 即可使用知识库。")
        sys.exit(0)
    else:
        print(f"⚠️  {failed} 项未通过,请按建议修复后重新诊断。")
        print("   完整排错手册: docs/troubleshooting.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
