"""Güven Kalibrasyonu — Sertifikasyonun 4. Ekseni.

4 eksen → tek kalibre güven skoru.
Zayıf halka kuralı: en zayıf eksen tüm skoru aşağı çeker.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfidenceScore:
    value: float           # 0→1
    level: str             # CERTAIN | STRONG | MODERATE | WEAK | UNCERTAIN
    axes: dict[str, float]  # eksen → katkı

    def __str__(self) -> str:
        return f"{self.level} ({self.value:.2f})"


def calibrate(
    structural: float,    # paradigm coverage 0→1
    achilles: float,      # 1 - achilles_score (zayıf paradigma yoksa 1.0)
    grounding: float,     # grounding score 0→1
    truth: float,         # truth consistency 0→1
) -> ConfidenceScore:
    """Ağırlıklı geometrik ortalama (zayıf halka kuralı)."""
    # Minimum floor 0.3 (PSD-valid zero eigenvalue hatasını engelle)
    s = max(0.3, structural)
    a = max(0.3, achilles)
    g = max(0.3, grounding)
    t = max(0.3, truth)

    # Geometrik ortalama: zayıf eksen tüm skoru aşağı çeker
    product = s * a * g * t
    score = product ** 0.25  # 4. kök

    axes = {"structural": s, "achilles": a, "grounding": g, "truth": t}

    if score >= 0.85:
        level = "CERTAIN"
    elif score >= 0.70:
        level = "STRONG"
    elif score >= 0.55:
        level = "MODERATE"
    elif score >= 0.40:
        level = "WEAK"
    else:
        level = "UNCERTAIN"

    return ConfidenceScore(value=score, level=level, axes=axes)
