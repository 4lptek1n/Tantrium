#!/usr/bin/env python3
"""Generate the Tantrium artifact manifest.

This tool is intentionally separate from the independent verifier.  It is the
seal step: it records the current repository, platform, command, and SHA256
digests for the proof-machine artifacts that must be independently auditable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = REPO_ROOT / "results" / "certificates"
MANIFEST_JSON = CERT_DIR / "artifact_manifest.json"
MANIFEST_MD = CERT_DIR / "artifact_manifest.md"


ARTIFACTS: list[dict[str, str | None]] = [
    {"path": "README.md", "role": "overview", "theorem_node": None, "certificate_id": None},
    {"path": "TIMELINE.md", "role": "history", "theorem_node": None, "certificate_id": None},
    {"path": "REPO_MAP.md", "role": "repository_map", "theorem_node": None, "certificate_id": None},
    {
        "path": "paper/TANTRIUM_RH_PROOF_v1.md",
        "role": "manuscript_v1",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": None,
    },
    {
        "path": "docs/TANTRIUM_INTERNAL_CLOSURE_STATUS.md",
        "role": "status_boundary",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": None,
    },
    {
        "path": "docs/DYADIC_TRANSPORT_THEOREM.md",
        "role": "theorem_document",
        "theorem_node": "DYADIC_TRANSPORT",
        "certificate_id": "d_positivity_parametric",
    },
    {
        "path": "docs/TANTRIUM_FINAL_MANUSCRIPT.md",
        "role": "manuscript",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": None,
    },
    {
        "path": "docs/TANTRIUM_CLOSURE_RESULT.md",
        "role": "closure_result",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": "rh_symbolic_closure",
    },
    {
        "path": "theorems/D_POSITIVITY_THEOREM.md",
        "role": "theorem_document",
        "theorem_node": "D_POSITIVITY",
        "certificate_id": "d_positivity_parametric",
    },
    {
        "path": "theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md",
        "role": "theorem_document",
        "theorem_node": "CELL_SUPPORT_POSITIVITY",
        "certificate_id": "d_positivity_parametric",
    },
    {
        "path": "theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md",
        "role": "theorem_document",
        "theorem_node": "AG_LGV_TRANSFER",
        "certificate_id": "ag_lgv_parametric",
    },
    {
        "path": "theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md",
        "role": "theorem_document",
        "theorem_node": "TAU_SUBDISCRIMINANT",
        "certificate_id": "tau_sturm_parametric",
    },
    {
        "path": "theorems/GATE_B_FINDINGS.md",
        "role": "historical_theorem_document",
        "theorem_node": "GATE_B_STAIRCASE_RAMP",
        "certificate_id": None,
    },
    {"path": "math/README.md", "role": "historical_math", "theorem_node": "LAH_SHADOW", "certificate_id": None},
    {"path": "math/SUMMARY.md", "role": "historical_math", "theorem_node": "GATE_A_PERTURBATION", "certificate_id": None},
    {"path": "math/gate_a.py", "role": "historical_executable", "theorem_node": "GATE_A_PERTURBATION", "certificate_id": None},
    {"path": "math/gate_a_verify.py", "role": "historical_executable", "theorem_node": "GATE_A_CROSS_RATIO", "certificate_id": None},
    {
        "path": "results/certificates/certificate_registry.json",
        "role": "certificate_registry",
        "theorem_node": None,
        "certificate_id": None,
    },
    {
        "path": "results/certificates/rh_symbolic_closure_certificate.json",
        "role": "closure_certificate",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": "rh_symbolic_closure",
    },
    {
        "path": "results/certificates/rh_proof_attempt_dag.json",
        "role": "proof_attempt_dag",
        "theorem_node": "RH_PROOF_ATTEMPT",
        "certificate_id": "rh_proof_attempt_dag",
    },
    {
        "path": "results/certificates/rh_gap_report.md",
        "role": "gap_report",
        "theorem_node": "RH_GAP_FINDER",
        "certificate_id": None,
    },
    {
        "path": "results/certificates/tantrium_rh_machine_latest.json",
        "role": "latest_machine_run",
        "theorem_node": "RH_CLOSURE",
        "certificate_id": None,
    },
    {
        "path": "results/certificates/independent_verifier_report.json",
        "role": "independent_verifier_report",
        "theorem_node": None,
        "certificate_id": None,
    },
    {
        "path": "results/atlas/manifest.json",
        "role": "atlas_manifest",
        "theorem_node": None,
        "certificate_id": None,
    },
    {
        "path": "results/atlas/status.md",
        "role": "atlas_status",
        "theorem_node": None,
        "certificate_id": None,
    },
    {
        "path": "tantrium/theorem_graph/theorem_graph.yaml",
        "role": "theorem_graph",
        "theorem_node": None,
        "certificate_id": None,
    },
    {
        "path": "results/certificates/goldbach_proof_attempt_dag.json",
        "role": "control_problem_dag",
        "theorem_node": "GOLDBACH_CONTROL",
        "certificate_id": None,
    },
    {
        "path": "results/certificates/goldbach_gap_report.md",
        "role": "control_problem_gap_report",
        "theorem_node": "GOLDBACH_CONTROL",
        "certificate_id": None,
    },
    {
        "path": "results/certificates/goldbach_circle_method_certificate.json",
        "role": "control_problem_certificate",
        "theorem_node": "GOLDBACH_MAJOR_ARC",
        "certificate_id": "goldbach_circle_method",
    },
    {
        "path": "results/certificates/goldbach_singular_series_certificate.json",
        "role": "control_problem_certificate",
        "theorem_node": "GOLDBACH_SINGULAR_SERIES",
        "certificate_id": "goldbach_singular_series",
    },
    {"path": "tools/tantrium_autosolver.py", "role": "autosolver", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_frontier_solver.py", "role": "frontier_solver", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_schema_lifter.py", "role": "schema_lifter", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_gap_certifier.py", "role": "gap_certifier", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_conjecture_machine.py", "role": "solve_or_certify_gap_machine", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_research_os.py", "role": "research_os_entrypoint", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_research_loop.py", "role": "research_os_loop", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_research_evaluator.py", "role": "research_os_evaluator", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_theorem_synthesizer.py", "role": "research_os_agent_tool", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_strategy_engine.py", "role": "research_os_agent_tool", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_counterexample_hunter.py", "role": "research_os_agent_tool", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_certificate_builder.py", "role": "research_os_agent_tool", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_formalization_bridge.py", "role": "research_os_agent_tool", "theorem_node": None, "certificate_id": None},
    {"path": "tools/tantrium_subresultant_recurrence_miner.py", "role": "research_os_v2_recurrence_miner", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_qjr_extractor.py", "role": "research_os_v2_qjr_extractor", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_recurrence_verifier.py", "role": "research_os_v2_recurrence_verifier", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_theorem_factory.py", "role": "research_os_v2_theorem_factory", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_proof_strategy_engine.py", "role": "research_os_v2_strategy_engine", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_counterexample_engine.py", "role": "research_os_v2_counterexample_engine", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "tools/tantrium_certificate_builder_v2.py", "role": "research_os_v2_certificate_builder", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_FULL_MACHINE_STATUS.md", "role": "full_machine_status", "theorem_node": None, "certificate_id": None},
    {"path": "docs/TANTRIUM_AUTOSOLVER_ARCHITECTURE.md", "role": "autosolver_architecture", "theorem_node": None, "certificate_id": None},
    {"path": "docs/TANTRIUM_RESEARCH_OS_ARCHITECTURE.md", "role": "research_os_architecture", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_RESEARCH_OS_MASTER_REPORT.md", "role": "research_os_master_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_THEOREM_SYNTHESIS_REPORT.md", "role": "research_os_synthesis_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_BENCHMARK_REPORT.md", "role": "research_os_benchmark_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/LEAN_FORMALIZATION_WORK_QUEUE.md", "role": "formalization_work_queue", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_RESEARCH_OS_V2_ARCHITECTURE.md", "role": "research_os_v2_architecture", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/SUBRESULTANT_RECURRENCE_CAMPAIGN_REPORT.md", "role": "subresultant_recurrence_report", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "docs/GATE_AB_THEOREM_SYNTHESIS_REPORT.md", "role": "gate_ab_synthesis_report", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_COUNTEREXAMPLE_ENGINE_REPORT.md", "role": "counterexample_engine_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_CERTIFICATE_BUILDER_V2_REPORT.md", "role": "certificate_builder_v2_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/TANTRIUM_RESEARCH_OS_V2_MASTER_REPORT.md", "role": "research_os_v2_master_report", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "docs/K7_SHARPNESS_STRUCTURE_ANALYSIS.md", "role": "k7_sharpness_analysis", "theorem_node": "K7_SHARPNESS", "certificate_id": None, "required": False},
    {"path": "docs/LEAN_GATE_AB_FORMALIZATION_PLAN.md", "role": "lean_gate_ab_plan", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "results/conjectures/rh/status.json", "role": "solve_status", "theorem_node": "RH_CLOSURE", "certificate_id": "rh_symbolic_closure", "required": False},
    {"path": "results/conjectures/rh/solve_report.json", "role": "solve_report", "theorem_node": "RH_CLOSURE", "certificate_id": "rh_symbolic_closure", "required": False},
    {"path": "results/conjectures/goldbach/status.json", "role": "solve_status", "theorem_node": "GOLDBACH_CONTROL", "certificate_id": None, "required": False},
    {"path": "results/conjectures/goldbach/blocker_certificate.json", "role": "named_blocker", "theorem_node": "MINOR_ARC_BOUND", "certificate_id": None, "required": False},
    {"path": "results/conjectures/lah/status.json", "role": "solve_status", "theorem_node": "GATE_A_PERTURBATION", "certificate_id": None, "required": False},
    {"path": "results/conjectures/lah/blocker_certificate.json", "role": "named_blocker", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/conjectures/hankel/status.json", "role": "solve_status", "theorem_node": "AG_LGV_TRANSFER", "certificate_id": "ag_lgv_parametric", "required": False},
    {"path": "results/conjectures/hankel/proof_certificate.json", "role": "proof_certificate", "theorem_node": "AG_LGV_TRANSFER", "certificate_id": "ag_lgv_parametric", "required": False},
    {"path": "results/conjectures/coefficient_positivity/status.json", "role": "solve_status", "theorem_node": "FIRST_UNCERTIFIED_ATLAS_FRONTIER", "certificate_id": None, "required": False},
    {"path": "results/conjectures/coefficient_positivity/frontier_certificate.json", "role": "frontier_certificate", "theorem_node": "FIRST_UNCERTIFIED_ATLAS_FRONTIER", "certificate_id": None, "required": False},
    {"path": "results/conjectures/coefficient_positivity/blocker_certificate.json", "role": "named_blocker", "theorem_node": "FIRST_UNCERTIFIED_ATLAS_FRONTIER", "certificate_id": None, "required": False},
    {"path": "results/research_os/blackboard.jsonl", "role": "research_blackboard", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "results/research_os/current_campaigns.json", "role": "research_campaign_index", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/lah_gate_ab/synthesis_status.json", "role": "research_campaign_status", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/coefficient_frontier/synthesis_status.json", "role": "research_campaign_status", "theorem_node": "FIRST_UNCERTIFIED_ATLAS_FRONTIER", "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/goldbach_minor_arc/synthesis_status.json", "role": "research_campaign_status", "theorem_node": "GOLDBACH_CONTROL", "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/rh_formalization/synthesis_status.json", "role": "research_campaign_status", "theorem_node": "RH_CLOSURE", "certificate_id": None, "required": False},
    {"path": "results/benchmarks/benchmark_report.json", "role": "research_os_benchmark", "theorem_node": None, "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/subresultant_recurrence/synthesis_status.json", "role": "research_os_v2_campaign_status", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/subresultant_recurrence/recurrence_candidates.json", "role": "research_os_v2_recurrence_candidates", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/campaigns/subresultant_recurrence/finite_verification.json", "role": "research_os_v2_finite_verification", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/candidates/gate_ab_candidate_catalog.json", "role": "research_os_v2_theorem_candidate_catalog", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/proof_attempts/subresultant_recurrence_strategy_summary.json", "role": "research_os_v2_proof_attempt_summary", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": None, "required": False},
    {"path": "results/research_os/counterexamples/subresultant_recurrence_counterexample_search.json", "role": "research_os_v2_counterexample_search", "theorem_node": "K7_SHARPNESS", "certificate_id": None, "required": False},
    {"path": "results/certificates/research_os/subresultant_recurrence_recurrence_candidate_certificate.json", "role": "research_os_v2_certificate", "theorem_node": "GATE_B_STAIRCASE_QUOTIENT", "certificate_id": "subresultant_recurrence_recurrence_candidate", "required": False},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"]) or "unknown"


def git_dirty() -> bool:
    return bool(run_git(["status", "--porcelain"]))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(spec: dict[str, str | None]) -> dict[str, Any]:
    path = REPO_ROOT / str(spec["path"])
    exists = path.exists()
    return {
        "path": spec["path"],
        "role": spec["role"],
        "theorem_node": spec["theorem_node"],
        "certificate_id": spec["certificate_id"],
        "required": spec.get("required", True),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists else None,
    }


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(command_used: str) -> dict[str, Any]:
    latest = load_json(CERT_DIR / "tantrium_rh_machine_latest.json")
    goldbach = load_json(CERT_DIR / "goldbach_proof_attempt_dag.json")
    return {
        "manifest_version": 2,
        "generated_at": now_iso(),
        "repo": "4lptek1n/Tantrium",
        "git_head": git_head(),
        "dirty_working_tree": git_dirty(),
        "python_version": sys.version.split()[0],
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
        },
        "command_used": command_used,
        "status_boundary": {
            "internal_tantrium_closure": "CLOSED",
            "rh_closure_status": "PROVEN_BY_CERTIFICATE",
            "proof_attempt_status": "NO_STRUCTURAL_GAP",
            "external_formalization": "PENDING",
        },
        "latest_verified_local_run": {
            "commit": latest.get("commit_sha"),
            "generated_at": latest.get("generated_at"),
            "closure_status": latest.get("closure_status"),
            "proof_attempt_status": latest.get("proof_attempt_status"),
            "rh_closure_status": latest.get("rh_closure_status"),
            "internal_tantrium_closure": latest.get("internal_tantrium_closure"),
            "external_formalization": latest.get("external_formalization"),
            "goldbach_control": goldbach.get("overall_status"),
        },
        "artifacts": [artifact_record(item) for item in ARTIFACTS],
    }


def write_manifest_md(manifest: dict[str, Any]) -> str:
    lines = [
        "# Tantrium Artifact Manifest",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Git HEAD: `{manifest['git_head']}`",
        f"Dirty working tree: `{manifest['dirty_working_tree']}`",
        f"Python: `{manifest['python_version']}`",
        f"Platform: `{manifest['platform']['system']} {manifest['platform']['release']} {manifest['platform']['machine']}`",
        f"Command: `{manifest['command_used']}`",
        "",
        "## Status Boundary",
        "",
        "| Field | Value |",
        "|-------|-------|",
    ]
    for key, value in manifest["status_boundary"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Latest Verified Local Run", "", "| Field | Value |", "|-------|-------|"])
    for key, value in manifest["latest_verified_local_run"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Artifact Hashes",
            "",
            "| Path | Role | Theorem Node | Certificate ID | Size | SHA256 |",
            "|------|------|--------------|----------------|-----:|--------|",
        ]
    )
    for artifact in manifest["artifacts"]:
        lines.append(
            "| `{path}` | `{role}` | `{node}` | `{cert}` | {size} | `{sha}` |".format(
                path=artifact["path"],
                role=artifact["role"],
                node=artifact.get("theorem_node") or "",
                cert=artifact.get("certificate_id") or "",
                size=artifact.get("size_bytes"),
                sha=artifact.get("sha256"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Tantrium artifact manifest")
    parser.add_argument(
        "--command-used",
        default="python tools/tantrium_artifact_manifest.py",
        help="Command recorded in the manifest metadata.",
    )
    args = parser.parse_args()

    CERT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args.command_used)
    MANIFEST_JSON.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    MANIFEST_MD.write_text(write_manifest_md(manifest), encoding="utf-8")

    missing = [item["path"] for item in manifest["artifacts"] if item.get("required", True) and not item["exists"]]
    print("TANTRIUM ARTIFACT MANIFEST")
    print(f"ARTIFACTS: {len(manifest['artifacts'])}")
    print(f"MISSING: {len(missing)}")
    print(f"RESULT: {'FAILED' if missing else 'GENERATED'}")
    if missing:
        print(f"FIRST_FAILURE: missing {missing[0]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
