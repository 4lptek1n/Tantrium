"""Load Gate A/B and Research OS data for recurrence mining."""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

SOURCE_PATHS = [
    "math/SUMMARY.md",
    "math/README.md",
    "math/gate_a.py",
    "math/gate_a_verify.py",
    "theorems/GATE_B_FINDINGS.md",
    "theorems/FIRST_FIVE_PIVOTS.md",
    "theorems/K5_J4_RESULT.md",
    "theorems/K6_J5_RESULT.md",
    "theorems/K7_SHARPNESS.md",
    "results/research_os/campaigns/lah_gate_ab/synthesis_status.json",
]


def file_record(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def load_sources() -> dict[str, Any]:
    records = [file_record(REPO_ROOT / rel) for rel in SOURCE_PATHS]
    text_hits: dict[str, list[str]] = {}
    for rel in SOURCE_PATHS:
        path = REPO_ROOT / rel
        if not path.exists() or path.suffix not in {".md", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = []
        for token in ["Q_", "Q_{j,r}", "H_{d,j}", "staircase", "subresultant", "K7", "Lah"]:
            if token in text:
                hits.append(token)
        text_hits[rel] = hits
    return {"source_records": records, "text_hits": text_hits}


def load_pickle_inventory() -> list[dict[str, Any]]:
    inventory = []
    for path in sorted(REPO_ROOT.rglob("*H*d*j*cache*.pkl")) + sorted(REPO_ROOT.rglob("H_d*j*_cache.pkl")):
        item = file_record(path)
        try:
            with path.open("rb") as handle:
                data = pickle.load(handle)
            item["loadable"] = True
            item["type"] = type(data).__name__
            item["length"] = len(data) if hasattr(data, "__len__") else None
        except Exception as exc:  # pragma: no cover - depends on optional local caches
            item["loadable"] = False
            item["error"] = str(exc)
        inventory.append(item)
    return inventory


def load_json_if_exists(rel: str) -> dict[str, Any]:
    path = REPO_ROOT / rel
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
