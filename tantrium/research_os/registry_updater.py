"""Update certificate registry with research OS campaign summaries."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .agent_protocol import ResearchEvent, now_iso
from .blackboard import append_event

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "results" / "certificates" / "certificate_registry.json"


def git_sha() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    return result.stdout.strip() or "unknown"


def update_registry(campaign_id: str, synthesis: dict[str, Any], out_dir: Path) -> None:
    registry: dict[str, Any] = {}
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    campaigns = registry.setdefault("research_os_campaigns", {})
    campaigns[campaign_id] = {
        "campaign_id": campaign_id,
        "status": synthesis["status"],
        "refined_subgap": synthesis["refined_subgap"],
        "report_path": str((out_dir / "synthesis_status.json").relative_to(REPO_ROOT)),
        "human_review_packet": str((out_dir / "human_review_packet.md").relative_to(REPO_ROOT)),
        "command_used": "python tools/tantrium_research_os.py --campaign <campaign> --deep",
        "generated_at": now_iso(),
        "commit_sha": git_sha(),
    }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(ResearchEvent(campaign_id, "Registry Updater", "registry_updated", synthesis["status"], outputs=[str(REGISTRY_PATH.relative_to(REPO_ROOT))]))
