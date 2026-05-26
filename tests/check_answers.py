"""SynHub 低功耗知识库答案质量检测工具。

逐题调用检索 API，对每题从四个维度评分（召回率、精确率、检索分数、内容相关性），
生成 eval_answers_report.md 评测报告。

用法:
    python tests/check_answers.py
    python tests/check_answers.py --questions tests/eval_questions_lp.md
    python tests/check_answers.py --top-k 10 --output tests/eval_answers_report.md
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 确保项目根目录在 sys.path 中，以便 import core / config
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.mify_client import retrieve  # noqa: E402

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

PASS_THRESHOLD = 60  # 总分 >= 60 为通过
HIGH_SCORE_THRESHOLD = 90  # >= 90 为标杆题目

# 题目类型名称 → 评测问题中的 section 标题
QUESTION_TYPE_MAP: dict[str, str] = {
    "CLP规则类": "CLP 规则类",
    "UPF实现类": "UPF 实现类",
    "LP Cell类": "LP Cell 类",
    "流程配置类": "流程与配置类",
    "案例分析类": "案例分析类",
}

# section 标题中的中文数字 → 类型名称
_SECTION_NUM_MAP: dict[str, str] = {
    "一": "CLP 规则类",
    "二": "UPF 实现类",
    "三": "LP Cell 类",
    "四": "流程与配置类",
    "五": "案例分析类",
}

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class Question:
    """一道评测问题。"""

    idx: str  # 编号，如 "1"
    text: str  # 问题文本
    expected_docs: list[str]  # 预期命中的文档名列表
    keywords: list[str]  # 核心检索词列表
    question_type: str = ""  # 题目类型（CLP规则类 / UPF实现类 / ...）


@dataclass
class ScoreResult:
    """单题评分结果。"""

    question: Question
    recall: float = 0.0  # 召回率得分 (0-30)
    precision: float = 0.0  # 精确率得分 (0-30)
    retrieval_score: float = 0.0  # 检索分数 (0-20)
    content_relevance: float = 0.0  # 内容相关性 (0-20)
    total: float = 0.0
    hit_docs: list[str] = field(default_factory=list)  # 命中的预期文档
    top_results: list[dict[str, Any]] = field(default_factory=list)  # 检索结果前几条
    error: str = ""

    @property
    def passed(self) -> bool:
        return self.total >= PASS_THRESHOLD and not self.error

    @property
    def is_benchmark(self) -> bool:
        return self.total >= HIGH_SCORE_THRESHOLD and not self.error


# ---------------------------------------------------------------------------
# 问题解析
# ---------------------------------------------------------------------------


def _parse_keywords(raw: str) -> list[str]:
    """解析核心检索词，支持逗号、顿号、分号分隔。"""
    raw = raw.strip()
    if not raw:
        return []
    # 支持中英文逗号、顿号、分号、斜杠分隔
    parts = re.split(r"[,，、;/]+", raw)
    return [p.strip() for p in parts if p.strip()]


def _parse_expected_docs(raw: str) -> list[str]:
    """解析预期命中文档名，支持逗号、顿号、分号、加号、斜杠分隔。

    注意：斜杠分隔仅在两边都有空格时使用（如 "A / B"），避免误拆文件路径。
    """
    raw = raw.strip()
    if not raw:
        return []
    # 先按 " / " 分隔（两边有空格的斜杠，表示多个文档名）
    parts = re.split(r"\s*/\s*", raw)
    # 再按其他分隔符拆分
    result: list[str] = []
    for part in parts:
        sub_parts = re.split(r"[,，、;+]+", part)
        result.extend(sub_parts)
    return [p.strip() for p in result if p.strip()]


def parse_questions(filepath: str | Path) -> list[Question]:
    """从 eval_questions_lp.md 解析所有评测问题。

    支持的 Markdown 表格格式（4列或5列）:
    | # | 问题 | 预期命中文档 | 核心检索词 |
    | # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
    """
    filepath = Path(filepath)
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    questions: list[Question] = []
    current_type: str = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测类型标题 (## 一、CLP 规则类（10 题） 或 ## CLP 规则类)
        if line.startswith("## "):
            title = line[3:].strip()
            # 尝试通过中文数字匹配
            matched = False
            for num_char, type_name in _SECTION_NUM_MAP.items():
                if num_char in title:
                    current_type = type_name
                    matched = True
                    break
            # 未匹配到中文数字时，尝试类型名称匹配
            if not matched:
                for type_name in QUESTION_TYPE_MAP.values():
                    if type_name in title:
                        current_type = type_name
                        break
            i += 1
            continue

        # 跳过分隔符、空行、引用行
        if line.startswith("---") or line.startswith(">") or line.startswith("#") or not line:
            i += 1
            continue

        # 解析表格行
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c != ""]  # 去除空字符串

            if len(cells) < 3:
                i += 1
                continue

            # 跳过表头行和分隔行
            if cells[0] in ("#", "---", "----") or cells[0].startswith("-"):
                i += 1
                continue

            # 支持 4 列和 5 列格式
            # 4 列: | # | 问题 | 预期命中文档 | 核心检索词 |
            # 5 列: | # | 问题 | 预期命中文档 | 核心检索词 | 难度 |
            idx = cells[0].strip().strip("`")

            # 跳过非问题行：第一列必须是数字编号
            if not idx.isdigit():
                i += 1
                continue

            text = cells[1].strip()
            expected_docs_raw = cells[2].strip() if len(cells) > 2 else ""
            keywords_raw = cells[3].strip() if len(cells) > 3 else ""
            # cells[4] 是难度（如有），暂不使用

            expected_docs = _parse_expected_docs(expected_docs_raw)
            keywords = _parse_keywords(keywords_raw)

            questions.append(Question(
                idx=idx,
                text=text,
                expected_docs=expected_docs,
                keywords=keywords,
                question_type=current_type,
            ))

        i += 1

    return questions


# ---------------------------------------------------------------------------
# 文档名匹配
# ---------------------------------------------------------------------------


def _doc_matches(expected_doc: str, actual_doc: str) -> bool:
    """检查预期文档名是否与实际文档名匹配（精确匹配或包含关系）。"""
    exp = expected_doc.strip().lower()
    act = actual_doc.strip().lower()

    # 精确匹配
    if exp == act:
        return True

    # 包含关系：预期文档名包含在实际文档名中
    if exp in act:
        return True

    # 反向包含：实际文档名包含在预期文档名中
    if act in exp:
        return True

    # 关键词匹配：预期文档名的核心词出现在实际文档名中
    # 例如 "UPF gen flow" 匹配 "UPF gen flow 低功耗"
    exp_words = set(exp.split())
    act_words = set(act.split())
    if exp_words and exp_words.issubset(act_words):
        return True

    return False


def _find_hit_docs(
    expected_docs: list[str],
    results: list[dict[str, Any]],
) -> list[str]:
    """找出检索结果中命中的预期文档名列表。"""
    hit_docs: list[str] = []
    for exp_doc in expected_docs:
        for r in results:
            actual_doc = r.get("document_name", "")
            if _doc_matches(exp_doc, actual_doc):
                if exp_doc not in hit_docs:
                    hit_docs.append(exp_doc)
                break
    return hit_docs


# ---------------------------------------------------------------------------
# 评分逻辑
# ---------------------------------------------------------------------------


def _compute_recall(expected_docs: list[str], hit_docs: list[str]) -> float:
    """计算召回率得分 (0-30)。

    命中 1 篇 = 15分，命中 2 篇 = 25分，全部命中 = 30分。
    """
    if not expected_docs:
        return 30.0  # 无预期文档时给满分

    n_hit = len(hit_docs)
    n_expected = len(expected_docs)

    if n_hit == 0:
        return 0.0
    elif n_hit == 1:
        return 15.0
    elif n_hit == 2:
        return 25.0
    else:
        # 全部命中 = 30分，按比例递增
        return min(30.0, 25.0 + (n_hit - 2) / max(n_expected - 2, 1) * 5.0)


def _compute_precision(
    results: list[dict[str, Any]],
    expected_docs: list[str],
) -> float:
    """计算精确率得分 (0-30)。

    如果 top-5 中有 >=3 篇是预期文档 = 满分 (30分)。
    按比例递减。
    """
    if not results:
        return 0.0

    top_5 = results[:5]
    top_10 = results[:10]

    # 计算 top-5 中命中的数量
    top_5_hits = 0
    for r in top_5:
        doc_name = r.get("document_name", "")
        for exp_doc in expected_docs:
            if _doc_matches(exp_doc, doc_name):
                top_5_hits += 1
                break

    # 计算 top-10 中命中的比例
    top_10_hits = 0
    for r in top_10:
        doc_name = r.get("document_name", "")
        for exp_doc in expected_docs:
            if _doc_matches(exp_doc, doc_name):
                top_10_hits += 1
                break

    # top-5 中有 >=3 篇是预期文档 = 满分
    if top_5_hits >= 3:
        return 30.0

    # 按 top-5 命中数计算
    if top_5_hits >= 1:
        base = top_5_hits / 3 * 30.0
    else:
        base = 0.0

    # 如果 top-10 中有更多命中，适当加分
    if len(top_10) > 0:
        ratio = top_10_hits / len(top_10)
        precision_score = base * 0.7 + ratio * 30.0 * 0.3
    else:
        precision_score = base

    return min(30.0, precision_score)


def _compute_retrieval_score(results: list[dict[str, Any]]) -> float:
    """计算检索分数 (0-20)。

    基于 Mify 返回的 score 字段。
    score >= 0.5 = 20分
    score >= 0.3 = 15分
    score >= 0.1 = 10分
    score > 0 = 5分
    """
    if not results:
        return 0.0

    # 取 top-3 的平均 score
    top_scores = [r.get("score", 0) for r in results[:3]]
    if not top_scores:
        return 0.0

    avg_score = sum(top_scores) / len(top_scores)

    if avg_score >= 0.5:
        return 20.0
    elif avg_score >= 0.3:
        return 15.0
    elif avg_score >= 0.1:
        return 10.0
    elif avg_score > 0:
        return 5.0
    else:
        return 0.0


def _compute_content_relevance(
    results: list[dict[str, Any]],
    keywords: list[str],
) -> float:
    """计算内容相关性得分 (0-20)。

    检查 top-3 结果的 content 是否包含问题中的核心检索词。
    每包含 1 个检索词 = 4分（最高 20分）。
    """
    if not results or not keywords:
        return 0.0

    top_3 = results[:3]
    # 合并 top-3 的 content
    all_content = " ".join(r.get("content", "") for r in top_3)
    all_content_lower = all_content.lower()

    hit_count = 0
    for kw in keywords:
        kw_lower = kw.strip().lower()
        if kw_lower and kw_lower in all_content_lower:
            hit_count += 1

    return min(20.0, hit_count * 4.0)


def score_question(
    question: Question,
    results: list[dict[str, Any]],
) -> ScoreResult:
    """对单个问题进行评分。"""
    sr = ScoreResult(
        question=question,
        top_results=results[:5],
    )

    if not results:
        sr.error = "检索无结果"
        return sr

    # 找出命中的预期文档
    sr.hit_docs = _find_hit_docs(question.expected_docs, results)

    # 1. 召回率 (30分)
    sr.recall = _compute_recall(question.expected_docs, sr.hit_docs)

    # 2. 精确率 (30分)
    sr.precision = _compute_precision(results, question.expected_docs)

    # 3. 检索分数 (20分)
    sr.retrieval_score = _compute_retrieval_score(results)

    # 4. 内容相关性 (20分)
    sr.content_relevance = _compute_content_relevance(results, question.keywords)

    # 总分
    sr.total = sr.recall + sr.precision + sr.retrieval_score + sr.content_relevance
    return sr


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------


def generate_report(
    results: list[ScoreResult],
    output_path: str | Path,
    elapsed: float = 0.0,
) -> None:
    """生成 eval_answers_report.md 评测报告。"""
    output_path = Path(output_path)

    total = len(results)
    if total == 0:
        output_path.write_text("# 评测报告\n\n没有评测问题。\n", encoding="utf-8")
        return

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed and not r.error]
    errors = [r for r in results if r.error]
    benchmarks = [r for r in results if r.is_benchmark]

    pass_rate = len(passed) / total * 100

    # 按题目类型统计
    by_type: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        by_type[r.question.question_type].append(r)

    lines: list[str] = []

    # ── 标题 ──
    lines.append("# SynHub 低功耗知识库答案质量评测报告")
    lines.append("")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总耗时: {elapsed:.1f}s")
    lines.append(f"问题总数: {total}")
    lines.append("")

    # ── 1. 总览 ──
    lines.append("## 1. 总览")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 总题数 | {total} |")
    lines.append(f"| 通过题数 (>=60分) | {len(passed)} |")
    lines.append(f"| **通过率** | **{pass_rate:.1f}%** |")
    lines.append(f"| 标杆题数 (>=90分) | {len(benchmarks)} |")
    lines.append(f"| 错误题数 | {len(errors)} |")
    lines.append("")

    # ── 2. 按类型统计 ──
    lines.append("## 2. 按类型统计")
    lines.append("")
    lines.append("| 题目类型 | 总数 | 通过数 | 通过率 | 平均分 |")
    lines.append("|----------|------|--------|--------|--------|")

    type_order = ["CLP 规则类", "UPF 实现类", "LP Cell 类", "流程与配置类", "案例分析类"]
    for type_name in type_order:
        type_results = by_type.get(type_name, [])
        if not type_results:
            continue
        type_total = len(type_results)
        type_passed = sum(1 for r in type_results if r.passed)
        type_avg = sum(r.total for r in type_results) / type_total
        type_rate = type_passed / type_total * 100
        lines.append(f"| {type_name} | {type_total} | {type_passed} | {type_rate:.1f}% | {type_avg:.1f} |")
    lines.append("")

    # ── 3. 各维度平均分 ──
    lines.append("### 各维度平均分")
    lines.append("")
    avg_recall = sum(r.recall for r in results) / total
    avg_precision = sum(r.precision for r in results) / total
    avg_retrieval = sum(r.retrieval_score for r in results) / total
    avg_content = sum(r.content_relevance for r in results) / total
    avg_total = sum(r.total for r in results) / total
    lines.append("| 维度 | 平均分 | 满分 |")
    lines.append("|------|--------|------|")
    lines.append(f"| 召回率 | {avg_recall:.1f} | 30 |")
    lines.append(f"| 精确率 | {avg_precision:.1f} | 30 |")
    lines.append(f"| 检索分数 | {avg_retrieval:.1f} | 20 |")
    lines.append(f"| 内容相关性 | {avg_content:.1f} | 20 |")
    lines.append(f"| **总分** | **{avg_total:.1f}** | **100** |")
    lines.append("")

    # ── 4. 每题详情 ──
    lines.append("## 3. 每题详情")
    lines.append("")
    lines.append("| 编号 | 题目类型 | 问题 | 召回 | 精确 | 检索分 | 内容分 | 总分 | 状态 |")
    lines.append("|------|----------|------|------|------|--------|--------|------|------|")
    for r in results:
        text = r.question.text[:30] + ("..." if len(r.question.text) > 30 else "")
        qtype = r.question.question_type[:8] if r.question.question_type else ""
        if r.error:
            status = "ERROR"
        elif r.is_benchmark:
            status = "BENCHMARK"
        elif r.passed:
            status = "PASS"
        else:
            status = "FAIL"
        lines.append(
            f"| {r.question.idx} | {qtype} | {text} "
            f"| {r.recall:.1f} | {r.precision:.1f} | {r.retrieval_score:.1f} | {r.content_relevance:.1f} "
            f"| {r.total:.1f} | {status} |"
        )
    lines.append("")

    # 命中文档详情
    lines.append("### 命中文档详情")
    lines.append("")
    for r in results:
        hit_str = ", ".join(r.hit_docs) if r.hit_docs else "无"
        exp_str = ", ".join(r.question.expected_docs) if r.question.expected_docs else "无"
        lines.append(f"**{r.question.idx}.** {r.question.text[:50]}...")
        lines.append(f"- 预期文档: {exp_str}")
        lines.append(f"- 命中文档: {hit_str}")
        lines.append("")

    # ── 5. 问题清单（失分题目） ──
    lines.append("## 4. 问题清单（得分 <60）")
    lines.append("")

    problem_questions = [r for r in results if r.total < 60 or r.error]
    if problem_questions:
        lines.append(f"共 {len(problem_questions)} 题未通过：")
        lines.append("")

        for r in problem_questions:
            # 标红（Markdown 中用加粗 + 警告标记）
            lines.append(f"### **[未通过] {r.question.idx}. {r.question.text}**")
            lines.append("")
            lines.append(f"- **总分: {r.total:.1f}/100** (通过线: 60)")
            lines.append(f"- 题目类型: {r.question.question_type}")

            if r.error:
                lines.append(f"- **错误: {r.error}**")

            # 失分原因分析
            reasons = []
            if r.recall < 15:
                reasons.append(f"召回率低 ({r.recall:.1f}/30): 未能命中预期文档")
            elif r.recall < 25:
                reasons.append(f"召回率不足 ({r.recall:.1f}/30): 仅部分命中预期文档")

            if r.precision < 15:
                reasons.append(f"精确率低 ({r.precision:.1f}/30): 检索结果中预期文档占比不足")

            if r.retrieval_score < 10:
                reasons.append(f"检索分数低 ({r.retrieval_score:.1f}/20): 返回结果的相关性分数不高")

            if r.content_relevance < 8:
                reasons.append(f"内容相关性低 ({r.content_relevance:.1f}/20): 检索结果未充分包含核心检索词")

            if reasons:
                lines.append("- **失分原因:**")
                for reason in reasons:
                    lines.append(f"  - {reason}")

            lines.append("")

            exp_str = ", ".join(r.question.expected_docs) if r.question.expected_docs else "无"
            hit_str = ", ".join(r.hit_docs) if r.hit_docs else "无"
            lines.append(f"  - 预期文档: {exp_str}")
            lines.append(f"  - 命中文档: {hit_str}")
            lines.append("")
    else:
        lines.append("所有题目均通过。")
        lines.append("")

    # ── 6. 高分标杆题 ──
    lines.append("## 5. 高分标杆题（>=90分）")
    lines.append("")

    if benchmarks:
        lines.append(f"共 {len(benchmarks)} 道标杆题目：")
        lines.append("")
        for r in benchmarks:
            lines.append(f"### **[标杆] {r.question.idx}. {r.question.text}**")
            lines.append(f"- 总分: **{r.total:.1f}/100**")
            lines.append(f"- 召回率: {r.recall:.1f}/30, 精确率: {r.precision:.1f}/30, "
                         f"检索分数: {r.retrieval_score:.1f}/20, 内容相关性: {r.content_relevance:.1f}/20")
            hit_str = ", ".join(r.hit_docs) if r.hit_docs else "无"
            lines.append(f"- 命中文档: {hit_str}")
            lines.append("")
    else:
        lines.append("暂无标杆题目（>=90分）。")
        lines.append("")

    # 写入文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已生成: {output_path}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run_check(
    questions_file: str | Path | None = None,
    output_file: str | Path | None = None,
    top_k: int = 10,
) -> list[ScoreResult]:
    """执行评测主流程。

    Args:
        questions_file: 问题文件路径，默认 tests/eval_questions_lp.md
        output_file: 输出报告路径，默认 tests/eval_answers_report.md
        top_k: 检索返回的文档数

    Returns:
        所有题目的评分结果列表
    """
    # 定位问题文件
    if questions_file is None:
        questions_file = Path(__file__).parent / "eval_questions_lp.md"
    questions_file = Path(questions_file)

    if not questions_file.exists():
        print(f"错误: 问题文件不存在: {questions_file}")
        return []

    # 定位输出文件
    if output_file is None:
        output_file = Path(__file__).parent / "eval_answers_report.md"
    output_file = Path(output_file)

    # 解析问题
    print(f"解析问题文件: {questions_file}")
    questions = parse_questions(questions_file)
    print(f"共解析到 {len(questions)} 道评测问题")

    if not questions:
        print("未解析到任何问题，请检查问题文件格式")
        return []

    # 检查 API 配置
    from config.settings import MIFY_API_KEY, MIFY_DATASET_ID
    if not MIFY_API_KEY or not MIFY_DATASET_ID:
        print("错误: 未配置 MIFY_API_KEY 或 MIFY_DATASET_ID，请检查 .env 文件")
        return []

    # 逐题评测
    score_results: list[ScoreResult] = []
    total_start = time.time()

    for i, q in enumerate(questions):
        progress = f"[{i + 1}/{len(questions)}]"
        print(f"\n{progress} 评测: {q.idx} - {q.text[:60]}...")

        try:
            start = time.time()
            results = retrieve(q.text, top_k=top_k)
            elapsed_q = time.time() - start

            sr = score_question(q, results)
            sr.top_results = results[:5]

            status = "PASS" if sr.passed else ("BENCHMARK" if sr.is_benchmark else "FAIL")
            print(
                f"  检索到 {len(results)} 条结果 ({elapsed_q:.1f}s) | "
                f"召回={sr.recall:.1f} 精确={sr.precision:.1f} "
                f"检索={sr.retrieval_score:.1f} 内容={sr.content_relevance:.1f} "
                f"总分={sr.total:.1f} {status}"
            )
            if sr.hit_docs:
                print(f"  命中文档: {', '.join(sr.hit_docs)}")

        except Exception as e:
            sr = ScoreResult(question=q, error=str(e))
            print(f"  错误: {e}")

        score_results.append(sr)

        # 每次 API 调用间隔 0.5 秒，避免被限流
        if i < len(questions) - 1:
            time.sleep(0.5)

    total_elapsed = time.time() - total_start

    # 生成报告
    print(f"\n评测完成，总耗时: {total_elapsed:.1f}s")
    passed = sum(1 for r in score_results if r.passed)
    total = len(score_results)
    print(f"通过: {passed}/{total} ({passed / total * 100:.1f}%)")
    generate_report(score_results, output_file, elapsed=total_elapsed)

    return score_results


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SynHub 低功耗知识库答案质量检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/check_answers.py                                    # 使用默认参数运行
  python tests/check_answers.py --questions tests/eval_questions_lp.md
  python tests/check_answers.py --top-k 10 --output report.md
        """,
    )
    parser.add_argument(
        "--questions", "-q",
        type=str,
        default=None,
        help="问题文件路径（默认 tests/eval_questions_lp.md）",
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=10,
        help="每题检索返回的文档数（默认 10）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出报告路径（默认 tests/eval_answers_report.md）",
    )

    args = parser.parse_args()

    results = run_check(
        questions_file=args.questions,
        output_file=args.output,
        top_k=args.top_k,
    )

    if results:
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        benchmarks = sum(1 for r in results if r.is_benchmark)
        print(f"\n最终结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%), "
              f"{benchmarks} 道标杆题")


if __name__ == "__main__":
    main()
