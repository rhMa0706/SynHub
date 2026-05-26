"""SynHub 知识库答案质量检测工具。

逐题调用检索 API，对每题从四个维度评分（召回率、精确率、RRF 融合质量、语义匹配），
生成 eval_report.md 评测报告。

用法:
    python tests/answer_evaluator.py
    python tests/answer_evaluator.py --top-k 10 --timeout 60 --output report.md
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

# 文档名 → 分类映射前缀
CATEGORY_PREFIXES: dict[str, str] = {
    "01-综合基础": "01-综合基础",
    "02-TCL脚本": "02-TCL脚本",
    "03-时序约束": "03-时序约束",
    "04-时序优化": "04-时序优化",
    "05-面积优化": "05-面积优化",
    "06-功耗优化": "06-功耗优化",
    "07-DFX": "07-DFX",
    "08-后端接口": "08-后端接口",
    "09-常见问题": "09-常见问题",
    "10-实战案例": "10-实战案例",
    "11-红区绿区": "11-红区绿区",
}

# 预期分类字符串中使用的简写 → 标准分类名
_CATEGORY_ALIASES: dict[str, str] = {
    "01": "01-综合基础",
    "02": "02-TCL脚本",
    "03": "03-时序约束",
    "04": "04-时序优化",
    "05": "05-面积优化",
    "06": "06-功耗优化",
    "07": "07-DFX",
    "08": "08-后端接口",
    "09": "09-常见问题",
    "10": "10-实战案例",
    "11": "11-红区绿区",
}

# 评分阈值
PASS_THRESHOLD = 60  # 总分 >= 60 为通过
RECALL_PASS = 18     # 召回 >= 60% of 30
PRECISION_PASS = 18  # 精确 >= 60% of 30
RRF_PASS = 12        # RRF >= 60% of 20
SEMANTIC_PASS = 12   # 语义 >= 60% of 20

# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class Question:
    """一道评测问题。"""

    idx: str  # 唯一编号，如 "1-3" 表示第一部分第 3 题
    text: str
    expected_categories: list[str]  # 标准分类名列表
    section: str  # 所属部分名称
    keywords: str = ""  # 关键检索词（可选）


@dataclass
class ScoreResult:
    """单题评分结果。"""

    question: Question
    recall: float = 0.0
    precision: float = 0.0
    rrf_quality: float = 0.0
    semantic: float = 0.0
    total: float = 0.0
    hit_categories: list[str] = field(default_factory=list)
    results_count: int = 0
    relevant_count: int = 0
    error: str = ""

    @property
    def passed(self) -> bool:
        return self.total >= PASS_THRESHOLD and not self.error


# ---------------------------------------------------------------------------
# 问题解析
# ---------------------------------------------------------------------------


def _normalize_category(raw: str) -> str:
    """将原始分类字符串标准化为分类名。"""
    raw = raw.strip()
    # 去掉分类名中的补充说明，如 "04-时序优化 / 08-后端接口" → 已在调用方 split
    # 先尝试 alias 匹配
    if raw in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[raw]
    # 尝试前缀匹配
    for prefix in CATEGORY_PREFIXES:
        if raw.startswith(prefix):
            return prefix
    # 尝试纯数字匹配
    digits = re.match(r"^(\d+)", raw)
    if digits and digits.group(1) in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[digits.group(1)]
    return raw


def _parse_category_string(raw: str) -> list[str]:
    """解析预期分类字符串，返回标准分类名列表。

    支持格式:
    - "04-时序优化"
    - "04-时序优化 / 06-功耗优化"
    - "01 + 02 + 03 + 04 + 08"
    - "04 + 06"
    """
    raw = raw.strip()
    if not raw:
        return []

    # 用 "+" 或 "/" 分隔
    parts = re.split(r"\s*[+/]\s*", raw)
    return [_normalize_category(p) for p in parts if p.strip()]


def _detect_section(line: str) -> str | None:
    """检测是否为部分标题行。

    返回值:
      - 标准分类名: 属于评测问题的部分
      - "_DONE_": 遇到附录等非题目部分，停止解析表格
      - None: 不是部分标题行
    """
    m = re.match(r"^##\s+(.+)", line)
    if m:
        title = m.group(1).strip()
        # 提取中文部分
        section_map = {
            "一": "单文档精准命中",
            "二": "多文档综合回答",
            "三": "语义近似问题",
            "四": "跨域隐含关联",
            "五": "边界与反例",
        }
        for num, name in section_map.items():
            if num in title:
                return name
        # 遇到附录、使用方法等非题目标题，标记停止
        if "附录" in title or "附" in title:
            return "_DONE_"
    return None


def parse_questions(filepath: str | Path) -> list[Question]:
    """从 eval_questions.md 解析所有评测问题。"""
    filepath = Path(filepath)
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    questions: list[Question] = []
    current_section: str = ""
    section_counter: int = 0

    # 各部分表格解析正则
    # Section 1 (单文档精准命中): | # | 问题 | 预期命中分类 | 关键检索词 |
    # Section 2 (多文档综合回答): | # | 问题 | 预期命中分类 | 考察能力 |
    # Section 3 (语义近似问题):   | 组 | 问题A | 问题B | 问题C | 核心语义 |
    # Section 4 (跨域隐含关联):   | # | 问题 | 隐含关联 | 预期命中 |
    # Section 5 (边界与反例):     | # | 问题 | 预期行为 | 考察点 |

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测部分标题
        sec = _detect_section(line)
        if sec is not None:
            if sec == "_DONE_":
                break  # 到达附录，停止解析
            current_section = sec
            i += 1
            continue

        # 跳过分隔符
        if line.startswith("---") or line.startswith(">") or line.startswith("#"):
            i += 1
            continue

        # 跳过空行
        if not line:
            i += 1
            continue

        # 非问题部分不解析表格
        if not current_section:
            i += 1
            continue

        # 解析表格行
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]  # 去除空字符串

            if len(cells) < 2:
                i += 1
                continue

            # 跳过表头和分隔行
            if cells[0] in ("#", "组") or cells[0].startswith("-"):
                i += 1
                continue

            if current_section == "单文档精准命中":
                # | # | 问题 | 预期命中分类 | 关键检索词 |
                if len(cells) >= 3:
                    idx = cells[0].strip("`")
                    text = cells[1]
                    categories = _parse_category_string(cells[2])
                    keywords = cells[3] if len(cells) > 3 else ""
                    questions.append(Question(
                        idx=f"1-{idx}",
                        text=text,
                        expected_categories=categories,
                        section=current_section,
                        keywords=keywords,
                    ))

            elif current_section == "多文档综合回答":
                # | # | 问题 | 预期命中分类 | 考察能力 |
                if len(cells) >= 3:
                    idx = cells[0].strip("`")
                    text = cells[1]
                    categories = _parse_category_string(cells[2])
                    questions.append(Question(
                        idx=f"2-{idx}",
                        text=text,
                        expected_categories=categories,
                        section=current_section,
                    ))

            elif current_section == "语义近似问题":
                # | 组 | 问题 A | 问题 B | 问题 C | 核心语义 |
                if len(cells) >= 3:
                    group = cells[0]
                    if not group.isdigit():
                        i += 1
                        continue
                    # 将每个子问题独立作为评测项
                    sub_questions = [cells[1]]  # 问题 A
                    if len(cells) > 2 and cells[2]:
                        sub_questions.append(cells[2])  # 问题 B
                    if len(cells) > 3 and cells[3]:
                        sub_questions.append(cells[3])  # 问题 C
                    core_semantic = cells[4] if len(cells) > 4 else ""

                    for j, sub_q in enumerate(sub_questions):
                        label = chr(ord("A") + j)
                        questions.append(Question(
                            idx=f"3-{group}{label}",
                            text=sub_q,
                            expected_categories=[],  # 语义近似组不指定具体分类
                            section=current_section,
                            keywords=core_semantic,
                        ))

            elif current_section == "跨域隐含关联":
                # | # | 问题 | 隐含关联 | 预期命中 |
                if len(cells) >= 4:
                    idx = cells[0].strip("`")
                    text = cells[1]
                    # cells[2] 是隐含关联说明，不用于检索
                    categories = _parse_category_string(cells[3])
                    questions.append(Question(
                        idx=f"4-{idx}",
                        text=text,
                        expected_categories=categories,
                        section=current_section,
                    ))

            elif current_section == "边界与反例":
                # | # | 问题 | 预期行为 | 考察点 |
                if len(cells) >= 2:
                    idx = cells[0].strip("`")
                    text = cells[1]
                    questions.append(Question(
                        idx=f"5-{idx}",
                        text=text,
                        expected_categories=[],  # 边界题不指定预期分类
                        section=current_section,
                    ))

        i += 1

    return questions


# ---------------------------------------------------------------------------
# 文档分类推断
# ---------------------------------------------------------------------------


def infer_category(document_name: str) -> str:
    """根据文档名推断所属分类。"""
    name_lower = document_name.lower()
    for prefix, category in CATEGORY_PREFIXES.items():
        if prefix.lower() in name_lower:
            return category
    # 尝试从文件路径结构推断
    parts = document_name.replace("\\", "/").split("/")
    for part in parts:
        for prefix, category in CATEGORY_PREFIXES.items():
            if prefix in part:
                return category
    return "未知分类"


# ---------------------------------------------------------------------------
# 评分逻辑
# ---------------------------------------------------------------------------


def _compute_recall(expected: list[str], hit_categories: list[str]) -> float:
    """计算召回率得分 (0-30)。

    没有预期分类的题（语义近似组、边界题）默认给满分。
    """
    if not expected:
        return 30.0  # 无预期分类时给满分

    expected_set = set(expected)
    hit_set = set(hit_categories)
    matched = expected_set & hit_set
    if not expected_set:
        return 30.0
    return len(matched) / len(expected_set) * 30.0


def _compute_precision(results: list[dict[str, Any]], expected: list[str]) -> tuple[float, int, int]:
    """计算精确率得分 (0-30)。

    如果有预期分类，检查 top-K 结果中有多少文档属于预期分类。
    如果没有预期分类，基于原始 score 字段评估。
    返回 (score, relevant_count, total_count)。
    """
    if not results:
        return 0.0, 0, 0

    total = len(results)

    if expected:
        expected_set = set(expected)
        relevant = sum(
            1 for r in results
            if infer_category(r.get("document_name", "")) in expected_set
        )
        return relevant / total * 30.0, relevant, total
    else:
        # 无预期分类：基于 score 字段评估质量
        good_scores = sum(1 for r in results if r.get("score", 0) >= 0.5)
        return good_scores / total * 30.0, good_scores, total


def _compute_rrf_quality(results: list[dict[str, Any]]) -> float:
    """计算 RRF 融合质量得分 (0-20)。

    评估标准:
    1. 是否存在 rrf_score（说明融合成功）: 5 分
    2. rrf_score 分布是否合理（top-1 应显著高于 top-K）: 5 分
    3. 高 score 的文档是否排在前面（排名一致性）: 5 分
    4. 结果数量是否足够: 5 分
    """
    if not results:
        return 0.0

    score_total = 0.0

    # 1. 存在 rrf_score (5分)
    has_rrf = all("rrf_score" in r for r in results)
    if has_rrf:
        score_total += 5.0
    elif any("rrf_score" in r for r in results):
        score_total += 3.0

    # 2. rrf_score 分布合理性 (5分)
    rrf_scores = [r.get("rrf_score", 0) for r in results]
    if len(rrf_scores) >= 2:
        top_rrf = rrf_scores[0]
        bottom_rrf = rrf_scores[-1]
        if top_rrf > 0 and bottom_rrf > 0:
            ratio = top_rrf / bottom_rrf
            # top 应该比 bottom 高，但不应极端
            if 1.0 < ratio <= 10.0:
                score_total += 5.0
            elif 1.0 < ratio <= 20.0:
                score_total += 3.0
            elif ratio > 20.0:
                score_total += 1.0  # 分布过于集中
            else:
                score_total += 2.0  # 分布过于平坦
        elif top_rrf > 0:
            score_total += 3.0
    elif len(rrf_scores) == 1:
        score_total += 3.0

    # 3. 排名一致性 (5分) —— score 高的文档排名也高
    score_values = [r.get("score", 0) for r in results]
    if len(score_values) >= 2:
        consistent = True
        for j in range(len(score_values) - 1):
            # 如果 rrf_score 排序中，score 低的排在 score 高的前面超过 3 次
            if rrf_scores[j] < rrf_scores[j + 1] and score_values[j] < score_values[j + 1]:
                pass  # rrf 排序和 score 排序不一致
            if score_values[j] < score_values[j + 1] and rrf_scores[j] > rrf_scores[j + 1]:
                consistent = False
        if consistent:
            score_total += 5.0
        else:
            score_total += 2.0
    else:
        score_total += 3.0

    # 4. 结果数量 (5分)
    n = len(results)
    if n >= 5:
        score_total += 5.0
    elif n >= 3:
        score_total += 3.0
    elif n >= 1:
        score_total += 1.0

    return score_total


def _compute_semantic(results: list[dict[str, Any]], query: str) -> float:
    """计算语义匹配得分 (0-20)。

    基于原始 score 字段评估查询和文档的语义相似度。
    """
    if not results:
        return 0.0

    scores = [r.get("score", 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    # score 范围通常 0-1，映射到 0-20
    # avg_score >= 0.7 → 20分; 0.5-0.7 → 12-16分; 0.3-0.5 → 6-10分; <0.3 → 0-4分
    if avg_score >= 0.7:
        return 20.0
    elif avg_score >= 0.5:
        return 12.0 + (avg_score - 0.5) / 0.2 * 8.0
    elif avg_score >= 0.3:
        return 6.0 + (avg_score - 0.3) / 0.2 * 6.0
    elif avg_score >= 0.1:
        return (avg_score - 0.1) / 0.2 * 6.0
    else:
        return 0.0


def score_question(
    question: Question,
    results: list[dict[str, Any]],
) -> ScoreResult:
    """对单个问题进行评分。"""
    sr = ScoreResult(question=question, results_count=len(results))

    if not results:
        sr.error = "无检索结果"
        return sr

    # 1. 召回率
    hit_categories = list({infer_category(r.get("document_name", "")) for r in results})
    sr.hit_categories = hit_categories
    sr.recall = _compute_recall(question.expected_categories, hit_categories)

    # 2. 精确率
    sr.precision, sr.relevant_count, _ = _compute_precision(results, question.expected_categories)

    # 3. RRF 融合质量
    sr.rrf_quality = _compute_rrf_quality(results)

    # 4. 语义匹配
    sr.semantic = _compute_semantic(results, question.text)

    # 总分
    sr.total = sr.recall + sr.precision + sr.rrf_quality + sr.semantic
    return sr


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------


def generate_report(
    results: list[ScoreResult],
    output_path: str | Path,
    elapsed: float = 0.0,
) -> None:
    """生成 eval_report.md 评测报告。"""
    output_path = Path(output_path)

    total = len(results)
    if total == 0:
        output_path.write_text("# 评测报告\n\n没有评测问题。\n", encoding="utf-8")
        return

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    errors = [r for r in results if r.error]

    pass_rate = len(passed) / total * 100

    # 按分类统计
    by_section: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        by_section[r.question.section].append(r)

    # 按预期分类统计
    by_category: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        for cat in r.question.expected_categories:
            by_category[cat].append(r)

    # 召回为 0 的问题
    zero_recall = [r for r in results if r.recall == 0 and not r.error]

    # top-5 相关率低于 50% 的问题
    low_relevance = [
        r for r in results
        if r.results_count > 0 and r.relevant_count / r.results_count < 0.5
    ]

    lines: list[str] = []
    lines.append("# SynHub 知识库评测报告")
    lines.append("")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总耗时: {elapsed:.1f}s")
    lines.append(f"问题总数: {total}")
    lines.append("")

    # ── 总体结果 ──
    lines.append("## 总体结果")
    lines.append("")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 通过数 | {len(passed)} / {total} |")
    lines.append(f"| **通过率** | **{pass_rate:.1f}%** |")
    lines.append(f"| 错误数 | {len(errors)} |")
    lines.append("")

    # ── 各维度通过率 ──
    lines.append("### 各维度通过率")
    lines.append("")
    dim_recall = sum(1 for r in results if r.recall >= RECALL_PASS) / total * 100
    dim_precision = sum(1 for r in results if r.precision >= PRECISION_PASS) / total * 100
    dim_rrf = sum(1 for r in results if r.rrf_quality >= RRF_PASS) / total * 100
    dim_semantic = sum(1 for r in results if r.semantic >= SEMANTIC_PASS) / total * 100
    lines.append(f"| 维度 | 通过率 | 阈值 |")
    lines.append(f"|------|--------|------|")
    lines.append(f"| 召回率 (Recall) | {dim_recall:.1f}% | >= {RECALL_PASS}/30 |")
    lines.append(f"| 精确率 (Precision) | {dim_precision:.1f}% | >= {PRECISION_PASS}/30 |")
    lines.append(f"| RRF 融合质量 | {dim_rrf:.1f}% | >= {RRF_PASS}/20 |")
    lines.append(f"| 语义匹配 | {dim_semantic:.1f}% | >= {SEMANTIC_PASS}/20 |")
    lines.append("")

    # ── 各维度平均分 ──
    lines.append("### 各维度平均分")
    lines.append("")
    avg_recall = sum(r.recall for r in results) / total
    avg_precision = sum(r.precision for r in results) / total
    avg_rrf = sum(r.rrf_quality for r in results) / total
    avg_semantic = sum(r.semantic for r in results) / total
    avg_total = sum(r.total for r in results) / total
    lines.append(f"| 维度 | 平均分 | 满分 |")
    lines.append(f"|------|--------|------|")
    lines.append(f"| 召回率 | {avg_recall:.1f} | 30 |")
    lines.append(f"| 精确率 | {avg_precision:.1f} | 30 |")
    lines.append(f"| RRF 融合质量 | {avg_rrf:.1f} | 20 |")
    lines.append(f"| 语义匹配 | {avg_semantic:.1f} | 20 |")
    lines.append(f"| **总分** | **{avg_total:.1f}** | **100** |")
    lines.append("")

    # ── 按部分通过率 ──
    lines.append("## 按问题类型通过率")
    lines.append("")
    lines.append("| 部分 | 总数 | 通过数 | 通过率 | 平均分 |")
    lines.append("|------|------|--------|--------|--------|")
    for section_name in ["单文档精准命中", "多文档综合回答", "语义近似问题", "跨域隐含关联", "边界与反例"]:
        section_results = by_section.get(section_name, [])
        if not section_results:
            continue
        sec_total = len(section_results)
        sec_passed = sum(1 for r in section_results if r.passed)
        sec_avg = sum(r.total for r in section_results) / sec_total if sec_total else 0
        sec_rate = sec_passed / sec_total * 100 if sec_total else 0
        lines.append(f"| {section_name} | {sec_total} | {sec_passed} | {sec_rate:.1f}% | {sec_avg:.1f} |")
    lines.append("")

    # ── 按分类通过率 ──
    lines.append("## 按知识库分类通过率")
    lines.append("")
    lines.append("| 分类 | 相关题数 | 平均召回 | 平均精确 | 平均总分 |")
    lines.append("|------|----------|----------|----------|----------|")
    sorted_cats = sorted(by_category.keys())
    for cat in sorted_cats:
        cat_results = by_category[cat]
        cat_n = len(cat_results)
        cat_recall = sum(r.recall for r in cat_results) / cat_n if cat_n else 0
        cat_precision = sum(r.precision for r in cat_results) / cat_n if cat_n else 0
        cat_total = sum(r.total for r in cat_results) / cat_n if cat_n else 0
        lines.append(f"| {cat} | {cat_n} | {cat_recall:.1f} | {cat_precision:.1f} | {cat_total:.1f} |")
    lines.append("")

    # ── 召回为 0 的问题 ──
    lines.append("## 召回为 0 的问题（重点关注）")
    lines.append("")
    if zero_recall:
        lines.append(f"共 {len(zero_recall)} 题召回为 0：")
        lines.append("")
        lines.append("| 编号 | 问题 | 预期分类 | 错误信息 |")
        lines.append("|------|------|----------|----------|")
        for r in zero_recall:
            cats = ", ".join(r.question.expected_categories) or "无"
            err = r.error or "检索结果为空"
            text = r.question.text[:50] + ("..." if len(r.question.text) > 50 else "")
            lines.append(f"| {r.question.idx} | {text} | {cats} | {err} |")
        lines.append("")
    else:
        lines.append("无。")
        lines.append("")

    # ── Top-5 相关率低于 50% 的问题 ──
    lines.append("## Top-K 相关率低于 50% 的问题")
    lines.append("")
    if low_relevance:
        lines.append(f"共 {len(low_relevance)} 题相关率低于 50%：")
        lines.append("")
        lines.append("| 编号 | 问题 | 检索数 | 相关数 | 相关率 | 命中分类 |")
        lines.append("|------|------|--------|--------|--------|----------|")
        for r in low_relevance:
            rel_rate = r.relevant_count / r.results_count * 100 if r.results_count else 0
            cats = ", ".join(r.hit_categories) or "未知"
            text = r.question.text[:40] + ("..." if len(r.question.text) > 40 else "")
            lines.append(
                f"| {r.question.idx} | {text} | {r.results_count} "
                f"| {r.relevant_count} | {rel_rate:.0f}% | {cats} |"
            )
        lines.append("")
    else:
        lines.append("无。")
        lines.append("")

    # ── 逐题明细 ──
    lines.append("## 逐题评分明细")
    lines.append("")
    lines.append("| 编号 | 问题 | 召回 | 精确 | RRF | 语义 | 总分 | 通过 |")
    lines.append("|------|------|------|------|-----|------|------|------|")
    for r in results:
        text = r.question.text[:35] + ("..." if len(r.question.text) > 35 else "")
        status = "PASS" if r.passed else ("ERR" if r.error else "FAIL")
        lines.append(
            f"| {r.question.idx} | {text} "
            f"| {r.recall:.1f} | {r.precision:.1f} | {r.rrf_quality:.1f} | {r.semantic:.1f} "
            f"| {r.total:.1f} | {status} |"
        )
    lines.append("")

    # ── 未通过问题详情 ──
    if failed:
        lines.append("## 未通过问题详情")
        lines.append("")
        for r in failed:
            lines.append(f"### {r.question.idx}: {r.question.text}")
            lines.append("")
            cats = ", ".join(r.question.expected_categories) or "无"
            lines.append(f"- 预期分类: {cats}")
            lines.append(f"- 总分: {r.total:.1f} / 100")
            if r.error:
                lines.append(f"- 错误: {r.error}")
            lines.append(f"- 召回: {r.recall:.1f}/30, 精确: {r.precision:.1f}/30, "
                         f"RRF: {r.rrf_quality:.1f}/20, 语义: {r.semantic:.1f}/20")
            lines.append(f"- 命中分类: {', '.join(r.hit_categories) or '无'}")
            lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n报告已生成: {output_path}")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def run_evaluation(
    questions_file: str | Path | None = None,
    output_file: str | Path | None = None,
    top_k: int = 5,
    timeout: float = 60.0,
    max_questions: int = 0,
    section_filter: str | None = None,
) -> list[ScoreResult]:
    """执行评测主流程。

    Args:
        questions_file: 问题文件路径，默认查找 eval_questions_v2.md 或 eval_questions.md
        output_file: 输出报告路径，默认 tests/eval_report.md
        top_k: 检索返回的文档数
        timeout: 每题检索超时时间（秒）
        max_questions: 最多评测的题目数（0 表示不限制）
        section_filter: 只评测指定部分（如 "单文档精准命中"），None 表示全部

    Returns:
        所有题目的评分结果列表
    """
    # 定位问题文件
    if questions_file is None:
        tests_dir = Path(__file__).parent
        v2_path = tests_dir / "eval_questions_v2.md"
        v1_path = tests_dir / "eval_questions.md"
        if v2_path.exists():
            questions_file = v2_path
        elif v1_path.exists():
            questions_file = v1_path
        else:
            print("错误: 未找到 eval_questions.md 或 eval_questions_v2.md")
            return []

    questions_file = Path(questions_file)
    if not questions_file.exists():
        print(f"错误: 问题文件不存在: {questions_file}")
        return []

    # 定位输出文件
    if output_file is None:
        output_file = Path(__file__).parent / "eval_report.md"
    output_file = Path(output_file)

    # 解析问题
    print(f"解析问题文件: {questions_file}")
    questions = parse_questions(questions_file)
    print(f"共解析到 {len(questions)} 道评测问题")

    # 部分过滤
    if section_filter:
        questions = [q for q in questions if q.section == section_filter]
        print(f"过滤后剩余 {len(questions)} 道题（部分: {section_filter}）")

    # 数量限制
    if max_questions > 0:
        questions = questions[:max_questions]
        print(f"限制为前 {max_questions} 道题")

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

            if elapsed_q > timeout:
                print(f"  警告: 检索耗时 {elapsed_q:.1f}s (超过 {timeout}s 阈值)")

            sr = score_question(q, results)
            sr.results_count = len(results)
            print(
                f"  检索到 {len(results)} 条结果 | "
                f"召回={sr.recall:.1f} 精确={sr.precision:.1f} "
                f"RRF={sr.rrf_quality:.1f} 语义={sr.semantic:.1f} "
                f"总分={sr.total:.1f} {'PASS' if sr.passed else 'FAIL'}"
            )

        except Exception as e:
            sr = ScoreResult(question=q, error=str(e))
            print(f"  错误: {e}")

        score_results.append(sr)

    total_elapsed = time.time() - total_start

    # 生成报告
    print(f"\n评测完成，总耗时: {total_elapsed:.1f}s")
    print(f"通过: {sum(1 for r in score_results if r.passed)} / {len(score_results)}")
    generate_report(score_results, output_file, elapsed=total_elapsed)

    return score_results


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SynHub 知识库答案质量检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/answer_evaluator.py                          # 运行全部评测
  python tests/answer_evaluator.py --top-k 10              # 返回 10 条结果
  python tests/answer_evaluator.py --max-questions 5       # 只测前 5 题
  python tests/answer_evaluator.py --section 单文档精准命中  # 只测某一类
  python tests/answer_evaluator.py --output my_report.md   # 自定义输出路径
        """,
    )
    parser.add_argument(
        "--questions", "-q",
        type=str,
        default=None,
        help="问题文件路径（默认自动查找 eval_questions_v2.md 或 eval_questions.md）",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出报告路径（默认 tests/eval_report.md）",
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=5,
        help="每题检索返回的文档数（默认 5）",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=60.0,
        help="每题检索超时时间，单位秒（默认 60）",
    )
    parser.add_argument(
        "--max-questions", "-m",
        type=int,
        default=0,
        help="最多评测的题目数（默认 0 = 不限制）",
    )
    parser.add_argument(
        "--section", "-s",
        type=str,
        default=None,
        choices=["单文档精准命中", "多文档综合回答", "语义近似问题", "跨域隐含关联", "边界与反例"],
        help="只评测指定部分",
    )

    args = parser.parse_args()

    results = run_evaluation(
        questions_file=args.questions,
        output_file=args.output,
        top_k=args.top_k,
        timeout=args.timeout,
        max_questions=args.max_questions,
        section_filter=args.section,
    )

    if results:
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"\n最终结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
