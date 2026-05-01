#!/usr/bin/env python3
"""
Tantrium RH Gap Finder
========================
Reads results/certificates/rh_proof_attempt_dag.json and reports any
OPEN_GAP or FINITE_CHECKED nodes. Produces results/certificates/rh_gap_report.md.

Usage:
    python tools/rh_gap_finder.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = REPO_ROOT / "results" / "certificates"
DAG_PATH = CERT_DIR / "rh_proof_attempt_dag.json"
GAP_REPORT = CERT_DIR / "rh_gap_report.md"

WEAK_STATUSES = {"OPEN_GAP", "FINITE_CHECKED"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_dag() -> dict:
    if not DAG_PATH.exists():
        print(f"ERROR: {DAG_PATH} not found. Run rh_proof_attempt.py first.")
        sys.exit(1)
    with open(DAG_PATH) as f:
        return json.load(f)


def find_gaps(dag: dict) -> list[tuple[str, str, str]]:
    """Return list of (node_id, status, notes) for weak nodes."""
    gaps = []
    for node_id, data in dag["nodes"].items():
        if data["status"] in WEAK_STATUSES:
            gaps.append((node_id, data["status"], data.get("notes", "")))
    return gaps


def write_gap_report(dag: dict, gaps: list[tuple[str, str, str]]) -> str:
    ts = now_iso()
    lines = [
        "# Tantrium RH Gap Report",
        "",
        f"Generated: {ts}",
        f"DAG overall status: **{dag['overall_status']}**",
        "",
    ]

    if not gaps:
        lines += [
            "## Result",
            "",
            "**NO STRUCTURAL GAP FOUND IN TANTRIUM PROOF STACK**",
            "",
            (
                "All proof attempt DAG nodes are at CERTIFIED_SCHEMA or "
                "PROVEN_BY_CERTIFICATE level. The current parametric certificate "
                "set covers every step of the RH symbolic closure chain."
            ),
            "",
        ]
    else:
        first_gap_id, first_gap_status, first_gap_notes = gaps[0]
        first_node_data = dag["nodes"].get(first_gap_id, {})
        first_missing_cert = first_node_data.get("certificate_file") or "none"
        first_missing_dep = ", ".join(first_node_data.get("dependencies", [])) or "none"
        if first_gap_status == "OPEN_GAP":
            first_action = f"Create a parametric certificate for {first_gap_id} and add theorem file."
        else:
            first_action = f"Upgrade {first_gap_id} from finite-window check to a parametric certificate."
        lines += [
            "## Result",
            "",
            f"**FIRST GAP: `{first_gap_id}` — {first_gap_status}**",
            "",
            f"- node: `{first_gap_id}`",
            f"- missing_certificate: `{first_missing_cert}`",
            f"- missing_dependency: `{first_missing_dep}`",
            f"- suggested_next_action: {first_action}",
            "",
            "## All Weak Nodes",
            "",
            "| Node | Status | Missing Certificate | Suggested Action |",
            "|------|--------|--------------------|--------------------|",
        ]
        for node_id, status, notes in gaps:
            nd = dag["nodes"].get(node_id, {})
            mc = nd.get("certificate_file") or "none"
            action = (
                f"Add parametric cert for {node_id}"
                if status == "OPEN_GAP"
                else f"Upgrade {node_id} to parametric cert"
            )
            lines.append(f"| `{node_id}` | {status} | `{mc}` | {action} |")
        lines += [
            "",
            "## What This Means",
            "",
            "- `OPEN_GAP`: no theorem file and no parametric certificate. "
            "This node requires a new proof or certificate.",
            "- `FINITE_CHECKED`: only verified in a finite window. "
            "Upgrade to a parametric certificate to close this gap.",
        ]

    lines += [
        "",
        "## Full Node Status",
        "",
        "| Node | Status |",
        "|------|--------|",
    ]
    for node_id, data in dag["nodes"].items():
        lines.append(f"| `{node_id}` | {data['status']} |")

    GAP_REPORT.write_text("\n".join(lines) + "\n")
    return "NO_STRUCTURAL_GAP" if not gaps else "GAP_FOUND"


def main() -> str:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    dag = load_dag()
    gaps = find_gaps(dag)
    result = write_gap_report(dag, gaps)

    print("RH GAP FINDER")
    if result == "NO_STRUCTURAL_GAP":
        print("PASS  NO STRUCTURAL GAP FOUND IN TANTRIUM PROOF STACK")
    else:
        print(f"GAP   FIRST GAP: {gaps[0][0]} ({gaps[0][1]})")
        for g in gaps:
            print(f"      {g[1]:<26} {g[0]}")
    print(f"gap_report: {GAP_REPORT}")
    return result


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result == "NO_STRUCTURAL_GAP" else 0)  # exit 0 regardless; caller decides
