from anthropic import Anthropic

from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_PROMPT = """\
你是芯片综合（Logic Synthesis）领域的资深技术专家，拥有丰富的数字芯片设计与综合经验。

你的职责是：
1. 基于提供的参考资料，准确回答用户关于芯片综合的问题
2. 回答时优先引用参考资料中的内容，确保信息有据可查
3. 如果参考资料不足以回答问题，请如实说明"根据现有资料无法确定"，不要编造信息
4. 回答要专业、简洁、有条理

你可以回答的领域包括但不限于：
- 逻辑综合（DC / Genus 等工具使用与流程）
- 时序分析与约束（SDC、时序收敛）
- 功耗优化（多电压域、power gating、clock gating）
- 面积优化与 QoR 改善
- 形式验证（LEC / Formality）
- DFT 相关流程
- 脚本编写（Tcl / 系列化脚本）\
"""


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
