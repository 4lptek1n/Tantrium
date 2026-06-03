"""Natural Language Output: certified speech.

The speaker maps certified NetworkRun paths to fluent natural language.
It only says what the system can prove. Silence is not failure — it is precision.

Every word the speaker emits is backed by a certificate.
Every gap is named, not silenced.

Architecture:
  - Paradigm templates: one sentence per certified paradigm
  - Gap templates: one sentence per named gap (no evasion)
  - Narrative modes: brief (one sentence), standard (paragraph), detailed (full report)
  - Comparison: what A and B share vs. where they diverge

The speaker does not invent. It reads the NetworkRun and translates certificates
to human language. The translation is lossless — every certified fact appears.

Language topology (Pe paradigm):
  - The manifold proximity determines which words are chosen
  - Nearest concepts in the SemanticManifold inform phrasing
  - This is not metaphor — it is the same geometry as the proof system
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tantrium.core.network import CertificationRun as NetworkRun
from tantrium.core.semantic import Concept, SemanticManifold


# ─── Paradigm sentence templates ──────────────────────────────────────────

_CERTIFIED_TEMPLATES: dict[str, str] = {
    "ALEPH":  "{name} exists in the real manifold. Its moment sequence is positive semi-definite.",
    "BET":    "All transformations of {name} are information-lossless. Nothing is lost.",
    "GIMEL":  "The Achilles point of {name} is identified. The optimal move is known.",
    "DALET":  "The spectral structure of {name} is non-negative. Eigenvalues ≥ 0.",
    "HE":     "The system {name} has a Lyapunov attractor. It flows toward a stable state.",
    "VAV":    "The tensor composition of {name} is dimensionally consistent.",
    "ZAYIN":  "The path system of {name} satisfies the LGV lemma. Paths are non-intersecting.",
    "HET":    "The gradient of {name} flows downhill. The potential is monotone decreasing.",
    "TET":    "The cross-ratio of {name} is preserved. Projective invariance holds.",
    "YOD":    "The minimum description length of {name} is certified. MDL principle satisfied.",
    "KAF":    "The map of {name} is injective. Every element has a unique image.",
    "LAMED":  "The observable structure of {name} is locally visible. No hidden degrees.",
    "MEM":    "The gauge equivalence classes of {name} are identified. Indistinguishables merged.",
    "NUN":    "The dimensional multiplicativity of {name} is certified.",
    "SHIN":   "The optimal action for {name} is chosen. Maximum score selected.",
    "AYIN":   "The distinct pairs in {name} are separable by measurement.",
    "PE":     "The semantic map of {name} is defined. Meaning is geometrically located.",
    "TSADI":  "The sensor-certificate chain of {name} is verified. Hash integrity confirmed.",
    "KUF":    "The topological index of {name} is 18 (Z₃ × C₆). Index certified.",
    "RESH":   "The partial trace of {name} is well-defined. Subsystem information bounded.",
    "EMET":   "{name} is consistent. All certified claims hold. No contradictions detected.",
    "TAV":    "The fixed point of {name} is reached. The system has converged.",
    "SU3":    "The SU(3) symmetry of {name} is certified. Z₃ center of order 3.",
}

_GAP_TEMPLATES: dict[str, str] = {
    "ALEPH":  "{name} does not exist in the real manifold. Gap: {gap}.",
    "BET":    "Information loss detected in {name}. Gap: {gap}.",
    "GIMEL":  "The Achilles point of {name} is not identified. Gap: {gap}.",
    "DALET":  "Spectral non-negativity of {name} is not certified. Gap: {gap}.",
    "HE":     "No Lyapunov attractor found for {name}. Gap: {gap}.",
    "VAV":    "Tensor composition of {name} fails dimensionality check. Gap: {gap}.",
    "ZAYIN":  "LGV path system of {name} is unverified. Gap: {gap}.",
    "HET":    "Gradient flow of {name} is not downhill. Gap: {gap}.",
    "TET":    "Cross-ratio invariance of {name} is not certified. Gap: {gap}.",
    "YOD":    "Minimum description length of {name} is unresolved. Gap: {gap}.",
    "KAF":    "The map of {name} has a collision. Injectivity not certified. Gap: {gap}.",
    "LAMED":  "Observable structure of {name} is not locally visible. Gap: {gap}.",
    "MEM":    "Gauge classes of {name} are not identified. Gap: {gap}.",
    "NUN":    "Dimensional multiplicativity of {name} is not certified. Gap: {gap}.",
    "SHIN":   "No optimal action selected for {name}. Gap: {gap}.",
    "AYIN":   "Distinct pairs in {name} are not measurably separable. Gap: {gap}.",
    "PE":     "Semantic map of {name} is not defined. Gap: {gap}.",
    "TSADI":  "Sensor-certificate integrity of {name} is broken. Gap: {gap}.",
    "KUF":    "Topological index of {name} is not 18. Gap: {gap}.",
    "RESH":   "Partial trace of {name} is not well-defined. Gap: {gap}.",
    "EMET":   "{name} has a contradiction. Consistency not certified. Gap: {gap}.",
    "TAV":    "Fixed point of {name} not reached within iteration budget. Gap: {gap}.",
    "SU3":    "SU(3) symmetry of {name} is not certified. Gap: {gap}.",
}

_DEFAULT_CERTIFIED = "{name} satisfies paradigm {pid}."
_DEFAULT_GAP = "{name} does not satisfy paradigm {pid}. Gap: {gap}."
_DEP_BLOCKED = "Paradigm {pid} of {name} is blocked by an upstream gap ({dep_gap})."


# ─── A single certified statement ────────────────────────────────────────

@dataclass
class CertifiedStatement:
    """One true sentence — backed by a certificate."""
    paradigm_id: str
    status: str       # CERTIFIED | GAP | DEP_BLOCKED
    text: str
    evidence: list[str] = field(default_factory=list)


# ─── The speaker ──────────────────────────────────────────────────────────

class Speaker:
    """Maps certified NetworkRuns to natural language.

    Only emits what is certified. Names every gap precisely.
    Never invents. Never guesses. Never omits a named gap.

    detail levels:
      "line"     — one sentence: "X is certified" or "X has gap Y"
      "brief"    — key facts only (ALEPH + frontier)
      "standard" — all certified paradigms + all genuine gaps
      "full"     — standard + cascade-blocked + evidence snippets
    """

    def __init__(self, manifold: SemanticManifold | None = None) -> None:
        self.manifold = manifold or SemanticManifold()

    # ─── Core: one statement per paradigm ────────────────────────────────

    def _certified_sentence(self, pid: str, name: str) -> str:
        template = _CERTIFIED_TEMPLATES.get(pid, _DEFAULT_CERTIFIED)
        return template.format(name=name, pid=pid)

    def _gap_sentence(self, pid: str, name: str, gap: str) -> str:
        template = _GAP_TEMPLATES.get(pid, _DEFAULT_GAP)
        return template.format(name=name, pid=pid, gap=gap)

    def _dep_blocked_sentence(self, pid: str, name: str, dep_gap: str) -> str:
        return _DEP_BLOCKED.format(pid=pid, name=name, dep_gap=dep_gap)

    def _build_statements(self, run: NetworkRun) -> list[CertifiedStatement]:
        stmts = []
        for pid, node in run.nodes.items():
            name = run.obj.name
            if node.status == "CERTIFIED" and node.result:
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="CERTIFIED",
                    text=self._certified_sentence(pid, name),
                    evidence=node.result.evidence[:2],
                ))
            elif node.blocked_by_dependency and node.result:
                dep_gap = node.result.gap_name or "UNKNOWN_DEP"
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="DEP_BLOCKED",
                    text=self._dep_blocked_sentence(pid, name, dep_gap),
                ))
            elif node.status == "BLOCKED" and node.result:
                gap = node.result.gap_name or "UNNAMED_GAP"
                stmts.append(CertifiedStatement(
                    paradigm_id=pid,
                    status="GAP",
                    text=self._gap_sentence(pid, name, gap),
                    evidence=node.result.evidence[:2],
                ))
        return stmts

    # ─── Narrate ─────────────────────────────────────────────────────────

    def narrate(self, run: NetworkRun, detail: str = "standard") -> str:
        """Narrate a NetworkRun in natural language.

        detail:
          "line"     — single-line summary
          "brief"    — key facts (existence + frontier)
          "standard" — all certified + genuine gaps
          "full"     — all statements including cascade-blocked
        """
        name = run.obj.name
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        if detail == "line":
            if certified == total:
                return f"{name} is fully certified ({certified}/{total} paradigms)."
            elif certified == 0:
                return f"{name} is blocked at the first paradigm. It does not exist in this manifold."
            else:
                gaps = ", ".join(frontier) if frontier else "none"
                return f"{name}: {certified}/{total} paradigms certified. Open questions: {gaps}."

        stmts = self._build_statements(run)
        certified_stmts = [s for s in stmts if s.status == "CERTIFIED"]
        gap_stmts = [s for s in stmts if s.status == "GAP"]
        dep_stmts = [s for s in stmts if s.status == "DEP_BLOCKED"]

        lines = []

        if detail in ("brief", "standard", "full"):
            # Opening
            if certified == total:
                lines.append(
                    f"{name} is fully certified. All {total} mathematical paradigms are satisfied."
                )
            elif certified == 0:
                lines.append(
                    f"{name} is not certifiable. It does not pass the existence filter."
                )
            else:
                lines.append(
                    f"{name} is partially certified: {certified} of {total} paradigms satisfied."
                )

        if detail == "brief":
            # Only ALEPH + frontier
            aleph = next((s for s in certified_stmts if s.paradigm_id == "ALEPH"), None)
            if aleph:
                lines.append(aleph.text)
            if frontier:
                lines.append(f"Open questions: " + "; ".join(
                    self._gap_sentence(pid, name,
                        run.nodes[pid].result.gap_name if run.nodes[pid].result else "UNKNOWN")
                    for pid in frontier
                ))

        elif detail in ("standard", "full"):
            if certified_stmts:
                lines.append("")
                lines.append("What is known:")
                for s in certified_stmts:
                    lines.append(f"  {s.text}")

            if gap_stmts:
                lines.append("")
                lines.append("What is not yet known (genuine gaps):")
                for s in gap_stmts:
                    lines.append(f"  {s.text}")
                lines.append(
                    "These are the precise boundaries of knowledge — not failures, "
                    "but exact statements of what remains open."
                )

            if detail == "full" and dep_stmts:
                lines.append("")
                lines.append("Cascade-blocked (blocked by upstream gap):")
                for s in dep_stmts:
                    lines.append(f"  {s.text}")

        return "\n".join(lines)

    # ─── Explain: readable paragraph ─────────────────────────────────────

    def explain(self, run: NetworkRun) -> str:
        """Generate a readable paragraph explaining what this object is.

        Uses only certified facts. Expresses the object's certified nature
        in plain language.
        """
        name = run.obj.name
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        certified_pids = [pid for pid, n in run.nodes.items() if n.status == "CERTIFIED"]

        if certified == 0:
            return (
                f"The object '{name}' was tested against all {total} mathematical paradigms "
                f"and failed at the first: existence. Its moment sequence is not positive "
                f"semi-definite. This object does not correspond to any real measure — "
                f"it cannot exist in the manifold. This is not an error. It is precise knowledge."
            )

        # Build readable summary from certified paradigms
        highlights = []
        if "ALEPH" in certified_pids:
            highlights.append("it exists (Hankel PSD certified)")
        if "BET" in certified_pids:
            highlights.append("all its transformations conserve information")
        if "TAV" in certified_pids:
            highlights.append("it converges to a fixed point")
        if "EMET" in certified_pids:
            highlights.append("it is internally consistent")
        if "HE" in certified_pids:
            highlights.append("it has a Lyapunov attractor")
        if "KAF" in certified_pids:
            highlights.append("its mappings are injective")

        highlight_str = "; ".join(highlights) if highlights else f"{certified} paradigms certified"

        parts = [
            f"'{name}' is a certified mathematical object.",
            f"It satisfies {certified} of {total} paradigms: {highlight_str}.",
        ]

        if frontier:
            gap_names = [
                run.nodes[pid].result.gap_name if run.nodes[pid].result else "UNKNOWN"
                for pid in frontier
            ]
            parts.append(
                f"The open questions are: {', '.join(frontier)}. "
                f"Specifically: {'; '.join(gap_names)}. "
                f"These are the exact limits of what the system knows about this object."
            )
        else:
            parts.append("There are no open questions about this object.")

        return " ".join(parts)

    # ─── Compare two runs ─────────────────────────────────────────────────

    def compare(self, run_a: NetworkRun, run_b: NetworkRun) -> str:
        """Compare two objects: what they share and where they diverge."""
        name_a = run_a.obj.name
        name_b = run_b.obj.name

        cert_a = {pid for pid, n in run_a.nodes.items() if n.status == "CERTIFIED"}
        cert_b = {pid for pid, n in run_b.nodes.items() if n.status == "CERTIFIED"}

        shared = cert_a & cert_b
        only_a = cert_a - cert_b
        only_b = cert_b - cert_a

        gap_a = set(run_a.knowledge_frontier())
        gap_b = set(run_b.knowledge_frontier())
        shared_gaps = gap_a & gap_b

        lines = [
            f"═══ COMPARISON: {name_a} vs {name_b} ═══",
            f"",
            f"Shared certified paradigms ({len(shared)}): "
            f"{', '.join(sorted(shared)) or 'none'}",
        ]

        if only_a:
            lines.append(
                f"Certified in {name_a} only ({len(only_a)}): "
                f"{', '.join(sorted(only_a))}"
            )
        if only_b:
            lines.append(
                f"Certified in {name_b} only ({len(only_b)}): "
                f"{', '.join(sorted(only_b))}"
            )
        if shared_gaps:
            lines.append(
                f"Shared open questions ({len(shared_gaps)}): "
                f"{', '.join(sorted(shared_gaps))}"
            )

        if not only_a and not only_b:
            lines.append(
                f"\n{name_a} and {name_b} are certified on exactly the same paradigms. "
                f"They are indistinguishable at the level of the Aleph-Tekin network."
            )
        else:
            lines.append(
                f"\n{name_a} and {name_b} differ on {len(only_a) + len(only_b)} paradigm(s)."
            )

        return "\n".join(lines)

    # ─── Manifold proximity phrasing ──────────────────────────────────────

    def locate(self, concept: Concept, n: int = 3) -> str:
        """Describe where a concept sits on the semantic manifold.

        Uses Pe (semantic mapping) and the manifold's nearest-neighbor geometry.
        Only reports certified proximity — if the manifold is empty, says so.
        """
        if not self.manifold.concepts:
            return (
                f"'{concept.name}' cannot be located on the manifold — "
                f"the manifold is empty. Teach certified concepts first."
            )

        if not concept.is_real():
            return (
                f"'{concept.name}' cannot be located — it does not pass the Aleph filter. "
                f"It does not exist in the real manifold."
            )

        neighbors = self.manifold.nearest(concept, n)
        if not neighbors:
            return f"'{concept.name}' is isolated — no neighbors in the current manifold."

        parts = [f"'{concept.name}' is located on the semantic manifold."]
        parts.append(f"Nearest certified concepts:")
        for name, dist in neighbors:
            parts.append(f"  {name} (distance: {dist})")
        return "\n".join(parts)

    # ─── Synthesize TAU facts into fluent Turkish paragraph ───────────────

    _TR_VERB: dict[str, str] = {
        "IS_A":     "bir {t} türüdür",
        "USES":     "{t} kullanır",
        "ACHIEVES": "{t} elde eder",
        "REQUIRES": "{t} gerektirir",
        "DEFINES":  "{t} tanımlar",
        "COMPOSED": "bileşenlerinden biri {t}",
    }

    def synthesize(
        self,
        concept_name: str,
        facts: dict[str, list[str]],
        max_per_paradigm: int = 3,
    ) -> str:
        """TAU kenarlarından akıcı Türkçe paragraf üret.

        facts: {"IS_A": ["tool", "method"], "ACHIEVES": ["stability"], ...}
        Döner: certified Türkçe paragraf (her cümle TAU'da kenar).
        """
        if not facts:
            return f"'{concept_name}' hakkında TAU'da yeterli bilgi yok."

        sentences: list[str] = []
        for paradigm, targets in facts.items():
            tops = targets[:max_per_paradigm]
            if not tops:
                continue
            tmpl = self._TR_VERB.get(paradigm)
            if tmpl is None:
                continue
            if len(tops) == 1:
                phrase = tmpl.format(t=tops[0])
            elif len(tops) == 2:
                phrase = tmpl.format(t=f"{tops[0]} ve {tops[1]}")
            else:
                joined = ", ".join(tops[:-1]) + " ve " + tops[-1]
                phrase = tmpl.format(t=joined)
            sentences.append(f"'{concept_name}' {phrase}.")

        if not sentences:
            return f"'{concept_name}' için TAU paradigmaları tanımsız."

        return " ".join(sentences)

    # ─── Express a single named gap ───────────────────────────────────────

    def name_gap(self, paradigm_id: str, gap_name: str, obj_name: str) -> str:
        """Express a named gap in precise language.

        A named gap is not an error. It is the system's exact statement of
        what it does not know. This is more powerful than a guess.
        """
        gap_sentence = self._gap_sentence(paradigm_id, obj_name, gap_name)
        return (
            f"{gap_sentence}\n"
            f"This is a named gap: the system knows precisely that it does not know this.\n"
            f"A named gap is more valuable than a guess — it is exact knowledge of the boundary."
        )
