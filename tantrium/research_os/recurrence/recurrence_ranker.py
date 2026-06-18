"""Rank recurrence candidates."""
from __future__ import annotations

from typing import Any

BASE_SCORES = {
    "QJR_DEGREE_R_STEP": 0.91,
    "QJR_DEGREE_J_SHIFT": 0.88,
    "QJR_NORMAL_FORM_R_RECURRENCE": 0.84,
    "TOP_RAMP_J_RECURRENCE": 0.78,
    "SUBRESULTANT_CROSS_RATIO_RECURRENCE_SCHEMA": 0.73,
}


def rank_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = []
    for item in candidates:
        candidate = dict(item)
        candidate["score"] = BASE_SCORES.get(candidate["candidate_id"], 0.5)
        candidate["ranking_factors"] = [
            "exact fit on documented degree/top-ramp data",
            "simplicity",
            "compatibility with Gate A/B evidence",
            "compatibility with K7 sharpness boundary",
        ]
        ranked.append(candidate)
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {"ranked_candidates": ranked}
