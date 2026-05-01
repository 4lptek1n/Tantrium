#!/usr/bin/env python3
"""Create theorem-level named blocker certificates."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results" / "conjectures"


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, cert: dict[str, Any]) -> None:
    lines = [
        f"# {cert['problem']} Blocker Certificate",
        "",
        f"Generated: {cert['generated_at']}",
        f"Final status: `{cert['final_status']}`",
        f"Named gap: `{cert['named_gap']}`",
        "",
        "## Reason",
        "",
        cert["reason"],
        "",
        "## Dependency Status",
        "",
        "| Dependency | Status |",
        "|------------|--------|",
    ]
    for item in cert["dependencies"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` |")
    lines.extend(["", "## Suggested Attack Path", ""])
    for step in cert.get("suggested_attack_path", []):
        lines.append(f"- {step}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def goldbach_blocker() -> dict[str, Any]:
    return {
        "certificate_type": "named_blocker",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": "goldbach",
        "final_status": "BLOCKED_BY_NAMED_GAP",
        "first_gap": "MINOR_ARC_UNCONDITIONAL_BOUND",
        "named_gap": "MINOR_ARC_UNCONDITIONAL_BOUND",
        "blocked_node": "MINOR_ARC_BOUND",
        "reason": (
            "Binary Goldbach closure requires an unconditional minor arc bound "
            "strong enough to dominate the Hardy-Littlewood major arc main term."
        ),
        "dependencies": [
            {"name": "singular_series_positivity", "status": "PROVEN_BY_CERTIFICATE"},
            {"name": "circle_method_major_arc", "status": "CERTIFIED_SCHEMA"},
            {"name": "minor_arc", "status": "BLOCKED_BY_NAMED_GAP"},
        ],
        "suggested_attack_path": [
            "Strengthen binary minor arc estimates without GRH.",
            "Produce a certificate that |I_minor(N)| is o(N/log(N)^2).",
            "Bind the estimate to the existing major-arc certificate.",
        ],
    }


def generic_blocker(problem: str, named_gap: str, reason: str) -> dict[str, Any]:
    return {
        "certificate_type": "named_blocker",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
        "problem": problem,
        "final_status": "BLOCKED_BY_NAMED_GAP",
        "first_gap": named_gap,
        "named_gap": named_gap,
        "blocked_node": named_gap,
        "reason": reason,
        "dependencies": [],
        "suggested_attack_path": [
            "Identify the precise theorem statement.",
            "Generate finite probes and candidate symbolic law.",
            "Promote the law to a parametric certificate.",
        ],
    }


def create_blocker(problem: str, named_gap: str | None = None, reason: str | None = None) -> dict[str, Any]:
    if problem == "goldbach":
        cert = goldbach_blocker()
    else:
        cert = generic_blocker(
            problem,
            named_gap or "UNSPECIFIED_NAMED_GAP",
            reason or "A named proof dependency is not yet certified.",
        )
    out_dir = RESULTS_ROOT / problem
    write_json(out_dir / "blocker_certificate.json", cert)
    write_md(out_dir / "blocker_certificate.md", cert)
    return cert


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Tantrium named blocker certificate")
    parser.add_argument("--problem", required=True)
    parser.add_argument("--named-gap")
    parser.add_argument("--reason")
    args = parser.parse_args()

    cert = create_blocker(args.problem, args.named_gap, args.reason)
    print("TANTRIUM GAP CERTIFIER")
    print(f"PROBLEM: {args.problem}")
    print(f"FINAL_STATUS: {cert['final_status']}")
    print(f"FIRST_GAP: {cert['first_gap']}")
    print("RESULT: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
