#!/usr/bin/env python3
"""Central Tantrium solve-or-certify-gap loop."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tantrium_frontier_solver import solve_coefficient_frontier
from tantrium_gap_certifier import create_blocker
from tantrium_schema_lifter import lift_schema


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results" / "conjectures"
INPUT_ROOT = REPO_ROOT / "inputs" / "conjectures"
CERT_DIR = REPO_ROOT / "results" / "certificates"
GRAPH_PATH = REPO_ROOT / "tantrium" / "theorem_graph" / "theorem_graph.yaml"
REGISTRY_PATH = CERT_DIR / "certificate_registry.json"

FINAL_STATUSES = {
    "INTERNAL_CLOSED",
    "PROVEN_BY_CERTIFICATE",
    "COUNTEREXAMPLE_FOUND",
    "BLOCKED_BY_NAMED_GAP",
}
INTERMEDIATE_STATUSES = {
    "CERTIFIED_SCHEMA",
    "ATLAS_DRIVEN",
    "VERIFIED_FINITE",
    "CONDITIONAL_GAP",
    "OPEN_GAP",
}


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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# Tantrium Autosolver Report: {report['problem']}",
        "",
        f"Generated: {report['generated_at']}",
        f"Final status: `{report['final_status']}`",
        f"First gap: `{report['first_gap']}`",
        f"Proof certificate: `{report.get('proof_certificate_path')}`",
        f"Blocker certificate: `{report.get('blocker_certificate_path')}`",
        f"Counterexample: `{report.get('counterexample_path')}`",
        "",
        "## Strategies",
        "",
    ]
    for step in report["strategies"]:
        lines.append(f"- `{step['name']}`: `{step['status']}`")
    lines.extend(["", "## Notes", ""])
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_command(command: list[str], out_dir: Path, name: str) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (out_dir / f"{name}.stderr.log").write_text(result.stderr, encoding="utf-8")
    detail = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()
    return result.returncode == 0, detail


def read_problem_spec(problem: str) -> dict[str, Any]:
    path = INPUT_ROOT / f"{problem}.yaml"
    return {
        "path": str(path.relative_to(REPO_ROOT)) if path.exists() else None,
        "exists": path.exists(),
        "raw": path.read_text(encoding="utf-8") if path.exists() else "",
    }


def base_report(problem: str) -> dict[str, Any]:
    return {
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": problem,
        "problem_spec": read_problem_spec(problem),
        "theorem_graph_loaded": GRAPH_PATH.exists(),
        "certificate_registry_loaded": REGISTRY_PATH.exists(),
        "strategies": [],
        "notes": [],
        "final_status": "OPEN_GAP",
        "first_gap": None,
        "proof_certificate_path": None,
        "blocker_certificate_path": None,
        "counterexample_path": None,
        "command_used": f"python tools/tantrium_autosolver.py --problem {problem}",
    }


def solve_rh(report: dict[str, Any], full: bool) -> dict[str, Any]:
    out_dir = RESULTS_ROOT / "rh"
    if full:
        ok, detail = run_command([sys.executable, "tools/tantrium_rh_machine.py", "--full"], out_dir, "autosolver_rh_machine")
        report["strategies"].append({"name": "rh_machine_full", "status": "PASS" if ok else "FAIL", "detail": detail})
        if not ok:
            report["final_status"] = "BLOCKED_BY_NAMED_GAP"
            report["first_gap"] = "RH_MACHINE_FULL_RUN_FAILED"
            blocker = create_blocker("rh", "RH_MACHINE_FULL_RUN_FAILED", detail)
            report["blocker_certificate_path"] = "results/conjectures/rh/blocker_certificate.json"
            report["notes"].append(blocker["reason"])
            return report
    latest = read_json(CERT_DIR / "tantrium_rh_machine_latest.json")
    if (
        latest.get("closure_status") == "PASS"
        and latest.get("proof_attempt_status") == "NO_STRUCTURAL_GAP"
        and latest.get("rh_closure_status") == "PROVEN_BY_CERTIFICATE"
    ):
        report["final_status"] = "INTERNAL_CLOSED"
        report["proof_certificate_path"] = "results/certificates/rh_symbolic_closure_certificate.json"
        report["notes"].append("RH remains internally closed by Tantrium certificate stack.")
    else:
        report["final_status"] = "BLOCKED_BY_NAMED_GAP"
        report["first_gap"] = "RH_CERTIFICATE_STATUS_MISMATCH"
        create_blocker("rh", "RH_CERTIFICATE_STATUS_MISMATCH", "RH latest machine status does not match expected closure fields.")
        report["blocker_certificate_path"] = "results/conjectures/rh/blocker_certificate.json"
    return report


def solve_goldbach(report: dict[str, Any], full: bool) -> dict[str, Any]:
    out_dir = RESULTS_ROOT / "goldbach"
    if full:
        ok, detail = run_command([sys.executable, "tools/goldbach_machine.py"], out_dir, "autosolver_goldbach_machine")
        report["strategies"].append({"name": "goldbach_machine", "status": "PASS" if ok else "FAIL", "detail": detail})
    blocker = create_blocker("goldbach")
    report["final_status"] = "BLOCKED_BY_NAMED_GAP"
    report["first_gap"] = blocker["first_gap"]
    report["blocker_certificate_path"] = "results/conjectures/goldbach/blocker_certificate.json"
    report["notes"].append(blocker["reason"])
    return report


def solve_lah(report: dict[str, Any]) -> dict[str, Any]:
    cert = lift_schema("lah")
    report["strategies"].append({"name": "schema_lifter_lah", "status": cert["final_status"], "detail": cert["reason"]})
    report["final_status"] = cert["final_status"]
    report["first_gap"] = cert.get("first_gap")
    report["blocker_certificate_path"] = cert.get("blocker_certificate_path")
    report["notes"].append(cert["reason"])
    return report


def solve_hankel(report: dict[str, Any]) -> dict[str, Any]:
    cert = lift_schema("hankel")
    report["strategies"].append({"name": "schema_lifter_hankel", "status": cert["final_status"], "detail": cert["reason"]})
    report["final_status"] = cert["final_status"]
    report["first_gap"] = cert.get("first_gap")
    report["proof_certificate_path"] = cert.get("proof_certificate_path")
    report["notes"].append(cert["reason"])
    return report


def solve_coefficient_positivity(report: dict[str, Any], max_frontier: int, deep: bool) -> dict[str, Any]:
    cert = solve_coefficient_frontier(max_frontier=max_frontier, deep=deep)
    report["strategies"].append(
        {
            "name": "frontier_solver_coefficient_positivity",
            "status": cert["final_status"],
            "detail": cert["reason"],
        }
    )
    report["final_status"] = cert["final_status"]
    report["first_gap"] = cert["first_gap"]
    report["blocker_certificate_path"] = "results/conjectures/coefficient_positivity/blocker_certificate.json"
    report["notes"].append(cert["reason"])
    return report


def solve_problem(problem: str, full: bool = False, max_frontier: int = 5, deep: bool = False) -> dict[str, Any]:
    report = base_report(problem)
    if problem == "rh":
        report = solve_rh(report, full)
    elif problem == "goldbach":
        report = solve_goldbach(report, full)
    elif problem == "lah":
        report = solve_lah(report)
    elif problem == "hankel":
        report = solve_hankel(report)
    elif problem == "coefficient_positivity":
        report = solve_coefficient_positivity(report, max_frontier=max_frontier, deep=deep)
    else:
        raise ValueError(f"Unsupported problem: {problem}")

    if report["final_status"] in INTERMEDIATE_STATUSES:
        raise RuntimeError(f"solve mode ended with intermediate status: {report['final_status']}")
    if report["final_status"] not in FINAL_STATUSES:
        raise RuntimeError(f"solve mode ended with invalid final status: {report['final_status']}")

    out_dir = RESULTS_ROOT / problem
    write_json(out_dir / "solve_report.json", report)
    write_md(out_dir / "solve_report.md", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium autonomous proof solver")
    parser.add_argument("--problem", required=True, choices=["rh", "goldbach", "lah", "hankel", "coefficient_positivity"])
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--max-frontier", type=int, default=5)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    report = solve_problem(args.problem, full=args.full, max_frontier=args.max_frontier, deep=args.deep)
    print("TANTRIUM AUTOSOLVER")
    print(f"PROBLEM: {args.problem}")
    print(f"FINAL_STATUS: {report['final_status']}")
    print(f"FIRST_GAP: {report['first_gap']}")
    print("RESULT: SOLVED_OR_CERTIFIED_GAP")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
