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
    # Gramatik zenginleştirme — yalnız yön-belirgin (savunulabilir) kompozisyonlar.
    # Gen/hücre bir aktivatör/inhibitör ÜRETİR/KODLAR → etki o yönde propagatlar.
    ("EXPRESSES", "ACTIVATES"): "ACTIVATES",
    ("EXPRESSES", "INHIBITS"):  "INHIBITS",
    ("EXPRESSES", "CAUSES"):    "CAUSES",
    ("ENCODES", "ACTIVATES"):   "ACTIVATES",
    ("ENCODES", "INHIBITS"):    "INHIBITS",
    # Fosforilasyon bir aktivasyon/inhibisyon zincirine bağlanırsa o yönü taşır.
    ("PHOSPHORYLATES", "ACTIVATES"): "ACTIVATES",
    ("PHOSPHORYLATES", "INHIBITS"):  "INHIBITS",
    # DÜRÜST SINIR: TARGETS/BINDS/REGULATES yön-belirsiz → transitife GİRMEZ
    # (yanlış kural, kuralsızlıktan kötüdür — biyokimya temiz transitif değil).
}

# Kausal ilişki paradigmaları (transitif çıkarıma giren kenar tipleri) — yön-belirgin olanlar.
CAUSAL_PARADIGMS: frozenset = frozenset({
    "INHIBITS", "ACTIVATES", "CAUSES", "EXPRESSES", "ENCODES", "PHOSPHORYLATES"})

# JENERİK terimler: hipotez öznesi/nesnesi olamaz (role/complex/factor → anlamsız "bilim").
# TEK-GERÇEK: growth._science_consolidate + cognition.ScienceStep ikisi de buradan okur.
GENERIC_TERMS: frozenset = frozenset({
    "role", "complex", "factor", "system", "activity", "expression", "degradation",
    "process", "function", "mechanism", "response", "regulation", "component",
    "structure", "level", "type", "form", "member", "family", "group", "part",
    "effect", "result", "change", "state", "region", "site", "domain", "unit",
    "product", "aspects", "fundamental", "protein", "proteins", "gene", "genes",
    "cell", "cells", "molecule", "pathway", "signal", "signals", "subunit",
    "undefined", "unknown", "other", "various", "several", "many", "thing",
})


def derive_transitive_hypotheses(engine, *, max_seeds: int = 12, max_hyps: int = 10,
                                 sturm_check: int = 6) -> list[dict]:
    """TAU grafından TRANSİTİF hipotez türet (A -rel1-> B -rel2-> C ⟹ A -derived-> C),
    YENİ olanları (doğrudan kenar OLMAYAN) RH-Sturm pivotuyla sertifikala.

    TEK-GERÇEK derivasyon: `growth._science_consolidate` (büyürken bilim) ve
    `cognition.ScienceStep` (döngüde bilim) ikisi de buna delege — kopya yok.
    Bounded/fail-open. Döner: hipotez dict listesi (statement/subj/obj/via/chain/sturm_ok).
    """
    out: list[dict] = []
    try:
        tau = engine.tau
        seeds: list = []
        for s, el in tau.edges.items():
            if s.startswith("⟨") or len(s) > 40 or s.lower() in GENERIC_TERMS:
                continue
            cz = [e for e in el if getattr(e, "paradigm", "") in CAUSAL_PARADIGMS]
            if len(cz) >= 2:
                seeds.append((s, cz))
            if len(seeds) >= max_seeds * 4:
                break
        seeds = seeds[:max_seeds]
        seen: set = set()
        for s, cz in seeds:
            for e1 in cz:
                b = str(getattr(e1, "target", ""))
                for e2 in tau.edges.get(b, []):
                    p2 = getattr(e2, "paradigm", "")
                    if p2 not in CAUSAL_PARADIGMS:
                        continue
                    c = str(getattr(e2, "target", ""))
                    derived = TRANSITIVE_CAUSAL.get((e1.paradigm, p2))
                    if (not derived or c == s or c == b
                            or c.lower() in GENERIC_TERMS or b.lower() in GENERIC_TERMS):
                        continue
                    key = (s, derived, c)
                    if key in seen:
                        continue
                    if any(str(getattr(e, "target", "")) == c
                           and getattr(e, "paradigm", "") == derived
                           for e in tau.edges.get(s, [])):
                        continue
                    seen.add(key)
                    out.append({"statement": f"{s} {derived} {c}", "subj": s,
                                "obj": c, "via": b,
                                "chain": f"{s} -{e1.paradigm}-> {b} -{p2}-> {c}"})
                    if len(out) >= max_hyps:
                        break
                if len(out) >= max_hyps:
                    break
            if len(out) >= max_hyps:
                break
        if not out:
            return out
        # RH-Sturm sertifika (bounded) — kritik hat / gerçek-ölçü yolu
        try:
            from tantrium.core.production import ProductionEngine
            pe = ProductionEngine(engine)
            for h in out[:sturm_check]:
                ca = engine.manifold.concepts.get(h["subj"])
                cc = engine.manifold.concepts.get(h["obj"])
                if ca is not None and cc is not None:
                    try:
                        _ok, pmin = pe._sturm_path_pivot_min(
                            [float(m) for m in ca.moments],
                            [float(m) for m in cc.moments])
                        h["sturm_ok"] = bool(pmin >= -1e-3)
                    except Exception:
                        h["sturm_ok"] = None
        except Exception:
            pass
    except Exception:
        return out
    return out
