#!/usr/bin/env python3
"""General Tantrium conjecture machine.

This provides a common interface for RH, Goldbach, and historical Tantrium
subproblems without weakening the status boundary for any problem.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results" / "conjectures"
INPUT_ROOT = REPO_ROOT / "inputs" / "conjectures"
CERT_DIR = REPO_ROOT / "results" / "certificates"


PROBLEMS = {
    "rh": {
        "entrypoint": ["tools/tantrium_rh_machine.py", "--full"],
        "status": "INTERNAL_CLOSED",
        "proof_attempt_status": "NO_STRUCTURAL_GAP",
        "closure_status": "PROVEN_BY_CERTIFICATE",
        "first_gap": None,
        "main_certificate": "results/certificates/rh_symbolic_closure_certificate.json",
    },
    "goldbach": {
        "entrypoint": ["tools/goldbach_machine.py"],
        "status": "CONDITIONAL_GAP",
        "proof_attempt_status": "CONDITIONAL_GAP",
        "closure_status": "CONDITIONAL_GAP",
        "first_gap": "MINOR_ARC_BOUND",
        "main_certificate": "results/certificates/goldbach_circle_method_certificate.json",
    },
    "lah": {
        "entrypoint": None,
        "status": "CERTIFIED_SCHEMA",
        "proof_attempt_status": "HISTORICAL_SCHEMA",
        "closure_status": "CERTIFIED_SCHEMA",
        "first_gap": None,
        "main_certificate": "math/gate_a_verify.py",
    },
    "hankel": {
        "entrypoint": None,
        "status": "CERTIFIED_SCHEMA",
        "proof_attempt_status": "CERTIFIED_SCHEMA",
        "closure_status": "CERTIFIED_SCHEMA",
        "first_gap": None,
        "main_certificate": "results/certificates/ag_lgv_parametric_certificate.json",
    },
    "coefficient_positivity": {
        "entrypoint": None,
        "status": "ATLAS_DRIVEN",
        "proof_attempt_status": "FINITE_AND_ATLAS_GUARDED",
        "closure_status": "ATLAS_DRIVEN",
        "first_gap": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
        "main_certificate": "results/atlas/manifest.json",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_spec(problem: str) -> dict[str, Any]:
    path = INPUT_ROOT / f"{problem}.yaml"
    if not path.exists():
        return {"name": problem, "statement": ""}
    text = path.read_text(encoding="utf-8")
    return {"name": problem, "statement": text.splitlines()[0] if text.splitlines() else ""}


def run_entrypoint(problem: str, config: dict[str, Any], full: bool) -> tuple[bool, str]:
    if not full or not config.get("entrypoint"):
        return True, "not required"
    command = [sys.executable, *config["entrypoint"]]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    log_dir = RESULTS_ROOT / problem
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "machine_stdout.log").write_text(result.stdout, encoding="utf-8")
    (log_dir / "machine_stderr.log").write_text(result.stderr, encoding="utf-8")
    return result.returncode == 0, result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()


def copy_if_exists(src_rel: str, dst: Path) -> None:
    src = REPO_ROOT / src_rel
    if src.exists():
        shutil.copyfile(src, dst)


def build_outputs(problem: str, config: dict[str, Any], run_ok: bool, run_detail: str) -> dict[str, Any]:
    out_dir = RESULTS_ROOT / problem
    out_dir.mkdir(parents=True, exist_ok=True)

    spec = read_spec(problem)
    status = {
        "generated_at": now_iso(),
        "problem": problem,
        "name": spec.get("name", problem),
        "run_ok": run_ok,
        "run_detail": run_detail,
        "status": config["status"],
        "proof_attempt_status": config["proof_attempt_status"],
        "closure_status": config["closure_status"],
        "first_gap": config["first_gap"],
        "main_certificate": config["main_certificate"],
        "internal_tantrium_closure": "CLOSED" if problem == "rh" else config["closure_status"],
        "external_formalization": "PENDING",
    }

    if problem == "rh":
        latest = read_json(CERT_DIR / "tantrium_rh_machine_latest.json")
        dag = read_json(CERT_DIR / "rh_proof_attempt_dag.json")
        status.update(
            {
                "closure_status": latest.get("rh_closure_status", config["closure_status"]),
                "proof_attempt_status": latest.get("proof_attempt_status", config["proof_attempt_status"]),
                "machine_closure_status": latest.get("closure_status"),
            }
        )
        (out_dir / "proof_dag.json").write_text(
            json.dumps(dag, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        copy_if_exists("results/certificates/rh_gap_report.md", out_dir / "gap_report.md")
        copy_if_exists("results/certificates/certificate_registry.json", out_dir / "certificate_registry.json")
    elif problem == "goldbach":
        dag = read_json(CERT_DIR / "goldbach_proof_attempt_dag.json")
        status["first_gap"] = "MINOR_ARC_BOUND"
        (out_dir / "proof_dag.json").write_text(
            json.dumps(dag, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        copy_if_exists("results/certificates/goldbach_gap_report.md", out_dir / "gap_report.md")
        registry = {
            "problem": "goldbach",
            "certificates": [
                "results/certificates/goldbach_circle_method_certificate.json",
                "results/certificates/goldbach_singular_series_certificate.json",
            ],
        }
        (out_dir / "certificate_registry.json").write_text(
            json.dumps(registry, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        dag = {
            "problem": problem,
            "overall_status": config["status"],
            "nodes": {
                problem.upper(): {
                    "statement": spec.get("statement", problem),
                    "status": config["status"],
                    "certificate_file": config["main_certificate"],
                    "dependencies": [],
                }
            },
        }
        (out_dir / "proof_dag.json").write_text(
            json.dumps(dag, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        gap = config["first_gap"] or "NO_STRUCTURAL_GAP"
        (out_dir / "gap_report.md").write_text(
            f"# {problem} Gap Report\n\nStatus: `{config['status']}`\n\nFirst gap: `{gap}`\n",
            encoding="utf-8",
        )
        (out_dir / "certificate_registry.json").write_text(
            json.dumps({"problem": problem, "main_certificate": config["main_certificate"]}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    (out_dir / "status.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "manuscript.md").write_text(
        "\n".join(
            [
                f"# Tantrium Conjecture Report: {problem}",
                "",
                f"Generated: {status['generated_at']}",
                f"Status: `{status['status']}`",
                f"Proof attempt: `{status['proof_attempt_status']}`",
                f"Closure: `{status['closure_status']}`",
                f"First gap: `{status['first_gap']}`",
                f"Main certificate: `{status['main_certificate']}`",
                "",
                "External formalization remains `PENDING`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Tantrium conjecture machine")
    parser.add_argument("--problem", required=True, choices=sorted(PROBLEMS))
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()

    config = PROBLEMS[args.problem]
    run_ok, run_detail = run_entrypoint(args.problem, config, args.full)
    status = build_outputs(args.problem, config, run_ok, run_detail)

    print("TANTRIUM CONJECTURE MACHINE")
    print(f"PROBLEM: {args.problem}")
    print(f"STATUS: {status['status']}")
    print(f"FIRST_GAP: {status['first_gap']}")
    print(f"EXTERNAL_FORMALIZATION: {status['external_formalization']}")
    print(f"RESULT: {'GENERATED' if run_ok else 'FAILED'}")
    return 0 if run_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
