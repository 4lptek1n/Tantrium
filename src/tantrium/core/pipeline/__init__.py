"""L0–L7 Sıralı Hesaplama Pipeline'ı (aynı-isimli paket).

Encoder değil, pipeline hesaplar. Her aşama öncekinden alır, sonrakine verir.
Filtre makinesi değil — makinenin kendisi.

Her aşama `state: dict` alıp günceller. Aşamalar sıralıdır:
  L0.5  BET   — Frobenius bilgi koruması
  L2.5  DALET — Gerçek spektrum (eigenvalues)  ← diğerleri buna bağlı
  L1.5  HE    — Lyapunov (eigenvalues'dan sonra)
  L2    ZAYIN — Hankel τ-determinantları + Schur
  L3    HET   — Li kriteri (bu objenin eigenvalue'ları, global sıfırlar değil!)
  L4    TAV   — de Bruijn-Newman heat-flow
  ANCK  —     Yardımcı paradigmalar (KAF, AYIN, MEM, LAMED, …)
  L5    GIMEL — Achilles: zayıf paradigma tespiti
  L6    EMET  — Matematiksel kimlik cross-check

Public yüzey eski monolitik `pipeline.py` ile BİT-BİT aynıdır:
`from tantrium.core.pipeline import run_pipeline` (ve tüm stage fonksiyonları).
"""
from __future__ import annotations

from ._run import run_pipeline
from ._stages_high import (
    stage_ancillary,
    stage_l4_tav_heatflow,
    stage_l5_gimel_admission,
    stage_l6_emet_certificate,
)
from ._stages_low import (
    _update_bet_entropy,
    stage_l05_bet_infocon,
    stage_l2_zayin_hankel,
    stage_l3_het_li,
    stage_l15_he_lyapunov,
    stage_l25_dalet_spectrum,
)

__all__ = [
    "run_pipeline",
    "stage_l05_bet_infocon",
    "stage_l25_dalet_spectrum",
    "stage_l15_he_lyapunov",
    "stage_l2_zayin_hankel",
    "stage_l3_het_li",
    "stage_l4_tav_heatflow",
    "stage_ancillary",
    "stage_l5_gimel_admission",
    "stage_l6_emet_certificate",
    "_update_bet_entropy",
]
