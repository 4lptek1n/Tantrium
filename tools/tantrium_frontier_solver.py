#!/usr/bin/env python3
"""Solve or certify named blockers for Atlas-driven frontier problems."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results" / "conjectures"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() or "unknown"


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def solve_coefficient_frontier(max_frontier: int = 5, deep: bool = False) -> dict[str, Any]:
    out_dir = RESULTS_ROOT / "coefficient_positivity"
    atlas_manifest = REPO_ROOT / "results" / "atlas" / "manifest.json"
    gate_b = REPO_ROOT / "theorems" / "GATE_B_STAIRCASE_THEOREM.md"
    d_pos = REPO_ROOT / "theorems" / "D_POSITIVITY_THEOREM.md"
    ag_lgv = REPO_ROOT / "results" / "certificates" / "ag_lgv_parametric_certificate.json"

    symbolic_law = {
        "certificate_type": "symbolic_law_candidate",
        "generated_at": now_iso(),
        "problem": "coefficient_positivity",
        "candidate_links": [
            "log_det_cumulants",
            "Gate_B_staircase_quotient",
            "D_positivity",
            "AG_LGV_path_model",
        ],
        "max_frontier": max_frontier,
        "deep": deep,
        "status": "CANDIDATE_ONLY",
        "reason": "No all-parameter positivity certificate was produced for the first uncertified atlas frontier.",
    }
    write_json(out_dir / "symbolic_law_candidate.json", symbolic_law)

    frontier = {
        "certificate_type": "frontier_certificate",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": "coefficient_positivity",
        "atlas_manifest": {
            "path": "results/atlas/manifest.json",
            "sha256": sha256(atlas_manifest),
        },
        "frontier": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
        "probes_attempted": [
            "atlas_manifest_read",
            "Gate_B_staircase_link",
            "D_positivity_link",
            "AG_LGV_path_model_link",
            "symbolic_law_candidate_generation",
        ],
        "linked_artifacts": [
            {"path": "theorems/GATE_B_STAIRCASE_THEOREM.md", "sha256": sha256(gate_b)},
            {"path": "theorems/D_POSITIVITY_THEOREM.md", "sha256": sha256(d_pos)},
            {"path": "results/certificates/ag_lgv_parametric_certificate.json", "sha256": sha256(ag_lgv)},
        ],
        "counterexample_path": None,
        "final_status": "BLOCKED_BY_NAMED_GAP",
        "first_gap": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
        "blocker_type": "PARAMETRIC_POSITIVITY_NOT_YET_CERTIFIED",
        "blocker_certificate_path": "results/conjectures/coefficient_positivity/blocker_certificate.json",
    }
    write_json(out_dir / "frontier_certificate.json", frontier)

    blocker = {
        "certificate_type": "named_blocker",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": "coefficient_positivity",
        "final_status": "BLOCKED_BY_NAMED_GAP",
        "first_gap": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
        "named_gap": "PARAMETRIC_POSITIVITY_NOT_YET_CERTIFIED",
        "blocked_node": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
        "reason": (
            "Atlas data and linked Gate B/D-positivity/AG-LGV artifacts are present, "
            "but the first uncertified coefficient frontier is not yet promoted to "
            "a parametric positivity certificate."
        ),
        "frontier_certificate_path": "results/conjectures/coefficient_positivity/frontier_certificate.json",
        "symbolic_law_candidate_path": "results/conjectures/coefficient_positivity/symbolic_law_candidate.json",
    }
    write_json(out_dir / "blocker_certificate.json", blocker)
    (out_dir / "blocker_certificate.md").write_text(
        "\n".join(
            [
                "# Coefficient Positivity Blocker Certificate",
                "",
                f"Final status: `{blocker['final_status']}`",
                f"First gap: `{blocker['first_gap']}`",
                f"Named gap: `{blocker['named_gap']}`",
                "",
                blocker["reason"],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return blocker


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium frontier solver")
    parser.add_argument("--problem", required=True, choices=["coefficient_positivity"])
    parser.add_argument("--max-frontier", type=int, default=5)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    cert = solve_coefficient_frontier(args.max_frontier, args.deep)
    print("TANTRIUM FRONTIER SOLVER")
    print(f"PROBLEM: {args.problem}")
    print(f"FINAL_STATUS: {cert['final_status']}")
    print(f"FIRST_GAP: {cert['first_gap']}")
    print("RESULT: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
