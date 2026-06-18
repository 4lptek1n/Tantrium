"""Map theorem candidates to Tantrium graph dependencies."""
from __future__ import annotations

COMMON = ["GATE_A_PERTURBATION", "GATE_A_CROSS_RATIO", "GATE_B_STAIRCASE_QUOTIENT"]


def map_dependencies(candidate_id: str) -> list[str]:
    deps = list(COMMON)
    if "K7" in candidate_id:
        deps.append("K7_SHARPNESS")
    if "POSITIVITY" in candidate_id:
        deps.extend(["FIRST_FIVE_PIVOTS", "D_POSITIVITY"])
    if "SUBRESULTANT" in candidate_id:
        deps.append("TAU_SUBDISCRIMINANT")
    return list(dict.fromkeys(deps))
