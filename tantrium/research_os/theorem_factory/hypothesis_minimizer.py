"""Conservative hypothesis minimization."""
from __future__ import annotations


def minimize_hypotheses(candidate_id: str, base: list[str]) -> list[str]:
    hypotheses = list(dict.fromkeys(base))
    if "K7" in candidate_id:
        hypotheses.append("K7 sharpness artifact is retained as boundary evidence")
    if "SAFE_WINDOW" in candidate_id:
        hypotheses.append("j,r remain inside the first-five pivot safe window")
    if "SUBRESULTANT" in candidate_id:
        hypotheses.append("subresultant cross-ratio normalization is fixed")
    return hypotheses
