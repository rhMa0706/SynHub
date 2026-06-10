"""SynHub 知识库一键反馈脚本。

用法(由 Claude 自动调用,不需要同事手动跑):
    python feedback.py \\
        --question "用户的原始问题" \\
        --answer "Claude 给出的回答" \\
        --tool-calls "调用的工具和参数(JSON 字符串或文本)" \\
        --reason "用户填的不满意原因(可选)"

行为:
    POST 到飞书自定义机器人 webhook,你在群里立刻看到反馈卡片。
    所有字段都不强制,缺啥就空着。
"""
import argparse
import json
import os
import platform
import sys
from datetime import datetime

# Windows 默认 GBK 终端无法打印 emoji/部分中文,统一切到 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    import httpx
except ImportError:
    sys.exit("缺少 httpx,请先 pip install httpx")

# 尝试加载 .env
# 加载顺序（后加载的覆盖先加载的）：
#   1. skill 目录自带 .env（同事场景：~/.claude/skills/synhub/.env）
#   2. 项目根 .env（维护者场景：SynHub/.env）
#   3. feishu-event-bot/.env（维护者场景：SynHub/feishu-event-bot/.env）
try:
    from dotenv import load_dotenv
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    # skill 根 = scripts/.. → .claude/skills/synhub/
    _skill_root = os.path.normpath(os.path.join(_script_dir, ".."))
    _skill_env = os.path.join(_skill_root, ".env")
    if os.path.isfile(_skill_env):
        load_dotenv(_skill_env, override=False)
    # 项目根 = scripts/../../../.. → SynHub/
    _project_root = os.path.normpath(os.path.join(_script_dir, "..", "..", "..", ".."))
    _root_env = os.path.join(_project_root, ".env")
    if os.path.isfile(_root_env):
        load_dotenv(_root_env, override=False)
    _feishu_env = os.path.join(_project_root, "feishu-event-bot", ".env")
    if os.path.isfile(_feishu_env):
        load_dotenv(_feishu_env, override=True)
except Exception:
    pass

# 飞书自建应用配置（用 API 发消息替代自定义机器人 webhook）
APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE = "https://open.feishu.cn/open-apis"

# 目标群 chat_id（必填）
CHAT_ID = os.getenv("FEEDBACK_CHAT_ID", "")

# 要 @ 的机器人 app_id（可选，默认用 FEISHU_APP_ID）
AT_APP_ID = os.getenv("FEEDBACK_AT_APP_ID") or APP_ID

# 兼容旧 webhook 模式（可选，优先用 API）
WEBHOOK = os.getenv("FEEDBACK_WEBHOOK_URL", "")

# 双写：收集服务地址（可选，留空则走 Bitable 直连）
COLLECT_URL = os.getenv("FEEDBACK_COLLECT_URL", "")

# Bitable 直连配置（COLLECT_URL 留空时使用）
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN", "")
BITABLE_TABLE_ID = os.getenv("BITABLE_TABLE_ID", "")

MAX_FIELD_LEN = 2000

# ========== tenant_access_token 缓存 ==========
_token_cache = {"token": "", "expires": 0}


def get_token() -> str:
    """获取 tenant_access_token，带缓存（2h 有效）。"""
    import time
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]

    if not APP_ID or not APP_SECRET:
        print("❌ FEISHU_APP_ID / FEISHU_APP_SECRET 未配置")
        return ""

    resp = httpx.post(
        f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code", 0) != 0:
        print(f"❌ 获取 tenant_access_token 失败: {data}")
        return ""

    token = data["tenant_access_token"]
    expire = data.get("expire", 7200)
    _token_cache["token"] = token
    _token_cache["expires"] = now + expire - 300  # 提前 5 分钟刷新
    return token


def truncate(s: str, n: int = MAX_FIELD_LEN) -> str:
    if not s:
        return "(空)"
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n] + f"\n\n... (已截断,原文 {len(s)} 字符)"


