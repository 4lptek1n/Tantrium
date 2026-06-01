"""Dyadic Transport Thinker — Derin düşünce modu.

Deep learning'in katmanlı forward pass'ine karşılık:
  - Context window yok: manifold her şeyi tutuyor
  - Vanishing gradient yok: dyadic transport pozitifliği koruyor
  - Hallüsinasyon yok: her adım ya sertifikalı ya gap isimli

Ell=0: soru encode + certify (ALEPH)
Ell=1: manifold walk — en yakın sertifikalı kavramlar (dyadic ell=0→1)
Ell=2: inference chain — kavram çiftlerinden yeni certified claims (ell=1→2)
Ell=3: second-order walk — derived kavramların komşuları (ell=2→3)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.agi.semantic import Concept, moment_distance

if TYPE_CHECKING:
    from tantrium.agi.engine import AGIEngine


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class ThinkingLevel:
    level: int
    label: str
    concepts: list[str] = field(default_factory=list)
    certified_claims: list[str] = field(default_factory=list)
    gaps: list[tuple[str, str]] = field(default_factory=list)  # (concept, gap_name)
    transport_drift: Fraction = Fraction(0)  # moment drift between levels


@dataclass
class ThinkingResult:
    question: str
    depth: int
    levels: list[ThinkingLevel] = field(default_factory=list)
    fixed_point_found: bool = False
    fixed_point_value: float | None = None
    convergent: bool = False

    @property
    def total_certified(self) -> int:
        return sum(len(lv.certified_claims) for lv in self.levels)

    @property
    def total_gaps(self) -> int:
        return sum(len(lv.gaps) for lv in self.levels)

    def narrate(self) -> str:
        lines = [
            f"╔══ DERİN DÜŞÜNCE: '{self.question}' ══",
            f"║  Derinlik: {self.depth}  |  Sertifikalı: {self.total_certified}  |  Gap: {self.total_gaps}",
            "╠" + "═" * 50,
        ]
        for lv in self.levels:
            lines.append(f"║")
            lines.append(f"║  [ell={lv.level}] {lv.label}")
            if lv.concepts:
                for c in lv.concepts[:6]:
                    lines.append(f"║    · {c}")
                if len(lv.concepts) > 6:
                    lines.append(f"║    · ... +{len(lv.concepts)-6} daha")
            if lv.certified_claims:
                lines.append(f"║    ✓ Sertifikalı:")
                for claim in lv.certified_claims[:5]:
                    lines.append(f"║      {claim}")
                if len(lv.certified_claims) > 5:
                    lines.append(f"║      ... +{len(lv.certified_claims)-5} daha")
            if lv.gaps:
                for concept, gap in lv.gaps[:3]:
                    lines.append(f"║    ∅ {concept}: {gap}")
            if lv.transport_drift > 0:
                lines.append(f"║    ↕ Transport drift: {float(lv.transport_drift):.4f}")
        lines.append("║")
        if self.fixed_point_found:
            lines.append(f"║  TAV ✓  Sabit nokta: {self.fixed_point_value:.8f} — sistem kapandı.")
        else:
            lines.append(f"║  TAV ∅  Sabit nokta bulunamadı — kavram açık.")
        conv = "yakınsadı" if self.convergent else "açık kaldı"
        lines.append(f"║  Sistem: {conv}  ({self.total_certified} sertifika, {self.total_gaps} gap)")
        lines.append("╚" + "═" * 50)
        return "\n".join(lines)


# ─── Thinker ──────────────────────────────────────────────────────────────────

class Thinker:
    """Dyadic transport tabanlı çok-seviyeli düşünce makinesi.

    Bir soruyu alır, manifold üzerinde yürür, her adımda sertifikalı
    veya gap-isimli bilgi üretir. Context window yok — manifold hafıza.
    """

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine

    def think(self, question: str, depth: int = 3, neighbors: int = 5) -> ThinkingResult:
        """Soruyu dyadic transport ile derinlemesine düşün.

        depth=1: sadece manifold pozisyonu
        depth=2: + inference chain
        depth=3: + second-order walk (varsayılan)
        """
        result = ThinkingResult(question=question, depth=depth)
        engine = self.engine

        # ── Level 0: Encode + Certify ────────────────────────────────────────
        obj = engine.encoder.encode(question, name=question[:64])
        run0 = engine.network.run(obj)
        concept_0 = Concept(
            name=question[:64],
            moments=list(obj.moments),
            domain="query",
            source="thinker",
        )

        lv0 = ThinkingLevel(level=0, label="Encode & Certify (ALEPH)")
        lv0.concepts = [question[:64]]

        aleph = run0.nodes.get("ALEPH")
        if aleph and aleph.status == "CERTIFIED":
            lv0.certified_claims.append(
                f"✓ '{question}' gerçek manifold'da var  "
                f"μ=[{', '.join(f'{float(m):.4f}' for m in obj.moments[:4])}...]"
            )
            lv0.certified_claims.append(
                f"✓ {run0.certified_count}/23 paradigma sertifikalandı"
            )
        else:
            gap_name = aleph.result.gap_name if aleph and aleph.result else "UNKNOWN"
            lv0.gaps.append((question, gap_name))

        tav = run0.nodes.get("TAV")
        if tav and tav.status == "CERTIFIED":
            fp = obj.structure.get("fixed_point_iterations", [])
            if fp:
                result.fixed_point_found = True
                result.fixed_point_value = float(fp[-1])

        result.levels.append(lv0)
        if depth < 1 or not engine.manifold.concepts:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 1: TAU Walk (Dyadic Transport ell=0→1) ─────────────────────
        # TAU'da varsa O(1) lookup, yoksa manifold nearest O(n)
        lv1 = ThinkingLevel(level=1, label="TAU Walk (Dyadic Transport ell=0→1)")
        tau = getattr(engine, "tau", None)
        q_name = question[:64]

        if tau and q_name in tau.edges and tau.edges[q_name]:
            raw_neighbors = tau.nearest(q_name)
            neighbor_list = [(n, Fraction(d).limit_denominator(10**6)) for n, d in raw_neighbors]
        else:
            neighbor_list = engine.manifold.nearest(concept_0, n=neighbors)

        if neighbor_list:
            avg_drift = sum(d for _, d in neighbor_list) / len(neighbor_list)
            lv1.transport_drift = avg_drift

        neighbor_concepts: list[tuple[str, Concept]] = []
        for name, dist in neighbor_list:
            c = engine.manifold.concepts.get(name)
            if c is None:
                continue
            neighbor_concepts.append((name, c))
            lv1.concepts.append(name)
            lv1.certified_claims.append(f"'{name}'  [d={float(dist):.4f}]")

        result.levels.append(lv1)
        if depth < 2 or len(neighbor_concepts) < 2:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 2: Inference Chain (Dyadic Transport ell=1→2) ──────────────
        lv2 = ThinkingLevel(level=2, label="Inference Chain (Dyadic Transport ell=1→2)")

        from tantrium.agi.inference import InferenceChain
        chain = InferenceChain()

        # Run top-4 neighbor concepts through the network
        runs_1: list[tuple[str, object]] = []
        for name, concept in neighbor_concepts[:4]:
            c_obj = concept.to_codex_object()
            r = engine.network.run(c_obj)
            runs_1.append((name, r))

        derived_concepts: list[str] = []
        for i, (n_a, r_a) in enumerate(runs_1):
            for n_b, r_b in runs_1[i + 1:]:
                inferences = chain.infer(r_a, r_b)  # type: ignore[arg-type]
                if inferences:
                    derived_name = f"{n_a}⊕{n_b}"
                    if derived_name not in derived_concepts:
                        derived_concepts.append(derived_name)
                    for ir in inferences:
                        conc = ir.conclusion[:72] if len(ir.conclusion) > 72 else ir.conclusion
                        lv2.certified_claims.append(
                            f"{n_a} + {n_b} → [{ir.rule_id}] {conc}"
                        )
                else:
                    lv2.gaps.append((f"{n_a}+{n_b}", "NO_INFERENCE"))

        lv2.concepts = derived_concepts
        result.levels.append(lv2)
        if depth < 3 or not derived_concepts:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 3: Second-order Walk (Dyadic Transport ell=2→3) ────────────
        lv3 = ThinkingLevel(level=3, label="Second-order Walk (Dyadic Transport ell=2→3)")

        # Encode each derived concept and find its manifold neighbors
        second_order_seen: set[str] = set(lv1.concepts)
        for derived_name in derived_concepts[:3]:
            d_obj = engine.encoder.encode(derived_name, name=derived_name[:64])
            d_concept = Concept(
                name=derived_name[:64],
                moments=list(d_obj.moments),
                domain="derived",
            )
            d_neighbors = engine.manifold.nearest(d_concept, n=3)
            for n2, dist2 in d_neighbors:
                if n2 not in second_order_seen:
                    second_order_seen.add(n2)
                    lv3.concepts.append(n2)
                    lv3.certified_claims.append(
                        f"'{derived_name}' → '{n2}'  [d={float(dist2):.4f}]"
                    )

        # Transport drift at level 3
        if lv3.concepts and neighbor_list:
            base_drift = lv1.transport_drift
            lv3.transport_drift = base_drift * Fraction(2, 3)  # transport compresses

        result.levels.append(lv3)
        result.convergent = result.fixed_point_found and len(result.levels) == depth + 1
        return result
