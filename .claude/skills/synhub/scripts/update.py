"""SynHub 仓库更新脚本(git pull + 同步 skill 端配置)。

用法:
    python <skill-path>/scripts/update.py [--synhub-dir DIR]

行为:
    1. 定位 SynHub 仓库
    2. git pull --ff-only(避免本地修改被覆盖)
    3. 从仓库读 datasets.json,补齐 skill/.env 里缺失的 MIFY_DATASET_IDS
       和 .mcp.json 里 env.MIFY_DATASET_IDS(都只追加、不覆盖已有值)
    4. 用 datasets.json 重写 skill/SKILL.md 里的"知识库范围与自动路由"表
    5. 提示重启 Claude Code
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Windows 控制台默认 GBK,emoji/中文输出会 UnicodeEncodeError;强制 stdout/stderr 用 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass


def skill_root() -> Path:
    """skill 根目录:scripts/.. → .claude/skills/synhub/"""
    return Path(__file__).resolve().parent.parent


def find_synhub_dir(hint: Path | None) -> Path | None:
    if hint and (hint / "adapters" / "mcp_server.py").exists():
        return hint.resolve()
    cwd = Path.cwd().resolve()
    for c in [cwd, cwd / "SynHub", *(p / "SynHub" for p in cwd.parents)]:
        if (c / "adapters" / "mcp_server.py").exists():
            return c
    return None


def load_datasets(synhub_dir: Path) -> list[dict] | None:
    """优先从仓库 skill 子目录读 datasets.json;缺失时返回 None,让上游跳过同步。"""
    candidates = [
        synhub_dir / ".claude" / "skills" / "synhub" / "datasets.json",
        skill_root() / "datasets.json",
    ]
    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and all("id" in d and "name" in d for d in data):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
    return None


def _parse_env(text: str) -> list[tuple[str, str, str]]:
    """把 .env 文本解析成 [(key, value, raw_line), ...],注释/空行 key 为空字符串。"""
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            out.append(("", "", raw))
            continue
        k, _, v = line.partition("=")
        out.append((k.strip(), v.strip(), raw))
    return out


def sync_env_dataset_ids(datasets: list[dict]) -> tuple[int, int]:
    """把 datasets 里的新 id 追加进 skill/.env 的 MIFY_DATASET_IDS。

    返回 (已有数, 新增数)。不覆盖用户已有的 id,只做并集追加。
    """
    env_file = skill_root() / ".env"
    if not env_file.exists():
        print(f"⚠️  {env_file} 不存在,跳过 .env 同步(先跑 setup.py)")
        return (0, 0)

    text = env_file.read_text(encoding="utf-8")
    parsed = _parse_env(text)

    existing_ids: list[str] = []
    idx = -1
    for i, (k, v, _) in enumerate(parsed):
        if k == "MIFY_DATASET_IDS":
            idx = i
            existing_ids = [x.strip() for x in v.split(",") if x.strip()]
            break

    known_ids = [d["id"] for d in datasets]
    to_add = [i for i in known_ids if i not in existing_ids]
    if not to_add:
        return (len(existing_ids), 0)

    merged = existing_ids + to_add
    new_value = ",".join(merged)

    if idx >= 0:
        parsed[idx] = ("MIFY_DATASET_IDS", new_value, f"MIFY_DATASET_IDS={new_value}")
    else:
        parsed.append(("MIFY_DATASET_IDS", new_value, f"MIFY_DATASET_IDS={new_value}"))

    new_text = "\n".join(line for _, _, line in parsed)
    if not new_text.endswith("\n"):
        new_text += "\n"
    env_file.write_text(new_text, encoding="utf-8")
    return (len(existing_ids), len(to_add))


def sync_mcp_dataset_ids(datasets: list[dict]) -> tuple[Path | None, int]:
    """把新 dataset id 补进项目根 .mcp.json 的 synhub.env.MIFY_DATASET_IDS。

    MCP server 运行时读的就是 .mcp.json 的 env,skill/.env 不会自动流过去。
    返回 (mcp_file_path, 新增数)。找不到 .mcp.json 或没配 synhub 时返回 (None, 0)。
    """
    cwd = Path.cwd().resolve()
    mcp_file: Path | None = None
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".mcp.json"
        if candidate.exists():
            mcp_file = candidate
            break
    if not mcp_file:
        return (None, 0)

    try:
        config = json.loads(mcp_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return (mcp_file, 0)

    servers = config.get("mcpServers") or {}
    synhub_cfg = servers.get("synhub")
    if not synhub_cfg:
        return (mcp_file, 0)

    env_map = synhub_cfg.setdefault("env", {})
    existing = [x.strip() for x in (env_map.get("MIFY_DATASET_IDS") or "").split(",") if x.strip()]
    known_ids = [d["id"] for d in datasets]
    to_add = [i for i in known_ids if i not in existing]
    if not to_add:
        return (mcp_file, 0)

    env_map["MIFY_DATASET_IDS"] = ",".join(existing + to_add)
    mcp_file.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return (mcp_file, len(to_add))


_TABLE_HEADER = "## 知识库范围与自动路由"
_TABLE_NEXT_HEADER_RE = re.compile(r"^## ", re.MULTILINE)


def _render_dataset_table(datasets: list[dict]) -> str:
    lines = [
        _TABLE_HEADER,
        "",
        f"当前接入 {len(datasets)} 个知识库,按查询关键词自动路由(完整关键词见 `config/settings.py:DOMAIN_MAP`):",
        "",
        "| 领域 | dataset_id | 触发关键词(部分) |",
        "|------|------|------|",
    ]
    for d in datasets:
        kws = ", ".join(d.get("keywords", [])[:6])
        lines.append(f"| {d['name']} | `{d['id']}` | {kws} |")
    lines.append("")
    lines.append("不传 `dataset_id` 时:命中某领域则只搜该库,跨域(差距 ≤ 1)则并搜,不命中则搜全部 + RRF 融合。")
    lines.append("")
    return "\n".join(lines)


def sync_skill_md(datasets: list[dict]) -> bool:
    """用 datasets 重写 SKILL.md 里的"知识库范围与自动路由"章节。"""
    skill_md = skill_root() / "SKILL.md"
    if not skill_md.exists():
        print(f"⚠️  {skill_md} 不存在,跳过 SKILL.md 同步")
        return False

    text = skill_md.read_text(encoding="utf-8")
    start = text.find(_TABLE_HEADER)
    if start < 0:
        print(f"⚠️  SKILL.md 未找到章节标题「{_TABLE_HEADER}」,跳过")
        return False

    tail = text[start + len(_TABLE_HEADER):]
    next_match = _TABLE_NEXT_HEADER_RE.search(tail)
    end = start + len(_TABLE_HEADER) + (next_match.start() if next_match else len(tail))

    new_section = _render_dataset_table(datasets)
    new_text = text[:start] + new_section + text[end:]
    if new_text == text:
        return False
    skill_md.write_text(new_text, encoding="utf-8")
    return True


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

    print("\n=== 同步 skill 端配置 ===")
    datasets = load_datasets(synhub_dir)
    if datasets is None:
        print("⚠️  未找到 datasets.json,跳过 .env / SKILL.md 同步")
    else:
        env_have, env_added = sync_env_dataset_ids(datasets)
        if env_added:
            print(f"✅ skill/.env: MIFY_DATASET_IDS 追加 {env_added} 个(原有 {env_have})")
        else:
            print(f"✅ skill/.env: MIFY_DATASET_IDS 已包含全部 {env_have} 个,无需变动")

        mcp_file, mcp_added = sync_mcp_dataset_ids(datasets)
        if mcp_file is None:
            print("ℹ️  未找到项目根 .mcp.json 或未配 synhub,跳过 .mcp.json 同步")
        elif mcp_added:
            print(f"✅ .mcp.json: MIFY_DATASET_IDS 追加 {mcp_added} 个 → {mcp_file}")
        else:
            print(f"✅ .mcp.json: MIFY_DATASET_IDS 已同步 → {mcp_file}")

        if sync_skill_md(datasets):
            print(f"✅ SKILL.md: 知识库表已刷新为 {len(datasets)} 库")
        else:
            print("ℹ️  SKILL.md 无需更新")

    print("\n✅ 更新完成! 重启 Claude Code 即可生效。")
    print(f"   建议跑诊断: python {Path(__file__).parent / 'doctor.py'}")


if __name__ == "__main__":
    main()
