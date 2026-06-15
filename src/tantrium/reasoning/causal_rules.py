"""Tek-gerçek kausal kural tablosu — transitif çıkarım için ORTAK kaynak.

`ai.hypothesize` (transitif hipotez) ve `growth._science_consolidate` (büyürken bilim)
ikisi de buradan okur — kural tablosu TEK yerde (kopya yok). Mimari ilke: gerçek
duplikasyon tek arayüze iner (FILE_LEDGER).

Transitif kausal: "A -rel1-> B -rel2-> C" ⟹ "A -derived-> C".
Örn: A INHIBITS B, B ACTIVATES C ⟹ A INHIBITS C (baskıladığını aktive edeni baskılar).
"""
from __future__ import annotations

# (rel1, rel2) → türetilen ilişki
TRANSITIVE_CAUSAL: dict[tuple[str, str], str] = {
    ("INHIBITS", "ACTIVATES"): "INHIBITS",
    ("INHIBITS", "CAUSES"):    "INHIBITS",
    ("INHIBITS", "INHIBITS"):  "ACTIVATES",
    ("ACTIVATES", "ACTIVATES"): "ACTIVATES",
    ("ACTIVATES", "CAUSES"):   "CAUSES",
    ("ACTIVATES", "INHIBITS"): "INHIBITS",
    ("CAUSES", "CAUSES"):      "CAUSES",
    ("CAUSES", "ACTIVATES"):   "CAUSES",
}

# Kausal ilişki paradigmaları (transitif çıkarıma giren kenar tipleri)
CAUSAL_PARADIGMS: frozenset = frozenset({"INHIBITS", "ACTIVATES", "CAUSES"})
