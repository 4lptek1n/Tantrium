"""Score theorem candidates."""
from __future__ import annotations

SCORES = {
    "GENERAL_QUOTIENT_DEGREE_THEOREM": 0.9,
    "SUBRESULTANT_QJR_RECURRENCE_THEOREM": 0.86,
    "GENERAL_STAIRCASE_DIVISOR_THEOREM": 0.8,
    "SAFE_WINDOW_POSITIVITY_THEOREM": 0.76,
    "K7_SHARPNESS_STRUCTURE_THEOREM": 0.74,
    "GATE_A_TO_GATE_B_TRANSFER_THEOREM": 0.7,
    "LAH_REFINEMENT_POSITIVITY_THEOREM": 0.68,
}


def score_candidate(candidate_id: str) -> float:
    return SCORES.get(candidate_id, 0.5)
