#!/usr/bin/env python3
"""Persistent theorem graph store.

The file is named theorem_graph.yaml for human convention, but its contents are
JSON, which is valid YAML 1.2 and keeps the implementation dependency-free.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tantrium.theorem_graph.state_machine import TheoremGraph, TheoremNode, default_graph


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def graph_to_dict(graph: TheoremGraph) -> dict[str, Any]:
    return {"nodes": {k: asdict(v) for k, v in graph.nodes.items()}}


def graph_from_dict(data: dict[str, Any]) -> TheoremGraph:
    graph = TheoremGraph()
    for _, rec in data.get("nodes", {}).items():
        graph.add(TheoremNode(**rec))
    return graph


def dependency_closed(graph: TheoremGraph, node: TheoremNode) -> bool:
    if not node.depends_on:
        return False
    good = {"proven", "certified_local"}
    return all(dep in graph.nodes and graph.nodes[dep].status in good for dep in node.depends_on)


class GraphStore:
    def __init__(self, path: str | Path = "tantrium/theorem_graph/theorem_graph.yaml") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(default_graph())

    def load(self) -> TheoremGraph:
        try:
            return graph_from_dict(json.loads(self.path.read_text()))
        except Exception:
            graph = default_graph(); self.save(graph); return graph

    def save(self, graph: TheoremGraph) -> None:
        self.path.write_text(json.dumps(graph_to_dict(graph), indent=2, sort_keys=True))

    def propagate(self, graph: TheoremGraph) -> TheoremGraph:
        changed = True
        while changed:
            changed = False
            for node in graph.nodes.values():
                if node.status in {"conjectural", "verified_finite"} and dependency_closed(graph, node):
                    node.status = "certified_local"
                    node.notes.append(f"auto-promoted by dependency closure at {now()}")
                    changed = True
        return graph

    def add_obstruction(self, theorem_id: str, title: str, artifacts: list[str] | None = None, note: str | None = None) -> None:
        graph = self.load()
        graph.add(TheoremNode(theorem_id=theorem_id, title=title, status="blocked", artifacts=artifacts or [], notes=[note or f"recorded {now()}"]))
        self.save(graph)

    def update_from_atlas(self, atlas_manifest: dict[str, Any]) -> TheoremGraph:
        graph = self.load()
        for cid, cert in atlas_manifest.get("certificates", {}).items():
            tid = cert.get("theorem_id", cid)
            status = "certified_local" if cert.get("status") == "verified_exact" else "blocked"
            if tid not in graph.nodes:
                graph.add(TheoremNode(theorem_id=tid, title=f"Certificate {tid}", status=status, artifacts=[cert.get("path", "")], notes=[f"ingested from Atlas at {now()}"],))
            elif status == "certified_local" and graph.nodes[tid].status in {"conjectural", "verified_finite", "blocked"}:
                graph.nodes[tid].status = "certified_local"
                graph.nodes[tid].notes.append(f"certificate verified in Atlas at {now()}")
        for oid, obs in atlas_manifest.get("obstructions", {}).items():
            tid = obs.get("theorem_id", oid) + "_obstruction"
            if tid not in graph.nodes:
                graph.add(TheoremNode(theorem_id=tid, title=f"Obstruction for {obs.get('theorem_id', oid)}", status="blocked", artifacts=[], notes=[json.dumps(obs.get("coordinates", {}), sort_keys=True)],))
        graph = self.propagate(graph)
        self.save(graph)
        return graph
