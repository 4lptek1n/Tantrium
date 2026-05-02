"""Generate structured theorem candidates for Gate A/B blockers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dependency_mapper import map_dependencies
from .hypothesis_minimizer import minimize_hypotheses
from .theorem_scorer import score_candidate
from .theorem_writer import write_candidate

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = REPO_ROOT / "results" / "research_os" / "candidates"

FAMILIES = [
    "GENERAL_STAIRCASE_DIVISOR_THEOREM",
    "GENERAL_QUOTIENT_DEGREE_THEOREM",
    "SUBRESULTANT_QJR_RECURRENCE_THEOREM",
    "SAFE_WINDOW_POSITIVITY_THEOREM",
    "K7_SHARPNESS_STRUCTURE_THEOREM",
    "LAH_REFINEMENT_POSITIVITY_THEOREM",
    "GATE_A_TO_GATE_B_TRANSFER_THEOREM",
]


def base_candidate(candidate_id: str, blocker: str, recurrence_summary: dict[str, Any]) -> dict[str, Any]:
    best_recurrence = recurrence_summary.get("synthesis", {}).get("best_candidate", "QJR_DEGREE_R_STEP")
    statements = {
        "GENERAL_STAIRCASE_DIVISOR_THEOREM": "The Gate B H-factor family admits a uniform staircase divisor compatible with all extracted Q_{j,r}(n).",
        "GENERAL_QUOTIENT_DEGREE_THEOREM": "For all admissible j,r, deg_n Q_{j,r}(n)=r(2j-r-1)/2.",
        "SUBRESULTANT_QJR_RECURRENCE_THEOREM": f"The extracted QJR family satisfies the recurrence represented by {best_recurrence}.",
        "SAFE_WINDOW_POSITIVITY_THEOREM": "Inside the first-five pivot safe window, the Gate B quotient factors preserve positivity.",
        "K7_SHARPNESS_STRUCTURE_THEOREM": "The K7 boundary is the first structural sharpness boundary of the safe window.",
        "LAH_REFINEMENT_POSITIVITY_THEOREM": "The Lah refinement induced by Gate A perturbation preserves positivity under the staircase quotient hypotheses.",
        "GATE_A_TO_GATE_B_TRANSFER_THEOREM": "The Gate A lambda^{-2} perturbation transfers to the Gate B staircase quotient structure.",
    }
    hypotheses = minimize_hypotheses(candidate_id, ["Gate A perturbation", "Gate B finite data", blocker])
    return {
        "candidate_id": candidate_id,
        "precise_statement": statements[candidate_id],
        "variables": ["d", "j", "r", "n", "t"],
        "hypotheses": hypotheses,
        "conclusion": statements[candidate_id],
        "known_evidence": [
            "math/gate_a.py",
            "math/gate_a_verify.py",
            "theorems/GATE_B_FINDINGS.md",
            "results/research_os/campaigns/subresultant_recurrence/recurrence_candidates.json",
        ],
        "possible_proof_strategies": [
            "induction",
            "generating_function_extraction",
            "subresultant_chain",
            "bezoutian_block_structure",
            "lgv_path_model",
            "positivity_basis",
        ],
        "dependencies": map_dependencies(candidate_id),
        "risks": ["finite evidence may not identify the true hidden H quotient", "K7 sharpness may force a narrower safe window"],
        "expected_blocker_if_proof_fails": "MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR",
        "lean_skeleton_target": f"formal/lean/Tantrium/{lean_name(candidate_id)}.lean",
        "score": score_candidate(candidate_id),
    }


def lean_name(candidate_id: str) -> str:
    return "".join(part.title() for part in candidate_id.lower().split("_"))


def generate_theorem_candidates(blocker: str = "MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR") -> dict[str, Any]:
    recurrence_path = REPO_ROOT / "results" / "research_os" / "campaigns" / "subresultant_recurrence" / "synthesis_status.json"
    recurrence_summary = json.loads(recurrence_path.read_text(encoding="utf-8")) if recurrence_path.exists() else {}
    candidates = [base_candidate(candidate_id, blocker, {"synthesis": recurrence_summary}) for candidate_id in FAMILIES]
    CANDIDATE_ROOT.mkdir(parents=True, exist_ok=True)
    for candidate in candidates:
        write_candidate(CANDIDATE_ROOT, candidate)
    catalog = {"blocker": blocker, "candidate_count": len(candidates), "candidates": candidates}
    (CANDIDATE_ROOT / "gate_ab_candidate_catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_catalog_md(catalog)
    return catalog


def write_catalog_md(catalog: dict[str, Any]) -> None:
    lines = ["# Tantrium Theorem Candidate Catalog", "", f"Blocker: `{catalog['blocker']}`", "", "| Candidate | Score | Expected blocker |", "|---|---:|---|"]
    for item in catalog["candidates"]:
        lines.append(f"| `{item['candidate_id']}` | `{item['score']}` | `{item['expected_blocker_if_proof_fails']}` |")
    lines.append("")
    lines.append("These are theorem candidates. None is marked proven without a certificate.")
    (REPO_ROOT / "docs" / "TANTRIUM_THEOREM_CANDIDATE_CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
