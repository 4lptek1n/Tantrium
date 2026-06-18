"""Atlas memory writer for research OS events."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent, now_iso
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]
ATLAS_EVENTS = REPO_ROOT / "results" / "atlas" / "events.jsonl"


def write_atlas_event(campaign_id: str, synthesis: dict[str, Any]) -> None:
    payload = {
        "timestamp": now_iso(),
        "source": "research_os",
        "campaign": campaign_id,
        "status": synthesis["status"],
        "refined_subgap": synthesis["refined_subgap"],
    }
    ATLAS_EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with ATLAS_EVENTS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    append_event(ResearchEvent(campaign_id, "Atlas Writer", "atlas_event_written", synthesis["status"], outputs=[str(ATLAS_EVENTS.relative_to(REPO_ROOT))]))
