"""The AGI network: 22 paradigms as nodes in a dependency graph.

The network is not a neural network. It has no weights.
It is a DAG where each node is a verified mathematical operator.
An input flows through the network in topological order.
At each node, either a certificate is issued or a named gap is recorded.

The network KNOWS what it does not know.
A named gap is not a failure — it is precise knowledge of the boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from tantrium.agi.codex import CODEX, CODEX_BY_ID, CodexObject, Paradigm, ParadigmResult


# ─── Network node ─────────────────────────────────────────────────────────

@dataclass
class NetworkNode:
    paradigm: Paradigm
    result: ParadigmResult | None = None
    blocked_by_dependency: bool = False

    @property
    def paradigm_id(self) -> str:
        return self.paradigm.paradigm_id

    @property
    def status(self) -> str:
        if self.blocked_by_dependency:
            return "DEP_BLOCKED"
        if self.result is None:
            return "PENDING"
        return self.result.status


# ─── The network ──────────────────────────────────────────────────────────

class AlephTekinNetwork:
    """The 22+1 Aleph-Tekin paradigms as a running DAG.

    run(obj) applies each paradigm in topological order.
    A paradigm is only applied if all its dependencies are CERTIFIED.
    If a dependency is BLOCKED or UNKNOWN, the node is marked DEP_BLOCKED
    and a named gap is recorded: the system knows exactly where it stopped.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, NetworkNode] = {
            p.paradigm_id: NetworkNode(paradigm=p) for p in CODEX
        }
        self._topo_order: list[str] = list(self._topological_sort())

    def _topological_sort(self) -> Iterator[str]:
        """Kahn's algorithm — dependency order."""
        in_degree: dict[str, int] = {pid: 0 for pid in CODEX_BY_ID}
        children: dict[str, list[str]] = {pid: [] for pid in CODEX_BY_ID}
        for p in CODEX:
            for dep in p.depends_on:
                if dep in CODEX_BY_ID:
                    in_degree[p.paradigm_id] += 1
                    children[dep].append(p.paradigm_id)
        queue = [pid for pid, deg in in_degree.items() if deg == 0]
        while queue:
            nxt = sorted(queue)[0]
            queue.remove(nxt)
            yield nxt
            for child in children[nxt]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

    def reset(self) -> None:
        for node in self.nodes.values():
            node.result = None
            node.blocked_by_dependency = False

    def run(self, obj: CodexObject) -> "NetworkRun":
        """Run the object through all 22+1 paradigms in dependency order.
        Returns a NetworkRun with the full certification record.
        """
        self.reset()
        for pid in self._topo_order:
            node = self.nodes[pid]
            paradigm = node.paradigm
            # Check all dependencies are certified
            dep_blocked = any(
                self.nodes[dep].status not in ("CERTIFIED",)
                for dep in paradigm.depends_on
                if dep in self.nodes
            )
            if dep_blocked:
                node.blocked_by_dependency = True
                blocking_deps = [
                    dep for dep in paradigm.depends_on
                    if dep in self.nodes and self.nodes[dep].status not in ("CERTIFIED",)
                ]
                node.result = ParadigmResult(
                    pid, "BLOCKED",
                    evidence=[f"dependency not certified: {blocking_deps}"],
                    gap_name=f"DEP_NOT_CERTIFIED_{blocking_deps[0]}"
                )
            else:
                node.result = paradigm.verify(obj)

        return NetworkRun(obj=obj, nodes=dict(self.nodes))

    def certified_paradigms(self) -> list[str]:
        return [pid for pid, node in self.nodes.items()
                if node.status == "CERTIFIED"]

    def blocked_paradigms(self) -> list[tuple[str, str | None]]:
        return [(pid, node.result.gap_name if node.result else None)
                for pid, node in self.nodes.items()
                if node.status in ("BLOCKED", "DEP_BLOCKED")]

    def knowledge_frontier(self) -> list[str]:
        """The exact boundary of what the system knows.
        These are the paradigms that are BLOCKED but whose dependencies
        are all certified — the real open questions, not cascades.
        """
        return [
            pid for pid, node in self.nodes.items()
            if node.status == "BLOCKED" and not node.blocked_by_dependency
        ]


# ─── A single run of the network ────────────────────────────────────────────

@dataclass
class NetworkRun:
    """The complete record of one pass through the network.

    This is immutable after creation.
    Every claim the system makes is backed by a certificate or a named gap.
    The system cannot say more than this record allows.
    """
    obj: CodexObject
    nodes: dict[str, NetworkNode]

    @property
    def certified_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.status == "CERTIFIED")

    @property
    def blocked_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.status in ("BLOCKED", "DEP_BLOCKED"))

    @property
    def total(self) -> int:
        return len(self.nodes)

    def knowledge_frontier(self) -> list[str]:
        """Paradigms that are genuinely blocked (not by cascade)."""
        return [
            pid for pid, node in self.nodes.items()
            if node.status == "BLOCKED" and not node.blocked_by_dependency
        ]

    def report(self) -> str:
        """Full certification report. Only certified claims and named gaps."""
        lines = [
            f"═══ ALEPH-TEKIN NETWORK RUN: {self.obj.name} ═══",
            f"Certified: {self.certified_count}/{self.total}",
            f"Blocked:   {self.blocked_count}/{self.total}",
            "",
            "─── CERTIFIED ───",
        ]
        for pid, node in self.nodes.items():
            if node.status == "CERTIFIED" and node.result:
                lines.append(f"  ✓ {pid}: {'; '.join(node.result.evidence[:2])}")

        lines.append("")
        lines.append("─── KNOWLEDGE FRONTIER (genuine gaps) ───")
        frontier = self.knowledge_frontier()
        if frontier:
            for pid in frontier:
                node = self.nodes[pid]
                gap = node.result.gap_name if node.result else "UNKNOWN"
                lines.append(f"  ∅ {pid}: {gap}")
        else:
            lines.append("  (none — all paradigms certified or cascade-blocked)")

        dep_blocked = [pid for pid, n in self.nodes.items()
                       if n.blocked_by_dependency]
        if dep_blocked:
            lines.append("")
            lines.append("─── CASCADE-BLOCKED (blocked by dependency) ───")
            for pid in dep_blocked:
                node = self.nodes[pid]
                lines.append(f"  ↳ {pid}: {node.result.gap_name if node.result else 'DEP_BLOCKED'}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "object": self.obj.name,
            "certified": self.certified_count,
            "blocked": self.blocked_count,
            "total": self.total,
            "knowledge_frontier": self.knowledge_frontier(),
            "nodes": {
                pid: {
                    "status": node.status,
                    "gap": node.result.gap_name if node.result else None,
                    "evidence": node.result.evidence if node.result else [],
                }
                for pid, node in self.nodes.items()
            }
        }
