import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx

from config.settings import (
    DOMAIN_MAP,
    MIFY_API_KEY,
    MIFY_BASE_URL,
    MIFY_DATASET_IDS,
    MIFY_NUM_VARIANTS,
    MIFY_RETRIEVE_WORKERS,
    MIFY_RRF_K,
    MIFY_TOP_K,
)

# ---------------------------------------------------------------------------
# Domain classification
# ---------------------------------------------------------------------------


def classify_domain(query: str) -> list[str]:
    """根据查询内容判断所属领域，返回匹配的 dataset_id 列表。

    匹配策略：查询词（含缩写展开）与领域关键词做子串匹配。
    返回空列表表示无法判断领域，应搜全部。
    """
    lower = query.lower()
    matched: dict[str, int] = {}  # dataset_id -> match count

    for ds_id, info in DOMAIN_MAP.items():
        count = 0
        for kw in info["keywords"]:
            if kw in lower:
                count += 1
        if count > 0:
            matched[ds_id] = count

    if not matched:
        return []

    # 返回匹配数接近的领域（差距 ≤ 1），解决 "Mick clp" 跨库路由漏洞：
    # memory(mick=1) + low_power(clp=1) → 两个库都搜
    # 但仍保留纯单域查询的路由精度：SDC(clock=3) >> others(0) → 只搜 SDC
    best_count = max(matched.values())
    return [ds_id for ds_id, c in matched.items() if c >= best_count - 1]


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
    # error code 前缀 → 领域关键词，辅助 domain routing 和检索
    "pte": "PrimeTime PTE timing check error",
    "uite": "PrimeTime UITE timing check error",
    "rc": "PrimeTime RC timing check",
    "sel": "PrimeTime SEL timing check",
    "lnk": "PrimeTime LNK timing check",
    "mc": "PrimeTime MC timing check",
    "exc": "Genus EXC timing check error",
    "gca": "Genus Clock Analysis GCA check",
    "cpi": "Genus CPI check",
    "bw": "Broadway memory",
    "mem": "memory",
    "sta": "static timing analysis",
    "pg": "power ground connection",
    "lvl": "level shifter cell",
    "mtcmos": "power switch MTCMOS",
    "pst": "power state table",
    "eco": "engineering change order",
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
    # 流程/规范/文档类
    "流程": "flow",
    "规范": "specification",
    "配置": "configuration",
    "方案": "solution",
    "策略": "strategy",
    "实现": "implementation",
    "验证": "verification",
    "检查": "check",
    "分析": "analysis",
    "报告": "report",
    "说明": "description",
    "清单": "checklist",
    "模板": "template",
    "交付": "delivery",
    # 操作类
    "处理": "handling",
    "排查": "debug",
    "调试": "debug",
    "修复": "fix",
    "步骤": "steps",
    "配合": "coordinate",
    "差异": "difference",
    "关系": "relationship",
    "限制": "limitation",
    "判定": "judgment",
    # 芯片领域
    "门控": "gating",
    "电源": "power supply",
    "电压": "voltage",
    "信号": "signal",
    "路径": "path",
    "端口": "port",
    "引脚": "pin",
    "单元": "cell",
    "模块": "module",
    "接口": "interface",
    "连接": "connection",
    "层级": "hierarchy",
    "状态": "state",
    "模式": "mode",
    "参数": "parameter",
    "脚本": "script",
    "工具": "tool",
    "仿真": "simulation",
    "违例": "violation",
    "冲突": "conflict",
    "警告": "warning",
    "错误": "error",
    "案例": "case study",
    # 高频复合词
    "工作原理": "working principle",
    "整体流程": "overall flow",
    "实现方案": "implementation plan",
    "常见原因": "common causes",
    "怎么处理": "how to handle",
    "怎么配置": "how to configure",
    "怎么配合": "how to coordinate",
    "怎么排查": "how to debug",
    "怎么修": "how to fix",
    "怎么用": "how to use",
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


# 策略 5/6 生成的英文变体中，过于通用的词不应作为独立变体（会匹配到无关文档）
_GENERIC_EN_WORDS = frozenset({
    "strategy", "module", "handling", "check", "analysis",
    "report", "description", "template", "verification",
    "implementation", "configuration", "specification",
})

_PROJECT_ABBREV_MAP: dict[str, str] = {
    "BroadwayV100": "BW",
    "Broadway": "BW",
}


