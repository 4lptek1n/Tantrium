"""Theorem candidate IR."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = REPO_ROOT / "results" / "research_os" / "candidates"


@dataclass
class TheoremCandidate:
    candidate_id: str
    statement_latex: str
    formal_variables: list[str]
    hypotheses: list[str]
    conclusion: str
    evidence: list[str] = field(default_factory=list)
    counterexample_search: dict[str, Any] = field(default_factory=dict)
    proof_strategies: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risk: str = "medium"
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write_candidates(campaign_id: str, candidates: list[dict[str, Any]]) -> Path:
    path = CANDIDATE_DIR / f"{campaign_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"campaign": campaign_id, "candidates": candidates}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
