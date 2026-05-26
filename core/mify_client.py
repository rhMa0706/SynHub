import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from config.settings import (
    MIFY_API_KEY,
    MIFY_BASE_URL,
    MIFY_DATASET_IDS,
    MIFY_NUM_VARIANTS,
    MIFY_RETRIEVE_WORKERS,
    MIFY_RRF_K,
    MIFY_TOP_K,
)

# ---------------------------------------------------------------------------
# Query expansion helpers
# ---------------------------------------------------------------------------

# 短缩写 → 展开后的查询词
_ABBREV_MAP: dict[str, str] = {
    "iso": "isolation cell",
    "upf": "UPF gen flow power format",
    "drc": "design rule check",
    "lvs": "layout versus schematic",
    "sdc": "synopsys design constraints",
    "lec": "logic equivalence check",
    "dft": "design for testability",
    "atpg": "automatic test pattern generation",
    "clp": "CLP check low power",
    "ls": "level shifter",
    "lsh": "level shifter",
    "pd": "power domain",
    "psw": "power switch",
    "aon": "always on",
    "clk": "clock",
    "cts": "clock tree synthesis",
    "rtl": "register transfer level",
    "qor": "quality of results",
}

# 中文芯片术语 → 英文同义词（embedding 模型对英文匹配更好）
_CN_BRIDGE: dict[str, str] = {
    "时序": "timing",
    "面积": "area",
    "功耗": "power",
    "时钟": "clock",
    "约束": "constraints",
    "综合": "synthesis",
    "隔离": "isolation",
    "电平转换": "level shifter",
    "电源域": "power domain",
    "电源开关": "power switch",
}

# 缓存：从 Mify 拉取的文档标题列表（按 dataset_id 分别缓存）
_doc_titles_cache: dict[str, list[str]] = {}


def _fetch_doc_titles(dataset_id: str) -> list[str]:
    """获取指定数据集中所有文档标题（带缓存）。"""
    if dataset_id in _doc_titles_cache:
        return _doc_titles_cache[dataset_id]

    url = f"{MIFY_BASE_URL}/{dataset_id}/documents"
    headers = {
        "Authorization": f"Bearer {MIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        resp = httpx.get(url, headers=headers, params={"page": 1, "limit": 200}, timeout=30)
        resp.raise_for_status()
        titles = [d["name"] for d in resp.json().get("data", [])]
    except Exception:
        titles = []
    _doc_titles_cache[dataset_id] = titles
    return titles


def _build_queries(query: str, dataset_id: str | None = None) -> list[str]:
    """根据查询词生成多个搜索变体，按优先级排列。

    策略:
    1. 原始查询
    2. 短缩写展开（如 ISO → isolation cell）
    3. 用文档标题做桥接（如 ISO → 包含 ISO 的文档标题）
    4. 部分缩写展开（查询中嵌入的缩写子串替换）
    5. 中英文桥接（中文术语 → 英文同义词）
    """
    stripped = query.strip()
    queries = [stripped]
    lower = stripped.lower()

    # 策略2: 短缩写展开
    if lower in _ABBREV_MAP and len(stripped) <= 5:
        queries.append(_ABBREV_MAP[lower])

    # 策略3: 纯大写缩写（2-5字母），用文档标题做桥接
    if re.fullmatch(r"[A-Z]{2,5}", stripped):
        titles = _fetch_doc_titles(dataset_id) if dataset_id else []
        matching = [t for t in titles if stripped in t]
        for t in matching[:3]:
            if t not in queries:
                queries.append(t)

    # 策略4: 部分缩写展开 —— 对查询中嵌入的缩写做子串替换
    expanded = stripped
    for abbr, full in _ABBREV_MAP.items():
        pattern = r"\b" + re.escape(abbr) + r"\b"
        if re.search(pattern, expanded, re.IGNORECASE):
            expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
    if expanded != stripped and expanded not in queries:
        queries.append(expanded)

    # 策略5: 中英文桥接 —— 含中文时生成英文变体
    if re.search(r"[一-鿿]", stripped):
        en_parts = []
        for cn, en in _CN_BRIDGE.items():
            if cn in stripped:
                en_parts.append(en)
        if en_parts:
            en_query = " ".join(en_parts)
            if en_query not in queries:
                queries.append(en_query)

    # 策略6: 多关键词拆分 —— 空格分隔的多个词，各自作为独立查询变体
    # 解决 "mem2reg MCP2 MCP3" 这类复合查询打分过低的问题
    words = stripped.split()
    if len(words) > 1:
        for w in words:
            if w not in queries:
                queries.append(w)

    return queries[:MIFY_NUM_VARIANTS]


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------


def _rrf_fuse(
    variant_results: list[list[dict[str, Any]]],
    k: int,
    top_k: int,
) -> list[dict[str, Any]]:
    """用 Reciprocal Rank Fusion 合并多个查询变体的检索结果。

    score(d) = Σ 1/(k + rank_i(d))，rank_i 为 0-based 排名。
    """
    doc_scores: dict[str, float] = {}
    doc_data: dict[str, dict[str, Any]] = {}

    for results in variant_results:
        for rank, r in enumerate(results):
            doc_id = r.get("id", r.get("content", ""))
            if doc_id not in doc_scores:
                doc_scores[doc_id] = 0.0
                doc_data[doc_id] = r
            doc_scores[doc_id] += 1.0 / (k + rank)

    ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {**doc_data[doc_id], "rrf_score": score}
        for doc_id, score in ranked[:top_k]
    ]


