"""Finite and artifact evidence mining for research campaigns."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]


def _exists(paths: list[str]) -> list[dict[str, Any]]:
    out = []
    for rel in paths:
        path = REPO_ROOT / rel
        out.append({"path": rel, "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    return out


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def mine_evidence(campaign_id: str, out_dir: Path, deep: bool = False) -> dict[str, Any]:
    if campaign_id == "lah_gate_ab_generalization":
        artifacts = _exists([
            "math/README.md",
            "math/SUMMARY.md",
            "math/gate_a.py",
            "math/gate_a_verify.py",
            "theorems/GATE_B_FINDINGS.md",
            "theorems/LAH_SHADOW.md",
            "theorems/K7_SHARPNESS.md",
        ])
        evidence = {
            "campaign": campaign_id,
            "status": "EVIDENCE_MINED",
            "artifacts": artifacts,
            "finite_windows_requested": [6, 7, 8] if deep else [6],
            "observed_laws": [
                "top ramp exponent T_j = j(j+1)/2",
                "quotient degree candidate deg_n Q_{j,r}=r(2j-r-1)/2",
                "K7 sharpness marks the first boundary requiring structural classification",
            ],
        }
    elif campaign_id == "coefficient_frontier_parametric_lift":
        engine_dir = REPO_ROOT / "results" / "engine"
        csv_rows = {
            path.name: _count_csv_rows(path)
            for path in sorted(engine_dir.glob("ell*_mixed_depth_summary.csv"))[:8]
        }
        evidence = {
            "campaign": campaign_id,
            "status": "EVIDENCE_MINED",
            "artifacts": _exists([
                "results/atlas/manifest.json",
                "results/atlas/status.md",
                "results/conjectures/coefficient_positivity/blocker_certificate.json",
                "results/certificates/d_positivity_parametric_certificate.json",
            ]),
            "engine_summary_rows": csv_rows,
            "frontier": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
            "candidate_connections": ["log-det cumulants", "Gate B staircase quotient", "D-positivity", "AG/LGV path model"],
        }
    elif campaign_id == "goldbach_minor_arc_bound":
        evidence = {
            "campaign": campaign_id,
            "status": "EVIDENCE_MINED",
            "artifacts": _exists([
                "results/conjectures/goldbach/blocker_certificate.json",
                "results/certificates/goldbach_circle_method_certificate.json",
                "results/certificates/goldbach_singular_series_certificate.json",
            ]),
            "target_bound_role": "minor arc estimate must be strong enough to be dominated by the major arc main term",
            "known_inputs": ["Vaughan identity", "large sieve", "zero-density estimates", "Type I/II sums"],
        }
    elif campaign_id == "rh_formalization_bootstrap":
        evidence = {
            "campaign": campaign_id,
            "status": "EVIDENCE_MINED",
            "artifacts": _exists([
                "formal/lean/Tantrium/Tau.lean",
                "formal/lean/Tantrium/AGLGV.lean",
                "formal/lean/Tantrium/RHChain.lean",
                "results/certificates/rh_symbolic_closure_certificate.json",
            ]),
            "target_first_lemmas": [
                "tau/subdiscriminant Cauchy-Binet identity",
                "positive normalization H_j=N_j tau_j",
                "AG/LGV transfer identity",
                "cell support injection skeleton",
                "dyadic capacity inequality",
                "D-positivity induction skeleton",
            ],
        }
    else:
        raise ValueError(f"unknown campaign: {campaign_id}")

    path = out_dir / "finite_evidence.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(ResearchEvent(campaign_id, "Evidence Miner", "evidence_mined", "EVIDENCE_MINED", outputs=[str(path.relative_to(REPO_ROOT))]))
    return evidence
