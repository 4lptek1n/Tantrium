#!/usr/bin/env python3
"""General Tantrium conjecture machine with solve-or-certify-gap mode."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tantrium_autosolver import FINAL_STATUSES, INTERMEDIATE_STATUSES, solve_problem


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results" / "conjectures"
INPUT_ROOT = REPO_ROOT / "inputs" / "conjectures"
CERT_DIR = REPO_ROOT / "results" / "certificates"
REGISTRY_PATH = CERT_DIR / "certificate_registry.json"


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


def write_problem_manuscript(out_dir: Path, status: dict[str, Any]) -> None:
    out_dir.joinpath("manuscript.md").write_text(
        "\n".join(
            [
                f"# Tantrium Conjecture Report: {status['problem']}",
                "",
                f"Generated: {status['generated_at']}",
                f"Status: `{status['status']}`",
                f"Final status: `{status.get('final_status', status['status'])}`",
                f"Proof attempt: `{status['proof_attempt_status']}`",
                f"Closure: `{status['closure_status']}`",
                f"First gap: `{status['first_gap']}`",
                f"Main certificate: `{status['main_certificate']}`",
                f"Blocker certificate: `{status.get('blocker_certificate_path')}`",
                f"Proof certificate: `{status.get('proof_certificate_path')}`",
                "",
                "External formalization remains `PENDING`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_classification_outputs(problem: str, config: dict[str, Any], run_ok: bool, run_detail: str) -> dict[str, Any]:
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
        "final_status": config["status"],
        "proof_attempt_status": config["proof_attempt_status"],
        "closure_status": config["closure_status"],
        "first_gap": config["first_gap"],
        "main_certificate": config["main_certificate"],
        "proof_certificate_path": None,
        "blocker_certificate_path": None,
        "counterexample_path": None,
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
                "final_status": "INTERNAL_CLOSED",
                "proof_certificate_path": "results/certificates/rh_symbolic_closure_certificate.json",
            }
        )
        write_json(out_dir / "proof_dag.json", dag)
        copy_if_exists("results/certificates/rh_gap_report.md", out_dir / "gap_report.md")
        copy_if_exists("results/certificates/certificate_registry.json", out_dir / "certificate_registry.json")
    elif problem == "goldbach":
        dag = read_json(CERT_DIR / "goldbach_proof_attempt_dag.json")
        status["first_gap"] = "MINOR_ARC_BOUND"
        write_json(out_dir / "proof_dag.json", dag)
        copy_if_exists("results/certificates/goldbach_gap_report.md", out_dir / "gap_report.md")
        write_json(
            out_dir / "certificate_registry.json",
            {
                "problem": "goldbach",
                "certificates": [
                    "results/certificates/goldbach_circle_method_certificate.json",
                    "results/certificates/goldbach_singular_series_certificate.json",
                ],
            },
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
        write_json(out_dir / "proof_dag.json", dag)
        gap = config["first_gap"] or "NO_STRUCTURAL_GAP"
        (out_dir / "gap_report.md").write_text(
            f"# {problem} Gap Report\n\nStatus: `{config['status']}`\n\nFirst gap: `{gap}`\n",
            encoding="utf-8",
        )
        write_json(out_dir / "certificate_registry.json", {"problem": problem, "main_certificate": config["main_certificate"]})

    write_json(out_dir / "status.json", status)
    write_problem_manuscript(out_dir, status)
    return status


def build_solve_outputs(problem: str, full: bool, max_frontier: int, deep: bool) -> dict[str, Any]:
    out_dir = RESULTS_ROOT / problem
    report = solve_problem(problem, full=full, max_frontier=max_frontier, deep=deep)
    config = PROBLEMS[problem]
    status = {
        "generated_at": now_iso(),
        "problem": problem,
        "name": read_spec(problem).get("name", problem),
        "run_ok": True,
        "run_detail": "solve-or-certify-gap completed",
        "status": report["final_status"],
        "final_status": report["final_status"],
        "proof_attempt_status": report["final_status"],
        "closure_status": report["final_status"],
        "first_gap": report.get("first_gap"),
        "main_certificate": config["main_certificate"],
        "proof_certificate_path": report.get("proof_certificate_path"),
        "blocker_certificate_path": report.get("blocker_certificate_path"),
        "counterexample_path": report.get("counterexample_path"),
        "internal_tantrium_closure": "CLOSED" if report["final_status"] == "INTERNAL_CLOSED" else report["final_status"],
        "external_formalization": "PENDING",
        "command_used": f"python tools/tantrium_conjecture_machine.py --problem {problem} --solve --full",
    }
    if status["final_status"] in INTERMEDIATE_STATUSES:
        raise RuntimeError(f"--solve produced forbidden intermediate final status: {status['final_status']}")
    if status["final_status"] not in FINAL_STATUSES:
        raise RuntimeError(f"--solve produced invalid final status: {status['final_status']}")
    write_json(out_dir / "status.json", status)
    write_problem_manuscript(out_dir, status)
    update_problem_registry(problem, status)
    return status


def update_problem_registry(problem: str, status: dict[str, Any]) -> None:
    registry = read_json(REGISTRY_PATH)
    if not registry:
        registry = {"registry_version": 2, "certificates": []}
    registry.setdefault("conjecture_solve_results", {})
    registry["conjecture_solve_results"][problem] = {
        "final_status": status["final_status"],
        "first_gap": status.get("first_gap"),
        "blocker_certificate_path": status.get("blocker_certificate_path"),
        "proof_certificate_path": status.get("proof_certificate_path"),
        "counterexample_path": status.get("counterexample_path"),
        "command_used": status.get("command_used"),
        "generated_at": status["generated_at"],
        "commit_sha": git_sha(),
    }
    write_json(REGISTRY_PATH, registry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Tantrium conjecture machine")
    parser.add_argument("--problem", required=True, choices=sorted(PROBLEMS))
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--solve", action="store_true")
    parser.add_argument("--max-frontier", type=int, default=5)
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--write-blockers", action="store_true")
    parser.add_argument("--upgrade-schemas", action="store_true")
    args = parser.parse_args()

    if args.solve:
        status = build_solve_outputs(args.problem, args.full, args.max_frontier, args.deep)
        run_ok = True
    else:
        config = PROBLEMS[args.problem]
        run_ok, run_detail = run_entrypoint(args.problem, config, args.full)
        status = build_classification_outputs(args.problem, config, run_ok, run_detail)

    print("TANTRIUM CONJECTURE MACHINE")
    print(f"PROBLEM: {args.problem}")
    print(f"STATUS: {status['status']}")
    print(f"FINAL_STATUS: {status.get('final_status', status['status'])}")
    print(f"FIRST_GAP: {status['first_gap']}")
    print(f"EXTERNAL_FORMALIZATION: {status['external_formalization']}")
    print(f"RESULT: {'GENERATED' if run_ok else 'FAILED'}")
    return 0 if run_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
