"""Moleküler Genesis — Saf Matematiksel Türetim.

Tahmin yok. Benzerlik yok. Kütüphane yok.

Hedef → momentler → spektral imza → atom atom inşa
Her adımda: W2(yeni_molekül, hedef) azalıyorsa ekle, artıyorsa dur.

Bu benzerlik araması değil — TÜREV.
Hamburger Teoremi: momentler ölçüyü tek biçimde belirler.
Sistem hedefin matematiksel zorunluluğunu okur, molekülü oradan kurar.

Paket düzeni (eski tek-dosya molecular_derivation.py'den bölündü):
  _types.py   ← GenesisCandidate / SimStep / SimulationReport / GenesisReport + sabitler
  _genesis.py ← MolecularGenesis sınıfı
"""
from __future__ import annotations

from ._genesis import MolecularGenesis
from ._types import (
    _ATOMS,
    _BONDS,
    GenesisCandidate,
    GenesisReport,
    SimStep,
    SimulationReport,
)

__all__ = [
    "GenesisCandidate",
    "GenesisReport",
    "SimStep",
    "SimulationReport",
    "MolecularGenesis",
    "_ATOMS",
    "_BONDS",
]
