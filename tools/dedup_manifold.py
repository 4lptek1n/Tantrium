"""Manifold dedup — büyüme-üreteci pencere-kopyalarını temizle.

SORUN: algoritmik dizi üreteci her dizi için ~1500 "pencere" (`algo:<aile>_b<N>`)
yaratıyor ve encoder pencere indeksini yok sayıyor → bir ailenin tüm pencereleri
TIPATIP aynı momente çöküyor (L1=0). Sonuç: ~7500 hayalet kopya, 5 noktada.
`ai.consolidate()` bunları atlıyor (":" önekli adları hariç tutar).

ÇÖZÜM: her (aile, tam-moment) grubunda TEK temsilci tut, kalan pencereleri sil,
kenarlarını temsilciye yönlendir. Gerçek kelime/teorem isimlerine (öneksiz) DOKUNMA.

Kullanım:
  python tools/dedup_manifold.py --dry-run   # sadece raporla
  python tools/dedup_manifold.py --apply      # uygula + persist
"""
from __future__ import annotations

import re
import sys

sys.path.insert(0, "src")

_FAMILY_RE = re.compile(r"^(.*?)_b\d+$")  # algo:lucas_b37 -> algo:lucas


def _family(name: str) -> str | None:
    """Üreteç pencere-kopyası mı? Aile kökünü döndür, değilse None."""
    if ":" not in name:
        return None  # gerçek kelime/teorem — dokunma
    m = _FAMILY_RE.match(name)
    return m.group(1) if m else None


def dedup(apply: bool = False) -> dict:
    import tantrium

    ai = tantrium.AI()
    manifold = ai.engine.manifold
    tau = ai.engine.tau
    concepts = manifold.concepts

    # (aile, tam-moment imzası) → o gruptaki tüm pencere adları
    groups: dict[tuple[str, tuple], list[str]] = {}
    for name, c in concepts.items():
        fam = _family(name)
        if fam is None:
            continue
        key = (fam, tuple(c.moments))  # tam (Fraction) eşitlik
        groups.setdefault(key, []).append(name)

    # her grupta b-index'i en küçük olanı temsilci tut, kalanı sil
    def _bidx(n: str) -> int:
        m = re.search(r"_b(\d+)$", n)
        return int(m.group(1)) if m else 0

    remap: dict[str, str] = {}   # silinen → temsilci
    rep_count = 0
    for (fam, _moments), members in groups.items():
        if len(members) < 2:
            continue
        members.sort(key=_bidx)
        rep = members[0]
        rep_count += 1
        for dead in members[1:]:
            remap[dead] = rep

    n_before = len(concepts)
    e_before = sum(len(v) for v in tau.edges.values())

    if apply and remap:
        # 1) silinenlere işaret eden kenarları temsilciye yönlendir
        for src, edges in list(tau.edges.items()):
            for e in edges:
                if e.target in remap:
                    e.target = remap[e.target]
        # 2) silinen düğümlerin kendi kenar listelerini temsilciye taşı + sil
        for dead, rep in remap.items():
            dead_edges = tau.edges.pop(dead, [])
            if dead_edges:
                tau.edges.setdefault(rep, []).extend(
                    KnowledgeEdgeRetarget(e, rep) for e in dead_edges
                )
            manifold.concepts.pop(dead, None)
            tau.nodes.pop(dead, None)
        # 3) kenarları tekilleştir (self-loop ve (target,paradigm) tekrarı)
        for src, edges in tau.edges.items():
            seen = set()
            uniq = []
            for e in edges:
                if e.target == src:
                    continue
                k = (e.target, e.paradigm)
                if k in seen:
                    continue
                seen.add(k)
                uniq.append(e)
            tau.edges[src] = uniq
        tau._dirty = True
        ai.engine.auto_persist()

    n_after = len(manifold.concepts)
    e_after = sum(len(v) for v in tau.edges.values())
    return {
        "families_collapsed": rep_count,
        "copies_to_delete": len(remap),
        "concepts_before": n_before,
        "concepts_after": n_after if apply else n_before - len(remap),
        "edges_before": e_before,
        "edges_after": e_after,
        "applied": apply,
    }


def KnowledgeEdgeRetarget(e, new_source):
    """Taşınan kenarın source'unu temsilciye çevir (target korunur)."""
    e.source = new_source
    return e


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    rep = dedup(apply=apply)
    print("=== MANIFOLD DEDUP ===")
    for k, v in rep.items():
        print(f"  {k}: {v}")
    if not apply:
        print("\n(kuru-çalıştırma — silmek için --apply)")
