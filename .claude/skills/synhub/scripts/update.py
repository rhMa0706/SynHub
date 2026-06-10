"""SynHub 仓库更新脚本(git pull)。

用法:
    python <skill-path>/scripts/update.py [--synhub-dir DIR]

行为:
    1. 定位 SynHub 仓库
    2. git pull --ff-only(避免本地修改被覆盖)
    3. 提示重启 Claude Code
"""
import argparse
import subprocess
import sys
from pathlib import Path


def find_synhub_dir(hint: Path | None) -> Path | None:
    if hint and (hint / "adapters" / "mcp_server.py").exists():
        return hint.resolve()
    cwd = Path.cwd().resolve()
    for c in [cwd, cwd / "SynHub", *(p / "SynHub" for p in cwd.parents)]:
        if (c / "adapters" / "mcp_server.py").exists():
            return c
    return None


def main():
    parser = argparse.ArgumentParser(description="更新 SynHub 仓库")
    parser.add_argument("--synhub-dir", type=Path, default=None)
    args = parser.parse_args()

    synhub_dir = find_synhub_dir(args.synhub_dir)
    if not synhub_dir:
        sys.exit("❌ 未找到 SynHub 仓库,请用 --synhub-dir 指定")

    print(f"=== 更新 {synhub_dir} ===\n")
    try:
        subprocess.check_call(["git", "pull", "--ff-only"], cwd=str(synhub_dir))
    except subprocess.CalledProcessError:
        sys.exit(
            "❌ git pull 失败。可能原因:\n"
            "   - 本地有未提交修改 → 先 commit 或 stash\n"
            "   - 远端有 force-push → 联系仓库维护者"
        )

    print("\n✅ 更新完成! 重启 Claude Code 即可生效。")
    print(f"   建议跑诊断: python {Path(__file__).parent / 'doctor.py'}")


if __name__ == "__main__":
    main()
