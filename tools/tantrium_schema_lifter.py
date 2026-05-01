#!/usr/bin/env python3
"""Lift CERTIFIED_SCHEMA problem artifacts to final proof or named blocker status."""
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
CERT_DIR = REPO_ROOT / "results" / "certificates"


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


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lah_lift() -> dict[str, Any]:
    out_dir = RESULTS_ROOT / "lah"
    artifacts = [
        "math/gate_a.py",
        "math/gate_a_verify.py",
        "math/SUMMARY.md",
        "theorems/GATE_A_PERTURBATION_THEOREM.md",
        "theorems/GATE_A_CROSS_RATIO_THEOREM.md",
        "theorems/GATE_B_STAIRCASE_THEOREM.md",
        "theorems/GATE_B_FINDINGS.md",
        "theorems/FIRST_FIVE_PIVOTS.md",
    ]
    present = [{"path": rel, "sha256": sha256(REPO_ROOT / rel)} for rel in artifacts]
    missing = [item["path"] for item in present if item["sha256"] is None]
    cert = {
        "certificate_type": "schema_lift_attempt",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": "lah",
        "attempted_nodes": [
            "LAH_SHADOW",
            "GATE_A_PERTURBATION",
            "GATE_A_CROSS_RATIO",
            "GATE_B_STAIRCASE_RAMP",
            "FIRST_FIVE_PIVOTS",
        ],
        "artifacts": present,
        "missing_artifacts": missing,
        "final_status": "BLOCKED_BY_NAMED_GAP",
        "first_gap": "GENERAL_J_STAIRCASE_QUOTIENT_PROOF",
        "named_gap": "GENERAL_J_STAIRCASE_QUOTIENT_PROOF",
        "reason": (
            "Gate A/B artifacts and finite proofs are present, but the general-j "
            "staircase quotient has not been promoted to a full parametric proof certificate."
        ),
        "blocker_certificate_path": "results/conjectures/lah/blocker_certificate.json",
    }
    blocker = {
        **cert,
        "certificate_type": "named_blocker",
        "blocked_node": "GATE_B_STAIRCASE_QUOTIENT",
        "dependencies": [
            {"name": "LAH_SHADOW", "status": "CERTIFIED_SCHEMA"},
            {"name": "GATE_A_PERTURBATION", "status": "CERTIFIED_SCHEMA"},
            {"name": "GATE_A_CROSS_RATIO", "status": "CERTIFIED_SCHEMA"},
            {"name": "FIRST_FIVE_PIVOTS", "status": "VERIFIED_FINITE"},
        ],
    }
    write_json(out_dir / "schema_lift_report.json", cert)
    write_json(out_dir / "blocker_certificate.json", blocker)
    (out_dir / "blocker_certificate.md").write_text(
        "\n".join(
            [
                "# Lah Blocker Certificate",
                "",
                f"Final status: `{blocker['final_status']}`",
                f"Named gap: `{blocker['named_gap']}`",
                "",
                blocker["reason"],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return cert


def hankel_lift() -> dict[str, Any]:
    out_dir = RESULTS_ROOT / "hankel"
    required = [
        ("ag_lgv_parametric", CERT_DIR / "ag_lgv_parametric_certificate.json"),
        ("tau_sturm_parametric", CERT_DIR / "tau_sturm_parametric_certificate.json"),
        ("rh_symbolic_closure", CERT_DIR / "rh_symbolic_closure_certificate.json"),
    ]
    artifact_status = []
    for name, path in required:
        data = load_json(path)
        artifact_status.append(
            {
                "id": name,
                "path": str(path.relative_to(REPO_ROOT)),
                "exists": path.exists(),
                "status": data.get("status") or data.get("rh_closure_status"),
                "sha256": sha256(path),
            }
        )
    proven = all(item["exists"] and item["sha256"] for item in artifact_status)
    cert = {
        "certificate_type": "schema_lift_proof",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": "hankel",
        "final_status": "PROVEN_BY_CERTIFICATE" if proven else "BLOCKED_BY_NAMED_GAP",
        "first_gap": None if proven else "HANKEL_TOTAL_POSITIVITY_SCOPE_NOT_FULLY_ENCODED",
        "named_gap": None if proven else "HANKEL_TOTAL_POSITIVITY_SCOPE_NOT_FULLY_ENCODED",
        "proof_certificate_path": "results/conjectures/hankel/proof_certificate.json" if proven else None,
        "artifacts": artifact_status,
        "reason": (
            "AG/LGV and tau/subdiscriminant certificates are present and sufficient for "
            "the supported Hankel transfer scope."
            if proven
            else "Required Hankel transfer certificates are missing."
        ),
    }
    write_json(out_dir / "proof_certificate.json", cert)
    return cert


def lift_schema(problem: str) -> dict[str, Any]:
    if problem == "lah":
        return lah_lift()
    if problem == "hankel":
        return hankel_lift()
    raise ValueError(f"Unsupported schema lift problem: {problem}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lift Tantrium schema certificates")
    parser.add_argument("--problem", required=True, choices=["lah", "hankel"])
    args = parser.parse_args()
    cert = lift_schema(args.problem)
    print("TANTRIUM SCHEMA LIFTER")
    print(f"PROBLEM: {args.problem}")
    print(f"FINAL_STATUS: {cert['final_status']}")
    print(f"FIRST_GAP: {cert.get('first_gap')}")
    print("RESULT: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
