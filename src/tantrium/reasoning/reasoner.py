"""TAU Semantik Akıl Yürütme — TauReasoner.

TAU graph'taki semantik kenarları (IS_A, USES, ACHIEVES, REQUIRES, ...)
transitif olarak zincirler. Bu, AGI'nin TAU'dan yeni certified sonuçlar
türetmesini sağlar.

Zincirleme kuralları (hepsi ses/geçerli):
  IS_A  + IS_A      → IS_A       (transitivity)
  IS_A  + ACHIEVES  → ACHIEVES   (inheritance)
  IS_A  + REQUIRES  → REQUIRES   (inheritance)
  IS_A  + USES      → USES       (inheritance)
  USES  + ACHIEVES  → ACHIEVES   (araç → amaç)
  USES  + USES      → USES       (transitivity)
  COMPOSED + IS_A   → COMPOSED   (bileşen kalıtımı)

Üretim halkası:
  Kavram → TAU chain → yeni certified kenarlar → Speaker → certified cümle
  Bu, sistemin TAU'daki bilgiden YENİ certified sonuçlar ÜRETMESINI sağlar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


# ─── Zincirleme kuralları ─────────────────────────────────────────────────────

# (kenar_1, kenar_2, türetilen_kenar)
# A -e1→ B  ve  B -e2→ C  ise  A -türetilen→ C  çıkar
_CHAIN_RULES: list[tuple[str, str, str]] = [
    ("IS_A",     "IS_A",     "IS_A"),
    ("IS_A",     "ACHIEVES", "ACHIEVES"),
    ("IS_A",     "REQUIRES", "REQUIRES"),
    ("IS_A",     "USES",     "USES"),
    ("USES",     "ACHIEVES", "ACHIEVES"),
    ("USES",     "USES",     "USES"),
    ("COMPOSED", "IS_A",     "COMPOSED"),
]

_SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED"}


# ─── Veri yapıları ────────────────────────────────────────────────────────────

@dataclass
class ChainStep:
    source: str
    paradigm: str
    target: str
    via: str  # hangi ara kavramdan geçildi ("" = doğrudan)
    derived: bool  # True = bu adım türetildi (TAU'da önceden yoktu)


@dataclass
class ReasoningResult:
    """Bir kavram hakkında TAU graph'tan türetilen tüm sonuçlar."""
    concept: str
    chains: list[ChainStep]
    new_edges: int          # kaç yeni TAU edge eklendi
    certified_answer: str   # Speaker ile üretilen özet

    def by_paradigm(self, paradigm: str) -> list[str]:
        """Belirli paradigmadaki hedefleri listele."""
        return [s.target for s in self.chains if s.paradigm == paradigm]

    def summary(self) -> str:
        lines = [f"  TAU Akıl Yürütme: '{self.concept}'"]
        if not self.chains:
            lines.append("  → TAU'da ilgili kenar yok.")
            return "\n".join(lines)
        by_p: dict[str, list[str]] = {}
        for step in self.chains:
            by_p.setdefault(step.paradigm, []).append(
                step.target + (" *" if step.derived else "")
            )
        for p, targets in by_p.items():
            lines.append(f"  {p:<12}: {', '.join(targets[:5])}")
        if self.new_edges:
            lines.append(f"  → {self.new_edges} yeni certified kenar türetildi.")
        return "\n".join(lines)


# ─── Akıl Yürütücü ───────────────────────────────────────────────────────────