def _build_queries(query: str, dataset_id: str | None = None, *, num_variants: int | None = None) -> list[str]:
    """根据查询词生成多个搜索变体，按优先级排列。

    策略:
    1. 原始查询
    1.5. 项目名缩写桥接（如 BroadwayV100 → BW）
    2. 短缩写展开（如 ISO → isolation cell）
    2.5. 技术标识符文档标题桥接（error code → 标题匹配）
    3. 部分缩写展开（查询中嵌入的缩写子串替换）
    4. 英文短语 n-gram 提取（中英混合查询）
    5. 中英文桥接（中文术语 → 英文同义词）
    5.5. 中文文档标题桥接（中文关键词 → 标题匹配）
    6. 多关键词拆分（空格分隔的多个词各自独立搜索）
    """
    stripped = query.strip()
    queries = [stripped]
    lower = stripped.lower()

    # 策略1.5: 项目名缩写桥接
    # 当查询含项目全名（如 BroadwayV100）时，用缩写（BW）替换生成变体，
    # 使关键词能匹配以缩写开头的文档（如 BW-464）。
    for full_name, abbrev in _PROJECT_ABBREV_MAP.items():
        if full_name.lower() in lower:
            variant = stripped.replace(full_name, abbrev)
            if variant not in queries:
                queries.append(variant)
            break

    # 策略2: 短缩写展开
    if lower in _ABBREV_MAP and len(stripped) <= 5:
        queries.append(_ABBREV_MAP[lower])

    # 策略2.5: 技术标识符文档标题桥接
    # 查询中包含 error code 类标识符（如 1801_REF_OBJ_NOT_FOUND）时，
    # 在文档标题缓存中搜完整标题作为 RRF 变体。
    # 原因：Mify 分词器把【clp】粘进 token，裸 error code 做 keyword search 找不到目标文档。
    # error code 特征：含下划线的技术标识符（如 1801_REF_OBJ_NOT_FOUND、ISO_REDUNDANT）
    # 当 domain 路由失败时，遍历所有 dataset 的标题缓存（SDC 文档无前缀，低功耗文档含【clp】前缀）
    _tech_id_re = re.compile(r"\b[A-Z0-9]+_[A-Z0-9_]+(?:-[A-Z0-9]+)?\b")
    tech_tokens = _tech_id_re.findall(stripped)
    if tech_tokens:
        # 路由到具体 dataset；路由失败时搜全部 dataset
        ds_ids = [dataset_id] if dataset_id else MIFY_DATASET_IDS
        for ds in ds_ids:
            titles = _fetch_doc_titles(ds)
            for token in tech_tokens[:4]:      # 最多处理 4 个标识符
                matching = [t for t in titles if token in t and t not in queries]
                for t in matching[:2]:         # 每标识符最多加 2 个标题
                    queries.append(t)

    # 策略3: 部分缩写展开 —— 对查询中嵌入的缩写做子串替换
    expanded = stripped
    for abbr, full in _ABBREV_MAP.items():
        pattern = r"\b" + re.escape(abbr) + r"\b"
        if re.search(pattern, expanded, re.IGNORECASE):
            expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
    if expanded != stripped and expanded not in queries:
        queries.append(expanded)

    # 策略4: 英文短语提取 —— 中英混合查询中，连续英文词 n-gram 作为短语变体
    # 例: "clock relation table 和 Maxwell" → "clock relation table", "clock relation", "clock table"
    # 放在策略5(中英桥接)之前，因为短语变体比单英文词桥接更精准
    if re.search(r"[一-鿿]", stripped) and re.search(r"[A-Za-z]{2,}", stripped):
        words = stripped.split()
        phrases: list[str] = []
        i = 0
        while i < len(words):
            if re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", words[i]):
                j = i + 1
                while j < len(words) and re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", words[j]):
                    j += 1
                seq_len = j - i
                if seq_len >= 2:
                    # 全序列优先
                    full = " ".join(words[i:j])
                    if full not in phrases:
                        phrases.append(full)
                    # 首尾 bigram（word[0] + word[-1]），对 3 词序列等同于 skip-1
                    if seq_len >= 3:
                        edge = " ".join([words[i], words[j - 1]])
                        if edge not in phrases:
                            phrases.append(edge)
                    # 相邻 bigram
                    for start in range(i, j - 1):
                        bigram = " ".join(words[start:start + 2])
                        if bigram not in phrases:
                            phrases.append(bigram)
                i = j
            else:
                i += 1
        for phrase in phrases[:3]:  # 最多 3 个短语变体
            # 过滤：如果短语中所有词都是通用词，跳过（避免匹配无关文档）
            words_in_phrase = phrase.lower().split()
            if all(w in _GENERIC_EN_WORDS for w in words_in_phrase):
                continue
            if phrase not in queries:
                queries.append(phrase)

    # 策略5: 中英文桥接 —— 含中文时生成英文变体
    if re.search(r"[一-鿿]", stripped):
        en_parts = []
        for cn, en in _CN_BRIDGE.items():
            if cn in stripped:
                en_parts.append(en)
        if en_parts:
            en_query = " ".join(en_parts)
            # 过滤：如果翻译结果全是通用词，跳过
            en_words = en_query.lower().split()
            if not all(w in _GENERIC_EN_WORDS for w in en_words):
                if en_query not in queries:
                    queries.append(en_query)

    # 策略5.5: 中文文档标题桥接 —— 查询中的中文关键词，在文档标题缓存中找匹配标题
    # 例: "低功耗 SOP" → 找到 "低功耗综合相关配置说明"，添加中文短语变体
    _cn_word_re = re.compile(r"[一-鿿]{2,}")
    cn_words = _cn_word_re.findall(stripped)
    if cn_words and dataset_id:
        titles = _fetch_doc_titles(dataset_id)
        cn_phrases: list[str] = []
        for cn_word in cn_words[:3]:
            matching = [t for t in titles if cn_word in t]
            for t in matching[:2]:
                idx = t.find(cn_word)
                if idx >= 0:
                    # 取该中文词前后各扩展2个中文字符作为搜索短语
                    start = max(0, idx - 2)
                    end = min(len(t), idx + len(cn_word) + 4)
                    phrase = t[start:end]
                    cn_phrase = "".join(_cn_word_re.findall(phrase))
                    if len(cn_phrase) >= 4 and cn_phrase != cn_word and cn_phrase not in cn_phrases:
                        cn_phrases.append(cn_phrase)
        for phrase in cn_phrases[:3]:  # 最多 3 个中文短语变体
            if phrase not in queries:
                queries.append(phrase)

    # 策略6: 多关键词拆分 —— 空格分隔的多个词，各自作为独立查询变体
    # 解决 "mem2reg MCP2 MCP3" 这类复合查询打分过低的问题
    words = stripped.split()
    if len(words) > 1:
        for w in words:
            if w not in queries:
                queries.append(w)

    limit = num_variants if num_variants is not None else MIFY_NUM_VARIANTS
    return queries[:limit]


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
                "keyword_setting": {"keyword_weight": 0.2},
                "vector_setting": {
                    "embedding_provider_name": "langgenius/siliconflow/siliconflow",
                    "embedding_model_name": "Qwen/Qwen3-Embedding-8B_mi_sys",
                    "vector_weight": 0.8,
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
    *,
    rrf_k: int | None = None,
    num_variants: int | None = None,
) -> list[dict[str, Any]]:
    """从单个知识库检索（RAG-Fusion）。"""
    url = f"{MIFY_BASE_URL}/{dataset_id}/retrieve"
    headers = {
        "Authorization": f"Bearer {MIFY_API_KEY}",
        "Content-Type": "application/json",
    }

    queries = _build_queries(query, dataset_id, num_variants=num_variants)

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

    k = rrf_k if rrf_k is not None else MIFY_RRF_K
    return _rrf_fuse(variant_results, k=k, top_k=top_k)


