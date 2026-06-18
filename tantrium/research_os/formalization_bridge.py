"""Lean/Coq formalization bridge for research campaigns."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]
FORMALIZATION_DIR = REPO_ROOT / "results" / "formalization"


def build_formalization_outputs(campaign_id: str, candidates: list[dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    queue = []
    if campaign_id == "rh_formalization_bootstrap":
        targets = [
            ("TauCauchyBinet", "formal/lean/Tantrium/Tau.lean", "Matrix.det / Cauchy-Binet"),
            ("PositiveNormalization", "formal/lean/Tantrium/Subdiscriminant.lean", "ordered ring normalization"),
            ("AGLGVTransfer", "formal/lean/Tantrium/AGLGV.lean", "Finset path enumeration"),
            ("CellSupportInjection", "formal/lean/Tantrium/DyadicTransport.lean", "finite injections"),
            ("DyadicCapacity", "formal/lean/Tantrium/DyadicTransport.lean", "finite inequality"),
            ("DPositivityInduction", "formal/lean/Tantrium/DPositivity.lean", "induction and positivity"),
        ]
    else:
        targets = [
            (candidate["candidate_id"], f"formal/lean/Tantrium/{candidate['candidate_id'].title().replace('_', '')}.lean", "new lemma skeleton")
            for candidate in candidates
        ]
    for rank, (name, lean_file, mathlib_anchor) in enumerate(targets, start=1):
        queue.append(
            {
                "work_item_id": f"{campaign_id}:{name}",
                "lean_file": lean_file,
                "source_campaign": campaign_id,
                "mathlib_anchor": mathlib_anchor,
                "difficulty": "medium" if rank <= 2 else "high",
                "status": "SKELETON_OR_QUEUE",
            }
        )
    payload = {"campaign": campaign_id, "status": "FORMALIZATION_SCAFFOLD_GENERATED", "work_queue": queue}
    FORMALIZATION_DIR.mkdir(parents=True, exist_ok=True)
    (FORMALIZATION_DIR / "lean_work_queue.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (FORMALIZATION_DIR / "theorem_to_lean_map.json").write_text(
        json.dumps({"campaign": campaign_id, "items": queue}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (FORMALIZATION_DIR / "lean_gap_report.md").write_text(render_lean_gap_report(payload), encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "formalization_work_queue.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(ResearchEvent(campaign_id, "Formalization Bridge", "formalization_scaffold_generated", "FORMALIZATION_SCAFFOLD_GENERATED", outputs=["results/formalization/lean_work_queue.json"]))
    return payload


def render_lean_gap_report(payload: dict[str, Any]) -> str:
    lines = ["# Lean Gap Report", "", f"Campaign: `{payload['campaign']}`", ""]
    for item in payload["work_queue"]:
        lines.append(f"- `{item['work_item_id']}` -> `{item['lean_file']}` ({item['difficulty']})")
    lines.append("")
    lines.append("External formalization remains `PENDING`; this queue is a scaffold and work plan.")
    return "\n".join(lines) + "\n"
