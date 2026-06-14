"""Certified Generative Engine — TAU walk as trajectory, not sampling.

Temel fark:
  LLM:  P(next_token | context) — olasılık dağılımından örnekle
  Bu:   argmin_{n ∈ TAU_neighbors} moment_distance(n, context) — zorunlu sonraki adım

Sturm pivot positivity: moment dizisi biliniyorsa sistem nereye evrileceği zorunlu.
D-positivity:           her adımda moment yapısı korunur.
Hamburger teoremi:      sınırlı destek → moment dizisi ölçüyü TEK biçimde belirler.

Üretim = semantik manifold üzerinde certified yörünge.
Tahmin değil, türetim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED",
             "COMPONENT_OF", "HAS_SIGNAL", "HAS_COMPOUND", "HAS_IMAGE",
             "INHIBITS", "CAUSES", "ACTIVATES"}
# ALEPH (Hankel/Wasserstein certified) kullanılabilir — moment uzayında komşu.
# SPECTRAL_BRIDGE hariç: genesis yapay köprüsüdür, anlamsal bilgi taşımaz.
# Kritik hat: yalnız moment-uzayı değil, anlamsal TAU kökü olan kavramlar.
_CERTIFIED = {"ALEPH"}

_CONNECTIVE: dict[str, str] = {
    "IS_A":            "{src}, bir {tgt} türüdür",
    "USES":            "{src}, {tgt} kullanır",
    "ACHIEVES":        "{src}, {tgt} elde eder",
    "REQUIRES":        "{src}, {tgt} gerektirir",
    "DEFINES":         "{src}, {tgt} tanımlar",
    "COMPOSED":        "{src}, {tgt} bileşenine sahiptir",
    "COMPONENT_OF":    "{src}, {tgt}'nin parçasıdır",
    "HAS_SIGNAL":      "{src}, {tgt} sinyaliyle algılanır",
    "HAS_COMPOUND":    "{src}, {tgt} bileşiğini içerir",
    "HAS_IMAGE":       "{src}, {tgt} görüntüsüyle temsil edilir",
    "INHIBITS":        "{src}, {tgt}'yi engeller",
    "CAUSES":          "{src}, {tgt}'ye yol açar",
    "ACTIVATES":       "{src}, {tgt}'yi etkinleştirir",
    "ALEPH":           "{src}, moment uzayında {tgt} ile komşu",
    "SPECTRAL_BRIDGE": "{src}, {tgt} ile spektral köprü kuruyor",
}

_EN_CONNECTIVE: dict[str, str] = {
    "IS_A":            "{src} is a {tgt}",
    "USES":            "{src} uses {tgt}",
    "ACHIEVES":        "{src} achieves {tgt}",
    "REQUIRES":        "{src} requires {tgt}",
    "DEFINES":         "{src} defines {tgt}",
    "COMPOSED":        "{src} is composed of {tgt}",
    "COMPONENT_OF":    "{src} is part of {tgt}",
    "HAS_SIGNAL":      "{src} is sensed via {tgt}",
    "HAS_COMPOUND":    "{src} contains compound {tgt}",
    "HAS_IMAGE":       "{src} is represented by {tgt}",
    "INHIBITS":        "{src} inhibits {tgt}",
    "CAUSES":          "{src} causes {tgt}",
    "ACTIVATES":       "{src} activates {tgt}",
    "ALEPH":           "{src} is moment-adjacent to {tgt}",
    "SPECTRAL_BRIDGE": "{src} has a spectral bridge to {tgt}",
}


@dataclass
class GeneratedStep:
    """Tek üretim adımı."""
    concept: str
    paradigm: str
    from_concept: str
    distance: float
    clause: str        # certified cümle parçası


@dataclass
class GenerationResult:
    """Certified üretim sonucu."""
    seed: str
    steps: list[GeneratedStep]
    text: str          # birleşik certified metin
    certified: bool = True
    lang: str = "tr"   # "tr" | "en"

    def summary(self) -> str:
        lines = [
            f"  ── Certified Üretim: '{self.seed}' ──────────────────",
            f"  {len(self.steps)} adım | Dil: {self.lang} | Certified: {'✓' if self.certified else '✗'}",
            "",
            self.text,
            "",
            f"  ─────────────────────────────────────────────────────",
        ]
        return "\n".join(lines)


class CertifiedGenerator:
    """TAU manifold üzerinde yörünge tabanlı certified metin üretici.

    next-token sampling değil: Sturm garantili deterministic walk.

    Algoritma:
      1. seed → moment encode (Aleph certify)
      2. Hedef varsa → goal_moment encode
      3. Her adımda: TAU komşuları arasından context'e en yakın kavramı seç
         → argmin moment_distance(candidate, context_moment)
      4. context_moment = α·current + (1-α)·next  (konveks, PSD korunur)
      5. (source, paradigm, target) → certified cümle
      6. Birleştir → coherent certified paragraf

    D-positivity garantisi: her adım konveks kombinasyon → Hankel PSD korunur.
    Sturm bağlantısı: moment dizisi → polinomun sıfır yapısı → yörünge zorunlu.
    """

    def __init__(self, engine: "CertificationEngine", lang: str = "tr") -> None:
        self.engine = engine
        self.lang = lang  # "tr" | "en"

    def _get_topo_encoder(self):
        if not hasattr(self, "_topo_enc"):
            from tantrium.core.topology_encode import TopologyEncoder
            self._topo_enc = TopologyEncoder(self.engine)
        return self._topo_enc

    def _is_grounded_proxy(self, name: str) -> bool:
        """Kavramın anlamsal TAU kenarı ≥ 1 → 'kritik hat' üzerinde.

        Hilbert-Pólya ilkesi: yörüngede yalnız semantik TAU'ya köklü kavramlar.
        SPECTRAL_BRIDGE/ALEPH-only kavramlar (xqzwvbnmkjhgfd, beauty gibi) moment
        uzayında yakın ama anlamsal yalıtık — kritik hattan sapan 'karmaşık sıfır'.
        """
        edges = self.engine.tau.edges.get(name, [])
        return any(e.paradigm in _SEMANTIC for e in edges)

    def generate(
        self,
        seed: str,
        max_steps: int = 8,
        goal_name: str | None = None,
        beam: int = 3,
        context_decay: float = 0.7,
        use_meaning: bool = False,
    ) -> GenerationResult:
        """Seed kavramından başlayarak certified yörünge üret.

        seed:          başlangıç kavramı
        max_steps:     kaç adım ilerlenecek
        goal_name:     hedefe doğru yönlendir (opsiyonel)
        beam:          kaç adayı değerlendir (bellek/kalite dengesi)
        context_decay: context momentum faktörü (α=0.7 → ağırlık mevcut)
        """
        from tantrium.core.semantic import moment_distance

        manifold = self.engine.manifold
        tau = self.engine.tau

        # 1. Seed kavramını bul ya da encode et
        seed_concept = manifold.concepts.get(seed)
        if seed_concept is None:
            from tantrium.core.semantic import Concept
            raw = self.engine.encoder.encode(seed, name=seed[:64])
            seed_concept = Concept(name=seed[:64], moments=list(raw.moments), domain="input")
            if not seed_concept.is_real():
                return GenerationResult(
                    seed=seed, steps=[],
                    text=f"'{seed}' Aleph filtresini geçemiyor — certified değil.",
                    certified=False, lang=self.lang,
                )

        # 2. Hedef moment (opsiyonel)
        goal_moment = None
        if goal_name:
            gc = manifold.concepts.get(goal_name)
            if gc and gc.is_real():
                goal_moment = gc.moments

        # context_moment başlangıçta seed
        context_moments = list(seed_concept.moments)

        steps: list[GeneratedStep] = []
        current = seed
        visited: set[str] = {seed}

        for _ in range(max_steps):
            nxt = self._next_step(
                current, context_moments, goal_moment,
                visited, beam,
                fallback_concept=seed_concept,
                use_meaning=use_meaning,
            )
            if nxt is None:
                break

            next_name, paradigm, dist = nxt
            clause = self._clause(current, paradigm, next_name)

            steps.append(GeneratedStep(
                concept=next_name,
                paradigm=paradigm,
                from_concept=current,
                distance=dist,
                clause=clause,
            ))

            visited.add(next_name)
            current = next_name

            # context_moment güncelle: konveks blend (PSD garantili)
            nc = manifold.concepts.get(next_name)
            if nc:
                k = min(len(context_moments), len(nc.moments))
                context_moments = [
                    context_decay * float(context_moments[i])
                    + (1.0 - context_decay) * float(nc.moments[i])
                    for i in range(k)
                ]

        text = self._build_text(seed, steps)

        return GenerationResult(
            seed=seed,
            steps=steps,
            text=text,
            certified=True,
            lang=self.lang,
        )

    def _next_step(
        self,
        current: str,
        context_moments: list,
        goal_moments,
        visited: set[str],
        beam: int,
        fallback_concept=None,
        use_meaning: bool = False,
    ) -> tuple[str, str, float] | None:
        """TAU komşularından en yakın adayı döndür.

        Deterministic: argmin moment_distance — sampling yok.
        """
        from tantrium.core.semantic import moment_distance, Concept

        tau = self.engine.tau
        manifold = self.engine.manifold

        ref_concept = Concept(
            name="_ctx",
            moments=[Fraction(x).limit_denominator(10**9) for x in context_moments],
            domain="internal",
            source="generator",
        )

        def _score(tc) -> float:
            if goal_moments is not None:
                goal_c = Concept(name="_goal", moments=goal_moments,
                                 domain="internal", source="generator")
                surf = float(moment_distance(goal_c, tc))
            else:
                surf = float(moment_distance(ref_concept, tc))
            if use_meaning:
                enc = self._get_topo_encoder()
                m_tc = enc.encode(tc.name)
                m_cur = enc.encode(current)
                if m_tc and m_cur:
                    k = min(len(m_tc.moments), len(m_cur.moments))
                    mdist = sum(abs(float(m_tc.moments[i]) - float(m_cur.moments[i]))
                                for i in range(k))
                    return 0.6 * surf + 0.4 * mdist
            return surf

        # Pass 1: prefer certified semantic edges (produce human-readable text)
        candidates: list[tuple[float, str, str]] = []
        for edge in tau.edges.get(current, []):
            if edge.paradigm not in _SEMANTIC:
                continue
            if edge.target in visited or edge.target == current:
                continue
            tc = manifold.concepts.get(edge.target)
            if tc is None or not tc.is_real():
                continue
            candidates.append((_score(tc), edge.target, edge.paradigm))

        # Pass 2: no semantic edges → fall back to Hankel/Wasserstein certified edges
        # Jensen hiperbolisitesi: sadece TAU'da topraklı (≥3 kenar) kavramlar — kritik hat.
        # Topraklı olmayan kavramlar (xqzwvbnmkjhgfd, beauty) kritik hattan sapar → filtrelenir.
        if not candidates:
            for edge in tau.edges.get(current, []):
                if edge.paradigm not in _CERTIFIED:
                    continue
                if edge.target in visited or edge.target == current:
                    continue
                tc = manifold.concepts.get(edge.target)
                if tc is None or not tc.is_real():
                    continue
                if not self._is_grounded_proxy(edge.target):
                    continue
                candidates.append((_score(tc), edge.target, edge.paradigm))

        # Pass 3 (canlı moment arama) KALDIRILDI — Jensen hiperbolisitesi ihlali.
        # manifold.nearest() topraklı olmayan kavramları da döndürür: kritik hattan
        # sapma = anlamsız metin. Yörünge topraklı komşu bulamazsa durur.

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        d, name, paradigm = candidates[0]
        return name, paradigm, d

    def _clause(self, src: str, paradigm: str, tgt: str) -> str:
        """(source, paradigm, target) → certified cümle."""
        if self.lang == "en":
            tmpl = _EN_CONNECTIVE.get(paradigm, "{src} relates to {tgt}")
        else:
            tmpl = _CONNECTIVE.get(paradigm, "'{src}' → {tgt}")
        return tmpl.format(src=src, tgt=tgt)

    def _build_text(self, seed: str, steps: list[GeneratedStep]) -> str:
        """Adımları tutarlı paragraf olarak birleştir."""
        if not steps:
            if self.lang == "en":
                return f"'{seed}': no TAU neighbors found — isolated concept."
            return f"'{seed}': TAU komşusu bulunamadı — izole kavram."

        sentences = []
        buffer: list[str] = []
        prev_p = steps[0].paradigm
        current_subject = seed  # konu başlangıçta seed

        for step in steps:
            if step.paradigm == prev_p:
                buffer.append(step.concept)
            else:
                if buffer:
                    sentences.append(self._flush_buffer(current_subject, prev_p, buffer))
                    current_subject = buffer[-1]  # son kavram yeni konu olur
                buffer = [step.concept]
                prev_p = step.paradigm

        if buffer:
            sentences.append(self._flush_buffer(current_subject, prev_p, buffer))

        return ". ".join(s.rstrip(".") for s in sentences) + "."

    def _flush_buffer(self, src: str, paradigm: str, targets: list[str]) -> str:
        conj = " and " if self.lang == "en" else " ve "
        joined = ", ".join(targets[:-1]) + (conj if len(targets) > 1 else "") + targets[-1]
        if self.lang == "en":
            tmpl = _EN_CONNECTIVE.get(paradigm, "{src} relates to {tgt}")
        else:
            tmpl = _CONNECTIVE.get(paradigm, "{src} → {tgt}")
        return tmpl.format(src=src, tgt=joined)
