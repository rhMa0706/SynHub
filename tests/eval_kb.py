"""SynHub KB 检索评估器 v2 — 按技术域加权 36 题。

用法:
    python tests/eval_kb.py                          # 跑全部 36 题
    python tests/eval_kb.py --top-k 5 --output report.md
    python tests/eval_kb.py --max-questions 10       # 只跑前 10 题
    python tests/eval_kb.py --domain A               # 只跑域 A 的题
    python tests/eval_kb.py --section B3             # 只跑子域 B3 的题
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 确保项目根目录在 sys.path 中
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.mify_client import retrieve, _retrieve_one_dataset  # noqa: E402
from config.settings import MIFY_API_KEY, MIFY_DATASET_IDS, DOMAIN_MAP  # noqa: E402

# ---------------------------------------------------------------------------
# 复用旧评估器的工具函数
# ---------------------------------------------------------------------------
from tests.check_answers import _doc_matches, _find_hit_docs  # noqa: E402
from tests.answer_evaluator import _compute_rrf_quality  # noqa: E402

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

PASS_THRESHOLD = 60
TAU = 0.35                  # 边界题诚实度阈值
PREFIX_NEIGHBOR_PENALTY = 4  # 前缀邻居扣分（每篇）
NOISE_HIT_PENALTY = 5        # 边界题噪声命中扣分（每篇）

# KB 名 → dataset_id 映射
_KB_NAME_TO_ID: dict[str, str] = {v["name"]: k for k, v in DOMAIN_MAP.items()}
# 别名映射(题集中使用的简称)
# v3 题库的预期文档是"飞书 token .md 文件名",这些文件全部在各 PartN/新库里,
# 因此 SDC/Memory 别名指向 Part2/新库对应的 dataset_id
_KB_ALIAS_TO_ID: dict[str, str] = {
    # 主库(v3 用飞书 token 文件名 → 全部落在这些库)
    "SDC": "dce185be-b1c9-4a86-bd4d-7e6d43346255",           # SDC Part2
    "Memory": "52dfe94f-507e-4cff-a172-6d86d90bc582",         # Memory Part2
    "低功耗": "e7c1e746-e1d0-4bb3-b378-d36e6fe08291",         # 低功耗 Part 2(v3 飞书 token 文档全在此)
    # v3 扩展别名
    "时序": "bb4d9587-8010-46b1-b8cf-8798b0c6a0eb",           # 时序分析
    "综合": "2fb30098-e238-4daa-992c-d7b9d735e87c",           # 综合策略
    "DFT": "5c906757-2747-4718-9522-bd17852035ab",
    "PPA": "39a13266-3e70-43bb-9e38-32c7ff6e5eea",
    "Signoff": "acc7250a-026f-437f-86bc-28c45f2b383f",
    "formal": "fb33c54a-42ea-45ae-8b1a-668d6c71d8c4",         # LEC 库
    "穿线": "82a67a2c-f83c-41be-9fa8-d8646bdad631",
    "交付": "a7851884-20e8-47f8-a46f-2492de614646",
    "复盘": "e4821655-d759-41ce-ad6d-7d09ee6de943",
    "—": "",  # boundary 题占位
    # 保留 v2 老库别名(如需回归 v2 题库时用)
    "SDC-legacy": "b26e181e-fc6c-4371-8a11-3e19580afd85",
    "Memory-legacy": "fa43ebb5-0333-4e8f-9351-33952daafaec",
}
# 反向：id → 简称
_ID_TO_KB_ALIAS: dict[str, str] = {v: k for k, v in _KB_ALIAS_TO_ID.items()}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class Question:
    """一道评测问题。"""

    idx: str
    qtype: str          # single_doc / multi_doc / cross_kb / semantic_group / boundary
    kb: str             # 所属知识库简称（SDC / Memory / 低功耗 / "Memory + 低功耗"）
    domain: str         # 技术域 A/B/C/D/E/G
    subdomain: str      # 子域 A1/B3/...
    difficulty: str     # easy / mid / hard
    prefix_family: str  # 前缀家族（仅 single_doc 的 error code 题填写）
    text: str           # 问题文本（语义近似题存 | 分隔的变体）
    variants: list[str]  # 语义近似题的 3 个变体
    expected_docs: list[str]  # 预期命中文档名列表
    expected_kb_map: dict[str, str]  # cross_kb: doc_name → kb_alias
    dataset_id: str     # 主检索目标 dataset_id


@dataclass
class ScoreResult:
    """单题评分结果。"""

    question: Question
    recall: float = 0.0
    precision: float = 0.0
    rrf_quality: float = 0.0
    semantic: float = 0.0
    total: float = 0.0
    hit_docs: list[str] = field(default_factory=list)
    top_results: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""
    # 附加诊断字段
    score_mode: str = "precision_recall"
    noise_hit_count: int = 0
    prefix_neighbor_hit_count: int = 0
    per_kb_hits: dict[str, list[str]] = field(default_factory=dict)  # cross_kb
    s_max: float = 0.0  # boundary
    jaccard_mean: float = 0.0  # semantic_group
    intersection_ratio: float = 0.0  # semantic_group

    @property
    def passed(self) -> bool:
        return self.total >= PASS_THRESHOLD and not self.error


# ---------------------------------------------------------------------------
# 问题解析
# ---------------------------------------------------------------------------


def _parse_expected_docs(raw: str) -> list[str]:
    """解析预期命中文档名，支持 + / / 分隔。"""
    raw = raw.strip()
    if not raw:
        return []
    parts = re.split(r"\s*\+\s*|\s*/\s*", raw)
    return [p.strip() for p in parts if p.strip()]


def _parse_cross_kb_expected(raw: str) -> tuple[list[str], dict[str, str]]:
    """解析 cross_kb 题的预期文档，提取 KB 标注。

    "Mick [clp] 使用说明(UPF) (Memory 库) + clp报告分析 (低功耗库)"
    → (["Mick [clp] 使用说明(UPF)", "clp报告分析"],
       {"Mick [clp] 使用说明(UPF)": "Memory", "clp报告分析": "低功耗"})
    """
    parts = re.split(r"\s*\+\s*", raw)
    docs: list[str] = []
    kb_map: dict[str, str] = {}
    for part in parts:
        part = part.strip()
        # 提取末尾的 (KB名) 标注
        m = re.search(r"\(([^)]*(?:库|领域))\)\s*$", part)
        if m:
            kb_label = m.group(1)
            doc_name = part[:m.start()].strip()
            # 标准化 KB 名
            for alias in _KB_ALIAS_TO_ID:
                if alias in kb_label:
                    kb_map[doc_name] = alias
                    break
            docs.append(doc_name)
        else:
            docs.append(part)
    return docs, kb_map


def parse_questions_v2(filepath: str | Path) -> list[Question]:
    """解析 eval_questions_kb.md 的所有评测问题。

    支持三种表格格式：
    - 标准（域 A/B/C/D/E/G）：| id | 类型 | 库 | 子域 | 难度 | 前缀家族 | 问题 | 预期命中 |
    - 语义近似组：| id | 类型 | 库 | 难度 | 前缀家族 | 变体1 | 变体2 | 变体3 | 预期命中 |
    - 边界组：| id | 类型 | 库 | 难度 | 前缀家族 | 问题(库外) | 预期 | 备注 |
    """
    filepath = Path(filepath)
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    questions: list[Question] = []
    current_domain: str = ""
    current_subdomain: str = ""
    in_table: bool = False
    table_format: str = ""  # "standard" | "semantic" | "boundary"

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 检测域标题（v2 只 A-G；v3 扩展到 A-Z)
        m = re.match(r"^##\s+域\s+([A-Z]):", line)
        if m:
            current_domain = m.group(1)
            current_subdomain = ""
            i += 1
            continue

        # 检测语义近似组 / 边界组标题
        if "语义近似" in line and line.startswith("##"):
            current_domain = "semantic"
            current_subdomain = ""
            i += 1
            continue
        if "边界" in line and "拒答" in line and line.startswith("##"):
            current_domain = "boundary"
            current_subdomain = ""
            i += 1
            continue

        # 检测表格分隔行
        if line.startswith("|") and "---" in line:
            # 上一行是表头，用于判断格式
            if i > 0:
                header = lines[i - 1].strip()
                if "变体" in header:
                    table_format = "semantic"
                elif "问题(库外)" in header or "备注" in header:
                    table_format = "boundary"
                else:
                    table_format = "standard"
            in_table = True
            i += 1
            continue

        # 跳过非表格行
        if not line.startswith("|"):
            in_table = False
            i += 1
            continue

        if not in_table:
            i += 1
            continue

        # 解析表格行：保留内部空 cell（如 | | 表示空列），只去掉首尾空 cell
        raw_cells = [c.strip() for c in line.split("|")]
        # 去掉 leading 空 cell（来自行首的 |）
        if raw_cells and raw_cells[0] == "":
            raw_cells = raw_cells[1:]
        # 去掉 trailing 空 cell（来自行尾的 |）
        if raw_cells and raw_cells[-1] == "":
            raw_cells = raw_cells[:-1]
        cells = raw_cells

        if len(cells) < 2:
            i += 1
            continue

        # 跳过表头行
        if cells[0] in ("id", "#") or cells[0].startswith("-"):
            i += 1
            continue

        idx = cells[0].strip("`").strip()

        if table_format == "standard":
            if len(cells) < 8:
                i += 1
                continue
            # | id | 类型 | 库 | 子域 | 难度 | 前缀家族 | 问题 | 预期命中 |
            qtype = cells[1]
            kb = cells[2]
            subdomain = cells[3]
            difficulty = cells[4]
            prefix_family = cells[5].strip("`").strip()
            text = cells[6]
            expected_raw = cells[7] if len(cells) > 7 else ""

            expected_docs = _parse_expected_docs(expected_raw)
            expected_kb_map: dict[str, str] = {}
            variants: list[str] = []

        elif table_format == "semantic":
            if len(cells) < 8:
                i += 1
                continue
            # | id | 类型 | 库 | 难度 | 前缀家族 | 变体1 | 变体2 | 变体3 | 预期命中 |
            qtype = cells[1]
            kb = cells[2]
            subdomain = ""
            difficulty = cells[3]
            prefix_family = cells[4].strip("`").strip()
            variants = [cells[5], cells[6], cells[7]]
            text = " | ".join(variants)
            expected_raw = cells[8] if len(cells) > 8 else ""
            expected_docs = _parse_expected_docs(expected_raw)
            expected_kb_map = {}

        elif table_format == "boundary":
            if len(cells) < 7:
                i += 1
                continue
            # | id | 类型 | 库 | 难度 | 前缀家族 | 问题(库外) | 预期 | 备注 |
            qtype = cells[1]
            kb = cells[2]
            subdomain = ""
            difficulty = cells[3]
            prefix_family = cells[4].strip("`").strip()
            text = cells[5]
            expected_docs = []  # 边界题不预期命中任何文档
            expected_kb_map = {}
            variants = []
        else:
            i += 1
            continue

        # 确定 dataset_id
        if " + " in kb:
            # cross_kb: 取第一个库作为主 dataset_id
            primary_kb = kb.split(" + ")[0].strip()
            dataset_id = _KB_ALIAS_TO_ID.get(primary_kb, "")
        else:
            dataset_id = _KB_ALIAS_TO_ID.get(kb, "")

        # 解析 cross_kb 的预期文档 KB 映射
        if qtype == "cross_kb" and expected_raw:
            expected_docs, expected_kb_map = _parse_cross_kb_expected(expected_raw)

        questions.append(Question(
            idx=idx,
            qtype=qtype,
            kb=kb,
            domain=current_domain,
            subdomain=subdomain,
            difficulty=difficulty,
            prefix_family=prefix_family,
            text=text,
            variants=variants,
            expected_docs=expected_docs,
            expected_kb_map=expected_kb_map,
            dataset_id=dataset_id,
        ))

        i += 1

    return questions


# ---------------------------------------------------------------------------
# 噪声黑名单（从 inventory_v2 加载）
# ---------------------------------------------------------------------------


def load_noise_set(inventory_path: str | Path | None = None) -> set[str]:
    """从 .kb_inventory_v2.json 加载 noise=true 的文档名集合。"""
    if inventory_path is None:
        inventory_path = Path(__file__).parent / ".kb_inventory_v2.json"
    inventory_path = Path(inventory_path)
    if not inventory_path.exists():
        return set()
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    noise: set[str] = set()
    for ds_name, ds_info in data.get("datasets", {}).items():
        for doc in ds_info.get("docs", []):
            if doc.get("noise", False):
                noise.add(doc["name"])
    return noise


# ---------------------------------------------------------------------------
# 评分逻辑
# ---------------------------------------------------------------------------


def _compute_recall_v2(expected: list[str], hit_docs: list[str]) -> float:
    """召回率得分 (0-30)。线性比例：30 × hit / len(expected)。"""
    if not expected:
        return 30.0
    return 30.0 * len(hit_docs) / len(expected)


def _compute_precision_v2(
    results: list[dict[str, Any]],
    expected: list[str],
    prefix_family: str = "",
) -> tuple[float, int]:
    """精确率得分 (0-30) + 前缀邻居惩罚。

    single_doc: top-1=30, top-3=20, top-5=10, 不在=0
    multi_doc: 30 × (top-5 中预期数 / 5)
    额外：前缀邻居每篇扣 PREFIX_NEIGHBOR_PENALTY 分。
    返回 (final_precision, prefix_neighbor_count)。
    """
    if not results or not expected:
        return 0.0, 0

    top_5 = results[:5]
    expected_set = set(expected)

    if len(expected) == 1:
        # single_doc: 按命中位置给分
        exp_doc = expected[0]
        base = 0.0
        for rank, r in enumerate(top_5):
            if _doc_matches(exp_doc, r.get("document_name", "")):
                if rank == 0:
                    base = 30.0
                elif rank < 3:
                    base = 20.0
                else:
                    base = 10.0
                break
    else:
        # multi_doc
        hits = sum(
            1 for r in top_5
            if any(_doc_matches(e, r.get("document_name", "")) for e in expected)
        )
        base = 30.0 * hits / len(top_5)

    # 前缀邻居惩罚
    prefix_neighbors = 0
    if prefix_family:
        for r in top_5:
            doc_name = r.get("document_name", "")
            if doc_name.startswith(prefix_family) and not any(
                _doc_matches(e, doc_name) for e in expected
            ):
                prefix_neighbors += 1

    final = max(0.0, base - PREFIX_NEIGHBOR_PENALTY * prefix_neighbors)
    return final, prefix_neighbors


def _compute_semantic_score(results: list[dict[str, Any]]) -> float:
    """语义匹配得分 (0-20)。基于 top-3 平均 score。"""
    if not results:
        return 0.0
    scores = [r.get("score", 0) for r in results[:3]]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return min(20.0, avg * 20.0)


# --- 各类型评分入口 ---


def _score_single_or_multi(
    q: Question,
    results: list[dict[str, Any]],
) -> ScoreResult:
    """single_doc / multi_doc 评分。"""
    sr = ScoreResult(
        question=q,
        top_results=results[:5],
        score_mode="precision_recall",
    )

    if not results:
        sr.error = "无检索结果"
        return sr

    sr.hit_docs = _find_hit_docs(q.expected_docs, results)
    sr.recall = _compute_recall_v2(q.expected_docs, sr.hit_docs)

    prec, pn_count = _compute_precision_v2(results, q.expected_docs, q.prefix_family)
    sr.precision = prec
    sr.prefix_neighbor_hit_count = pn_count

    sr.rrf_quality = _compute_rrf_quality(results)
    sr.semantic = _compute_semantic_score(results)
    sr.total = sr.recall + sr.precision + sr.rrf_quality + sr.semantic
    return sr


def _score_semantic_group(
    q: Question,
    top_k: int,
    timeout: float,
) -> ScoreResult:
    """语义近似组评分：3 变体各检索，算 Jaccard + 交集占比。"""
    sr = ScoreResult(
        question=q,
        score_mode="semantic_group",
    )

    if len(q.variants) != 3:
        sr.error = f"语义近似题需 3 个变体，实际 {len(q.variants)}"
        return sr

    doc_sets: list[set[str]] = []
    all_results: list[list[dict[str, Any]]] = []
    all_rrf_scores: list[float] = []
    all_semantic_scores: list[float] = []

    for variant in q.variants:
        try:
            results = retrieve(variant, top_k=top_k, dataset_id=q.dataset_id)
            doc_set = {r.get("document_name", "") for r in results[:top_k]}
            doc_sets.append(doc_set)
            all_results.append(results)
            all_rrf_scores.append(_compute_rrf_quality(results))
            all_semantic_scores.append(_compute_semantic_score(results))
        except Exception:
            doc_sets.append(set())
            all_results.append([])
            all_rrf_scores.append(0.0)
            all_semantic_scores.append(0.0)

    # Merge top_results for report
    merged: list[dict[str, Any]] = []
    for res in all_results:
        merged.extend(res[:top_k])
    sr.top_results = merged[:top_k * 3]

    # Jaccard
    s_a, s_b, s_c = doc_sets
    j_ab = len(s_a & s_b) / len(s_a | s_b) if (s_a | s_b) else 0.0
    j_ac = len(s_a & s_c) / len(s_a | s_c) if (s_a | s_c) else 0.0
    j_bc = len(s_b & s_c) / len(s_b | s_c) if (s_b | s_c) else 0.0
    sr.jaccard_mean = (j_ab + j_ac + j_bc) / 3.0

    # 三者交集占比
    triple = s_a & s_b & s_c
    sr.intersection_ratio = len(triple) / top_k if top_k > 0 else 0.0

    sr.recall = 30.0 * sr.jaccard_mean
    sr.precision = 30.0 * sr.intersection_ratio
    sr.rrf_quality = sum(all_rrf_scores) / 3.0 if all_rrf_scores else 0.0
    sr.semantic = sum(all_semantic_scores) / 3.0 if all_semantic_scores else 0.0
    sr.total = sr.recall + sr.precision + sr.rrf_quality + sr.semantic
    return sr


def _score_boundary(
    q: Question,
    results: list[dict[str, Any]],
    noise_set: set[str],
) -> ScoreResult:
    """边界题评分：τ=0.35 诚实度 + noise 惩罚。"""
    sr = ScoreResult(
        question=q,
        top_results=results[:5],
        score_mode="boundary_honesty",
    )

    if not results:
        # 空结果 = 完美诚实
        sr.s_max = 0.0
        sr.recall = 30.0
        sr.precision = 30.0
        sr.rrf_quality = 20.0
        sr.semantic = 20.0
        sr.total = 100.0
        return sr

    scores = [r.get("score", 0) for r in results]
    sr.s_max = max(scores) if scores else 0.0

    # Recall: 诚实度
    if sr.s_max < TAU:
        sr.recall = 30.0
    elif sr.s_max >= 1.0:
        sr.recall = 0.0
    else:
        sr.recall = 30.0 * (1.0 - sr.s_max) / (1.0 - TAU)

    # Precision: 低分占比
    n_below = sum(1 for s in scores if s < TAU)
    sr.precision = 30.0 * n_below / len(scores) if scores else 0.0

    # RRF: 低分占比 × 20
    sr.rrf_quality = 20.0 * n_below / len(scores) if scores else 20.0

    # Semantic: 1 - s_max
    sr.semantic = 20.0 * (1.0 - sr.s_max)

    # Noise 诱捕
    noise_hits = 0
    for r in results:
        if r.get("document_name", "") in noise_set:
            noise_hits += 1
    sr.noise_hit_count = noise_hits

    sr.total = max(0.0,
        sr.recall + sr.precision + sr.rrf_quality + sr.semantic
        - NOISE_HIT_PENALTY * noise_hits
    )
    return sr


def _score_cross_kb(
    q: Question,
    top_k: int,
    timeout: float,
) -> ScoreResult:
    """Cross-KB 题评分：逐库检索后 union 评分。"""
    sr = ScoreResult(
        question=q,
        score_mode="cross_kb",
    )

    all_results: list[dict[str, Any]] = []
    per_kb_hits: dict[str, list[str]] = {}

    # 确定需要检索哪些库
    kb_ids: list[str] = []
    if " + " in q.kb:
        for alias in q.kb.split(" + "):
            alias = alias.strip()
            if alias in _KB_ALIAS_TO_ID:
                kb_ids.append(_KB_ALIAS_TO_ID[alias])
    else:
        kb_ids = MIFY_DATASET_IDS[:]

    for ds_id in kb_ids:
        kb_alias = _ID_TO_KB_ALIAS.get(ds_id, ds_id[:8])
        try:
            results = _retrieve_one_dataset(q.text, ds_id, top_k)
            all_results.extend(results)
            # 记录该库命中的预期文档
            hits = _find_hit_docs(q.expected_docs, results)
            per_kb_hits[kb_alias] = hits
        except Exception:
            per_kb_hits[kb_alias] = []

    sr.per_kb_hits = per_kb_hits
    sr.top_results = all_results[:top_k * len(kb_ids)]

    if not all_results:
        sr.error = "所有库检索均无结果"
        return sr

    # 召回：union 后算命中
    all_hit = _find_hit_docs(q.expected_docs, all_results)
    sr.hit_docs = all_hit
    sr.recall = _compute_recall_v2(q.expected_docs, all_hit)

    # 精确率：各库分别算后取均值
    precisions: list[float] = []
    for ds_id in kb_ids:
        kb_alias = _ID_TO_KB_ALIAS.get(ds_id, ds_id[:8])
        # 该库对应的预期文档
        kb_expected = [d for d, ka in q.expected_kb_map.items() if ka == kb_alias]
        if not kb_expected:
            kb_expected = [d for d in q.expected_docs if d in per_kb_hits.get(kb_alias, [])]
        if not kb_expected:
            continue
        # 从 all_results 里筛选该库的结果
        # （简化：用 per_kb_hits 的命中数 / 预期数）
        kb_prec = len(per_kb_hits.get(kb_alias, [])) / len(kb_expected) * 30.0 if kb_expected else 0.0
        precisions.append(kb_prec)

    sr.precision = sum(precisions) / len(precisions) if precisions else 0.0

    sr.rrf_quality = _compute_rrf_quality(all_results)
    sr.semantic = _compute_semantic_score(all_results)
    sr.total = sr.recall + sr.precision + sr.rrf_quality + sr.semantic
    return sr


# --- 分发器 ---


def score_question(
    q: Question,
    results: list[dict[str, Any]] | None = None,
    top_k: int = 5,
    timeout: float = 60.0,
    noise_set: set[str] | None = None,
) -> ScoreResult:
    """按 qtype 分发到对应评分函数。

    Args:
        q: 问题对象
        results: 预检索结果（非语义近似/非 cross_kb 时提供）
        top_k: 检索 top-K
        timeout: 超时
        noise_set: 噪声文档名集合
    """
    if noise_set is None:
        noise_set = set()

    if q.qtype == "semantic_group":
        return _score_semantic_group(q, top_k, timeout)
    elif q.qtype == "cross_kb":
        return _score_cross_kb(q, top_k, timeout)
    elif q.qtype == "boundary":
        if results is None:
            try:
                results = retrieve(q.text, top_k=top_k, dataset_id=q.dataset_id)
            except Exception as e:
                sr = ScoreResult(question=q, error=str(e), score_mode="boundary_honesty")
                return sr
        return _score_boundary(q, results, noise_set)
    else:
        # single_doc / multi_doc
        if results is None:
            try:
                results = retrieve(q.text, top_k=top_k, dataset_id=q.dataset_id)
            except Exception as e:
                sr = ScoreResult(question=q, error=str(e))
                return sr
        return _score_single_or_multi(q, results)


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------


def generate_report(
    results: list[ScoreResult],
    output_path: str | Path,
    elapsed: float = 0.0,
) -> None:
    """生成 eval_kb_report.md。"""
    output_path = Path(output_path)
    total = len(results)
    if total == 0:
        output_path.write_text("# 评测报告\n\n没有评测问题。\n", encoding="utf-8")
        return

    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed and not r.error]
    errors = [r for r in results if r.error]
    pass_rate = len(passed) / total * 100

    # 按域分组
    by_domain: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        by_domain[r.question.domain].append(r)

    # 按子域分组（仅 B 域）
    by_subdomain: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        if r.question.subdomain:
            by_subdomain[r.question.subdomain].append(r)

    lines: list[str] = []
    lines.append("# SynHub KB 检索评估报告 v2")
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
    lines.append(f"| 通过数 | {len(passed)} / {total} |")
    lines.append(f"| **通过率** | **{pass_rate:.1f}%** |")
    lines.append(f"| 错误数 | {len(errors)} |")
    lines.append("")

    # 各维度平均分
    avg_recall = sum(r.recall for r in results) / total
    avg_precision = sum(r.precision for r in results) / total
    avg_rrf = sum(r.rrf_quality for r in results) / total
    avg_semantic = sum(r.semantic for r in results) / total
    avg_total = sum(r.total for r in results) / total
    lines.append("### 各维度平均分")
    lines.append("")
    lines.append("| 维度 | 平均分 | 满分 |")
    lines.append("|------|--------|------|")
    lines.append(f"| 召回率 | {avg_recall:.1f} | 30 |")
    lines.append(f"| 精确率 | {avg_precision:.1f} | 30 |")
    lines.append(f"| RRF 质量 | {avg_rrf:.1f} | 20 |")
    lines.append(f"| 语义匹配 | {avg_semantic:.1f} | 20 |")
    lines.append(f"| **总分** | **{avg_total:.1f}** | **100** |")
    lines.append("")

    # ── 2. 按域汇总（主视图）──
    lines.append("## 2. 按技术域汇总")
    lines.append("")
    lines.append("| 域 | 名称 | 题数 | 平均召回 | 平均精确 | 平均 RRF | 平均语义 | 域总分 |")
    lines.append("|------|------|------|----------|----------|----------|----------|--------|")
    domain_order = [
        ("A", "时钟与时序约束"),
        ("B", "多电源域 CLP 规则"),
        ("C", "LP cell 物理实现"),
        ("D", "Memory 综合"),
        ("E", "RTL 工具链"),
        ("G", "流程规范"),
        ("semantic", "语义近似"),
        ("boundary", "边界/拒答"),
    ]
    for d_code, d_name in domain_order:
        d_results = by_domain.get(d_code, [])
        if not d_results:
            continue
        n = len(d_results)
        d_recall = sum(r.recall for r in d_results) / n
        d_prec = sum(r.precision for r in d_results) / n
        d_rrf = sum(r.rrf_quality for r in d_results) / n
        d_sem = sum(r.semantic for r in d_results) / n
        d_total = sum(r.total for r in d_results) / n
        lines.append(
            f"| {d_code} | {d_name} | {n} | {d_recall:.1f} | {d_prec:.1f} "
            f"| {d_rrf:.1f} | {d_sem:.1f} | {d_total:.1f} |"
        )
    lines.append("")

    # ── 3. B 域子域明细 ──
    if by_subdomain:
        lines.append("### B 域子域明细")
        lines.append("")
        lines.append("| 子域 | 题数 | 平均召回 | 平均精确 | 平均总分 |")
        lines.append("|------|------|----------|----------|----------|")
        for sd in ["B1", "B2", "B3", "B4", "B5"]:
            sd_results = by_subdomain.get(sd, [])
            if not sd_results:
                continue
            n = len(sd_results)
            sd_recall = sum(r.recall for r in sd_results) / n
            sd_prec = sum(r.precision for r in sd_results) / n
            sd_total = sum(r.total for r in sd_results) / n
            lines.append(f"| {sd} | {n} | {sd_recall:.1f} | {sd_prec:.1f} | {sd_total:.1f} |")
        lines.append("")

    # ── 4. 按知识库汇总（辅助视图）──
    lines.append("## 3. 按知识库汇总（辅助视图）")
    lines.append("")
    by_kb: dict[str, list[ScoreResult]] = defaultdict(list)
    for r in results:
        kb = r.question.kb
        if " + " in kb:
            kb = kb.split(" + ")[0].strip()
        by_kb[kb].append(r)
    lines.append("| 知识库 | 题数 | 平均总分 |")
    lines.append("|--------|------|----------|")
    for kb_name in ["SDC", "Memory", "低功耗"]:
        kb_results = by_kb.get(kb_name, [])
        if not kb_results:
            continue
        n = len(kb_results)
        kb_total = sum(r.total for r in kb_results) / n
        lines.append(f"| {kb_name} | {n} | {kb_total:.1f} |")
    lines.append("")

    # ── 5. 每题明细 ──
    lines.append("## 4. 每题明细")
    lines.append("")
    lines.append("| id | 域 | 类型 | 问题 | 召回 | 精确 | RRF | 语义 | 总分 | 状态 | 诊断 |")
    lines.append("|------|------|------|------|------|------|-----|------|------|------|------|")
    for r in results:
        text = r.question.text[:40] + ("..." if len(r.question.text) > 40 else "")
        status = "PASS" if r.passed else ("ERR" if r.error else "FAIL")
        # 诊断摘要
        diag_parts: list[str] = []
        if r.error:
            diag_parts.append(f"ERR:{r.error[:20]}")
        if r.prefix_neighbor_hit_count > 0:
            diag_parts.append(f"相邻:{r.prefix_neighbor_hit_count}")
        if r.noise_hit_count > 0:
            diag_parts.append(f"噪声:{r.noise_hit_count}")
        if r.score_mode == "boundary_honesty":
            diag_parts.append(f"s_max={r.s_max:.2f}")
        if r.score_mode == "semantic_group":
            diag_parts.append(f"J={r.jaccard_mean:.2f}")
        diag = ", ".join(diag_parts) if diag_parts else "—"
        lines.append(
            f"| {r.question.idx} | {r.question.domain} | {r.question.qtype} | {text} "
            f"| {r.recall:.1f} | {r.precision:.1f} | {r.rrf_quality:.1f} | {r.semantic:.1f} "
            f"| {r.total:.1f} | {status} | {diag} |"
        )
    lines.append("")

    # ── 6. 边界题 noise 命中 ──
    boundary_results = [r for r in results if r.score_mode == "boundary_honesty"]
    if boundary_results:
        lines.append("## 5. 边界题诊断")
        lines.append("")
        lines.append("| id | 问题 | s_max | noise 命中 | 总分 |")
        lines.append("|------|------|-------|------------|------|")
        for r in boundary_results:
            text = r.question.text[:50] + ("..." if len(r.question.text) > 50 else "")
            noise_info = str(r.noise_hit_count) if r.noise_hit_count > 0 else "无"
            lines.append(f"| {r.question.idx} | {text} | {r.s_max:.3f} | {noise_info} | {r.total:.1f} |")
        lines.append("")

    # ── 7. Cross-KB 命中详情 ──
    cross_results = [r for r in results if r.score_mode == "cross_kb"]
    if cross_results:
        lines.append("## 6. Cross-KB 命中详情")
        lines.append("")
        for r in cross_results:
            lines.append(f"### {r.question.idx}: {r.question.text[:60]}...")
            lines.append("")
            for kb_name, hits in r.per_kb_hits.items():
                hit_str = ", ".join(hits) if hits else "无"
                lines.append(f"- **{kb_name}**: {hit_str}")
            lines.append(f"- 召回: {r.recall:.1f}/30, 精确: {r.precision:.1f}/30")
            lines.append("")

    # ── 8. 失败题详情 ──
    if failed or errors:
        lines.append("## 7. 失败题详情")
        lines.append("")
        for r in failed + errors:
            lines.append(f"### {r.question.idx}: {r.question.text}")
            lines.append("")
            lines.append(f"- 域: {r.question.domain} / 子域: {r.question.subdomain}")
            lines.append(f"- 类型: {r.question.qtype} / 难度: {r.question.difficulty}")
            lines.append(f"- 总分: {r.total:.1f} / 100")
            if r.error:
                lines.append(f"- 错误: {r.error}")
            lines.append(f"- 召回: {r.recall:.1f}/30, 精确: {r.precision:.1f}/30, "
                         f"RRF: {r.rrf_quality:.1f}/20, 语义: {r.semantic:.1f}/20")
            if r.question.expected_docs:
                lines.append(f"- 预期文档: {', '.join(r.question.expected_docs)}")
            lines.append(f"- 命中文档: {', '.join(r.hit_docs) if r.hit_docs else '无'}")
            if r.prefix_neighbor_hit_count > 0:
                lines.append(f"- 前缀邻居命中: {r.prefix_neighbor_hit_count} 篇(每篇扣 {PREFIX_NEIGHBOR_PENALTY} 分)")
            if r.noise_hit_count > 0:
                lines.append(f"- 噪声文档命中: {r.noise_hit_count} 篇(每篇扣 {NOISE_HIT_PENALTY} 分)")
            if r.score_mode == "boundary_honesty":
                lines.append(f"- s_max: {r.s_max:.3f} (τ={TAU})")
            if r.score_mode == "semantic_group":
                lines.append(f"- Jaccard 均值: {r.jaccard_mean:.3f}")
                lines.append(f"- 三者交集占比: {r.intersection_ratio:.3f}")
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    domain_filter: str | None = None,
    section_filter: str | None = None,
    id_filter: list[str] | None = None,
    inventory_path: str | Path | None = None,
) -> list[ScoreResult]:
    """执行评测主流程。"""
    # 定位问题文件
    if questions_file is None:
        questions_file = Path(__file__).parent / "eval_questions_kb.md"
    questions_file = Path(questions_file)
    if not questions_file.exists():
        print(f"错误: 问题文件不存在: {questions_file}")
        return []

    if output_file is None:
        output_file = Path(__file__).parent / "eval_kb_report.md"
    output_file = Path(output_file)

    # 检查 API 配置
    if not MIFY_API_KEY or not MIFY_DATASET_IDS:
        print("错误: 未配置 MIFY_API_KEY 或 MIFY_DATASET_IDS，请检查 .env 文件")
        return []

    # 解析问题
    print(f"解析问题文件: {questions_file}")
    questions = parse_questions_v2(questions_file)
    print(f"共解析到 {len(questions)} 道评测问题")

    # 过滤
    if domain_filter:
        questions = [q for q in questions if q.domain == domain_filter]
        print(f"过滤后剩余 {len(questions)} 道题（域: {domain_filter}）")
    if section_filter:
        questions = [q for q in questions if q.subdomain == section_filter]
        print(f"过滤后剩余 {len(questions)} 道题（子域: {section_filter}）")
    if id_filter:
        id_set = {i.strip().upper() for i in id_filter}
        questions = [q for q in questions if q.idx.upper() in id_set]
        print(f"过滤后剩余 {len(questions)} 道题（题号: {sorted(id_set)}）")
    if max_questions > 0:
        questions = questions[:max_questions]
        print(f"限制为前 {max_questions} 道题")

    # 加载噪声黑名单
    noise_set = load_noise_set(inventory_path)
    print(f"噪声文档黑名单: {len(noise_set)} 篇")

    # 逐题评测
    score_results: list[ScoreResult] = []
    total_start = time.time()

    for i, q in enumerate(questions):
        progress = f"[{i + 1}/{len(questions)}]"
        print(f"\n{progress} 评测: {q.idx} [{q.qtype}] {q.text[:60]}...")

        try:
            start = time.time()

            if q.qtype == "semantic_group":
                sr = score_question(q, top_k=top_k, timeout=timeout, noise_set=noise_set)
            elif q.qtype == "cross_kb":
                sr = score_question(q, top_k=top_k, timeout=timeout, noise_set=noise_set)
            else:
                results = retrieve(q.text, top_k=top_k, dataset_id=q.dataset_id)
                sr = score_question(q, results=results, top_k=top_k, noise_set=noise_set)

            elapsed_q = time.time() - start
            if elapsed_q > timeout:
                print(f"  警告: 检索耗时 {elapsed_q:.1f}s (超过 {timeout}s 阈值)")

            print(
                f"  检索到 {len(sr.top_results)} 条结果 ({elapsed_q:.1f}s) | "
                f"召回={sr.recall:.1f} 精确={sr.precision:.1f} "
                f"RRF={sr.rrf_quality:.1f} 语义={sr.semantic:.1f} "
                f"总分={sr.total:.1f} {'PASS' if sr.passed else 'FAIL'}"
            )
            if sr.hit_docs:
                print(f"  命中文档: {', '.join(sr.hit_docs)}")
            if sr.error:
                print(f"  错误: {sr.error}")

        except Exception as e:
            sr = ScoreResult(question=q, error=str(e))
            print(f"  异常: {e}")

        score_results.append(sr)

        if i < len(questions) - 1:
            time.sleep(0.5)

    total_elapsed = time.time() - total_start

    # 生成报告
    print(f"\n评测完成，总耗时: {total_elapsed:.1f}s")
    passed_count = sum(1 for r in score_results if r.passed)
    total_count = len(score_results)
    print(f"通过: {passed_count}/{total_count} ({passed_count / total_count * 100:.1f}%)")
    generate_report(score_results, output_file, elapsed=total_elapsed)

    return score_results


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SynHub KB 检索评估器 v2 — 按技术域加权 36 题",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/eval_kb.py                          # 跑全部 36 题
  python tests/eval_kb.py --top-k 10               # 返回 10 条结果
  python tests/eval_kb.py --max-questions 10       # 只跑前 10 题
  python tests/eval_kb.py --domain A               # 只跑域 A 的题
  python tests/eval_kb.py --section B3             # 只跑子域 B3 的题
  python tests/eval_kb.py --output my_report.md    # 自定义输出路径
        """,
    )
    parser.add_argument(
        "--questions", "-q", type=str, default=None,
        help="问题文件路径（默认 tests/eval_questions_kb.md）",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="输出报告路径（默认 tests/eval_kb_report.md）",
    )
    parser.add_argument(
        "--top-k", "-k", type=int, default=5,
        help="每题检索返回的文档数（默认 5）",
    )
    parser.add_argument(
        "--timeout", "-t", type=float, default=60.0,
        help="每题检索超时时间，单位秒（默认 60）",
    )
    parser.add_argument(
        "--max-questions", "-m", type=int, default=0,
        help="最多评测的题目数（默认 0 = 不限制）",
    )
    parser.add_argument(
        "--domain", "-d", type=str, default=None,
        help="只评测指定域（A/B/C/D/E/G/semantic/boundary）",
    )
    parser.add_argument(
        "--section", "-s", type=str, default=None,
        help="只评测指定子域（B1/B2/B3/B4/B5 等）",
    )
    parser.add_argument(
        "--ids", type=str, default=None,
        help="只评测指定题号列表,逗号分隔(如 A-06,B-06,S-01)",
    )

    args = parser.parse_args()

    id_filter = None
    if args.ids:
        id_filter = [x for x in args.ids.split(",") if x.strip()]

    results = run_evaluation(
        questions_file=args.questions,
        output_file=args.output,
        top_k=args.top_k,
        timeout=args.timeout,
        max_questions=args.max_questions,
        domain_filter=args.domain,
        section_filter=args.section,
        id_filter=id_filter,
    )

    if results:
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"\n最终结果: {passed}/{total} 通过 ({passed / total * 100:.1f}%)")


if __name__ == "__main__":
    main()