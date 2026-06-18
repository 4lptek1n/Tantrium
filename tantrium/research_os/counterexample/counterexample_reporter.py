"""Counterexample engine reporter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .false_conjecture_benchmark import false_staircase_benchmark
from .parameter_search import search_window
from .polynomial_sign_search import sign_search_normal_qjr
from .sharpness_detector import detect_k7_sharpness

REPO_ROOT = Path(__file__).resolve().parents[3]
COUNTEREXAMPLE_ROOT = REPO_ROOT / "results" / "research_os" / "counterexamples"
SHARPNESS_ROOT = REPO_ROOT / "results" / "research_os" / "sharpness"


def run_counterexample_engine(campaign: str = "subresultant_recurrence", deep: bool = False) -> dict[str, Any]:
    COUNTEREXAMPLE_ROOT.mkdir(parents=True, exist_ok=True)
    SHARPNESS_ROOT.mkdir(parents=True, exist_ok=True)
    window = search_window(deep=deep)
    qjr_search = sign_search_normal_qjr()
    false_case = false_staircase_benchmark()
    sharpness = detect_k7_sharpness()
    report = {
        "campaign": campaign,
        "search_window": window,
        "real_candidate_search": qjr_search,
        "false_benchmark": false_case,
        "sharpness": sharpness,
        "status": "SHARPNESS_BOUNDARY_DETECTED",
        "counterexample_result": "NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW",
        "refined_subgap": sharpness["refined_subgap"],
    }
    (COUNTEREXAMPLE_ROOT / f"{campaign}_counterexample_search.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (COUNTEREXAMPLE_ROOT / "false_staircase_counterexample.json").write_text(json.dumps(false_case, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (SHARPNESS_ROOT / "k7_sharpness_boundary.json").write_text(json.dumps(sharpness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_k7_doc(sharpness)
    return report


def write_k7_doc(sharpness: dict[str, str]) -> None:
    (REPO_ROOT / "docs" / "K7_SHARPNESS_STRUCTURE_ANALYSIS.md").write_text(
        "\n".join(
            [
                "# K7 Sharpness Structure Analysis",
                "",
                f"Status: `{sharpness['status']}`",
                f"Boundary: `{sharpness['boundary']}`",
                "",
                sharpness["interpretation"],
                "",
                f"Refined subgap: `{sharpness['refined_subgap']}`.",
                "",
                "No general positivity theorem is promoted past this boundary without a new classification lemma.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
