"""Güven Kalibrasyonu — her yargıya kalibre edilmiş tek sayı.

Sistem CERTIFIED/UNKNOWN diyordu ama NE KADAR emin olduğunu söylemiyordu.
"23/23 ama en zayıf margin 0.001" ile "23/23 margin 0.4" çok farklı şeyler —
ilki bıçak sırtında, ikincisi sağlam. Bu modül o farkı tek sayıya indirir.

Dört bağımsız sinyali birleştirir (hepsi [0,1]):
  1. KAPSAMA   — certified_count / total (kaç paradigma geçti)
  2. MARGIN    — en zayıf paradigmanın payı (Aşil topuğu / GIMEL)
                 0'a yakın = bıçak sırtı, büyük = güvenli pay
  3. TOPRAKLAMA— grounding_score (TAU'da köklülük)
  4. DOĞRULUK  — truth_score (komşularla tutarlılık)

Birleştirme: ağırlıklı geometrik ortalama. Geometrik çünkü herhangi bir
sinyalin sıfıra gitmesi toplam güveni çökertmeli (zayıf halka kuralı).
Bir eksen tamamen başarısızsa, diğerleri telafi edemez — dürüst kalibrasyon.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Confidence:
    """Bir yargının kalibre edilmiş güveni."""

    value: float  # 0.0 (güvensiz) → 1.0 (tam güven)
    level: str  # CERTAIN | STRONG | MODERATE | WEAK | UNCERTAIN

    coverage: float  # paradigma kapsama
    margin: float  # en zayıf paradigma payı (Aşil)
    grounding: float  # topraklama skoru
    truth: float  # tutarlılık skoru

    weakest_axis: str  # en düşük sinyal hangisi

    def summary(self) -> str:
        bar = int(self.value * 20)
        bar_str = "█" * bar + "░" * (20 - bar)
        return (
            f"GÜVEN [{bar_str}] {self.value:.3f}  ({self.level})\n"
            f"  kapsama={self.coverage:.2f}  margin={self.margin:.2f}  "
            f"topraklama={self.grounding:.2f}  doğruluk={self.truth:.2f}\n"
            f"  zayıf halka: {self.weakest_axis}"
        )


def _level(value: float) -> str:
    if value >= 0.85:
        return "CERTAIN"
    if value >= 0.65:
        return "STRONG"
    if value >= 0.45:
        return "MODERATE"
    if value >= 0.25:
        return "WEAK"
    return "UNCERTAIN"


def calibrate(
    coverage: float,
    margin: float,
    grounding: float,
    truth: float,
    weights: tuple[float, float, float, float] = (0.3, 0.3, 0.2, 0.2),
) -> Confidence:
    """Dört sinyali kalibre tek güvene birleştir (ağırlıklı geometrik ortalama).

    Geometrik ortalama: herhangi bir eksen sıfıra giderse toplam güven çöker
    (zayıf halka kuralı — dürüst kalibrasyon, telafi yok).
    """
    # Margin'i [0,1]'e sıkıştır. ÖNEMLİ: margin=0 bir BAŞARISIZLIK değil —
    # sıfır özdeğer PSD'de geçerlidir (rank-eksik ölçü). Bu yüzden taban 0.3:
    # bıçak sırtı (tight) güveni düşürür ama sıfırlamaz. Gerçek başarısızlık
    # zaten kapsama (coverage<1) ekseninden yakalanır.
    margin_norm = 0.3 + 0.7 * min(1.0, max(0.0, margin) / 0.3)

    signals = {
        "kapsama": max(0.0, min(1.0, coverage)),
        "margin": margin_norm,
        "topraklama": max(0.0, min(1.0, grounding)),
        "doğruluk": max(0.0, min(1.0, truth)),
    }

    # Ağırlıklı geometrik ortalama: exp(Σ wᵢ·ln(sᵢ + ε)) / normalize
    import math

    eps = 1e-6
    names = ["kapsama", "margin", "topraklama", "doğruluk"]
    w = weights
    wsum = sum(w)
    log_sum = sum(w[i] * math.log(signals[names[i]] + eps) for i in range(4))
    value = math.exp(log_sum / wsum)
    value = max(0.0, min(1.0, value))

    weakest = min(signals, key=signals.get)

    return Confidence(
        value=round(value, 4),
        level=_level(value),
        coverage=round(signals["kapsama"], 4),
        margin=round(margin_norm, 4),
        grounding=round(signals["topraklama"], 4),
        truth=round(signals["doğruluk"], 4),
        weakest_axis=weakest,
    )


def from_run(run, grounding_score: float = 0.5, truth_score: float = 0.5) -> Confidence:
    """CertificationRun + topraklama + doğruluk → kalibre güven.

    Aşil margin'i run.obj.structure["achilles_margin"]'den okunur.
    """
    coverage = run.certified_count / run.total if run.total else 0.0
    margin = 0.0
    try:
        margin = float(run.obj.structure.get("achilles_margin", 0.0) or 0.0)
    except Exception:
        margin = 0.0
    return calibrate(coverage, margin, grounding_score, truth_score)
