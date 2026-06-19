"""Varlık normalleştirme yardımcısı (edinme/gözlem katmanı kaldırıldı).

ASİ öğrenmez/gözlemlemez; mevcut manifold üzerinde hesaplar. Eski AutonomousObserver,
metin-ilişki çıkarımı ve evren-kapısı (edinme) kaldırıldı. Yalnız saf string normalleştirme
kaldı (causal_chain/what_if gürültü-suffix temizliği için).
"""
from __future__ import annotations

# Gürültü son-ekleri: "ras pathway" → "ras" (kausal varlık eşleştirmesi için)
_NOISE_SUFFIXES = (
    " pathway", " signaling", " cascade", " network", " complex",
    " receptor", " ligand", " protein", " gene", " family",
    " system", " process", " activity", " function", " mechanism",
    " activation", " inhibition", " phosphorylation", " expression",
    " regulation", " response", " production", " proliferation",
    " enzyme", " kinase", " factor", " domain", " subunit",
    " formation", " degradation", " synthesis", " metabolism",
)


def _normalize_entity(term: str) -> str:
    """Gürültü suffix'lerini temizle: "ras pathway" → "ras"."""
    t = term.strip().lower()
    for sfx in _NOISE_SUFFIXES:
        if t.endswith(sfx) and len(t) - len(sfx) > 2:
            t = t[: -len(sfx)].strip()
    return t
