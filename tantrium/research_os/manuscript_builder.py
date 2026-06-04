"""Human-readable campaign report builder."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_manuscripts(campaign_id: str, out_dir: Path, evidence: dict[str, Any], candidates: list[dict[str, Any]], attempts: dict[str, Any], synthesis: dict[str, Any]) -> None:
    lines = [
        f"# Human Review Packet: {campaign_id}",
        "",
        f"Terminal research status: `{synthesis['status']}`",
        f"Refined subgap: `{synthesis['refined_subgap']}`",
        "",
        "## Evidence",
        "",
        json.dumps(evidence, indent=2, sort_keys=True),
        "",
        "## Candidate Theorems",
        "",
    ]
    for candidate in candidates:
        lines.extend(
            [
                f"### {candidate['candidate_id']}",
                "",
                candidate["statement_latex"],
                "",
                f"Risk: `{candidate['risk']}`  Score: `{candidate['score']}`",
                "",
            ]
        )
    lines.extend(["## Proof Attempts", "", Path(out_dir / "proof_attempts.md").read_text(encoding="utf-8")])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "human_review_packet.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "inferred_laws.md").write_text(render_laws(campaign_id, evidence, synthesis), encoding="utf-8")
    append_event(ResearchEvent(campaign_id, "Manuscript Builder", "manuscript_sections_generated", "NEXT_SUBGAP_IDENTIFIED", outputs=[str((out_dir / "human_review_packet.md").relative_to(REPO_ROOT))]))


def render_laws(campaign_id: str, evidence: dict[str, Any], synthesis: dict[str, Any]) -> str:
    lines = [f"# Inferred Laws: {campaign_id}", ""]
    for law in evidence.get("observed_laws", []):
        lines.append(f"- {law}")
    if not evidence.get("observed_laws"):
        lines.append(f"- Current machine conclusion: `{synthesis['refined_subgap']}`.")
    lines.extend(["", f"Research status: `{synthesis['status']}`", "No external formal proof is claimed."])
    return "\n".join(lines) + "\n"
