"""Write theorem candidate JSON and Markdown artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_candidate(root: Path, candidate: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    stem = candidate["candidate_id"]
    (root / f"{stem}.json").write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {stem}",
        "",
        f"Score: `{candidate['score']}`",
        "",
        "## Statement",
        "",
        candidate["precise_statement"],
        "",
        "## Hypotheses",
        "",
    ]
    lines.extend(f"- {item}" for item in candidate["hypotheses"])
    lines.extend(["", "## Proof Strategies", ""])
    lines.extend(f"- `{item}`" for item in candidate["possible_proof_strategies"])
    lines.extend(["", f"Expected blocker if proof fails: `{candidate['expected_blocker_if_proof_fails']}`", ""])
    (root / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