def build_content(question: str, answer: str, tool_calls: str, reason: str) -> list:
    """构建飞书 post 消息的 content 数组。"""
    user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    if AT_APP_ID:
        lines.append([{"tag": "at", "user_id": AT_APP_ID}])
        lines.append([{"tag": "text", "text": "\n"}])

    lines.append([{"tag": "text", "text": f"📝 SynHub 反馈 @ {ts}"}])

    if question:
        lines.append([{"tag": "text", "text": f"\n🙋 提问\n{truncate(question)}"}])
    if answer:
        lines.append([{"tag": "text", "text": f"\n🤖 回答\n{truncate(answer)}"}])
    if tool_calls and tool_calls.strip():
        lines.append([{"tag": "text", "text": f"\n🔧 检索过程\n{truncate(tool_calls, 1500)}"}])
    if reason and reason.strip():
        lines.append([{"tag": "text", "text": f"\n💬 用户反馈\n{truncate(reason, 1000)}"}])

    lines.append([{"tag": "text", "text": f"\n---\n👤 {user}"}])

    return lines


def send_api(content: list) -> bool:
    """通过飞书 API 发消息到群。"""
    token = get_token()
    if not token:
        return False

    if not CHAT_ID:
        print("❌ FEEDBACK_CHAT_ID 未配置（目标群的 chat_id）")
        return False

    post_content = {
        "zh_cn": {
            "title": "SynHub 反馈",
            "content": content,
        }
    }
    payload = {
        "receive_id": CHAT_ID,
        "msg_type": "post",
        "content": json.dumps(post_content, ensure_ascii=False),
    }

    try:
        resp = httpx.post(
            f"{FEISHU_BASE}/im/v1/messages?receive_id_type=chat_id",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        print("status:", resp.status_code)
        print("resp.text:", resp.text)
        print("resp.json:", resp.json())
        resp.raise_for_status()
        result = resp.json()
        if result.get("code", 0) == 0:
            return True
        print(f"⚠️  飞书返回非零状态: {result}")
        return False
    except httpx.HTTPError as e:
        print(f"❌ 发送失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发送失败: {e}")
        return False


def send_webhook(payload: dict) -> bool:
    """通过自定义机器人 webhook 发消息（fallback）。"""
    if not WEBHOOK or "REPLACE_ME" in WEBHOOK:
        return False
    try:
        resp = httpx.post(WEBHOOK, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        return result.get("code", 0) == 0 or result.get("StatusCode") == 0
    except Exception:
        return False


def send_to_collect(question: str, answer: str, tool_calls: str, reason: str,
                    message_id: str = "", chat_id: str = "",
                    doc_names: str = "", scores: str = "") -> bool:
    """双写：把反馈写入多维表格。
    优先 COLLECT_URL（本机 collect.js 转发），否则直连飞书 Bitable API。
    """
    user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 字段必须与多维表格实际列名一致：
    # time / query / answer / tool_calls / reason / doc_names / scores
    # （表上还有一列“文本”保留留空，不在此处发送）
    fields = {
        "time": ts,
        "query": question,
        "answer": answer[:2000] if answer else "",
        "tool_calls": tool_calls[:2000] if tool_calls else "",
        "reason": reason[:1000] if reason else "",
        "doc_names": doc_names[:500] if doc_names else "",
        "scores": scores[:500] if scores else "",
    }
    records = [{"fields": fields}]

    if COLLECT_URL and "REPLACE_ME" not in COLLECT_URL:
        try:
            resp = httpx.post(COLLECT_URL, json={"records": records}, timeout=10)
            resp.raise_for_status()
            return resp.json().get("ok") is True
        except Exception as e:
            print(f"⚠️  collect 服务双写失败: {e}")
            return False

    if not BITABLE_APP_TOKEN or not BITABLE_TABLE_ID:
        return False

    token = get_token()
    if not token:
        return False

    url = (
        f"{FEISHU_BASE}/bitable/v1/apps/{BITABLE_APP_TOKEN}"
        f"/tables/{BITABLE_TABLE_ID}/records/batch_create"
    )
    try:
        resp = httpx.post(
            url,
            json={"records": records},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("code", 0) == 0:
            return True
        print(f"⚠️  Bitable 直连返回非零状态: {result}")
        return False
    except Exception as e:
        print(f"⚠️  Bitable 直连失败: {e}")
        return False


def preflight() -> bool:
    """启动前自检:关键 .env 配置全在,缺一个就明确告诉同事缺啥、文件在哪、怎么修。"""
    skill_root = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    )
    env_file = os.path.join(skill_root, ".env")

    required = {
        "FEISHU_APP_ID": APP_ID,
        "FEISHU_APP_SECRET": APP_SECRET,
        "FEEDBACK_CHAT_ID": CHAT_ID,
        "BITABLE_APP_TOKEN": BITABLE_APP_TOKEN,
        "BITABLE_TABLE_ID": BITABLE_TABLE_ID,
    }
    missing = [k for k, v in required.items() if not v]

    if not os.path.isfile(env_file):
        print(f"❌ 飞书配置未初始化: 找不到 {env_file}")
        print("   解压 skill 包时,部分系统会跳过 . 开头的隐藏文件。")
        print("   修法: 重新解压并打开\"显示隐藏文件\",确认 synhub/.env 存在后再填值。")
        return False

    if missing:
        print(f"❌ 飞书配置未初始化: {env_file} 中以下 key 未填:")
        for k in missing:
            print(f"   - {k}")
        print(f"\n   修法: 编辑 {env_file},把 7 个 key 全部填齐(找接入指南要凭证)。")
        print(f"   注意: feedback.py 只读 synhub/.env,改 .mcp.json 没用。")
        return False

    return True


def send(question: str, answer: str, tool_calls: str, reason: str) -> bool:
    """发送反馈:优先用 API,失败时 fallback 到 webhook。同时双写多维表格。"""
    if not preflight():
        return False

    content = build_content(question, answer, tool_calls, reason)

    # 从 tool_calls 中提取文档名和分数
    doc_names = ""
    scores = ""
    if tool_calls:
        import re
        # 提取文档名：文档: xxx
        doc_matches = re.findall(r'文档:\s*(.+?)(?:\n|$)', tool_calls)
        if doc_matches:
            doc_names = "; ".join(doc_matches)
        # 提取分数：score=x.xxx 或 rrf_score=x.xxxx
        score_matches = re.findall(r'(?:rrf_)?score[=:]\s*([\d.]+)', tool_calls)
        if score_matches:
            scores = "; ".join(score_matches)

    ok = False
    if APP_ID and APP_SECRET and CHAT_ID:
        if send_api(content):
            ok = True
        else:
            print("⚠️  API 发送失败，尝试 fallback webhook...")

    if not ok:
        user = os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text_lines = [f"📝 SynHub 反馈 @ {ts}"]
        if question:
            text_lines.append(f"🙋 提问: {truncate(question)}")
        if answer:
            text_lines.append(f"🤖 回答: {truncate(answer)}")
        if tool_calls and tool_calls.strip():
            text_lines.append(f"🔧 检索: {truncate(tool_calls, 1500)}")
        if reason and reason.strip():
            text_lines.append(f"💬 反馈: {truncate(reason, 1000)}")
        text_lines.append(f"👤 {user}")
        if send_webhook({"msg_type": "text", "content": {"text": "\n".join(text_lines)}}):
            ok = True

    # 双写：无论群消息是否成功，都尝试写多维表格
    send_to_collect(question, answer, tool_calls, reason, doc_names=doc_names, scores=scores)

    return ok


def main():
    parser = argparse.ArgumentParser(description="一键反馈 SynHub 知识库回答")
    parser.add_argument("--question", default="", help="用户的原始问题")
    parser.add_argument("--answer", default="", help="Claude 给出的回答")
    parser.add_argument("--tool-calls", default="", help="本次回答用到的检索 query / 文档 / 思考过程")
    parser.add_argument("--reason", default="", help="用户填写的不满意原因(可选)")
    args = parser.parse_args()

    if not (args.question or args.answer or args.reason):
        sys.exit("❌ 至少要提供 --question、--answer 或 --reason 之一")

    if send(args.question, args.answer, args.tool_calls, args.reason):
        print("✅ 反馈已发送给 SynHub 维护者,谢谢!")
    else:
        print("\n如果反复失败,请把以下内容贴给 rhMa0706:")
        print("---")
        print(json.dumps({
            "question": args.question,
            "answer": args.answer,
            "tool_calls": args.tool_calls,
            "reason": args.reason,
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
