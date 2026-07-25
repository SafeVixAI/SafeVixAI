# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
from __future__ import annotations


def ndcg_at_k(relevance_scores: list[float], k: int) -> float:
    if not relevance_scores or k <= 0:
        return 0.0
    actual_k = min(k, len(relevance_scores))
    dcg = sum((2 ** relevance_scores[i] - 1) / (i + 2) for i in range(actual_k))
    ideal = sorted(relevance_scores, reverse=True)[:actual_k]
    idcg = sum((2 ** ideal[i] - 1) / (i + 2) for i in range(len(ideal)))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(relevant: int, total_relevant: int, k: int) -> float:
    if total_relevant <= 0 or k <= 0:
        return 0.0
    return relevant / min(total_relevant, k)


def precision_at_k(relevant: int, k: int) -> float:
    if k <= 0:
        return 0.0
    return relevant / k


def mean_reciprocal_rank(rank_positions: list[int]) -> float:
    if not rank_positions:
        return 0.0
    return sum(1.0 / r for r in rank_positions if r > 0) / len(rank_positions)


def compute_all_metrics(
    relevance_scores: list[float],
    total_relevant: int,
    k: int,
    rank_positions: list[int],
) -> dict[str, float]:
    min(k, len(relevance_scores))
    relevant = sum(1 for s in relevance_scores[:k] if s > 0)
    return {
        "ndcg@k": ndcg_at_k(relevance_scores, k),
        "recall@k": recall_at_k(relevant, total_relevant, k),
        "precision@k": precision_at_k(relevant, k),
        "mrr": mean_reciprocal_rank(rank_positions),
    }
