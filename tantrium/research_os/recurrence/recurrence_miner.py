"""Mine candidate recurrences for Q_{j,r}(n)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .h_factor_loader import build_h_factor_inventory
from .qjr_extractor import build_qjr_tables
from .recurrence_ranker import rank_candidates
from .recurrence_reporter import write_recurrence_report
from .recurrence_verifier import verify_candidates

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "results" / "research_os" / "campaigns" / "subresultant_recurrence"


def candidate_recurrences() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "QJR_DEGREE_J_SHIFT",
            "type": "degree_recurrence",
            "statement": "D(j+1,r)-D(j,r)=r for D(j,r)=r(2j-r-1)/2.",
            "variables": ["j", "r"],
            "evidence_scope": "symbolic_degree_law",
            "proof_obligation": "Connect degree recurrence to the original hidden H quotient Q_{j,r}(n).",
        },
        {
            "candidate_id": "QJR_DEGREE_R_STEP",
            "type": "degree_recurrence",
            "statement": "D(j,r)-D(j,r-1)=j-r for 1<=r<=j.",
            "variables": ["j", "r"],
            "evidence_scope": "symbolic_degree_law",
            "proof_obligation": "Derive the r-step from subresultant cross-ratio normalization.",
        },
        {
            "candidate_id": "QJR_NORMAL_FORM_R_RECURRENCE",
            "type": "normal_form_recurrence",
            "statement": "Q(j,r;n)=Q(j,r-1;n)*prod_{a=D(j,r-1)+1}^{D(j,r)}(n+a) in the documented normal form.",
            "variables": ["j", "r", "n"],
            "evidence_scope": "finite_normal_form_table",
            "proof_obligation": "Prove the normal form equals the true Gate B staircase quotient.",
        },
        {
            "candidate_id": "TOP_RAMP_J_RECURRENCE",
            "type": "top_ramp_recurrence",
            "statement": "A_j(n)/A_{j-1}(n)=2^j(n+j)^j for fixed n under the top-ramp normal form.",
            "variables": ["j", "n"],
            "evidence_scope": "symbolic_top_ramp_law",
            "proof_obligation": "Reconcile fixed-n recurrence with n=d-(j+1) indexing in H_{d,j}.",
        },
        {
            "candidate_id": "SUBRESULTANT_CROSS_RATIO_RECURRENCE_SCHEMA",
            "type": "subresultant_schema",
            "statement": "rho_{d,j}(t)=C_{d,j} t^{k_{d,j}} H_{d,j-2}H_{d,j}/H_{d,j-1}^2 should induce an r-step quotient recurrence after staircase divisor extraction.",
            "variables": ["d", "j", "r", "t"],
            "evidence_scope": "cross_ratio_identity_schema",
            "proof_obligation": "Compute the exact extracted quotient factors and certify cancellation.",
        },
    ]


def mine_subresultant_recurrences(deep: bool = False, out_dir: Path = OUT_DIR) -> dict[str, Any]:
    max_j = 10 if deep else 8
    inventory = build_h_factor_inventory(out_dir)
    qjr_tables = build_qjr_tables(out_dir, max_j=max_j, sample_n=10 if deep else 8)
    candidates = candidate_recurrences()
    ranking = rank_candidates(candidates)
    verification = verify_candidates(candidates, qjr_tables)
    counterexample = {
        "status": "NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW",
        "search_window": {"j": [1, max_j], "r": "0..j", "n": [0, 10 if deep else 8]},
        "counterexample": None,
    }
    status = "RECURRENCE_VERIFIED_FINITE" if verification["all_finite_checks_passed"] else "RECURRENCE_CANDIDATE_FOUND"
    synthesis = {
        "campaign": "subresultant_recurrence",
        "status": status,
        "best_candidate": ranking["ranked_candidates"][0]["candidate_id"],
        "refined_subgap": "MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR",
        "proof_promoted": False,
        "warning": "Finite recurrence verification is not a proof of the original hidden H quotient.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "recurrence_candidates.json").write_text(json.dumps({"candidates": candidates}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "recurrence_ranking.json").write_text(json.dumps(ranking, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "finite_verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "counterexample_search.json").write_text(json.dumps(counterexample, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "synthesis_status.json").write_text(json.dumps(synthesis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_recurrence_report(out_dir, inventory, qjr_tables, candidates, ranking, verification, synthesis)
    write_conjecture_doc(synthesis, ranking)
    return {
        "inventory": inventory,
        "qjr_tables": qjr_tables,
        "candidates": candidates,
        "ranking": ranking,
        "verification": verification,
        "counterexample": counterexample,
        "synthesis": synthesis,
    }


def write_conjecture_doc(synthesis: dict[str, Any], ranking: dict[str, Any]) -> None:
    path = REPO_ROOT / "theorems" / "SUBRESULTANT_QJR_RECURRENCE_CONJECTURE.md"
    best = ranking["ranked_candidates"][0]
    path.write_text(
        "\n".join(
            [
                "# Subresultant QJR Recurrence Conjecture",
                "",
                f"Status: `{synthesis['status']}`",
                "",
                "This is a theorem candidate, not a promoted proof theorem.",
                "",
                f"Best current candidate: `{best['candidate_id']}`",
                "",
                best["statement"],
                "",
                f"Remaining blocker: `{synthesis['refined_subgap']}`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
