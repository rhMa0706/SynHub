"""Tests for core.mify_client — RAG-Fusion retrieval logic."""

from unittest.mock import MagicMock, patch

import pytest

from core.mify_client import _build_queries, _rrf_fuse, retrieve


# ---------------------------------------------------------------------------
# _rrf_fuse tests
# ---------------------------------------------------------------------------


class TestRrfFuse:
    def test_single_variant(self):
        """单个变体时，RRF 退化为原始排序。"""
        variant_a = [
            {"id": "d1", "content": "a", "score": 0.9, "document_name": "A", "doc_url": ""},
            {"id": "d2", "content": "b", "score": 0.8, "document_name": "B", "doc_url": ""},
        ]
        result = _rrf_fuse([variant_a], k=60, top_k=2)
        assert len(result) == 2
        assert result[0]["id"] == "d1"
        assert result[1]["id"] == "d2"

    def test_overlapping_docs_rank_higher(self):
        """在多个变体中出现的文档应排在前面。"""
        variant_a = [
            {"id": "d1", "content": "a", "score": 0.9, "document_name": "A", "doc_url": ""},
            {"id": "d2", "content": "b", "score": 0.8, "document_name": "B", "doc_url": ""},
        ]
        variant_b = [
            {"id": "d2", "content": "b", "score": 0.85, "document_name": "B", "doc_url": ""},
            {"id": "d3", "content": "c", "score": 0.7, "document_name": "C", "doc_url": ""},
        ]
        result = _rrf_fuse([variant_a, variant_b], k=60, top_k=3)
        # d2 出现在两个变体中，应排第一
        assert result[0]["id"] == "d2"
        # d1 只在 variant_a，但 rank 更高，排第二
        assert result[1]["id"] == "d1"
        # d3 只在 variant_b，rank 较低
        assert result[2]["id"] == "d3"

    def test_rrf_score_calculation(self):
        """验证 RRF 分数计算正确：score(d) = Σ 1/(k + rank)。"""
        variant_a = [{"id": "d1", "content": "a", "score": 0, "document_name": "", "doc_url": ""}]
        variant_b = [{"id": "d1", "content": "a", "score": 0, "document_name": "", "doc_url": ""}]
        result = _rrf_fuse([variant_a, variant_b], k=60, top_k=1)
        expected = 1.0 / (60 + 0) + 1.0 / (60 + 0)
        assert abs(result[0]["rrf_score"] - expected) < 1e-9

    def test_top_k_truncation(self):
        """top_k 截断正确。"""
        variants = [
            [{"id": f"d{i}", "content": str(i), "score": 0, "document_name": "", "doc_url": ""}]
            for i in range(10)
        ]
        result = _rrf_fuse(variants, k=60, top_k=3)
        assert len(result) == 3

    def test_empty_variants(self):
        """所有变体为空时返回空列表。"""
        result = _rrf_fuse([[], []], k=60, top_k=5)
        assert result == []


# ---------------------------------------------------------------------------
# _build_queries tests
# ---------------------------------------------------------------------------


class TestBuildQueries:
    def test_original_always_first(self):
        """原始查询始终是第一个变体。"""
        queries = _build_queries("some random query")
        assert queries[0] == "some random query"

    def test_short_abbrev_expansion(self):
        """短缩写被展开。"""
        queries = _build_queries("ISO")
        assert "isolation cell" in queries

    def test_long_query_with_embedded_abbrev(self):
        """长查询中嵌入的缩写被部分展开。"""
        queries = _build_queries("ISO cell sizing issue")
        # 应该包含原始查询
        assert "ISO cell sizing issue" in queries
        # 应该包含展开后的版本
        expanded = [q for q in queries if "isolation cell" in q.lower()]
        assert len(expanded) > 0

    def test_chinese_query_gets_english_bridge(self):
        """中文查询应生成英文变体。"""
        queries = _build_queries("功耗分析")
        # 应该包含英文变体
        english = [q for q in queries if "power" in q.lower()]
        assert len(english) > 0

    def test_num_variants_capped(self):
        """变体数量不超过 MIFY_NUM_VARIANTS。"""
        from config.settings import MIFY_NUM_VARIANTS

        queries = _build_queries("ISO")
        assert len(queries) <= MIFY_NUM_VARIANTS

    def test_no_duplicate_variants(self):
        """变体列表不应有重复。"""
        queries = _build_queries("clock gating")
        assert len(queries) == len(set(queries))


# ---------------------------------------------------------------------------
# retrieve tests (mocked HTTP)
# ---------------------------------------------------------------------------


class TestRetrieve:
    def _mock_response(self, records):
        """构造 mock httpx.Response。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": records}
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def _make_record(self, seg_id, content, score, doc_name="doc"):
        return {
            "segment": {
                "id": seg_id,
                "content": content,
                "document": {"name": doc_name, "doc_url": f"http://{doc_name}"},
            },
            "score": score,
        }

    @patch("core.mify_client.httpx.post")
    def test_parallel_retrieval_no_early_break(self, mock_post):
        """所有变体都被调用（没有 early-break）。"""
        mock_post.return_value = self._mock_response([])
        retrieve("ISO", top_k=5)
        # 应该至少调用 2 次（原始 + 展开）
        assert mock_post.call_count >= 2

    @patch("core.mify_client.httpx.post")
    def test_returns_correct_keys(self, mock_post):
        """返回的 dict 包含 MCP server 需要的字段。"""
        mock_post.return_value = self._mock_response([
            self._make_record("s1", "content", 0.9, "my_doc"),
        ])
        results = retrieve("ISO", top_k=5)
        assert len(results) > 0
        r = results[0]
        assert "content" in r
        assert "score" in r
        assert "document_name" in r
        assert "doc_url" in r
        assert "rrf_score" in r
        assert "id" not in r  # 内部 id 应被移除

    @patch("core.mify_client.httpx.post")
    def test_failed_variant_doesnt_crash(self, mock_post):
        """某个变体调用失败时，其他变体仍然返回结果。"""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("network error")
            return self._mock_response([
                self._make_record("s1", "ok", 0.9),
            ])

        mock_post.side_effect = side_effect
        results = retrieve("ISO", top_k=5)
        assert len(results) > 0

    @patch("core.mify_client.httpx.post")
    def test_top_k_truncation(self, mock_post):
        """结果数量不超过 top_k。"""
        records = [
            self._make_record(f"s{i}", f"content{i}", 0.9 - i * 0.01)
            for i in range(20)
        ]
        mock_post.return_value = self._mock_response(records)
        results = retrieve("ISO", top_k=3)
        assert len(results) <= 3

    @patch("core.mify_client.httpx.post")
    def test_deduplication_across_variants(self, mock_post):
        """跨变体的重复文档通过 RRF 合并，不会出现重复条目。"""
        # 两个变体返回相同的 segment id
        mock_post.return_value = self._mock_response([
            self._make_record("s1", "same content", 0.9),
        ])
        results = retrieve("ISO", top_k=5)
        seg_ids = [r.get("content") for r in results]
        # 同一文档不应出现两次（RRF 会合并同 id 的条目）
        assert len(seg_ids) == len(set(seg_ids))
