#!/usr/bin/env python3
"""File-backed Atlas database for Tantrium Proof Foundry.

Storage:
  results/atlas/manifest.json
  results/atlas/events.jsonl
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AtlasDB:
    def __init__(self, root: str | Path = "results/atlas") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.json"
        self.events_path = self.root / "events.jsonl"
        if not self.manifest_path.exists():
            self.manifest_path.write_text(json.dumps({"kernels": {}, "certificates": {}, "obstructions": {}, "structure_reports": {}}, indent=2))

    def manifest(self) -> dict[str, Any]:
        return json.loads(self.manifest_path.read_text())

    def _save(self, data: dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def event(self, kind: str, payload: dict[str, Any]) -> None:
        record = {"time": utc_now(), "kind": kind, "payload": payload}
        with self.events_path.open("a") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def register_kernel(self, kernel_id: str, path: str, ell: int | None = None, kind: str = "mixed_depth", rows: int | None = None) -> None:
        data = self.manifest()
        rec = {"kernel_id": kernel_id, "path": path, "ell": ell, "kind": kind, "rows": rows, "created_at": utc_now()}
        data.setdefault("kernels", {})[kernel_id] = rec
        self._save(data)
        self.event("kernel", rec)

    def register_certificate(self, certificate_id: str, summary: dict[str, Any], path: str, q_target: int | None = None, model: str | None = None) -> None:
        data = self.manifest()
        rec = dict(summary)
        rec.update({"certificate_id": certificate_id, "path": path, "q_target": q_target, "model": model, "created_at": utc_now()})
        data.setdefault("certificates", {})[certificate_id] = rec
        self._save(data)
        self.event("certificate", rec)

    def register_obstruction(self, obstruction_id: str, theorem_id: str, kernel_id: str, missing_mass: str, coordinates: dict[str, Any]) -> None:
        data = self.manifest()
        rec = {"obstruction_id": obstruction_id, "theorem_id": theorem_id, "kernel_id": kernel_id, "missing_mass": missing_mass, "coordinates": coordinates, "created_at": utc_now()}
        data.setdefault("obstructions", {})[obstruction_id] = rec
        self._save(data)
        self.event("obstruction", rec)

    def register_structure_report(self, report_id: str, kernel_id: str, path: str, summary: dict[str, Any]) -> None:
        data = self.manifest()
        rec = dict(summary)
        rec.update({"report_id": report_id, "kernel_id": kernel_id, "path": path, "created_at": utc_now()})
        data.setdefault("structure_reports", {})[report_id] = rec
        self._save(data)
        self.event("structure_report", rec)

    def status_table(self) -> str:
        data = self.manifest()
        lines = ["# Atlas DB Status", ""]
        for section in ["kernels", "certificates", "obstructions", "structure_reports"]:
            lines.append(f"## {section}")
            items = data.get(section, {})
            if not items:
                lines.append("_empty_")
            else:
                for key, value in sorted(items.items()):
                    lines.append(f"- `{key}`: {value}")
            lines.append("")
        return "\n".join(lines)
