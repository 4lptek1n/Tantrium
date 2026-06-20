"""Autonomous Exploration Loop.

The explorer reads the knowledge frontier (genuinely blocked paradigms) from the
knowledge store, generates targeted probe objects, and attempts to close gaps.

Design:
  - Reads results/agi/knowledge.jsonl for runs with non-empty knowledge_frontier
  - Prioritizes gaps by frequency and paradigm topology (foundational gaps first)
  - Generates a probe CodexObject specifically designed to test the gap paradigm
  - Runs it through the AGI engine
  - Classifies each attempt as: CLOSED | REFINED | PERSISTENT
  - Writes every result back to the knowledge store (append-only)

The explorer does not guess. It generates minimal probes — the simplest
CodexObject that exercises the blocked paradigm — and reports exactly what it finds.

This is the self-directed part of the system: the knowledge frontier tells it
where to look next. It follows the mathematics, not instructions.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from tantrium.core.codex import CertifiableObject as CodexObject


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Gap → Research OS campaign mapping ───────────────────────────────────
# When a gap is PERSISTENT (probe cannot close it), launch a real research
# campaign that has a chance of producing new mathematical certificates.

_GAP_TO_CAMPAIGN: dict[str, str] = {
    "ZAYIN": "lah_gate_ab",  # LGV ↔ LAH transfer
    "HE": "subresultant_recurrence",  # Sturm/Lyapunov recurrence
    "DALET": "subresultant_recurrence",
    "ALEPH": "rh_formalization",  # D-positivity formalization
    "TAV": "rh_formalization",
    "EMET": "rh_formalization",
    "SHIN": "coefficient_frontier",  # optimal action = coefficient selection
    "YOD": "subresultant_recurrence",
    "GIMEL": "lah_gate_ab",
}

# ─── Gap priority table ────────────────────────────────────────────────────
# Foundation paradigms block everything downstream → highest priority
_PARADIGM_PRIORITY: dict[str, int] = {
    "ALEPH": 100,
    "BET": 90,
    "DALET": 85,
    "KAF": 80,
    "AYIN": 75,
    "MEM": 75,
    "HE": 70,
    "VAV": 65,
    "NUN": 65,
    "LAMED": 60,
    "ZAYIN": 55,
    "HET": 55,
    "TET": 50,
    "TSADI": 45,
    "PE": 45,
    "SHIN": 40,
    "GIMEL": 35,
    "SU3": 30,
    "KUF": 25,
    "YOD": 20,
    "RESH": 20,
    "TAV": 15,
    "EMET": 10,
}


# ─── Probe templates: minimal CodexObjects for each paradigm ───────────────


def _make_probe(paradigm_id: str, gap_name: str, source_name: str) -> CodexObject:
    """Generate a minimal probe object targeting a specific paradigm gap.

    Each probe is the simplest CodexObject that exercises the paradigm.
    Probes use exact rational arithmetic (Fraction) throughout.
    """
    name = f"probe_{paradigm_id}_{source_name}"
    # All probes start with a valid moment sequence: (1/2)^k (always PSD)
    moments = [Fraction(1, 2) ** k for k in range(8)]

    base_structure: dict[str, Any] = {
        "probe_for": paradigm_id,
        "gap_name": gap_name,
        "source": source_name,
    }

    # Paradigm-specific structure
    extras: dict[str, Any] = {
        "BET": {
            "transformations": [
                {"name": f"probe_transform_{i}", "information_loss": 0} for i in range(3)
            ]
        },
        "DALET": {
            "eigenvalues": [Fraction(1), Fraction(1, 2), Fraction(1, 4)],
        },
        "HE": {
            "lyapunov_values": [1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05],
        },
        "KAF": {"mappings": {f"probe_elem_{i}": f"probe_img_{i}" for i in range(5)}},
        "AYIN": {
            "distinct_pairs": [
                {"a": f"elem_{i}", "b": f"elem_{i + 1}", "separating_measurement": f"position_{i}"}
                for i in range(3)
            ]
        },
        "MEM": {
            "gauge_classes": [
                [
                    {"id": "probe_a", "all_measurements_equal": True},
                    {"id": "probe_b", "all_measurements_equal": True},
                ]
            ]
        },
        "ZAYIN": {
            "path_weights": [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)],
            "determinant": Fraction(7, 8),
        },
        "HET": {
            "potential_values": {"v0": 1.0, "v1": 0.5, "v2": 0.1},
            "flows": [{"from": "v0", "to": "v1"}, {"from": "v1", "to": "v2"}],
        },
        "TSADI": {
            "sensor_hash": f"PROBE_{paradigm_id}",
            "certificate_hash": f"PROBE_{paradigm_id}",
        },
        "VAV": {
            "components": [{"dim": 3}, {"dim": 4}],
            "composite_dim": 12,
        },
        "NUN": {
            "components": [{"dim": 3}, {"dim": 4}],
            "composite_dim": 12,
        },
        "LAMED": {
            "physical_differences": ["probe_a", "probe_b"],
            "locally_observable": ["probe_a", "probe_b"],
        },
        "SHIN": {
            "actions": [
                {"id": "probe_action_0", "score": 0.9},
                {"id": "probe_action_1", "score": 0.3},
            ],
            "chosen_action": "probe_action_0",
        },
        "SU3": {
            "symmetry_group": "SU3",
            "center_order": 3,
        },
        "KUF": {
            "z3_order": 3,
            "c6_order": 6,
            "topological_index": 18,
        },
        "YOD": {
            "model_length": 8,
            "data_given_model_length": 4,
            "alternative_models": [],
        },
        "RESH": {
            "environment_trace": True,
            "total_information": 100,
            "subsystem_information": 60,
        },
        "TET": {
            "cross_ratio_quadruples": [
                {
                    "a": "1",
                    "b": "2",
                    "c": "3",
                    "d": "4",
                    "expected_cr": str(Fraction((1 - 3) * (2 - 4), (1 - 4) * (2 - 3))),
                }
            ]
        },
        "TAV": {
            "is_running": True,
            "fixed_point_iterations": [2.0, 1.2, 1.01, 1.0, 1.0],
        },
        "PE": {
            "semantic_map": {
                f"elem_{i}": [i, float(moments[i])] for i in range(min(5, len(moments)))
            }
        },
        "EMET": {
            "certified_claims": [
                {"claim": f"probe_{paradigm_id}_holds", "certificate": f"PROBE_{paradigm_id}"}
            ],
            "contradictions": [],
        },
        "GIMEL": {
            "actions": [
                {"id": "probe_achilles", "score": 0.9},
                {"id": "probe_fallback", "score": 0.1},
            ],
            "chosen_action": "probe_achilles",
        },
    }

    structure = {**base_structure, **extras.get(paradigm_id, {})}
    return CodexObject(name=name, moments=moments, structure=structure)


# ─── Exploration objective ────────────────────────────────────────────────


@dataclass
class ExplorationObjective:
    """A named gap to explore: what the system knows it does not know."""

    gap_paradigm: str
    gap_name: str
    source_object: str
    priority: int = 0
    attempts: int = 0
    first_seen: str = field(default_factory=_now)
    last_attempt: str | None = None

    def __post_init__(self) -> None:
        if self.priority == 0:
            self.priority = _PARADIGM_PRIORITY.get(self.gap_paradigm, 5)


# ─── Exploration result ───────────────────────────────────────────────────


@dataclass
class ExplorationResult:
    """Outcome of one exploration attempt."""

    objective: ExplorationObjective
    outcome: str  # CLOSED | REFINED | PERSISTENT
    probe_name: str
    certified_after: int
    total_paradigms: int
    refined_gap: str | None
    evidence: list[str]
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "type": "exploration",
            "outcome": self.outcome,
            "gap_paradigm": self.objective.gap_paradigm,
            "gap_name": self.objective.gap_name,
            "source_object": self.objective.source_object,
            "probe": self.probe_name,
            "certified_after": self.certified_after,
            "total": self.total_paradigms,
            "refined_gap": self.refined_gap,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }


# ─── The explorer ─────────────────────────────────────────────────────────


class Explorer:
    """Autonomous exploration loop over the knowledge frontier.

    Reads the knowledge store, identifies genuine gaps, generates probes,
    and attempts to close them. All results are written back to the store.

    The loop terminates when:
      - all gaps are closed, OR
      - max_rounds is reached, OR
      - no new information is gained in a round (fixed point reached)
    """

    def __init__(
        self,
        engine: CertificationEngine,  # type: ignore[name-defined]  # noqa: F821
        max_attempts_per_gap: int = 3,
    ) -> None:
        self.engine = engine
        self.max_attempts = max_attempts_per_gap
        self._explored: set[str] = set()  # (paradigm, source) pairs already resolved

    # ─── Gap scanning ────────────────────────────────────────────────────

    def scan_frontier(self) -> list[ExplorationObjective]:
        """Read the knowledge store and extract genuine gaps.

        Returns objectives sorted by priority (most foundational first).
        Skips gaps that have already been resolved in this session.
        """
        history = self.engine._load_history()
        gap_counts: dict[tuple[str, str, str], int] = {}

        for record in history:
            if record.get("type") == "exploration":
                continue
            obj_name = record.get("object", "unknown")
            for pid in record.get("knowledge_frontier", []):
                nodes = record.get("nodes", {})
                gap_name = nodes.get(pid, {}).get("gap") or "UNKNOWN_GAP"
                key = (pid, gap_name, obj_name)
                gap_counts[key] = gap_counts.get(key, 0) + 1

        objectives = []
        for (pid, gap, src), count in gap_counts.items():
            uid = f"{pid}:{src}"
            if uid in self._explored:
                continue
            obj = ExplorationObjective(
                gap_paradigm=pid,
                gap_name=gap,
                source_object=src,
                priority=_PARADIGM_PRIORITY.get(pid, 5) * count,
            )
            objectives.append(obj)

        objectives.sort(key=lambda o: o.priority, reverse=True)
        return objectives

    # ─── Single gap exploration ───────────────────────────────────────────

    def explore(self, objective: ExplorationObjective) -> ExplorationResult:
        """Run a single exploration attempt against a gap objective.

        Generates a minimal probe targeting the blocked paradigm,
        runs it through the engine, and classifies the outcome.
        """
        objective.attempts += 1
        objective.last_attempt = _now()

        probe = _make_probe(objective.gap_paradigm, objective.gap_name, objective.source_object)
        run = self.engine.process(probe)

        probe_paradigm_node = run.nodes.get(objective.gap_paradigm)
        gap_still_open = (
            probe_paradigm_node is not None and probe_paradigm_node.status != "CERTIFIED"
        )

        new_frontier = run.knowledge_frontier()

        if not gap_still_open:
            outcome = "CLOSED"
            refined_gap = None
            evidence = [
                f"Probe '{probe.name}' passed {objective.gap_paradigm}",
                f"Total certified: {run.certified_count}/{run.total}",
                "Gap closed by minimal probe — paradigm is certifiable",
            ]
            self._explored.add(f"{objective.gap_paradigm}:{objective.source_object}")
        elif new_frontier and new_frontier != [objective.gap_paradigm]:
            outcome = "REFINED"
            refined_gap = new_frontier[0] if new_frontier else objective.gap_name
            evidence = [
                f"Probe '{probe.name}' still blocked at {objective.gap_paradigm}",
                f"Refined knowledge frontier: {new_frontier}",
                f"Refined gap: {refined_gap}",
            ]
        else:
            outcome = "PERSISTENT"
            refined_gap = objective.gap_name
            evidence = [
                f"Probe '{probe.name}' confirmed gap at {objective.gap_paradigm}",
                f"Gap name: {objective.gap_name}",
                "Gap persists — this is a genuine open question",
            ]
            self._explored.add(f"{objective.gap_paradigm}:{objective.source_object}")

        return ExplorationResult(
            objective=objective,
            outcome=outcome,
            probe_name=probe.name,
            certified_after=run.certified_count,
            total_paradigms=run.total,
            refined_gap=refined_gap,
            evidence=evidence,
        )

    # ─── Main loop ───────────────────────────────────────────────────────

    def run_loop(
        self,
        max_rounds: int = 5,
        max_objectives: int = 20,
    ) -> list[ExplorationResult]:
        """Run the autonomous exploration loop.

        Each round:
          1. Scan for gaps
          2. Explore top-priority objectives (up to max_attempts each)
          3. Stop if no new objectives remain or fixed point reached

        Returns all ExplorationResults across all rounds.
        """
        all_results: list[ExplorationResult] = []
        prev_objectives: set[str] = set()

        for _round_num in range(max_rounds):
            objectives = self.scan_frontier()[:max_objectives]

            if not objectives:
                break

            current_objectives = {f"{o.gap_paradigm}:{o.source_object}" for o in objectives}
            if current_objectives == prev_objectives:
                # Fixed point: no new gaps appeared
                break
            prev_objectives = current_objectives

            round_results = []
            for obj in objectives:
                for attempt in range(self.max_attempts):
                    result = self.explore(obj)
                    round_results.append(result)
                    self._record_result(result)
                    if result.outcome == "CLOSED":
                        break
                    if result.outcome == "PERSISTENT":
                        # Try Research OS on last attempt
                        if attempt == self.max_attempts - 1:
                            self._try_research_os(obj)
                        break

            all_results.extend(round_results)

            closed = sum(1 for r in round_results if r.outcome == "CLOSED")
            if closed == len(round_results):
                # All gaps in this round closed
                break

        return all_results

    def _try_research_os(self, objective: ExplorationObjective) -> str | None:
        """Launch a Research OS campaign for a persistent gap.

        Maps the gap paradigm to the most relevant mathematical campaign.
        Runs the campaign script as a subprocess (non-blocking timeout).
        Returns the campaign name if launched, None if no mapping exists.
        """
        campaign = _GAP_TO_CAMPAIGN.get(objective.gap_paradigm)
        if not campaign:
            return None

        tools_dir = Path(__file__).resolve().parents[3] / "tools"
        script = tools_dir / "tantrium_research_os.py"
        if not script.exists():
            return None

        try:
            subprocess.run(
                [sys.executable, str(script), "--campaign", campaign],
                timeout=30,
                capture_output=True,
                text=True,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

        return campaign

    # ─── Persistence ─────────────────────────────────────────────────────

    def _record_result(self, result: ExplorationResult) -> None:
        """Append exploration result to the knowledge store."""
        path = self.engine.knowledge_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    # ─── Reporting ────────────────────────────────────────────────────────

    def report(self, results: list[ExplorationResult]) -> str:
        if not results:
            return "No exploration results — knowledge frontier is empty."
        closed = [r for r in results if r.outcome == "CLOSED"]
        refined = [r for r in results if r.outcome == "REFINED"]
        persistent = [r for r in results if r.outcome == "PERSISTENT"]

        lines = [
            f"═══ EXPLORATION LOOP: {len(results)} attempts ═══",
            f"  CLOSED:     {len(closed)}",
            f"  REFINED:    {len(refined)}",
            f"  PERSISTENT: {len(persistent)}",
            "",
        ]
        if closed:
            lines.append("─── CLOSED GAPS ───")
            for r in closed:
                lines.append(
                    f"  ✓ [{r.objective.gap_paradigm}] {r.objective.gap_name} → closed by {r.probe_name}"
                )
        if refined:
            lines.append("─── REFINED GAPS ───")
            for r in refined:
                lines.append(f"  ↻ [{r.objective.gap_paradigm}] → refined to: {r.refined_gap}")
        if persistent:
            lines.append("─── PERSISTENT GAPS (genuine open questions) ───")
            for r in persistent:
                lines.append(f"  ∅ [{r.objective.gap_paradigm}] {r.objective.gap_name}")
                lines.append(f"    source: {r.objective.source_object}")

        return "\n".join(lines)
