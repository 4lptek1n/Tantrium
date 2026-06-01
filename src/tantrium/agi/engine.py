"""AGI Engine: the running system.

Takes any input (mathematical, linguistic, physical).
Passes it through the 22+1 Aleph-Tekin paradigms.
Emits only what it can certify. Names every gap it cannot close.

The engine does not predict. It does not guess.
It flows through the network and reports exactly what it finds.

Integration with the existing Tantrium theorem graph and Atlas:
  - Certified results are added to the theorem graph as new nodes.
  - Named gaps are recorded as obstructions.
  - The Atlas accumulates. The engine never forgets what it proved.
  - The knowledge frontier grows — not by losing old knowledge, but by
    extending it. Every run adds to the foundation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from tantrium.agi.codex import CodexObject, ParadigmResult
from tantrium.agi.network import AlephTekinNetwork, NetworkRun
from tantrium.agi.semantic import Concept, SemanticManifold


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── AGI Engine ────────────────────────────────────────────────────────────

class AGIEngine:
    """The Aleph-Tekin AGI engine.

    This is not a chatbot. It is not a predictor.
    It is a certification machine with a named-gap memory.

    What it can do:
      - Take any CodexObject and run it through all 22+1 paradigms
      - Certify what is certifiable
      - Name every gap precisely
      - Remember every result (never loses what it proved)
      - Grow its knowledge frontier over time

    What it cannot do:
      - Lie (every claim requires a certificate)
      - Hallucinate (unknown ≠ false; it says UNKNOWN with a named gap)
      - Forget (the knowledge store is append-only)

    Language topology:
      - Concepts enter as moment sequences (Concept objects)
      - They are converted to CodexObjects and run through the paradigms
      - The engine only emits concepts that pass the Aleph filter
      - Meaning emerges from the fixed-point structure (Tav)
    """

    def __init__(
        self,
        knowledge_path: str | Path = "results/agi/knowledge.jsonl",
        graph_path: str | Path = "tantrium/theorem_graph/theorem_graph.yaml",
    ) -> None:
        self.network = AlephTekinNetwork()
        self.knowledge_path = Path(knowledge_path)
        self.graph_path = Path(graph_path)
        self.manifold = SemanticManifold()
        self._run_count = 0
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)

    # ─── Core: process any object ──────────────────────────────────────────

    def process(self, obj: CodexObject) -> NetworkRun:
        """Run any object through the 22+1 paradigms.
        Returns a NetworkRun — the complete certification record.
        """
        self._run_count += 1
        run = self.network.run(obj)
        self._record(run)
        self._sync_theorem_graph(run)
        return run

    def process_concept(self, concept: Concept) -> NetworkRun:
        """Run a linguistic/semantic concept through the network.
        The concept's moment sequence is the input.
        Same engine. Same mathematics. Language is not special.
        """
        return self.process(concept.to_codex_object())

    # ─── Respond: what the system says ─────────────────────────────────────

    def respond(self, query: str, obj: CodexObject | None = None) -> str:
        """Generate a response to a query.

        The system responds ONLY from certified knowledge.
        If it does not know, it says so — with a precise named gap.
        This is not a limitation. It is the architecture.

        A system that only says what it can prove is more powerful than
        a system that says anything — because every word it emits is true.
        """
        if obj is None:
            return self._respond_from_memory(query)

        run = self.process(obj)
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        lines = [f"Query: {query}", f"Object: {obj.name}", ""]

        if certified == total:
            lines.append(f"CERTIFIED ({certified}/{total} paradigms passed).")
            lines.append("This object satisfies all 22+1 Aleph-Tekin paradigms.")
            lines.append("No gaps. No open questions for this object.")
        elif certified > 0:
            lines.append(f"PARTIALLY CERTIFIED: {certified}/{total} paradigms passed.")
            lines.append("")
            lines.append("What I know:")
            for pid, node in run.nodes.items():
                if node.status == "CERTIFIED" and node.result:
                    lines.append(f"  ✓ {pid}")
            lines.append("")
            if frontier:
                lines.append("What I do not know (knowledge frontier):")
                for pid in frontier:
                    node = run.nodes[pid]
                    gap = node.result.gap_name if node.result else "UNKNOWN"
                    lines.append(f"  ∅ {pid}: {gap}")
                lines.append("")
                lines.append("These are not failures. They are the precise boundary of knowledge.")
        else:
            lines.append("BLOCKED at the first paradigm (ALEPH — Positivity).")
            if run.nodes.get("ALEPH") and run.nodes["ALEPH"].result:
                lines.append(f"Gap: {run.nodes['ALEPH'].result.gap_name}")
            lines.append("The object does not pass the existence filter.")
            lines.append("It may not be real in this manifold.")

        return "\n".join(lines)

    def _respond_from_memory(self, query: str) -> str:
        """Respond from recorded knowledge without a new object."""
        history = self._load_history()
        relevant = [h for h in history if query.lower() in h.get("object", "").lower()]
        if not relevant:
            return (
                f"Query: {query}\n"
                f"UNKNOWN — no certified knowledge about '{query}'.\n"
                f"Named gap: NO_RECORD_IN_KNOWLEDGE_STORE\n"
                f"Provide an object to certify, and the engine will build from there."
            )
        latest = relevant[-1]
        lines = [
            f"Query: {query}",
            f"From memory (run at {latest.get('timestamp', 'unknown')}): "
            f"certified {latest.get('certified', 0)}/{latest.get('total', 0)} paradigms.",
        ]
        frontier = latest.get("knowledge_frontier", [])
        if frontier:
            lines.append(f"Known gaps: {', '.join(frontier)}")
        return "\n".join(lines)

    # ─── Language: teach the manifold a concept ────────────────────────────

    def teach(self, concept: Concept) -> str:
        """Attempt to add a concept to the semantic manifold.

        The Aleph filter decides if it exists.
        If it passes, the manifold grows.
        If it fails, a named gap explains why.

        The system cannot be taught incoherent concepts.
        This is the architecture — not a restriction.
        """
        result = concept.verify_existence()
        if result.is_certified():
            try:
                self.manifold.add(concept)
                return (
                    f"CERTIFIED: concept '{concept.name}' exists in the manifold.\n"
                    f"Domain: {concept.domain}\n"
                    f"Moments: {[str(m) for m in concept.moments[:5]]}"
                    f"{'...' if len(concept.moments) > 5 else ''}\n"
                    f"Hankel PSD: yes.\n"
                    f"The concept is real."
                )
            except Exception as e:
                return f"BLOCKED: {e}"
        else:
            return (
                f"BLOCKED: concept '{concept.name}' rejected by Aleph filter.\n"
                f"Gap: {result.gap_name}\n"
                f"Evidence: {result.evidence}\n"
                f"This concept does not exist in the real manifold.\n"
                f"It cannot be taught because it is not real."
            )

    def nearest_concepts(self, concept: Concept, n: int = 5) -> list[tuple[str, str]]:
        """Find the n nearest certified concepts (gradient direction on manifold)."""
        if not self.manifold.concepts:
            return []
        neighbors = self.manifold.nearest(concept, n)
        return [(name, str(dist)) for name, dist in neighbors]

    # ─── Persistence ────────────────────────────────────────────────────────

    def _record(self, run: NetworkRun) -> None:
        """Append run to the knowledge store. The store is append-only."""
        record = {
            "timestamp": _now(),
            "run": self._run_count,
            **run.to_dict(),
        }
        with self.knowledge_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _load_history(self) -> list[dict]:
        if not self.knowledge_path.exists():
            return []
        records = []
        for line in self.knowledge_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    def _sync_theorem_graph(self, run: NetworkRun) -> None:
        """Sync certified results and named gaps to the theorem graph.

        Certified paradigms become new theorem nodes (status: proven).
        Named gaps become obstruction nodes (status: blocked).
        The graph accumulates. Nothing is lost.
        """
        if not self.graph_path.exists():
            return
        try:
            from tantrium.theorem_graph.graph_store import GraphStore
            from tantrium.theorem_graph.state_machine import TheoremNode
        except ImportError:
            return

        store = GraphStore(self.graph_path)
        graph = store.load()

        for pid, node in run.nodes.items():
            theorem_id = f"AGI_{pid}_{run.obj.name}".replace(" ", "_").upper()
            if node.status == "CERTIFIED" and theorem_id not in graph.nodes:
                graph.add(TheoremNode(
                    theorem_id=theorem_id,
                    title=f"[AGI] {pid} certified for {run.obj.name}",
                    status="proven",
                    depends_on=[
                        f"AGI_{dep}_{run.obj.name}".replace(" ", "_").upper()
                        for dep in self.network.nodes[pid].paradigm.depends_on
                        if dep in self.network.nodes
                    ],
                    artifacts=[str(self.knowledge_path)],
                    notes=[f"auto-certified by AGI engine at {_now()}"],
                ))
            elif node.status == "BLOCKED" and not node.blocked_by_dependency:
                gap = node.result.gap_name if node.result else "UNKNOWN_GAP"
                store.add_obstruction(
                    theorem_id=theorem_id,
                    title=f"[AGI] {pid} blocked: {gap}",
                    artifacts=[str(self.knowledge_path)],
                    note=f"named gap '{gap}' for object '{run.obj.name}' at {_now()}",
                )
                graph = store.load()

        graph = store.propagate(graph)
        store.save(graph)

    # ─── Status ────────────────────────────────────────────────────────────

    def status(self) -> str:
        history = self._load_history()
        manifold_size = len(self.manifold.concepts)
        lines = [
            "═══ ALEPH-TEKIN AGI ENGINE STATUS ═══",
            f"Runs completed:      {self._run_count}",
            f"Knowledge records:   {len(history)}",
            f"Manifold concepts:   {manifold_size}",
            f"Network paradigms:   {len(self.network.nodes)}",
            "",
            "The engine certifies or names its gap.",
            "It does not predict. It does not guess.",
            "Every word it emits is provable.",
        ]
        if history:
            last = history[-1]
            lines.append(
                f"\nLast run: {last.get('object', '?')} — "
                f"{last.get('certified', 0)}/{last.get('total', 0)} certified"
            )
        return "\n".join(lines)
