"""İlaç Dökümhanesi — Evren-Kapanışı, Çok-Stratejili, Deterministik.

RH ispat makinesinden doğan evrensel spektral motor: Jensen hiperbolikliği
⟺ Sturm pivot pozitifliği ⟺ H_{d,j}(t)≥0. Molekül bağlanması AYNI kriter:
referans→molekül konveks yolu Sturm-pozitif = gerçek-ölçü manifoldu.

produce() TEK GİRİŞ: çok-stratejili üretim → evren-kapanışı geçidi → 6 eksen
yargısı → fixed-point refine → sıralı gerçekten-çalışan moleküller.

Hedef tipi otomatik:
  protein  → bilinen ligand κ-profili (ileri)
  hastalık → κ_gerekli = κ_sağlıklı ⊟ κ_hastalık (ters)
  SMILES   → doğrudan imza

Çıktı: SMILES + 3D SDF (ETKDGv3) + evren-kapanışı kanıtı + 6 eksen sertifika.
Sistem tahmin etmez — kanıtlar. Sertifika deterministik, wet-lab onayı ayrıdır.

NOT: Bu modül aynı-isimli bir PAKETE bölündü (_types/_targets/_pool/_judge/
_helpers/_cross/_engine). `from tantrium.core.production import X` BİT-BİT korunur.
"""
from __future__ import annotations

from ._engine import ProductionEngine
from ._types import (
    _DISEASE_DRIVER_MAP,
    _FREE_ENTROPY_WEIGHT,
    _PRIMITIVES,
    _PROTEIN_DIRECT_MAP,
    _SPECTRAL_FIT_WEIGHT,
    CrossResult,
    MathDrug,
    MoleculeSignature,
    ProductionResult,
)

__all__ = [
    "ProductionEngine",
    "ProductionResult",
    "MathDrug",
    "CrossResult",
    "MoleculeSignature",
    "_PROTEIN_DIRECT_MAP",
    "_DISEASE_DRIVER_MAP",
    "_SPECTRAL_FIT_WEIGHT",
    "_FREE_ENTROPY_WEIGHT",
    "_PRIMITIVES",
]
