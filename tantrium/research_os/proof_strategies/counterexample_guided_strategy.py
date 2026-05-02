"""Coordinator for proof strategy attempts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from . import (
    bezoutian_strategy,
    dyadic_transport_strategy,
    factorization_strategy,
    generating_function_strategy,
    induction_strategy,
    lgv_strategy,
    positivity_basis_strategy,
    subresultant_strategy,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CANDIDATE_ROOT = REPO_ROOT / "results" / "research_os" / "candidates"
ATTEMPT_ROOT = REPO_ROOT / "results" / "research_os" / "proof_attempts"

STRATEGIES: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "induction": induction_strategy.attempt,
    "generating_function": generating_function_strategy.attempt,
    "subresultant": subresultant_strategy.attempt,
    "bezoutian": bezoutian_strategy.attempt,
    "lgv": lgv_strategy.attempt,
    "dyadic_transport": dyadic_transport_strategy.attempt,
    "factorization": factorization_strategy.attempt,
    "positivity_basis": positivity_basis_strategy.attempt,
}


def load_candidates(campaign: str) -> list[dict[str, Any]]:
    catalog = CANDIDATE_ROOT / "gate_ab_candidate_catalog.json"
    if catalog.exists():
        return json.loads(catalog.read_text(encoding="utf-8"))["candidates"]
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(CANDIDATE_ROOT.glob("*THEOREM.json"))]


def run_strategy_matrix(campaign: str = "subresultant_recurrence") -> dict[str, Any]:
    candidates = load_candidates(campaign)
    summaries = []
    for candidate in candidates:
        out_dir = ATTEMPT_ROOT / candidate["candidate_id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        attempts = [fn(candidate) for fn in STRATEGIES.values()]
        matrix = {"campaign": campaign, "candidate_id": candidate["candidate_id"], "attempts": attempts}
        (out_dir / "strategy_matrix.json").write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for attempt in attempts:
            name = attempt["strategy"]
            filename = f"{name}_attempt.md"
            if name == "generating_function":
                filename = "generating_function_attempt.md"
            (out_dir / filename).write_text(render_attempt(candidate, attempt), encoding="utf-8")
        refined = sorted({attempt["refined_subgap"] for attempt in attempts if attempt.get("refined_subgap")})
        (out_dir / "refined_subgaps.json").write_text(json.dumps({"candidate_id": candidate["candidate_id"], "refined_subgaps": refined}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out_dir / "proof_attempt_summary.md").write_text(render_summary(candidate, attempts, refined), encoding="utf-8")
        summaries.append({"candidate_id": candidate["candidate_id"], "attempt_count": len(attempts), "refined_subgaps": refined})
    payload = {"campaign": campaign, "candidate_count": len(candidates), "proof_attempts": summaries}
    (ATTEMPT_ROOT / f"{campaign}_strategy_summary.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def render_attempt(candidate: dict[str, Any], attempt: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {attempt['strategy']} Attempt: {candidate['candidate_id']}",
            "",
            f"Status: `{attempt['status']}`",
            f"Failed step: `{attempt['failed_step']}`",
            f"Refined subgap: `{attempt['refined_subgap']}`",
            "",
            "This is a recorded proof strategy attempt, not a proof promotion.",
        ]
    ) + "\n"


def render_summary(candidate: dict[str, Any], attempts: list[dict[str, Any]], refined: list[str]) -> str:
    lines = [f"# Proof Attempt Summary: {candidate['candidate_id']}", "", "| Strategy | Status | Failed step |", "|---|---|---|"]
    for attempt in attempts:
        lines.append(f"| `{attempt['strategy']}` | `{attempt['status']}` | {attempt['failed_step']} |")
    lines.extend(["", "## Refined Subgaps", ""])
    lines.extend(f"- `{item}`" for item in refined)
    return "\n".join(lines) + "\n"