# ---------------------------------------------------------------------------
# Mify API retrieval
# ---------------------------------------------------------------------------


def _fetch_one_variant(
    url: str,
    headers: dict[str, str],
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """对单个查询变体执行检索（供线程池调用）。"""
    payload = {
        "query": query,
        "top_k": top_k,
        "retrieval_model": {
            "search_method": "hybrid_search",
            "reranking_enable": True,
            "reranking_model": {
                "reranking_provider_name": "langgenius/tongyi/tongyi",
                "reranking_model_name": "gte-rerank-v2_mi_sys",
            },
            "score_threshold_enabled": False,
            "weights": {
                "weight_type": "customized",
                "keyword_setting": {"keyword_weights": {}},
                "vector_setting": {
                    "embedding_provider_name": "langgenius/azure_openai/azure_openai",
                    "embedding_model_name": "text-embedding-3-small_mi_sys",
                },
            },
        },
    }
    resp = httpx.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    results = []
    for record in resp.json().get("records", []):
        seg = record.get("segment", {})
        doc = seg.get("document", {})
        results.append({
            "id": seg.get("id", ""),
            "content": seg.get("content", ""),
            "score": record.get("score", 0),
            "document_name": doc.get("name", ""),
            "doc_url": doc.get("doc_url", ""),
        })
    return results


def _retrieve_one_dataset(
    query: str,
    dataset_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    """从单个知识库检索（RAG-Fusion）。"""
    url = f"{MIFY_BASE_URL}/{dataset_id}/retrieve"
    headers = {
        "Authorization": f"Bearer {MIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    queries = _build_queries(query, dataset_id)

    variant_results: list[list[dict[str, Any]]] = []
    with ThreadPoolExecutor(max_workers=MIFY_RETRIEVE_WORKERS) as pool:
        futures = [
            pool.submit(_fetch_one_variant, url, headers, q, top_k)
            for q in queries
        ]
        for future in futures:
            try:
                variant_results.append(future.result())
            except Exception:
                variant_results.append([])

    return _rrf_fuse(variant_results, k=MIFY_RRF_K, top_k=top_k)


def retrieve(
    query: str,
    top_k: int | None = None,
    dataset_id: str | None = None,
) -> list[dict[str, Any]]:
    """从 Mify 知识库检索相关内容。

    支持单个或多个知识库：
    - 指定 dataset_id: 只检索该知识库
    - 不指定: 并行检索所有知识库，RRF 融合排序

    返回列表，每项包含:
      - content: 文档片段内容
      - score: 原始相似度分数
      - rrf_score: RRF 融合分数
      - document_name: 文档名称
      - doc_url: 飞书文档链接
    """
    if top_k is None:
        top_k = MIFY_TOP_K

    # 单知识库检索
    if dataset_id:
        fused = _retrieve_one_dataset(query, dataset_id, top_k)
    else:
        # 多知识库：并行检索所有，合并结果
        all_results: list[list[dict[str, Any]]] = []
        with ThreadPoolExecutor(max_workers=len(MIFY_DATASET_IDS)) as pool:
            futures = [
                pool.submit(_retrieve_one_dataset, query, ds_id, top_k)
                for ds_id in MIFY_DATASET_IDS
            ]
            for future in futures:
                try:
                    all_results.append(future.result())
                except Exception:
                    all_results.append([])
        # 跨知识库 RRF 融合
        fused = _rrf_fuse(all_results, k=MIFY_RRF_K, top_k=top_k)

    # 移除内部 id 字段，保持对外接口干净
    for r in fused:
        r.pop("id", None)

    return fused


def search(query: str, top_k: int | None = None, dataset_id: str | None = None) -> str:
    """检索并格式化为可读文本，适合直接注入 LLM prompt。"""
    top_k = top_k or MIFY_TOP_K
    results = retrieve(query, top_k=top_k, dataset_id=dataset_id)

    if not results:
        return "未找到相关内容。"

    parts = []
    for i, r in enumerate(results, 1):
        parts.append(
            f"[{i}] (rrf_score={r['rrf_score']:.4f}, score={r['score']:.3f}) "
            f"文档: {r['document_name']}\n"
            f"内容: {r['content']}\n"
            f"来源: {r['doc_url']}"
        )
    return "\n\n".join(parts)


if __name__ == "__main__":
    q = "1801_REF_OBJ_NOT_FOUND"
    print(f"Query: {q}\n")
    print(search(q))
