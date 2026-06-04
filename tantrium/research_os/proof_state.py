"""Status taxonomy for the Tantrium research OS."""
from __future__ import annotations

FINAL_MATH_STATUSES = {
    "PROVEN_BY_CERTIFICATE",
    "INTERNAL_CLOSED",
    "PROVEN_NEW_THEOREM",
    "RECURRENCE_CANDIDATE_FOUND",
    "RECURRENCE_VERIFIED_FINITE",
    "RECURRENCE_COUNTEREXAMPLE_FOUND",
    "COUNTEREXAMPLE_FOUND",
    "BLOCKED_BY_NAMED_GAP",
    "REFINED_SUBGAP",
    "NEEDS_HUMAN_REVIEW",
}

RESEARCH_STATUSES = {
    "EVIDENCE_MINED",
    "CANDIDATE_THEOREMS_GENERATED",
    "STRATEGIES_RANKED",
    "PROOF_ATTEMPTED",
    "CERTIFICATE_ATTEMPTED",
    "FORMALIZATION_SCAFFOLD_GENERATED",
    "COUNTEREXAMPLE_SEARCH_COMPLETED",
    "NEXT_SUBGAP_IDENTIFIED",
    "FORMALIZATION_BOOTSTRAP_READY",
}

FORBIDDEN_FINAL_STATUSES = {
    "CERTIFIED_SCHEMA",
    "ATLAS_DRIVEN",
    "VERIFIED_FINITE",
    "CONDITIONAL_GAP",
    "OPEN_GAP",
}


def assert_terminal_status(status: str) -> None:
    if status in FORBIDDEN_FINAL_STATUSES:
        raise RuntimeError(f"research OS ended with vague final status: {status}")
    if status not in FINAL_MATH_STATUSES and status != "FORMALIZATION_BOOTSTRAP_READY":
        raise RuntimeError(f"unknown terminal status: {status}")
