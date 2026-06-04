"""Problem IR builders."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBLEM_DIR = REPO_ROOT / "results" / "research_os" / "problems"


@dataclass
class ProblemIR:
    problem_id: str
    statement: str
    objects: list[str]
    parameters: list[str]
    known_reductions: list[str]
    known_certificates: list[str]
    known_blockers: list[str]
    target_status: str
    campaign_priority: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROBLEMS: dict[str, ProblemIR] = {
    "subresultant_recurrence": ProblemIR(
        problem_id="subresultant_recurrence",
        statement="Discover finite-verifiable recurrence candidates for Q_{j,r}(n) and the hidden H-factor subresultant chain.",
        objects=["Q_{j,r}(n)", "H_{d,j}(t)", "subresultant cross-ratio", "staircase divisor"],
        parameters=["d", "j", "r", "n", "t"],
        known_reductions=["Gate A perturbation", "Gate B staircase quotient", "K7 sharpness boundary"],
        known_certificates=["results/research_os/campaigns/subresultant_recurrence/finite_verification.json"],
        known_blockers=["MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR"],
        target_status="RECURRENCE_VERIFIED_FINITE",
        campaign_priority=100,
    ),
    "lah_gate_ab_generalization": ProblemIR(
        problem_id="lah_gate_ab_generalization",
        statement="Refine or prove the general Gate B staircase quotient theorem behind the Lah/Gate A blocker.",
        objects=["H_{d,j}(t)", "Q_{j,r}(n)", "Lah shadow", "Gate B staircase quotients"],
        parameters=["d", "j", "r", "n", "t"],
        known_reductions=["Gate A lambda^{-2} perturbation", "Gate B top ramp", "first-five pivot positivity"],
        known_certificates=["math/gate_a_verify.py", "theorems/GATE_B_FINDINGS.md"],
        known_blockers=["GENERAL_J_STAIRCASE_QUOTIENT_PROOF"],
        target_status="REFINED_SUBGAP",
        campaign_priority=90,
    ),
    "coefficient_frontier_parametric_lift": ProblemIR(
        problem_id="coefficient_frontier_parametric_lift",
        statement="Attack the first uncertified coefficient positivity atlas frontier.",
        objects=["coefficient atlas", "log-det cumulants", "D-seed", "AG/LGV path model"],
        parameters=["ell", "q", "j", "k"],
        known_reductions=["D-positivity", "Gate B staircase quotient", "AG/LGV transfer"],
        known_certificates=["results/atlas/manifest.json", "results/certificates/d_positivity_parametric_certificate.json"],
        known_blockers=["FIRST_UNCERTIFIED_ATLAS_FRONTIER", "PARAMETRIC_POSITIVITY_NOT_YET_CERTIFIED"],
        target_status="REFINED_SUBGAP",
        campaign_priority=85,
    ),
    "goldbach_minor_arc_bound": ProblemIR(
        problem_id="goldbach_minor_arc_bound",
        statement="Specify the unconditional minor arc bound required by the Goldbach control machine.",
        objects=["minor arcs", "major arcs", "singular series", "prime exponential sums"],
        parameters=["N", "alpha", "Q", "eta"],
        known_reductions=["circle method decomposition", "singular series positivity", "major arc schema"],
        known_certificates=["results/conjectures/goldbach/blocker_certificate.json"],
        known_blockers=["MINOR_ARC_UNCONDITIONAL_BOUND"],
        target_status="BLOCKED_BY_NAMED_GAP",
        campaign_priority=70,
    ),
    "rh_formalization_bootstrap": ProblemIR(
        problem_id="rh_formalization_bootstrap",
        statement="Convert internal RH certificate closure into a concrete external Lean work queue.",
        objects=["tau/subdiscriminant", "Sturm pivots", "AG/LGV transfer", "dyadic capacity", "D-positivity"],
        parameters=["j", "ell", "cells", "paths"],
        known_reductions=["Tantrium RH certificate chain"],
        known_certificates=["results/certificates/rh_symbolic_closure_certificate.json"],
        known_blockers=["EXTERNAL_FORMALIZATION_PENDING"],
        target_status="FORMALIZATION_BOOTSTRAP_READY",
        campaign_priority=80,
    ),
}


def problem_ir(campaign_id: str) -> dict[str, Any]:
    if campaign_id not in PROBLEMS:
        raise ValueError(f"unknown campaign problem: {campaign_id}")
    return PROBLEMS[campaign_id].to_dict()


def write_problem_ir(campaign_id: str) -> Path:
    payload = problem_ir(campaign_id)
    path = PROBLEM_DIR / f"{campaign_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
