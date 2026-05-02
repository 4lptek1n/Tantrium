"""Inventory H-factor and engine data sources."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .data_loader import REPO_ROOT, file_record, load_pickle_inventory, load_sources


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def build_h_factor_inventory(out_dir: Path) -> dict[str, Any]:
    engine_files = []
    for path in sorted((REPO_ROOT / "results" / "engine").glob("ell*_*.csv")):
        record = file_record(path)
        record["rows"] = count_csv_rows(path)
        engine_files.append(record)
    inventory = {
        "sources": load_sources(),
        "pickle_caches": load_pickle_inventory(),
        "engine_csv_files": engine_files,
        "h_data_status": "FINITE_AND_ARTIFACT_INVENTORY",
        "notes": [
            "No proof is inferred from inventory alone.",
            "If raw H_{d,j}(t) caches are absent, QJR mining uses the documented degree/top-ramp normal form as finite evidence.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "h_factor_inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return inventory