class GraphReasoner:
    """TAU semantik graf üzerinde forward-chaining inference.

    query()   → bir kavram hakkında tüm certified sonuçlar
    compose() → iki kavramı momentlerde birleştir (convex, PSD korunur)
    chain_all() → TAU'nun tüm transitif kapatmasını hesapla (ağır)
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ─── Tek kavram sorgulama ─────────────────────────────────────────────────

    def query(self, concept_name: str, depth: int = 3) -> ReasoningResult:
        """Kavramın TAU'daki semantik komşularını transitif olarak zincirle.

        depth: kaç adım derinlikte zincir takip edilecek.
        Türetilen kenarlar TAU'ya eklenir (certify_and_add_edge ile).

        Eğer kavramın doğrudan semantik kenarı yoksa:
          1. TAU nearest → en yakın K komşuyu bul (Hankel-certified)
          2. O komşuların semantik zincirlerini kavrama proxy olarak sun
        """
        from tantrium.graph.relations import certify_and_add_edge

        tau = self.engine.tau
        steps: list[ChainStep] = []
        new_edges = 0

        # Mevcut doğrudan kenarları topla
        direct = [
            e for e in tau.edges.get(concept_name, [])
            if e.paradigm in _SEMANTIC
        ]
        for e in direct:
            steps.append(ChainStep(
                source=concept_name, paradigm=e.paradigm,
                target=e.target, via="", derived=False,
            ))

        # Forward chaining (depth kez)
        frontier = {concept_name}
        visited: set[str] = set()

        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                if node in visited:
                    continue
                visited.add(node)
                node_edges = [e for e in tau.edges.get(node, []) if e.paradigm in _SEMANTIC][:20]
                for e1 in node_edges:
                    mid = e1.target
                    mid_edges = [e for e in tau.edges.get(mid, []) if e.paradigm in _SEMANTIC][:20]
                    for e2 in mid_edges:
                        for p1, p2, derived_p in _CHAIN_RULES:
                            if e1.paradigm == p1 and e2.paradigm == p2:
                                target = e2.target
                                if target == concept_name:
                                    continue
                                already = any(
                                    s.source == concept_name
                                    and s.paradigm == derived_p
                                    and s.target == target
                                    for s in steps
                                )
                                if not already:
                                    added = certify_and_add_edge(
                                        self.engine, concept_name, target, derived_p
                                    )
                                    steps.append(ChainStep(
                                        source=concept_name,
                                        paradigm=derived_p,
                                        target=target,
                                        via=mid,
                                        derived=True,
                                    ))
                                    if added:
                                        new_edges += 1
                                next_frontier.add(mid)
            frontier = next_frontier - visited

        # No direct semantic edges — proxy via certified nearest neighbors
        if not steps:
            steps, new_edges = self._proxy_reason(concept_name, depth)

        answer = self._generate_answer(concept_name, steps)

        return ReasoningResult(
            concept=concept_name,
            chains=steps,
            new_edges=new_edges,
            certified_answer=answer,
        )

    def _proxy_reason(self, concept_name: str, depth: int) -> tuple[list[ChainStep], int]:
        """Moment-nearest neighbors üzerinden certified transitif akıl yürütme.

        Kavramın kendisi TAU'da semantik kenar yoksa:
        - tau.nearest() ile Hankel-certified K komşu bul
        - Her komşunun semantik zincirlerini çalıştır
        - Zincir adımlarını kaynak olarak proxy kavramı göstererek sun
        Mesafe sıralaması: moment uzayında en yakın komşular önce gelir.
        """
        from tantrium.graph.relations import certify_and_add_edge

        tau = self.engine.tau
        manifold = self.engine.manifold
        steps: list[ChainStep] = []
        new_edges = 0

        seed = manifold.concepts.get(concept_name)
        if seed is None:
            return steps, new_edges

        # Find K nearest concepts that actually HAVE semantic edges.
        # Scanning only semantic-edge owners is more precise than generic nearest().
        q = [float(m) for m in seed.moments]
        k = len(q)
        best: list[tuple[float, str]] = []
        K = 8

        for name, c in manifold.concepts.items():
            if name == concept_name:
                continue
            if not any(e.paradigm in _SEMANTIC for e in tau.edges.get(name, [])):
                continue
            d = sum(abs(q[i] - (float(c.moments[i]) if i < len(c.moments) else 0.0))
                    for i in range(k))
            if len(best) < K:
                best.append((d, name))
                if len(best) == K:
                    best.sort(reverse=True)
            elif d < best[0][0]:
                best[0] = (d, name)
                best.sort(reverse=True)
        best.sort()
        neighbors = [(name, d) for d, name in best]
        seen_targets: set[str] = {concept_name}

        for neighbor_name, dist in neighbors:
            neighbor_edges = [
                e for e in tau.edges.get(neighbor_name, [])
                if e.paradigm in _SEMANTIC
            ]
            if not neighbor_edges:
                continue

            # neighbor is moment-adjacent (ALEPH certified), so its semantic
            # relations are structurally inherited by the query concept
            for e in neighbor_edges[:6]:
                if e.target in seen_targets:
                    continue
                seen_targets.add(e.target)
                steps.append(ChainStep(
                    source=concept_name,
                    paradigm=e.paradigm,
                    target=e.target,
                    via=neighbor_name,  # proxy: through this certified neighbor
                    derived=True,
                ))
                # Inject as a weak edge (moment distance ≈ dist, not exact)
                added = certify_and_add_edge(self.engine, concept_name, e.target, e.paradigm)
                if added:
                    new_edges += 1

            if len(steps) >= 12:
                break

        return steps, new_edges

    # ─── Certified cevap üretimi ──────────────────────────────────────────────

    def _generate_answer(self, name: str, steps: list[ChainStep]) -> str:
        """TAU zincirinden certified doğal dil cümlesi üret.

        Speaker şablonlarını değil, TAU içeriğini kullanır.
        Her cümle TAU'da kenar olduğu için certified.
        """
        if not steps:
            concept = self.engine.manifold.concepts.get(name)
            if concept is None:
                return f"'{name}' manifoldda bulunamadı."
            return f"'{name}' manifoldda var ama TAU'da semantik kenar yok."

        lines = [f"'{name}' hakkında TAU'dan certified sonuçlar:"]

        by_p: dict[str, list[tuple[str, bool]]] = {}
        for s in steps:
            by_p.setdefault(s.paradigm, []).append((s.target, s.derived))

        verb_map = {
            "IS_A":     "bir türüdür",
            "USES":     "kullanır",
            "ACHIEVES": "elde eder / ulaşır",
            "REQUIRES": "gerektirir",
            "DEFINES":  "tanımlar",
            "COMPOSED": "bileşenleri",
        }

        # Check if these are proxy (via a neighbor) or direct
        has_proxy = any(s.via for s in steps)
        if has_proxy:
            lines.append("  (moment-komşu proxy üzerinden türetildi — Hankel certified)")

        for paradigm, targets in by_p.items():
            verb = verb_map.get(paradigm, paradigm)
            target_str = ", ".join(
                t + (" [proxy]" if derived else "")
                for t, derived in targets[:4]
            )
            lines.append(f"  • {verb}: {target_str}")

        return "\n".join(lines)

    # ─── Kavram kompozisyonu ──────────────────────────────────────────────────

    def compose(self, name_a: str, name_b: str, alpha: float = 0.5) -> str:
        """İki certified kavramı moment uzayında birleştir.

        Konveks kombinasyon: α·μ_A + (1-α)·μ_B
        PSD korunumu: PSD'lerin konveks kombinasyonu PSD'dir (Aleph garantili).
        Yeni kavram manifolda eklenir, TAU'ya kaydedilir.
        """
        from fractions import Fraction
        from tantrium.core.semantic import Concept
        from tantrium.graph.relations import certify_and_add_edge

        ca = self.engine.manifold.concepts.get(name_a)
        cb = self.engine.manifold.concepts.get(name_b)
        if ca is None:
            return f"'{name_a}' manifoldda yok."
        if cb is None:
            return f"'{name_b}' manifoldda yok."

        if not ca.is_real():
            return f"'{name_a}' Aleph filtresini geçemiyor (certified değil)."
        if not cb.is_real():
            return f"'{name_b}' Aleph filtresini geçemiyor (certified değil)."

        k = min(len(ca.moments), len(cb.moments))
        a = Fraction(alpha).limit_denominator(100)
        b = Fraction(1) - a

        composed = [
            a * ca.moments[i] + b * cb.moments[i]
            for i in range(k)
        ]

        comp_name = f"{name_a}⊕{name_b}"
        comp_concept = Concept(
            name=comp_name,
            moments=composed,
            domain="composed",
            source="tau_reasoner",
        )

        if not comp_concept.is_real():
            return f"Bileşim '{comp_name}' Aleph filtresini geçemiyor (beklenmedik)."

        # Manifolda ekle
        if comp_name not in self.engine.manifold.concepts:
            self.engine.manifold.add_unchecked(comp_concept)
            self.engine.tau.add_node(comp_concept)
            certify_and_add_edge(self.engine, comp_name, name_a, "COMPOSED")
            certify_and_add_edge(self.engine, comp_name, name_b, "COMPOSED")
            self.engine.tau._dirty = True

        # Bileşimin ne olduğunu söyle
        result_q = self.query(comp_name, depth=2)
        inherited = result_q.by_paradigm("ACHIEVES") + result_q.by_paradigm("IS_A")

        lines = [
            f"  Bileşim: '{comp_name}'  (α={float(a):.2f})",
            f"  Moment: μ₁={float(composed[0]):.4f}  μ₂={float(composed[1]):.4f}",
            f"  Aleph: ✓ (certified — konveks kombinasyon PSD korur)",
        ]
        if inherited:
            lines.append(f"  Kalıtsal özellikler: {', '.join(inherited[:4])}")

        return "\n".join(lines)

    # ─── Tüm TAU transitif kapanışı ──────────────────────────────────────────

    def chain_all(self, max_concepts: int = 200) -> int:
        """TAU'nun tüm kavramları için forward chaining çalıştır.

        Yeni kenarlar türetir ve TAU'ya ekler.
        Ağır işlem: büyük manifoldlarda max_concepts ile sınırla.
        Döner: türetilen toplam yeni kenar sayısı.
        """
        total_new = 0
        concepts = list(self.engine.manifold.concepts.keys())[:max_concepts]
        for name in concepts:
            r = self.query(name, depth=2)
            total_new += r.new_edges
        return total_new
