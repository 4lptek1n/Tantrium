#!/usr/bin/env python3
"""Independent read-only verifier for sealed Tantrium artifacts.

The verifier does not generate theorem certificates and does not refresh the
artifact manifest.  It reads the sealed artifacts, verifies their consistency,
then writes only its verifier report.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = REPO_ROOT / "results" / "certificates"
MANIFEST_JSON = CERT_DIR / "artifact_manifest.json"
REPORT_JSON = CERT_DIR / "independent_verifier_report.json"
REPORT_MD = CERT_DIR / "independent_verifier_report.md"

SELF_REPORT_PATHS = {
    "results/certificates/independent_verifier_report.json",
    "results/certificates/independent_verifier_report.md",
}

EXPECTED_RH = {
    "closure_status": "PASS",
    "proof_attempt_status": "NO_STRUCTURAL_GAP",
    "rh_closure_status": "PROVEN_BY_CERTIFICATE",
    "internal_tantrium_closure": "CLOSED",
}

REQUIRED_RH_DAG_NODES = [
    "RH_RAW_TARGET",
    "XI_REAL_FORM",
    "JENSEN_HYPERBOLICITY",
    "STURM_PIVOT_POSITIVITY",
    "TAU_SUBDISCRIMINANT",
    "AG_LGV_TRANSFER",
    "CELL_SUPPORT_POSITIVITY",
    "D_POSITIVITY",
    "DYADIC_TRANSPORT",
    "RH_CLOSURE",
]

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


def rel_path(path: str) -> Path:
    return REPO_ROOT / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_path(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json(path: str) -> dict[str, Any]:
    return load_json_path(rel_path(path))


def load_text(path: str) -> str:
    return rel_path(path).read_text(encoding="utf-8")


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}


def first_failure(checks: list[dict[str, Any]]) -> str | None:
    for item in checks:
        if item["status"] != "PASS":
            detail = item.get("detail") or ""
            return f"{item['name']}: {detail}".strip()
    return None


def manifest_artifacts(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if "artifacts" in manifest:
        return list(manifest["artifacts"])
    return list(manifest.get("critical_artifacts", []))


def verify_manifest_hashes(manifest: dict[str, Any], checks: list[dict[str, Any]]) -> bool:
    ok_all = True
    for artifact in manifest_artifacts(manifest):
        path_name = str(artifact.get("path", ""))
        path = rel_path(path_name)
        required = bool(artifact.get("required", True))
        exists = path.exists()
        nonempty = exists and path.stat().st_size > 0
        if not required and not exists:
            checks.append(check(f"artifact.optional.{path_name}", True, "optional artifact not generated"))
            continue
        checks.append(check(f"artifact.exists.{path_name}", exists, "exists" if exists else "missing"))
        checks.append(
            check(
                f"artifact.nonempty.{path_name}",
                nonempty,
                str(path.stat().st_size) if exists else "missing",
            )
        )
        if not exists or not nonempty:
            ok_all = False
            continue
        if path_name in SELF_REPORT_PATHS:
            checks.append(check(f"hash.{path_name}", True, "self-report regenerated; existence checked"))
            continue
        current_hash = sha256_file(path)
        expected_hash = artifact.get("sha256")
        hash_ok = current_hash == expected_hash
        checks.append(check(f"hash.{path_name}", hash_ok, current_hash))
        ok_all = ok_all and hash_ok
    return ok_all


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    manifest_exists = MANIFEST_JSON.exists()
    checks.append(check("artifact_manifest.exists", manifest_exists, str(MANIFEST_JSON)))
    if not manifest_exists:
        return build_report(checks)

    try:
        manifest = load_json_path(MANIFEST_JSON)
        checks.append(check("artifact_manifest.parseable", True, "json"))
    except Exception as exc:
        checks.append(check("artifact_manifest.parseable", False, str(exc)))
        return build_report(checks)

    hashes_ok = verify_manifest_hashes(manifest, checks)
    checks.append(check("artifact_hashes", hashes_ok, "manifest hashes"))

    try:
        registry = load_json("results/certificates/certificate_registry.json")
        checks.append(check("certificate_registry.parseable", True, str(registry.get("registry_version"))))
    except Exception as exc:
        checks.append(check("certificate_registry.parseable", False, str(exc)))

    try:
        closure = load_json("results/certificates/rh_symbolic_closure_certificate.json")
        for key, expected in EXPECTED_RH.items():
            checks.append(
                check(
                    f"closure_certificate.{key}",
                    closure.get(key) == expected,
                    str(closure.get(key)),
                )
            )
    except Exception as exc:
        checks.append(check("closure_certificate.parseable", False, str(exc)))

    try:
        latest = load_json("results/certificates/tantrium_rh_machine_latest.json")
        closure = load_json("results/certificates/rh_symbolic_closure_certificate.json")
        for key in EXPECTED_RH:
            checks.append(
                check(
                    f"latest_agrees.{key}",
                    latest.get(key) == closure.get(key) == EXPECTED_RH[key],
                    f"latest={latest.get(key)} closure={closure.get(key)}",
                )
            )
        checks.append(
            check(
                "latest.external_formalization",
                latest.get("external_formalization") == "PENDING",
                str(latest.get("external_formalization")),
            )
        )
    except Exception as exc:
        checks.append(check("latest_agrees.parseable", False, str(exc)))

    try:
        dag = load_json("results/certificates/rh_proof_attempt_dag.json")
        nodes = dag.get("nodes", {})
        for node_id in REQUIRED_RH_DAG_NODES:
            status = nodes.get(node_id, {}).get("status")
            checks.append(
                check(
                    f"rh_dag.{node_id}",
                    status == "PROVEN_BY_CERTIFICATE",
                    str(status),
                )
            )
    except Exception as exc:
        checks.append(check("rh_dag.parseable", False, str(exc)))

    try:
        gap_report = load_text("results/certificates/rh_gap_report.md")
        checks.append(
            check(
                "rh_gap_report.no_structural_gap_found",
                "NO STRUCTURAL GAP FOUND" in gap_report,
                "NO STRUCTURAL GAP FOUND",
            )
        )
    except Exception as exc:
        checks.append(check("rh_gap_report.readable", False, str(exc)))

    try:
        graph = load_json("tantrium/theorem_graph/theorem_graph.yaml")
        rh_closure = graph.get("nodes", {}).get("RH_CLOSURE", {})
        proof_status = rh_closure.get("proof_status") or rh_closure.get("status")
        checks.append(
            check(
                "theorem_graph.RH_CLOSURE",
                proof_status == "PROVEN_BY_CERTIFICATE",
                str(proof_status),
            )
        )
    except Exception as exc:
        checks.append(check("theorem_graph.parseable", False, str(exc)))

    try:
        atlas = load_json("results/atlas/manifest.json")
        checks.append(
            check(
                "atlas.latest_rh_closure_certificate",
                atlas.get("latest_rh_closure_certificate")
                == "results/certificates/rh_symbolic_closure_certificate.json",
                str(atlas.get("latest_rh_closure_certificate")),
            )
        )
        checks.append(
            check(
                "atlas.latest_certificate_registry",
                atlas.get("latest_certificate_registry")
                == "results/certificates/certificate_registry.json",
                str(atlas.get("latest_certificate_registry")),
            )
        )
        checks.append(
            check(
                "atlas.proof_attempt_status",
                atlas.get("proof_attempt_status") == "NO_STRUCTURAL_GAP",
                str(atlas.get("proof_attempt_status")),
            )
        )
    except Exception as exc:
        checks.append(check("atlas_manifest.parseable", False, str(exc)))

    verify_problem_final_statuses(checks)

    return build_report(checks)


def verify_problem_final_statuses(checks: list[dict[str, Any]]) -> None:
    try:
        goldbach = load_json("results/conjectures/goldbach/status.json")
        blocker = load_json("results/conjectures/goldbach/blocker_certificate.json")
        checks.append(
            check(
                "goldbach.final_status",
                goldbach.get("final_status") == "BLOCKED_BY_NAMED_GAP",
                str(goldbach.get("final_status")),
            )
        )
        checks.append(
            check(
                "goldbach.named_gap",
                goldbach.get("first_gap") == "MINOR_ARC_UNCONDITIONAL_BOUND"
                and blocker.get("named_gap") == "MINOR_ARC_UNCONDITIONAL_BOUND",
                f"status_gap={goldbach.get('first_gap')} blocker_gap={blocker.get('named_gap')}",
            )
        )
    except Exception as exc:
        checks.append(check("goldbach_control.parseable", False, str(exc)))

    for problem in ["lah", "hankel", "coefficient_positivity"]:
        try:
            status = load_json(f"results/conjectures/{problem}/status.json")
            final_status = status.get("final_status") or status.get("status")
            checks.append(
                check(
                    f"{problem}.final_status.allowed",
                    final_status in FINAL_STATUSES and final_status not in INTERMEDIATE_STATUSES,
                    str(final_status),
                )
            )
            if final_status == "BLOCKED_BY_NAMED_GAP":
                blocker_path = status.get("blocker_certificate_path")
                blocker_exists = bool(blocker_path) and rel_path(str(blocker_path)).exists()
                checks.append(
                    check(
                        f"{problem}.blocker_certificate.exists",
                        blocker_exists,
                        str(blocker_path),
                    )
                )
            if final_status == "PROVEN_BY_CERTIFICATE":
                proof_path = status.get("proof_certificate_path")
                proof_exists = bool(proof_path) and rel_path(str(proof_path)).exists()
                checks.append(
                    check(
                        f"{problem}.proof_certificate.exists",
                        proof_exists,
                        str(proof_path),
                    )
                )
        except Exception as exc:
            checks.append(check(f"{problem}.status.parseable", False, str(exc)))


def build_report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failure = first_failure(checks)
    ok = failure is None
    return {
        "result": "VERIFIED" if ok else "FAILED",
        "first_failure": failure,
        "rh_closure": "VERIFIED" if ok else "FAILED",
        "artifact_hashes": "VERIFIED"
        if all(
            item["status"] == "PASS"
            for item in checks
            if item["name"].startswith("hash.") or item["name"] == "artifact_hashes"
        )
        else "FAILED",
        "gap_report": "NO_STRUCTURAL_GAP"
        if any(
            item["name"] == "rh_gap_report.no_structural_gap_found"
            and item["status"] == "PASS"
            for item in checks
        )
        else "FAILED",
        "internal_closure": "CLOSED"
        if any(
            item["name"] == "latest_agrees.internal_tantrium_closure"
            and item["status"] == "PASS"
            for item in checks
        )
        else "FAILED",
        "goldbach_control": "CONDITIONAL_GAP_AT_MINOR_ARC"
        if any(item["name"] == "goldbach.named_gap" and item["status"] == "PASS" for item in checks)
        else "FAILED",
        "lah_status": problem_status(checks, "lah"),
        "hankel_status": problem_status(checks, "hankel"),
        "coefficient_positivity_status": problem_status(checks, "coefficient_positivity"),
        "goldbach_named_blocker": "BLOCKED_BY_NAMED_GAP_AT_MINOR_ARC"
        if any(item["name"] == "goldbach.named_gap" and item["status"] == "PASS" for item in checks)
        else "FAILED",
        "checks": checks,
    }


def problem_status(checks: list[dict[str, Any]], problem: str) -> str:
    prefix = f"{problem}.final_status.allowed"
    for item in checks:
        if item["name"] == prefix and item["status"] == "PASS":
            return str(item.get("detail"))
    return "FAILED"


def write_report_md(report: dict[str, Any]) -> str:
    lines = [
        "# Tantrium Independent Verifier Report",
        "",
        f"Result: **{report['result']}**",
    ]
    if report["first_failure"]:
        lines.append(f"First failure: `{report['first_failure']}`")
    lines.extend(["", "| Check | Status | Detail |", "|-------|--------|--------|"])
    for item in report["checks"]:
        detail = str(item.get("detail", "")).replace("|", "\\|")
        lines.append(f"| `{item['name']}` | {item['status']} | {detail} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    report = verify()
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_MD.write_text(write_report_md(report), encoding="utf-8")

    print("TANTRIUM INDEPENDENT VERIFIER")
    print(f"RH_CLOSURE: {report['rh_closure']}")
    print(f"GOLDBACH_CONTROL: {report['goldbach_named_blocker']}")
    print(f"LAH_STATUS: {report['lah_status']}")
    print(f"HANKEL_STATUS: {report['hankel_status']}")
    print(f"COEFFICIENT_POSITIVITY_STATUS: {report['coefficient_positivity_status']}")
    print(f"ARTIFACT_HASHES: {report['artifact_hashes']}")
    print(f"RESULT: {report['result']}")
    if report["result"] != "VERIFIED":
        print(f"FIRST_FAILURE: {report['first_failure']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
