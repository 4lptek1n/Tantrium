"""MeasurementSpace — encoder çıktısından kurulan tam ölçüm uzayı.

Encoder'ın tüm temsilleri (8 moment + 23 paradigma + RH kriterleri + 45-dim
vektör) bu uzayı oluşturur. Uzayın iki ekseni:

  GOE = geçmiş   (β=1, zaman-tersinir, reel-simetrik; G=AᵀA'nın doğal hali)
  GUE = gelecek  (β=2, zaman-tersinmez, karmaşık-Hermitian; Riemann ζ-sıfırları)

7 cosmos türü (universe.py'nin 7 yüzü) bu uzaydan türer:
  1 MADDE      → G operatörünün evrimi (rank/dim)
  2 FİZİK      → SpectralReading 4 katmanı (makro·mikro·simetri·özvektör)
  3 GEOMETRİ   → NCG spektral aksiyonu (boyut·eğrilik·etki)
  4 KUVVET     → ortamla kuplaj kuvveti
  5 HAYAT      → dolanıklık / entropi evrimi
  6 ZAMAN      → Lifecycle T₀→T₁₀ (run_cosmos)
  7 TOPOLOJİ   → SpectralFlow yük evrimi
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any


@dataclass
class MeasurementSpace:
    """Encoder çıktısından kurulan birleşik ölçüm uzayı.

    Tüm temsiller tek nesnede: her birinin hesaplanma kaynağı G=AᵀA.
    GOE/GUE ekseni zaman yönünü verir — geçmiş→gelecek.
    """
    # ── Kaynak ───────────────────────────────────────────────────────────────
    raw_input: Any
    moments: list[Fraction]           # 8 spektral moment (exact Fraction, G'den)
    eigenvalues: list[float]          # G'nin özdeğerleri (bir kez hesaplanmış)

    # ── 45-boyutlu ölçüm vektörü ─────────────────────────────────────────────
    fingerprint: list[float]          # paradigm_signature(structure): 45 boyut

    # ── 23 paradigma sayısal ölçümleri ───────────────────────────────────────
    paradigm_values: dict             # structure dict (tüm paradigma çıktıları)

    # ── RH kriterleri ────────────────────────────────────────────────────────
    rh: dict                          # rh_criteria.as_dict(): τ/pivot/rank/κ/Λ
    rh_rank: int                      # spektral atom sayısı (en ayırt edici)
    lambda_dbn: float                 # Λ = −κ₂ = −var₀ (de Bruijn-Newman)

    # ── Zaman ekseni: GOE = geçmiş, GUE = gelecek ───────────────────────────
    beta: int                         # Dyson β: 1=GOE (geçmiş), 2=GUE (gelecek)
    universality: str                 # "GOE" | "GUE" | "Poisson"
    r_ratio: float | None             # ⟨r⟩ seviye-aralığı oranı
    goe_dist: float                   # ⟨r⟩ → GOE referansına uzaklık
    gue_dist: float                   # ⟨r⟩ → GUE referansına uzaklık
    time_direction: str               # "past" (GOE) | "future" (GUE)

    # ── Moment-uzayındaki GUE referans uzaklığı (Riemann ζ-sıfırları) ────────
    zeta_moment_dist: float = 0.0     # moment L1 uzaklığı ZETA_ZEROS referansına

    # ── Meta ─────────────────────────────────────────────────────────────────
    encoder_path: str = ""
    seal: str = ""

    @property
    def in_future(self) -> bool:
        """Uzayın gelecek (GUE) tarafında mı?"""
        return self.time_direction == "future"

    @property
    def in_past(self) -> bool:
        """Uzayın geçmiş (GOE) tarafında mı?"""
        return self.time_direction == "past"

    def time_axis(self) -> tuple[float, float]:
        """(GOE mesafesi, GUE mesafesi) — geçmiş↔gelecek ekseni."""
        return (self.goe_dist, self.gue_dist)

    def cosmos_vector(self) -> list[float]:
        """7-boyutlu cosmos vektörü: her boyut universe.py'nin bir yüzüne karşılık gelir.

        1 MADDE      → matrix_rank  (G operatörünün etkin boyutu)
        2 FİZİK      → ⟨r⟩ seviye-aralığı oranı  (GOE=0.531, GUE=0.600)
        3 GEOMETRİ   → spectral_dimension (NCG Connes aksiyonu)
        4 KUVVET     → var(λ)  (özdeğer yayılımı = kuplaj kuvveti)
        5 HAYAT      → S_vN  (von Neumann entropisi = dolanıklık ölçüsü)
        6 ZAMAN      → Λ_dbn  (de Bruijn-Newman; RH ⟺ Λ≤0)
        7 TOPOLOJİ  → λ_max − λ_min  (spektral aralık = topolojik yük proxy)
        """
        import math as _math

        eigs = sorted(self.eigenvalues, reverse=True)

        # 1 MADDE: matrix rank
        d1 = float(self.paradigm_values.get("matrix_rank") or len([e for e in eigs if e > 1e-9]))

        # 2 FİZİK: ⟨r⟩
        d2 = float(self.r_ratio) if self.r_ratio is not None else 0.5307

        # 3 GEOMETRİ: NCG spectral dimension
        try:
            from tantrium.core.spectral_geometry import spectral_geometry as _sg
            d3 = float(_sg(self.raw_input).spectral_dimension)
            if not _math.isfinite(d3):
                d3 = 0.0
        except Exception:
            d3 = 0.0

        # 4 KUVVET: var(λ)
        if len(eigs) >= 2:
            mu = sum(eigs) / len(eigs)
            d4 = sum((e - mu) ** 2 for e in eigs) / len(eigs)
        else:
            d4 = 0.0

        # 5 HAYAT: S_vN
        total = sum(eigs)
        if total > 1e-12:
            p = [e / total for e in eigs if e > 1e-15]
            d5 = -sum(pi * _math.log(pi) for pi in p)
        else:
            d5 = 0.0

        # 6 ZAMAN: Λ_dbn (de Bruijn-Newman)
        d6 = self.lambda_dbn

        # 7 TOPOLOJİ: λ_max − λ_min (spektral aralık)
        d7 = (max(eigs) - min(eigs)) if len(eigs) >= 2 else 0.0

        return [d1, d2, d3, d4, d5, d6, d7]

    def summary(self) -> str:
        return (
            f"MeasurementSpace | β={self.beta} ({self.universality}) | "
            f"⟨r⟩={self.r_ratio:.4f if self.r_ratio else 'nan'} | "
            f"zaman={'gelecek (GUE)' if self.in_future else 'geçmiş (GOE)'} | "
            f"RH rank={self.rh_rank} Λ={self.lambda_dbn:+.4f} | "
            f"fingerprint {len(self.fingerprint)}-boyut"
        )


def build_measurement_space(raw_input: Any) -> MeasurementSpace:
    """Ham girdiden tam ölçüm uzayını kur.

    Encoder'ı bir kez çalıştırır; 8 moment + 23 paradigma + RH kriterleri +
    45-dim vektör + GOE/GUE zaman yönü tek geçişte hesaplanır.
    """
    from tantrium.core.encoder import encode
    from tantrium.core.metric import certificate_vector
    from tantrium.core.rh_criteria import rh_criteria as _rh_criteria

    obj = encode(raw_input)
    s = obj.structure
    fp = certificate_vector(raw_input)

    # RH kriterleri
    rh = _rh_criteria(obj.moments)
    rh_dict = rh.as_dict()

    def _mf(m):
        try:
            return float(m)
        except (OverflowError, ValueError):
            try:
                return float(m.limit_denominator(2 ** 52))
            except Exception:
                return 0.0

    # Zeta moment referans uzaklığı: moment-L1 to ZETA_ZEROS canonical moments
    try:
        from tantrium.graph.anchors import _power_moments, _ZETA_ZEROS
        zeta_mu = _power_moments(list(_ZETA_ZEROS), 8)
        zeta_dist = sum(abs(_mf(obj.moments[i]) - zeta_mu[i])
                        for i in range(min(8, len(obj.moments))))
    except Exception:
        zeta_dist = 0.0

    # Seal
    import hashlib
    _blob = "|".join(f"{_mf(m):.15g}" for m in obj.moments) + f"|{s.get('universality','GOE')}"
    seal = hashlib.sha256(_blob.encode()).hexdigest()[:16]

    return MeasurementSpace(
        raw_input=raw_input,
        moments=list(obj.moments),
        eigenvalues=list(s.get("eigenvalues") or []),
        fingerprint=fp,
        paradigm_values=s,
        rh=rh_dict,
        rh_rank=rh.rank,
        lambda_dbn=float(rh.lambda_dbn),
        beta=int(s.get("beta", 1)),
        universality=str(s.get("universality", "GOE")),
        r_ratio=s.get("r_ratio"),
        goe_dist=float(s.get("goe_dist", 0.0)),
        gue_dist=float(s.get("gue_dist", abs(0.5996 - 0.5307))),
        time_direction=str(s.get("time_direction", "past")),
        zeta_moment_dist=zeta_dist,
        encoder_path=str(s.get("encoder", "universal_spectral")),
        seal=seal,
    )