def retrieve(
    query: str,
    top_k: int | None = None,
    dataset_id: str | None = None,
    *,
    rrf_k: int | None = None,
    num_variants: int | None = None,
) -> list[dict[str, Any]]:
    """从 Mify 知识库检索相关内容。

    支持单个或多个知识库：
    - 指定 dataset_id: 只检索该知识库
    - 不指定: 先做领域分类，命中则只搜对应库，未命中则搜全部

    返回列表，每项包含:
      - content: 文档片段内容
      - score: 原始相似度分数
      - rrf_score: RRF 融合分数
      - document_name: 文档名称
      - doc_url: 飞书文档链接
    """
    if top_k is None:
        top_k = MIFY_TOP_K
    k = rrf_k if rrf_k is not None else MIFY_RRF_K

    # 单知识库检索
    if dataset_id:
        fused = _retrieve_one_dataset(query, dataset_id, top_k, rrf_k=rrf_k, num_variants=num_variants)
    else:
        # 预分类：根据查询内容判断领域
        target_ds = classify_domain(query)

        if target_ds:
            # 命中领域：只搜对应的知识库
            all_results: list[list[dict[str, Any]]] = []
            with ThreadPoolExecutor(max_workers=len(target_ds)) as pool:
                futures = [
                    pool.submit(_retrieve_one_dataset, query, ds_id, top_k, rrf_k=rrf_k, num_variants=num_variants)
                    for ds_id in target_ds
                ]
                for future in futures:
                    try:
                        all_results.append(future.result())
                    except Exception:
                        all_results.append([])
            fused = _rrf_fuse(all_results, k=k, top_k=top_k)
        else:
            # 未命中：搜全部知识库
            all_results: list[list[dict[str, Any]]] = []
            with ThreadPoolExecutor(max_workers=len(MIFY_DATASET_IDS)) as pool:
                futures = [
                    pool.submit(_retrieve_one_dataset, query, ds_id, top_k, rrf_k=rrf_k, num_variants=num_variants)
                    for ds_id in MIFY_DATASET_IDS
                ]
                for future in futures:
                    try:
                        all_results.append(future.result())
                    except Exception:
                        all_results.append([])
            # 跨知识库 RRF 融合
            fused = _rrf_fuse(all_results, k=k, top_k=top_k)

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
