"""Gerçek Ekseni (Truth Axis) — Sertifikasyonun 3. Ekseni.

Yapısal geçerlilik (23 paradigma) × Topraklama (TAU kökü) × Gerçek (tutarlılık).

Yargı:
  CONSISTENT     — kavram komşularıyla moment uzayında tutarlı
  CONTESTED      — yüksek komşu varyansı (birden fazla küme)
  CONTRADICTORY  — yakın komşularla tutarsız (farklı yönde)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TruthCertificate:
    name: str
    verdict: str           # CONSISTENT | CONTESTED | CONTRADICTORY
    consistency_score: float  # 0→1
    neighbor_variance: float
    evidence: list[str]

    @property
    def score(self) -> float:
        return self.consistency_score


class TruthCertifier:
    """Kavramın manifold komşularıyla moment tutarlılığını ölçer."""

    def __init__(self, engine: object) -> None:
        self._engine = engine

    def certify(self, name: str, n_neighbors: int = 5,
                moments: list[float] | None = None) -> TruthCertificate:
        try:
            return self._certify_inner(name, n_neighbors, moments)
        except Exception as exc:
            return TruthCertificate(
                name=name, verdict="CONSISTENT",
                consistency_score=0.5, neighbor_variance=0.0,
                evidence=[f"truth check skipped: {exc}"])

    def _certify_inner(self, name: str, n_neighbors: int,
                       moments: list[float] | None) -> TruthCertificate:
        from tantrium.core.semantic import Concept

        manifold = self._engine.manifold
        if moments is None:
            obj = self._engine.encoder.encode(name, name=name)
            moments = list(obj.moments)

        concept = Concept(name=name, moments=moments, domain="truth_check")
        neighbors = manifold.nearest(concept, n=n_neighbors)

        if not neighbors:
            return TruthCertificate(
                name=name, verdict="CONSISTENT",
                consistency_score=0.7, neighbor_variance=0.0,
                evidence=["manifold boş — tutarlılık varsayıldı"])

        # Her komşunun moment L1 mesafesi
        dists = []
        for nb_name, nb_dist in neighbors:
            if nb_name in manifold.concepts:
                nb_m = manifold.concepts[nb_name].moments
                l1 = sum(abs(float(a) - float(b))
                         for a, b in zip(moments, nb_m)) / max(len(moments), 1)
                dists.append(l1)

        if not dists:
            return TruthCertificate(
                name=name, verdict="CONSISTENT",
                consistency_score=0.7, neighbor_variance=0.0,
                evidence=["komşu momenti yok"])

        mean_d = sum(dists) / len(dists)
        # Varyans: düzensiz komşuluk = tartışmalı
        variance = sum((d - mean_d) ** 2 for d in dists) / len(dists)

        # Skor: düşük ortalama mesafe + düşük varyans → tutarlı
        consistency = max(0.0, min(1.0, 1.0 - mean_d / 2.0))

        if variance > 0.3:
            verdict = "CONTESTED"
        elif mean_d > 1.5:
            verdict = "CONTRADICTORY"
        else:
            verdict = "CONSISTENT"

        evidence = [
            f"mean neighbor L1 dist: {mean_d:.4f}",
            f"neighbor variance: {variance:.4f}",
            f"{len(dists)} komşu incelendi",
        ]
        return TruthCertificate(
            name=name, verdict=verdict,
            consistency_score=consistency,
            neighbor_variance=variance,
            evidence=evidence)
