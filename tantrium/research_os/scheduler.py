"""Campaign scheduler and aliases."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Campaign:
    public_name: str
    campaign_id: str
    result_dir: str
    blocker: str


CAMPAIGNS: dict[str, Campaign] = {
    "subresultant_recurrence": Campaign(
        "subresultant_recurrence",
        "subresultant_recurrence",
        "subresultant_recurrence",
        "MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR",
    ),
    "lah": Campaign("lah", "lah_gate_ab_generalization", "lah_gate_ab", "GENERAL_J_STAIRCASE_QUOTIENT_PROOF"),
    "lah_gate_ab": Campaign("lah_gate_ab", "lah_gate_ab_generalization", "lah_gate_ab", "GENERAL_J_STAIRCASE_QUOTIENT_PROOF"),
    "coefficient_frontier": Campaign(
        "coefficient_frontier",
        "coefficient_frontier_parametric_lift",
        "coefficient_frontier",
        "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
    ),
    "goldbach_minor_arc": Campaign(
        "goldbach_minor_arc",
        "goldbach_minor_arc_bound",
        "goldbach_minor_arc",
        "MINOR_ARC_UNCONDITIONAL_BOUND",
    ),
    "rh_formalization": Campaign(
        "rh_formalization",
        "rh_formalization_bootstrap",
        "rh_formalization",
        "EXTERNAL_FORMALIZATION_PENDING",
    ),
}

ORDER = ["subresultant_recurrence", "lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization"]


def resolve_campaign(name: str) -> Campaign:
    if name not in CAMPAIGNS:
        raise ValueError(f"unknown campaign: {name}")
    return CAMPAIGNS[name]


def expand_campaigns(name: str) -> list[Campaign]:
    if name == "all":
        return [resolve_campaign(item) for item in ORDER]
    return [resolve_campaign(name)]
