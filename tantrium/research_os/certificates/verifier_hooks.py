"""Build and register Research OS v2 certificates."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import blocker_certificate, evidence_certificate, proof_attempt_certificate, recurrence_certificate

REPO_ROOT = Path(__file__).resolve().parents[3]
CERT_ROOT = REPO_ROOT / "results" / "certificates" / "research_os"
REGISTRY_JSON = REPO_ROOT / "results" / "certificates" / "certificate_registry.json"
REGISTRY_MD = REPO_ROOT / "results" / "certificates" / "certificate_registry.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() or "unknown"


def write_cert(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_suffix(".md").write_text(
        f"# {payload['certificate_type']}\n\nArtifact: `{payload['artifact']}`\n\nStatus: `{payload['status']}`\n\nProof promotion: `{payload['proof_promotion']}`\n",
        encoding="utf-8",
    )


def build_research_os_certificates(campaign: str = "subresultant_recurrence") -> dict[str, Any]:
    campaign_dir = REPO_ROOT / "results" / "research_os" / "campaigns" / campaign
    mappings = [
        ("finite_evidence", campaign_dir / "qjr_tables.json", evidence_certificate.build),
        ("recurrence_candidate", campaign_dir / "recurrence_candidates.json", recurrence_certificate.build),
        ("proof_attempt", REPO_ROOT / "results" / "research_os" / "proof_attempts" / f"{campaign}_strategy_summary.json", proof_attempt_certificate.build),
        ("refined_subgap", campaign_dir / "synthesis_status.json", blocker_certificate.build),
    ]
    certificates = []
    for name, artifact, builder in mappings:
        if not artifact.exists():
            continue
        payload = builder(artifact)
        payload["campaign"] = campaign
        payload["generated_at"] = now_iso()
        payload["commit_sha"] = git_sha()
        cert_path = CERT_ROOT / f"{campaign}_{name}_certificate.json"
        write_cert(cert_path, payload)
        certificates.append(str(cert_path.relative_to(REPO_ROOT)))
    update_registry(campaign, certificates)
    return {"campaign": campaign, "certificate_count": len(certificates), "certificates": certificates}


def update_registry(campaign: str, certificates: list[str]) -> None:
    registry = json.loads(REGISTRY_JSON.read_text(encoding="utf-8")) if REGISTRY_JSON.exists() else {}
    section = registry.setdefault("research_os_v2_certificates", {})
    section[campaign] = {
        "campaign": campaign,
        "certificates": certificates,
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
    }
    REGISTRY_JSON.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = REGISTRY_MD.read_text(encoding="utf-8").splitlines() if REGISTRY_MD.exists() else ["# Certificate Registry"]
    marker = "## Research OS v2 Certificates"
    if marker not in lines:
        lines.extend(["", marker, ""])
    lines.append(f"- `{campaign}`: {len(certificates)} certificates generated at {now_iso()}")
    REGISTRY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
