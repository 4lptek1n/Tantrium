"""Certification engine: the stateless running system.

Takes any input (number, matrix, molecule, signal-as-number).
Passes it through the 22+1 Aleph-Tekin paradigms.
Emits only what it can certify. Names every gap it cannot close.

This is a pure, stateless certification machine. It has no learned manifold,
no language layer, no autonomous growth — it certifies what is put in front of
it and forgets nothing because it remembers nothing. Every run is reproducible
from the input alone.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tantrium.core.concept import Concept
from tantrium.core.encoder import UniversalEncoder
from tantrium.core.network import CertificationPipeline, CertificationRun
from tantrium.core.paradigms import CertifiableObject
from tantrium.domains.bridge import SemanticBridge


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Empty stand-ins ──────────────────────────────────────────────────────
# The grounding / truth axes were proximity checks against a learned manifold.
# In the stateless machine there is no learned reference set, so these stand-ins
# carry no concepts and the axes degrade to "N/A" (see grounding.py / truth.py).

class _NullManifold:
    concepts: dict = {}

    def nearest(self, concept: object, n: int = 5):
        return []


class _NullTau:
    edges: dict = {}
    nodes: dict = {}


# ─── Certification engine ──────────────────────────────────────────────────

class CertificationEngine:
    """The Aleph-Tekin certification engine — stateless.

    What it does:
      - Take any CertifiableObject (or raw input) and run all 22+1 paradigms
      - Certify what is certifiable; name every gap precisely
      - Expose the 4-axis CoreMachine (certification + transport + confidence;
        grounding/truth are N/A without a learned manifold)

    What it cannot do:
      - Lie (every claim requires a certificate)
      - Hallucinate (unknown ≠ false; it says UNKNOWN with a named gap)
    """

    def __init__(
        self,
        graph_path: str | Path = "tantrium/theorem_graph/theorem_graph.yaml",
        num_moments: int = 8,
    ) -> None:
        self.network = CertificationPipeline()
        self.encoder = UniversalEncoder(num_moments=num_moments)
        self.bridge = SemanticBridge(str(graph_path))
        self.manifold = _NullManifold()
        self.tau = _NullTau()
        self._run_count = 0
        self._core_machine = None
        from tantrium.core.grounding import GroundingCertifier
        self.grounder = GroundingCertifier(self)

    # ─── CoreMachine: one encode → one process → axes ─────────────────────
    @property
    def core(self) -> "object":
        if self._core_machine is None:
            from tantrium.core.unified import CoreMachine
            self._core_machine = CoreMachine(self)
        return self._core_machine

    def certify_unified(self, input_data: object, name: str | None = None,
                        adaptive: bool = True) -> "object":
        """Short path: engine.core.certify(input_data)."""
        return self.core.certify(input_data, name=name, adaptive=adaptive)

    # ─── Core: process any object ──────────────────────────────────────────
    def process(self, obj: CertifiableObject) -> CertificationRun:
        """Run any object through the 22+1 paradigms. Returns the full record."""
        self._run_count += 1
        return self.network.run(obj)

    def process_concept(self, concept: Concept) -> CertificationRun:
        """Run a concept (moment sequence) through the network."""
        return self.process(concept.to_codex_object())

    def process_raw(self, input: Any, name: str | None = None) -> CertificationRun:
        """Encode ANY raw input (number/matrix/molecule/signal) then certify."""
        obj = self.encoder.encode(input, name)
        return self.process(obj)

    # ─── Status ────────────────────────────────────────────────────────────
    def status(self) -> str:
        return "\n".join([
            "═══ TANTRIUM CERTIFICATION ENGINE ═══",
            f"Runs completed:    {self._run_count}",
            f"Network paradigms: {len(self.network.nodes)}",
            "",
            "Stateless. The engine certifies or names its gap.",
            "It does not predict. It does not guess.",
            "Every result is reproducible from the input alone.",
        ])
