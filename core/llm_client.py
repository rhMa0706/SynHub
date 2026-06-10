from pathlib import Path

from anthropic import Anthropic

from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# 从外部文件加载 system prompt，方便迭代优化，无需改代码
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8").strip()


def _build_context(context_docs: str) -> str:
    """将检索到的文档片段拼接为上下文文本。"""
    if not context_docs.strip():
        return ""
    return f"""\
<参考资料>
{context_docs}
</参考资料>"""


def ask_with_context(query: str, context_docs: str) -> str:
    """调用 LLM 回答问题。

    Args:
        query: 用户问题
        context_docs: 由 mify_client.search() 返回的格式化参考资料
    """
    client = Anthropic(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )

    context_block = _build_context(context_docs)
    if context_block:
        user_message = f"{context_block}\n\n用户问题：{query}"
    else:
        user_message = f"用户问题：{query}"

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text
