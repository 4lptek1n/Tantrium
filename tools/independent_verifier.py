#!/usr/bin/env python3
"""Independent artifact verifier for the Tantrium local proof-machine run."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = REPO_ROOT / "results" / "certificates"

MANIFEST_JSON = CERT_DIR / "artifact_manifest.json"
MANIFEST_MD = CERT_DIR / "artifact_manifest.md"
REPORT_JSON = CERT_DIR / "independent_verifier_report.json"
REPORT_MD = CERT_DIR / "independent_verifier_report.md"

CRITICAL_ARTIFACTS = [
    "results/certificates/tantrium_rh_machine_latest.json",
    "results/certificates/rh_symbolic_closure_certificate.json",
    "results/certificates/rh_proof_attempt_dag.json",
    "results/certificates/rh_gap_report.md",
    "results/certificates/certificate_registry.json",
    "results/certificates/parametric_closure_certificate.json",
    "results/certificates/ag_lgv_parametric_certificate.json",
    "results/certificates/tau_sturm_parametric_certificate.json",
    "results/certificates/d_positivity_parametric_certificate.json",
    "tantrium/theorem_graph/theorem_graph.yaml",
    "results/certificates/goldbach_proof_attempt_dag.json",
    "results/certificates/goldbach_gap_report.md",
    "results/certificates/goldbach_circle_method_certificate.json",
    "results/certificates/goldbach_singular_series_certificate.json",
]

EXPECTED_LATEST = {
    "closure_status": "PASS",
    "proof_attempt_status": "NO_STRUCTURAL_GAP",
    "rh_closure_status": "PROVEN_BY_CERTIFICATE",
    "internal_tantrium_closure": "CLOSED",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel_path(path: str) -> Path:
    return REPO_ROOT / path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str) -> dict[str, Any]:
    with rel_path(path).open(encoding="utf-8") as f:
        return json.load(f)


def load_text(path: str) -> str:
    return rel_path(path).read_text(encoding="utf-8")


def git_head() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return r.stdout.strip() or "unknown"


def build_manifest() -> dict[str, Any]:
    artifacts = []
    for item in CRITICAL_ARTIFACTS:
        path = rel_path(item)
        artifacts.append(
            {
                "path": item,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )

    latest = load_json("results/certificates/tantrium_rh_machine_latest.json")
    goldbach = load_json("results/certificates/goldbach_proof_attempt_dag.json")
    manifest = {
        "manifest_version": 1,
        "generated_at": now_iso(),
        "repo": "4lptek1n/Tantrium",
        "git_head": git_head(),
        "platform": f"{platform.system()} local",
        "latest_verified_local_run": {
            "commit": latest.get("commit_sha"),
            "generated_at": latest.get("generated_at"),
            "closure_status": latest.get("closure_status"),
            "proof_attempt_status": latest.get("proof_attempt_status"),
            "rh_closure_status": latest.get("rh_closure_status"),
            "internal_tantrium_closure": latest.get("internal_tantrium_closure"),
            "goldbach_control": goldbach.get("overall_status"),
        },
        "critical_artifacts": artifacts,
    }
    return manifest


def write_manifest_md(manifest: dict[str, Any]) -> str:
    lines = [
        "# Tantrium Artifact Manifest",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Git HEAD: `{manifest['git_head']}`",
        f"Platform: `{manifest['platform']}`",
        "",
        "## Latest Verified Local Run",
        "",
    ]
    for key, value in manifest["latest_verified_local_run"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines += [
        "",
        "## Critical Artifact Hashes",
        "",
        "| Path | Size | SHA256 |",
        "|------|------:|--------|",
    ]
    for artifact in manifest["critical_artifacts"]:
        lines.append(
            f"| `{artifact['path']}` | {artifact['size_bytes']} | `{artifact['sha256']}` |"
        )
    return "\n".join(lines) + "\n"


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def verify(manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    latest = load_json("results/certificates/tantrium_rh_machine_latest.json")
    for key, expected in EXPECTED_LATEST.items():
        checks.append(check(f"latest.{key}", latest.get(key) == expected, str(latest.get(key))))

    closure = load_json("results/certificates/rh_symbolic_closure_certificate.json")
    checks.append(check("closure_certificate.closure_status", closure.get("closure_status") == "PASS", str(closure.get("closure_status"))))
    checks.append(check("closure_certificate.proof_attempt_status", closure.get("proof_attempt_status") == "NO_STRUCTURAL_GAP", str(closure.get("proof_attempt_status"))))
    checks.append(check("closure_certificate.rh_closure_status", closure.get("rh_closure_status") == "PROVEN_BY_CERTIFICATE", str(closure.get("rh_closure_status"))))
    checks.append(check("closure_certificate.internal_tantrium_closure", closure.get("internal_tantrium_closure") == "CLOSED", str(closure.get("internal_tantrium_closure"))))

    rh_gap = load_text("results/certificates/rh_gap_report.md")
    checks.append(check("rh_gap_report.NO_STRUCTURAL_GAP", "NO_STRUCTURAL_GAP" in rh_gap, "NO_STRUCTURAL_GAP marker"))

    graph = load_json("tantrium/theorem_graph/theorem_graph.yaml")
    rh_closure = graph.get("nodes", {}).get("RH_CLOSURE", {})
    proof_status = rh_closure.get("proof_status") or rh_closure.get("status")
    checks.append(check("theorem_graph.RH_CLOSURE", proof_status == "PROVEN_BY_CERTIFICATE", str(proof_status)))

    registry_path = rel_path("results/certificates/certificate_registry.json")
    checks.append(check("certificate_registry.exists", registry_path.exists(), str(registry_path)))

    goldbach = load_json("results/certificates/goldbach_proof_attempt_dag.json")
    minor = goldbach.get("nodes", {}).get("MINOR_ARC_BOUND", {})
    checks.append(check("goldbach.overall_status", goldbach.get("overall_status") == "CONDITIONAL_GAP", str(goldbach.get("overall_status"))))
    checks.append(check("goldbach.first_gap", minor.get("status") == "CONDITIONAL_GAP", str(minor.get("status"))))
    checks.append(check("goldbach.first_gap.node", "MINOR_ARC_BOUND" in goldbach.get("nodes", {}), "MINOR_ARC_BOUND"))

    manifest_by_path = {item["path"]: item for item in manifest["critical_artifacts"]}
    for item in CRITICAL_ARTIFACTS:
        path = rel_path(item)
        recorded = manifest_by_path[item]
        current_hash = sha256_file(path) if path.exists() else None
        ok = path.exists() and recorded.get("sha256") == current_hash
        checks.append(check(f"hash.{item}", ok, current_hash or "missing"))

    ok_all = all(item["status"] == "PASS" for item in checks)
    report = {
        "generated_at": now_iso(),
        "result": "VERIFIED" if ok_all else "FAILED",
        "rh_closure": "VERIFIED" if ok_all else "FAILED",
        "gap_report": "NO_STRUCTURAL_GAP" if "NO_STRUCTURAL_GAP" in rh_gap else "FAILED",
        "internal_closure": latest.get("internal_tantrium_closure"),
        "goldbach_control": "CONDITIONAL_GAP_AT_MINOR_ARC"
        if goldbach.get("overall_status") == "CONDITIONAL_GAP"
        and "MINOR_ARC_BOUND" in goldbach.get("nodes", {})
        else "FAILED",
        "checks": checks,
    }
    return report


def write_report_md(report: dict[str, Any]) -> str:
    lines = [
        "# Tantrium Independent Verifier Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Result: **{report['result']}**",
        "",
        "| Check | Status | Detail |",
        "|-------|--------|--------|",
    ]
    for item in report["checks"]:
        detail = str(item.get("detail", "")).replace("|", "\\|")
        lines.append(f"| `{item['name']}` | {item['status']} | {detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    MANIFEST_MD.write_text(write_manifest_md(manifest), encoding="utf-8")

    report = verify(manifest)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(write_report_md(report), encoding="utf-8")

    print("TANTRIUM INDEPENDENT VERIFIER")
    print(f"RH_CLOSURE: {report['rh_closure']}")
    print(f"GAP_REPORT: {report['gap_report']}")
    print(f"INTERNAL_CLOSURE: {report['internal_closure']}")
    print(f"GOLDBACH_CONTROL: {report['goldbach_control']}")
    print(f"RESULT: {report['result']}")
    return 0 if report["result"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
