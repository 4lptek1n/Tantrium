"""Persistent research blackboard."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = REPO_ROOT / "results" / "research_os"
BLACKBOARD_PATH = RESULTS_ROOT / "blackboard.jsonl"
INDEX_PATH = RESULTS_ROOT / "blackboard_index.json"
CURRENT_CAMPAIGNS_PATH = RESULTS_ROOT / "current_campaigns.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(event: ResearchEvent | dict[str, Any]) -> dict[str, Any]:
    payload = event.to_dict() if isinstance(event, ResearchEvent) else dict(event)
    BLACKBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BLACKBOARD_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    rebuild_index()
    return payload


def read_events() -> list[dict[str, Any]]:
    if not BLACKBOARD_PATH.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in BLACKBOARD_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def rebuild_index() -> dict[str, Any]:
    events = read_events()
    by_campaign: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    latest_by_campaign: dict[str, dict[str, Any]] = {}
    for event in events:
        campaign = str(event.get("campaign", "unknown"))
        agent = str(event.get("agent", "unknown"))
        by_campaign[campaign] = by_campaign.get(campaign, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1
        latest_by_campaign[campaign] = event
    index = {
        "event_count": len(events),
        "by_campaign": by_campaign,
        "by_agent": by_agent,
        "latest_by_campaign": latest_by_campaign,
    }
    write_json(INDEX_PATH, index)
    return index


def update_current_campaign(campaign: str, status: dict[str, Any]) -> None:
    data: dict[str, Any] = {}
    if CURRENT_CAMPAIGNS_PATH.exists():
        data = json.loads(CURRENT_CAMPAIGNS_PATH.read_text(encoding="utf-8"))
    data[campaign] = status
    write_json(CURRENT_CAMPAIGNS_PATH, data)
