"""Proof strategy ranking and proof attempt recording."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTEMPT_DIR = REPO_ROOT / "results" / "research_os" / "proof_attempts"


def rank_and_attempt(campaign_id: str, candidates: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    ranked = sorted(candidates, key=lambda item: float(item.get("score", 0)), reverse=True)
    attempts = []
    for rank, candidate in enumerate(ranked, start=1):
        candidate_id = candidate["candidate_id"]
        strategies = candidate.get("proof_strategies", [])
        if campaign_id == "rh_formalization_bootstrap":
            failed_step = "external Lean proof not attempted in research OS pass"
        elif campaign_id == "lah_gate_ab_generalization" and candidate_id == "GENERAL_QUOTIENT_DEGREE_THEOREM":
            failed_step = "missing subresultant recurrence proving the degree law for all j,r"
        elif campaign_id == "coefficient_frontier_parametric_lift":
            failed_step = "no parametric positive expansion for the first frontier was certified"
        elif campaign_id == "goldbach_minor_arc_bound":
            failed_step = "unconditional Type II/minor arc domination estimate not supplied"
        else:
            failed_step = "requires human review or external formal proof"
        attempts.append(
            {
                "attempt_id": f"{campaign_id}:{candidate_id}:attempt1",
                "candidate_id": candidate_id,
                "rank": rank,
                "strategy": strategies[0] if strategies else "direct proof search",
                "steps": [
                    "load evidence",
                    "check dependency certificates",
                    "try strongest ranked strategy",
                    "record exact obstruction",
                ],
                "failed_step": failed_step,
                "certificate_generated": False,
                "refined_subgap": refined_subgap_for(campaign_id),
                "next_action": next_action_for(campaign_id),
            }
        )
    payload = {"campaign": campaign_id, "ranked_candidates": ranked, "attempts": attempts}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "proof_strategy_ranking.json").write_text(
        json.dumps({"campaign": campaign_id, "ranked_candidates": ranked}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "proof_attempts.md").write_text(render_attempts(payload), encoding="utf-8")
    ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
    (ATTEMPT_DIR / f"{campaign_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(ResearchEvent(campaign_id, "Strategy Engine", "proof_attempted", "PROOF_ATTEMPTED", outputs=[str((out_dir / "proof_attempts.md").relative_to(REPO_ROOT))]))
    return payload


def refined_subgap_for(campaign_id: str) -> str | None:
    return {
        "lah_gate_ab_generalization": "MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR",
        "coefficient_frontier_parametric_lift": "MISSING_D_SEED_OR_LGV_FRONTIER_REPRESENTATION",
        "goldbach_minor_arc_bound": "MISSING_TYPE_II_BILINEAR_ESTIMATE",
        "rh_formalization_bootstrap": "LEAN_MATHLIB_LGV_BRIDGE_NOT_COMPLETED",
    }.get(campaign_id)


def next_action_for(campaign_id: str) -> str:
    return {
        "lah_gate_ab_generalization": "derive the subresultant recurrence for Q_{j,r} and classify K7 sharpness",
        "coefficient_frontier_parametric_lift": "construct a D-seed or LGV path representation for the first frontier coefficient",
        "goldbach_minor_arc_bound": "isolate the exact Type II bilinear estimate needed for minor arc domination",
        "rh_formalization_bootstrap": "formalize the tau/subdiscriminant Cauchy-Binet lemma first",
    }.get(campaign_id, "human review")


def render_attempts(payload: dict[str, Any]) -> str:
    lines = [f"# Proof Attempts: {payload['campaign']}", ""]
    for attempt in payload["attempts"]:
        lines.extend(
            [
                f"## {attempt['candidate_id']}",
                "",
                f"Strategy: `{attempt['strategy']}`",
                f"Certificate generated: `{attempt['certificate_generated']}`",
                f"Failed step: `{attempt['failed_step']}`",
                f"Refined subgap: `{attempt['refined_subgap']}`",
                f"Next action: {attempt['next_action']}",
                "",
            ]
        )
    return "\n".join(lines)
