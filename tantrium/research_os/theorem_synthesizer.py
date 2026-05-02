"""Deterministic theorem candidate synthesis from blockers and evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .blackboard import append_event
from .theorem_ir import TheoremCandidate, write_candidates

REPO_ROOT = Path(__file__).resolve().parents[2]


def synthesize_candidates(campaign_id: str, evidence: dict[str, Any], out_dir: Path) -> list[dict[str, Any]]:
    if campaign_id == "lah_gate_ab_generalization":
        raw = [
            TheoremCandidate(
                "GENERAL_STAIRCASE_DIVISOR_THEOREM",
                r"H_{d,j}(t) \text{ admits a uniform staircase divisor compatible with all } Q_{j,r}(n).",
                ["d", "j", "r", "n", "t"],
                ["j >= 1", "0 <= r <= j", "Gate A perturbation data exists"],
                "The staircase quotient denominator and top-ramp factors follow the inferred general divisor law.",
                evidence=["Gate B first-five positivity", "K7 sharpness boundary"],
                proof_strategies=["induction on j", "subresultant recurrence", "LGV staircase Young diagram model"],
                dependencies=["GATE_A_PERTURBATION", "GATE_B_STAIRCASE_RAMP", "LAH_SHADOW"],
                risk="high",
                score=0.72,
            ),
            TheoremCandidate(
                "GENERAL_QUOTIENT_DEGREE_THEOREM",
                r"\deg_n Q_{j,r}(n)=r(2j-r-1)/2.",
                ["j", "r", "n"],
                ["j >= 1", "0 <= r <= j"],
                "The quotient degree law holds for the general Gate B quotient family.",
                evidence=["finite windows", "top ramp law"],
                proof_strategies=["generating function extraction", "recurrence discovery"],
                dependencies=["GATE_B_STAIRCASE_QUOTIENT"],
                risk="medium",
                score=0.81,
            ),
            TheoremCandidate(
                "K7_SHARPNESS_STRUCTURE_THEOREM",
                r"K7 \text{ is the first sharpness boundary of the safe positivity window}.",
                ["k", "j"],
                ["first-five pivot positivity"],
                "The boundary failure is structural rather than a finite-computation artifact.",
                evidence=["K7 sharpness artifact"],
                proof_strategies=["counterexample-guided refinement", "staircase boundary classification"],
                dependencies=["FIRST_FIVE_PIVOTS", "K7_SHARPNESS"],
                risk="medium",
                score=0.68,
            ),
        ]
    elif campaign_id == "coefficient_frontier_parametric_lift":
        raw = [
            TheoremCandidate(
                "ATLAS_FRONTIER_D_SEED_LIFT_THEOREM",
                r"\text{The first uncertified atlas frontier admits a D-seed positive representation}.",
                ["ell", "q", "j", "k"],
                ["frontier coefficient is inside current atlas support"],
                "The first frontier coefficient is certified by a D-seed expansion.",
                evidence=["engine mixed-depth summaries", "D-positivity certificate"],
                proof_strategies=["D-seed representation", "binomial basis expansion", "LGV lift"],
                dependencies=["D_POSITIVITY", "AG_LGV_TRANSFER"],
                risk="high",
                score=0.66,
            ),
            TheoremCandidate(
                "LOG_DET_CUMULANT_FRONTIER_THEOREM",
                r"\text{The frontier coefficient is a nonnegative log-det cumulant combination}.",
                ["ell", "q"],
                ["cumulant kernel data exists"],
                "A log-det cumulant expression gives a parametric positivity certificate.",
                evidence=["ell mixed-depth kernel CSVs"],
                proof_strategies=["factorization", "recurrence discovery"],
                dependencies=["LOG_DET_CUMULANT_PROGRAM"],
                risk="high",
                score=0.61,
            ),
        ]
    elif campaign_id == "goldbach_minor_arc_bound":
        raw = [
            TheoremCandidate(
                "MINOR_ARC_DOMINATION_BOUND",
                r"\int_{\mathfrak m}|S(\alpha)|^2 e(-N\alpha)d\alpha = o(\mathfrak S(N)N).",
                ["N", "alpha"],
                ["N even and sufficiently large", "unconditional prime exponential sum estimates"],
                "The minor arc contribution is dominated by the certified major arc main term.",
                evidence=["Goldbach blocker certificate", "circle method certificate"],
                proof_strategies=["Type I/II bilinear estimate", "large sieve", "zero-density estimates"],
                dependencies=["GOLDBACH_MAJOR_ARC_SCHEMA", "SINGULAR_SERIES_POSITIVITY"],
                risk="very_high",
                score=0.44,
            ),
        ]
    elif campaign_id == "rh_formalization_bootstrap":
        raw = [
            TheoremCandidate(
                "LEAN_TAU_CAUCHY_BINET_IDENTITY",
                r"\tau_j \text{ equals the required subdiscriminant by Cauchy-Binet}.",
                ["j", "matrix data"],
                ["finite matrix definitions match certificate normal form"],
                "First Lean lemma in the RH formalization queue.",
                evidence=["tau/sturm certificate", "Lean Tau scaffold"],
                proof_strategies=["mathlib Matrix.det", "Cauchy-Binet theorem"],
                dependencies=["TAU_SUBDISCRIMINANT"],
                risk="medium",
                score=0.83,
            ),
            TheoremCandidate(
                "LEAN_AG_LGV_TRANSFER_IDENTITY",
                r"\text{The AG/LGV transfer map preserves the certified determinant identity}.",
                ["path family", "weight"],
                ["finite acyclic graph", "nonintersecting path model"],
                "Formal bridge from path transfer certificate to Lean statement.",
                evidence=["AG/LGV certificate", "Lean AGLGV scaffold"],
                proof_strategies=["mathlib Finset", "LGV lemma statement skeleton"],
                dependencies=["AG_LGV_TRANSFER"],
                risk="high",
                score=0.77,
            ),
        ]
    else:
        raise ValueError(f"unknown campaign: {campaign_id}")

    candidates = [item.to_dict() for item in raw]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "candidate_theorems.json").write_text(
        json.dumps({"campaign": campaign_id, "candidates": candidates}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_candidates(campaign_id, candidates)
    append_event(ResearchEvent(campaign_id, "Theorem Synthesizer", "candidate_theorems_generated", "CANDIDATE_THEOREMS_GENERATED", outputs=[str((out_dir / "candidate_theorems.json").relative_to(REPO_ROOT))]))
    return candidates
