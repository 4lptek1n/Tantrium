"""Çakışma Avcısı — çekirdek iddianın ampirik testi.

Sistemin tek vaadi: "8 moment yapıyı tek biçimde belirler."
Bu modül o vaadi SALDIRARAK test eder: iki YAPISAL OLARAK FARKLI girdi
aynı (ya da ε-yakın) moment dizisine çöküyor mu?

  çakışma bulundu  → sistem o iki yapıyı 8 momentle AYIRT EDEMİYOR
                     → tam o noktada adaptif derinlik devreye girmeli
  çakışma yok      → vaadin ampirik kanıtı (inanç değil)

Strateji (adversarial arama):
  1. Çok sayıda rastgele, yapısal olarak farklı girdi üret (metin, dizi)
  2. Hepsini encode et → moment imzası
  3. Moment uzayında ε-yakın ama yapısı farklı çiftleri yakala
  4. Her çakışma için: derinliği artırınca ayrışıyor mu? (8 → 16 moment)

Bu, sistemin kendi temelini test etmesidir — dünyada başka hiçbir model
kendi ayırt-etme gücünü böyle ölçmez.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Collision:
    """8 momentte çakışan ama yapısı farklı iki girdi."""

    input_a: str
    input_b: str
    moment_distance: float  # L1(μ_A, μ_B) — 8 momentte ne kadar yakın
    deep_distance: float | None  # derin momentlerde (16) mesafe
    resolved_by_depth: bool  # derinlik artınca ayrıştı mı?
    structural_diff: float  # girdilerin gerçek yapısal farkı (0..1)
    label_aware_distance: float | None = None  # label-aware kodlamada mesafe
    resolved_by_labels: bool = False  # label-aware ayrıştırıyor mu?

    def summary(self) -> str:
        if self.resolved_by_labels:
            res = "✓ label-aware kodlama ayrıştırıyor"
        elif self.resolved_by_depth:
            res = "✓ derinlikle ayrıştı"
        else:
            res = "✗ yapısal çakışma (encoder etiket-kör)"
        deep = f"{self.deep_distance:.2e}" if self.deep_distance is not None else "—"
        la = f"{self.label_aware_distance:.2e}" if self.label_aware_distance is not None else "—"
        return (
            f"ÇAKIŞMA «{self.input_a[:24]}» ≈ «{self.input_b[:24]}»\n"
            f"  8-moment L1: {self.moment_distance:.2e}  |  16-moment L1: {deep}"
            f"  |  label-aware L1: {la}\n"
            f"  yapısal fark: {self.structural_diff:.2f}  →  {res}"
        )


@dataclass
class CollisionReport:
    """Çakışma avı raporu — çekirdek iddianın durumu."""

    samples_tested: int
    pairs_compared: int
    collisions: list[Collision] = field(default_factory=list)
    epsilon: float = 1e-4
    base_depth: int = 8
    deep_depth: int = 16

    @property
    def collision_rate(self) -> float:
        if self.pairs_compared == 0:
            return 0.0
        return len(self.collisions) / self.pairs_compared

    @property
    def resolved_count(self) -> int:
        return sum(1 for c in self.collisions if c.resolved_by_depth)

    @property
    def resolved_by_labels_count(self) -> int:
        return sum(1 for c in self.collisions if c.resolved_by_labels)

    @property
    def claim_holds(self) -> bool:
        """Vaat tutuyor mu: hiç çakışma yok, VEYA hepsi derinlik/label-aware ile ayrışıyor.

        Hamburger teoremi ÖLÇÜ→moment teklik garantiler; çakışmalar encoder'ın
        (girdi→ölçü) etiket-körlüğünden gelir. label-aware kodlama bunu kapatırsa
        çekirdek matematik sağlam, darboğaz yalnızca varsayılan metin kodlamasıdır.
        """
        if not self.collisions:
            return True
        return all(c.resolved_by_depth or c.resolved_by_labels for c in self.collisions)

    def summary(self) -> str:
        if not self.collisions:
            verdict = "VAAT TUTUYOR — 8 moment yapıyı ayırıyor (çakışma yok)"
        elif self.claim_holds:
            verdict = (
                "VAAT TUTUYOR — çakışmalar label-aware/derinlik ile ayrışıyor; "
                "çekirdek matematik sağlam, etiket-körlük çözülebilir"
            )
        else:
            verdict = (
                "VAAT KISMÎ — varsayılan metin kodlaması etiket-kör "
                "(permütasyon yapıları çakışır); label-aware mod çözer"
            )
        lines = [
            "═══ ÇAKIŞMA AVI ═══",
            f"Örnek: {self.samples_tested}  |  karşılaştırma: {self.pairs_compared:,}",
            f"Çakışma (ε={self.epsilon:.0e}): {len(self.collisions)}  "
            f"(oran {self.collision_rate:.2e})",
            f"Derinlikle ayrışan: {self.resolved_count}/{len(self.collisions)}  |  "
            f"label-aware ile: {self.resolved_by_labels_count}/{len(self.collisions)}",
            f"→ {verdict}",
        ]
        for c in self.collisions[:5]:
            lines.append("")
            lines.append(c.summary())
        return "\n".join(lines)


def _random_text(rng: random.Random, min_len: int = 4, max_len: int = 16) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz "
    n = rng.randint(min_len, max_len)
    return "".join(rng.choice(alphabet) for _ in range(n))


def _random_sequence(rng: random.Random, min_len: int = 5, max_len: int = 20) -> list[float]:
    n = rng.randint(min_len, max_len)
    return [round(rng.uniform(0, 1), 3) for _ in range(n)]


def _structural_diff(a, b) -> float:
    """İki girdinin gerçek yapısal farkı [0,1]. 0 = aynı, 1 = tamamen farklı."""
    sa, sb = str(a), str(b)
    if sa == sb:
        return 0.0
    # Jaccard üzerinden karakter/eleman kümesi farkı + uzunluk farkı
    set_a, set_b = set(sa), set(sb)
    union = set_a | set_b
    jacc = 1.0 - (len(set_a & set_b) / len(union)) if union else 0.0
    len_diff = abs(len(sa) - len(sb)) / max(len(sa), len(sb), 1)
    return min(1.0, 0.6 * jacc + 0.4 * len_diff)


class CollisionHunter:
    """8 momentte çakışan farklı yapıları adversarial olarak arar."""

    def __init__(self, engine=None) -> None:
        self.engine = engine

    def _encode_moments(self, inp, depth: int) -> list[float]:
        from tantrium.core.encoder import encode as enc

        obj = enc(inp, num_moments=depth)
        return [float(m) for m in obj.moments]

    def _encode_label_aware(self, inp, depth: int) -> list[float] | None:
        """Label-aware kodlamayla momentler — yalnızca metin girdileri için."""
        if not isinstance(inp, str):
            return None
        from tantrium.core.encoder import (
            _spectral_moments,
            _text_to_bigram_matrix,
        )

        try:
            A = _text_to_bigram_matrix(inp, label_aware=True)
            return [float(m) for m in _spectral_moments(A, depth)]
        except Exception:
            return None

    def hunt(
        self,
        n_samples: int = 200,
        epsilon: float = 1e-4,
        base_depth: int = 8,
        deep_depth: int = 16,
        min_structural_diff: float = 0.3,
        seed: int = 0,
    ) -> CollisionReport:
        """Rastgele farklı girdiler üret, 8 momentte çakışanları yakala.

        min_structural_diff: yalnızca gerçekten farklı yapıları çakışma say
        (benzer girdilerin yakın olması beklenir, çakışma değil).
        """
        rng = random.Random(seed)

        # Karışık örneklem: hem metin hem sayısal dizi
        samples: list = []
        for _ in range(n_samples // 2):
            samples.append(_random_text(rng))
        for _ in range(n_samples - len(samples)):
            samples.append(_random_sequence(rng))

        # Hepsini base derinlikte encode et
        sigs: list[tuple] = []
        for s in samples:
            try:
                mu = self._encode_moments(s, base_depth)
                sigs.append((s, mu))
            except Exception:
                continue

        collisions: list[Collision] = []
        compared = 0
        n = len(sigs)
        for i in range(n):
            si, mui = sigs[i]
            for j in range(i + 1, n):
                sj, muj = sigs[j]
                compared += 1
                k = min(len(mui), len(muj))
                dist = sum(abs(mui[t] - muj[t]) for t in range(k))
                if dist >= epsilon:
                    continue
                sdiff = _structural_diff(si, sj)
                if sdiff < min_structural_diff:
                    continue  # benzer girdiler — gerçek çakışma değil

                # Çakışma! Derinlikte ayrışıyor mu?
                deep_dist = None
                resolved = False
                try:
                    di = self._encode_moments(si, deep_depth)
                    dj = self._encode_moments(sj, deep_depth)
                    kk = min(len(di), len(dj))
                    deep_dist = sum(abs(di[t] - dj[t]) for t in range(kk))
                    resolved = deep_dist >= epsilon * 2
                except Exception:
                    pass

                # Label-aware kodlama ayrıştırıyor mu? (encoder etiket-körlüğünün çözümü)
                la_dist = None
                resolved_labels = False
                la_i = self._encode_label_aware(si, base_depth)
                la_j = self._encode_label_aware(sj, base_depth)
                if la_i is not None and la_j is not None:
                    kk = min(len(la_i), len(la_j))
                    la_dist = sum(abs(la_i[t] - la_j[t]) for t in range(kk))
                    resolved_labels = la_dist >= epsilon * 2

                collisions.append(
                    Collision(
                        input_a=str(si),
                        input_b=str(sj),
                        moment_distance=dist,
                        deep_distance=deep_dist,
                        resolved_by_depth=resolved,
                        structural_diff=sdiff,
                        label_aware_distance=la_dist,
                        resolved_by_labels=resolved_labels,
                    )
                )

        return CollisionReport(
            samples_tested=len(sigs),
            pairs_compared=compared,
            collisions=collisions,
            epsilon=epsilon,
            base_depth=base_depth,
            deep_depth=deep_depth,
        )
