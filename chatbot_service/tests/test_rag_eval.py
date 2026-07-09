# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations

import pytest

from rag.evaluation import (
    ndcg_at_k,
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    compute_all_metrics,
)


def test_ndcg_perfect():
    assert ndcg_at_k([1.0, 1.0, 1.0, 1.0, 1.0], 5) == pytest.approx(1.0)


def test_ndcg_zero():
    assert ndcg_at_k([0.0, 0.0, 0.0], 3) == pytest.approx(0.0)


def test_ndcg_partial():
    ndcg = ndcg_at_k([1.0, 0.0, 1.0], 3)
    assert 0.0 < ndcg < 1.0


def test_recall_all():
    assert recall_at_k(5, 5, 5) == pytest.approx(1.0)


def test_recall_half():
    assert recall_at_k(3, 6, 5) == pytest.approx(3.0 / 5.0)


def test_recall_none():
    assert recall_at_k(0, 5, 5) == pytest.approx(0.0)


def test_recall_capped():
    assert recall_at_k(3, 10, 5) == pytest.approx(3.0 / 5.0)


def test_precision_perfect():
    assert precision_at_k(5, 5) == pytest.approx(1.0)


def test_precision_zero():
    assert precision_at_k(0, 5) == pytest.approx(0.0)


def test_mrr_single_rank1():
    assert mean_reciprocal_rank([1]) == pytest.approx(1.0)


def test_mrr_multiple():
    mrr = mean_reciprocal_rank([1, 3, 5])
    expected = (1.0 + 1.0 / 3.0 + 1.0 / 5.0) / 3.0
    assert mrr == pytest.approx(expected)


def test_mrr_none_found():
    assert mean_reciprocal_rank([]) == pytest.approx(0.0)


def test_compute_all():
    metrics = compute_all_metrics(
        relevance_scores=[1.0, 0.5, 0.0],
        total_relevant=5,
        k=3,
        rank_positions=[1, 2],
    )
    assert "ndcg@k" in metrics
    assert "recall@k" in metrics
    assert "precision@k" in metrics
    assert "mrr" in metrics
    assert all(isinstance(v, float) for v in metrics.values())
