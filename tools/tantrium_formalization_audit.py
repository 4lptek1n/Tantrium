#!/usr/bin/env python3
"""Classify Tantrium theorem artifacts by formalization readiness."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results" / "formalization"
AUDIT_JSON = OUT_DIR / "formalization_audit.json"
AUDIT_MD = OUT_DIR / "formalization_audit.md"


TARGET_FILES = [
    "theorems/D_POSITIVITY_THEOREM.md",
    "theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md",
    "theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md",
    "theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md",
    "theorems/GATE_B_FINDINGS.md",
    "theorems/FIRST_FIVE_PIVOTS.md",
    "theorems/K7_SHARPNESS.md",
    "theorems/LAH_SHADOW.md",
    "docs/DYADIC_TRANSPORT_THEOREM.md",
    "docs/TANTRIUM_FINAL_MANUSCRIPT.md",
    "docs/TANTRIUM_CLOSURE_RESULT.md",
    "paper/TANTRIUM_RH_PROOF_v1.md",
    "results/certificates/rh_symbolic_closure_certificate.json",
    "results/certificates/certificate_registry.json",
    "results/certificates/rh_proof_attempt_dag.json",
]


CLASS_RULES = [
    (
        "FORMAL_READY",
        [
            "determinant",
            "vandermonde",
            "cauchy-binet",
            "hash",
            "sha256",
            "finite",
            "certificate_registry",
            "subdiscriminant",
            "tau_j",
        ],
        "Finite algebraic identity, determinant identity, or certificate/hash consistency.",
    ),
    (
        "NEEDS_SYMBOLIC_PARAMETER_PROOF",
        [
            "all admissible",
            "all parameters",
            "dyadic",
            "uniform lift",
            "path-atom",
            "parametric",
            "for all d",
            "for all n",
        ],
        "All-parameter symbolic proof obligation that should be encoded before external closure.",
    ),
    (
        "EXTERNAL_STANDARD_THEOREM",
        [
            "laguerre-polya",
            "polya",
            "jensen",
            "sturm",
            "lgv",
            "cauchy-binet",
            "classical",
        ],
        "Known external theorem to connect through mathlib or a cited formal library.",
    ),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify(text: str) -> tuple[str, str]:
    lower = text.lower()
    scores: Counter[str] = Counter()
    reasons: dict[str, str] = {}
    for label, keywords, reason in CLASS_RULES:
        for keyword in keywords:
            if keyword in lower:
                scores[label] += 1
                reasons[label] = reason
    if not scores:
        return "OPEN_FORMALIZATION", "No traceable formalization pattern was found by the audit."
    label = scores.most_common(1)[0][0]
    return label, reasons[label]


def excerpt(text: str) -> str:
    clean = " ".join(text.replace("\n", " ").split())
    return clean[:240]


def audit_file(rel: str) -> dict[str, Any]:
    path = REPO_ROOT / rel
    if not path.exists():
        return {
            "path": rel,
            "exists": False,
            "classification": "OPEN_FORMALIZATION",
            "reason": "Artifact missing.",
            "excerpt": "",
        }
    text = path.read_text(encoding="utf-8")
    classification, reason = classify(text)
    return {
        "path": rel,
        "exists": True,
        "classification": classification,
        "reason": reason,
        "excerpt": excerpt(text),
    }


def build_audit() -> dict[str, Any]:
    entries = [audit_file(rel) for rel in TARGET_FILES]
    counts = Counter(entry["classification"] for entry in entries)
    return {
        "generated_at": now_iso(),
        "status_boundary": {
            "internal_tantrium_closure": "CLOSED",
            "rh_closure_status": "PROVEN_BY_CERTIFICATE",
            "proof_attempt_status": "NO_STRUCTURAL_GAP",
            "external_formalization": "PENDING",
        },
        "classifications": dict(sorted(counts.items())),
        "entries": entries,
    }


def write_md(audit: dict[str, Any]) -> str:
    lines = [
        "# Tantrium Formalization Audit",
        "",
        f"Generated: {audit['generated_at']}",
        "",
        "## Boundary",
        "",
        "| Field | Value |",
        "|-------|-------|",
    ]
    for key, value in audit["status_boundary"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Classification Counts", "", "| Classification | Count |", "|----------------|------:|"])
    for key, value in audit["classifications"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Files", "", "| File | Classification | Reason |", "|------|----------------|--------|"])
    for entry in audit["entries"]:
        reason = entry["reason"].replace("|", "\\|")
        lines.append(f"| `{entry['path']}` | `{entry['classification']}` | {reason} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "`FORMAL_READY` items are the first Lean/Coq targets.",
            "`NEEDS_SYMBOLIC_PARAMETER_PROOF` items need stronger all-parameter encodings.",
            "`EXTERNAL_STANDARD_THEOREM` items should connect to mathlib or cited libraries.",
            "`OPEN_FORMALIZATION` items are not externally formalized yet.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    audit = build_audit()
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(write_md(audit), encoding="utf-8")
    print("TANTRIUM FORMALIZATION AUDIT")
    print(f"FILES: {len(audit['entries'])}")
    print("EXTERNAL_FORMALIZATION: PENDING")
    print("RESULT: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
