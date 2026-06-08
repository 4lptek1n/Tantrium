"""Hankel Genelleme — HankelGeneralizer.

İki sertifikalı kavramdan PSD-güvenli konveks kombinasyonla yeni kavram türetir.

Matematiksel temel:
  H_A PSD, H_B PSD → H_C = αH_A + (1-α)H_B PSD  (konveks kombinasyon)
  μ_C = α·μ_A + (1-α)·μ_B

Bu istatistik değil, saf lineer cebir:
  - Bilinen iki yapının arasındaki her nokta matematiksel olarak zorunlu
  - Ya Aleph'ten geçer (gerçekten var) ya geçmez (bu bölgede gerçek yok)
  - PSD konveksliği garanti eder — Aleph sertifikası asla ihlal edilmez

Kullanım:
  g.interpolate("gradient", "topology")  → aralarındaki kavramı türet
  g.derive(["algebra","manifold","topology"])  → üç kavramın merkezini türet
  g.explore_midpoints("A","B", steps=7)   → A→B arasında gap haritası
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.core.semantic import Concept

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


@dataclass
class DerivedConcept:
    """Hankel genellemeden türetilmiş kavram."""
    concept: Concept
    parents: list[str]
    alpha: float              # A ağırlığı (B = 1 - alpha)
    certified: bool           # Aleph filtresi geçti mi?
    method: str               # "interpolate" | "derive" | "extrapolate"
    paradigms_certified: int = 0

    def summary(self) -> str:
        icon = "✓" if self.certified else "∅"
        parents_str = " ⊕ ".join(self.parents[:3])
        return (
            f"  {icon} '{self.concept.name}'\n"
            f"    yöntem: {self.method}  α={self.alpha:.2f}\n"
            f"    ebeveyn: {parents_str}\n"
            f"    μ[0:4]: {[round(float(m), 4) for m in self.concept.moments[:4]]}\n"
            f"    paradigma: {self.paradigms_certified}/23"
        )


class HankelGeneralizer:
    """Moment uzayında sertifikalı kavramlardan yeni kavramlar türetir.

    Temel kural: H_A, H_B PSD → αH_A + (1-α)H_B PSD.
    Yani iki gerçek kavramın konveks kombinasyondaki her nokta da gerçek.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ─── Temel operasyonlar ───────────────────────────────────────────────────

    def interpolate(
        self,
        name_a: str,
        name_b: str,
        alpha: float = 0.5,
        derived_name: str | None = None,
    ) -> DerivedConcept | None:
        """A ve B arasında α ağırlıklı Hankel interpolasyonu.

        μ_C = α·μ_A + (1-α)·μ_B  [α ∈ [0,1] → konveks → PSD garantili]
        α=0.5: geometrik orta nokta (iki kavramın tam ortası).
        """
        ca = self.engine.manifold.concepts.get(name_a)
        cb = self.engine.manifold.concepts.get(name_b)
        if ca is None or cb is None:
            return None

        alpha = max(0.0, min(1.0, alpha))
        k = min(len(ca.moments), len(cb.moments))
        blended = [
            Fraction(
                alpha * float(ca.moments[i]) + (1.0 - alpha) * float(cb.moments[i])
            ).limit_denominator(10 ** 9)
            for i in range(k)
        ]

        name = derived_name or f"⟨{name_a}⊕{name_b}⟩"
        concept = Concept(
            name=name, moments=blended, domain="derived", source="hankel_interpolation"
        )
        return self._certify_and_add(concept, [name_a, name_b], alpha, "interpolate")

    def derive(self, concept_names: list[str]) -> DerivedConcept | None:
        """N kavramın moment ortalamasından yeni kavram türet.

        Uniform ağırlık: μ_C = (1/N)·Σ μᵢ
        PSD matrislerinin ortalaması PSD — Aleph garantisi korunur.
        """
        concepts = [self.engine.manifold.concepts.get(n) for n in concept_names]
        concepts = [c for c in concepts if c is not None]
        if len(concepts) < 2:
            return None

        k = min(len(c.moments) for c in concepts)
        n = len(concepts)
        avg = [
            Fraction(
                sum(float(c.moments[i]) for c in concepts) / n
            ).limit_denominator(10 ** 9)
            for i in range(k)
        ]

        name = "⟨" + "∪".join(concept_names[:4]) + "⟩"
        concept = Concept(
            name=name, moments=avg, domain="derived", source="hankel_derivation"
        )
        return self._certify_and_add(concept, concept_names, 1.0 / n, "derive")

    def explore_midpoints(
        self,
        name_a: str,
        name_b: str,
        steps: int = 7,
    ) -> list[DerivedConcept]:
        """A'dan B'ye giden yolda ara noktaları türet ve certify et.

        Her nokta α_i = i/(steps+1) — PSD garantili.
        Aleph geçen bölgeler: gerçek matematiksel alan.
        Aleph geçmeyen bölgeler: bu iki kavram arasındaki matematiksel void.
        """
        results = []
        for i in range(1, steps + 1):
            alpha = i / (steps + 1)
            dc = self.interpolate(name_a, name_b, alpha)
            if dc:
                results.append(dc)
        return results

    def weighted_blend(
        self,
        weighted_concepts: list[tuple[str, float]],
        derived_name: str | None = None,
    ) -> DerivedConcept | None:
        """Ağırlıklı kavram karışımı. [(isim, ağırlık), ...]

        Ağırlıklar normalize edilir → konveks kombinasyon → PSD garantili.
        """
        total_w = sum(w for _, w in weighted_concepts)
        if total_w == 0:
            return None

        concepts = []
        weights = []
        for name, w in weighted_concepts:
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                concepts.append(c)
                weights.append(w / total_w)

        if len(concepts) < 2:
            return None

        k = len(concepts[0].moments)
        blended = [
            Fraction(
                sum(weights[i] * float(concepts[i].moments[j]) for i in range(len(concepts)))
            ).limit_denominator(10 ** 9)
            for j in range(k)
        ]

        names = [n for n, _ in weighted_concepts]
        name = derived_name or "⟨" + "+".join(f"{n}×{w:.2f}" for n, w in weighted_concepts[:3]) + "⟩"
        concept = Concept(
            name=name, moments=blended, domain="derived", source="hankel_blend"
        )
        return self._certify_and_add(concept, names, weights[0] if weights else 0.5, "blend")

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _certify_and_add(
        self,
        concept: Concept,
        parents: list[str],
        alpha: float,
        method: str,
    ) -> DerivedConcept:
        run = self.engine.network.run(concept.to_codex_object())
        aleph = run.nodes.get("ALEPH")
        certified = bool(aleph and aleph.status == "CERTIFIED")

        if certified:
            try:
                self.engine.manifold.add(concept)
                tau = getattr(self.engine, "tau", None)
                if tau is not None:
                    tau.add_node(concept)
            except ValueError:
                certified = False

        return DerivedConcept(
            concept=concept,
            parents=parents,
            alpha=alpha,
            certified=certified,
            method=method,
            paradigms_certified=run.certified_count,
        )
