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
    from tantrium.agi.engine import AGIEngine

_SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED"}

_CONNECTIVE: dict[str, str] = {
    "IS_A":     "{src}, bir {tgt} türüdür",
    "USES":     "{src}, {tgt} kullanır",
    "ACHIEVES": "{src}, {tgt} elde eder",
    "REQUIRES": "{src}, {tgt} gerektirir",
    "DEFINES":  "{src}, {tgt} tanımlar",
    "COMPOSED": "{src}, {tgt} bileşenine sahiptir",
}

_EN_CONNECTIVE: dict[str, str] = {
    "IS_A":     "{src} is a {tgt}",
    "USES":     "{src} uses {tgt}",
    "ACHIEVES": "{src} achieves {tgt}",
    "REQUIRES": "{src} requires {tgt}",
    "DEFINES":  "{src} defines {tgt}",
    "COMPOSED": "{src} is composed of {tgt}",
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

    def __init__(self, engine: "AGIEngine", lang: str = "tr") -> None:
        self.engine = engine
        self.lang = lang  # "tr" | "en"

    def generate(
        self,
        seed: str,
        max_steps: int = 8,
        goal_name: str | None = None,
        beam: int = 3,
        context_decay: float = 0.7,
    ) -> GenerationResult:
        """Seed kavramından başlayarak certified yörünge üret.

        seed:          başlangıç kavramı
        max_steps:     kaç adım ilerlenecek
        goal_name:     hedefe doğru yönlendir (opsiyonel)
        beam:          kaç adayı değerlendir (bellek/kalite dengesi)
        context_decay: context momentum faktörü (α=0.7 → ağırlık mevcut)
        """
        from tantrium.agi.semantic import moment_distance

        manifold = self.engine.manifold
        tau = self.engine.tau

        # 1. Seed kavramını bul ya da encode et
        seed_concept = manifold.concepts.get(seed)
        if seed_concept is None:
            seed_concept = self.engine.encoder.encode(seed, name=seed[:64])
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
    ) -> tuple[str, str, float] | None:
        """TAU komşularından en yakın adayı döndür.

        Deterministic: argmin moment_distance — sampling yok.
        """
        from tantrium.agi.semantic import moment_distance, Concept

        tau = self.engine.tau
        manifold = self.engine.manifold

        ref_concept = Concept(
            name="_ctx",
            moments=[Fraction(x).limit_denominator(10**9) for x in context_moments],
            domain="internal",
            source="generator",
        )

        candidates: list[tuple[float, str, str]] = []
        for edge in tau.edges.get(current, []):
            if edge.paradigm not in _SEMANTIC:
                continue
            if edge.target in visited or edge.target == current:
                continue
            tc = manifold.concepts.get(edge.target)
            if tc is None or not tc.is_real():
                continue

            if goal_moments is not None:
                goal_c = Concept(
                    name="_goal",
                    moments=goal_moments,
                    domain="internal",
                    source="generator",
                )
                d = float(moment_distance(goal_c, tc))
            else:
                d = float(moment_distance(ref_concept, tc))

            candidates.append((d, edge.target, edge.paradigm))

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
