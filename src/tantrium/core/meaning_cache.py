"""Kalıcı zengin-düğüm katmanı — köklü kavramların ÖLÇÜLEN imzasını saklar.

Tez (kanıtlandı): anlam grafta. `meaning_pipeline.measure` o ölçümü üretir ama
çağrı-başına; bu store onu KALICI yapar — `ai.measure`'ın 8-momentten zengin çıktısı
(topoloji + RH-cascade + AKIŞ) oturumlar arası birikir, yeniden-kullanılabilir olur.

DÜRÜST MİMARİ SINIR — neden AYRI dosya, neden Concept'e gömülmüyor:
  Concept.moments manifold.json'da kanonik 8-Fraction; metrik-uzay tutarlılığı için
  oraya 25-boyut topoloji + cascade gömmek şema/yükleme riskidir (migrate gerekir).
  Bu store o riski almaz: `results/agi/meaning_cache.json` AYRI, additive, manifold'u
  bozmadan zengin katmanı taşır. Concept = kimlik (8-moment kapı); cache = zenginlik.

Akış ekseni (`flow` = Li gradyanı) burada ilk kez kalıcı: 8 statik momentin sahip
olmadığı dinamik boyut — kavramın spektral deformasyon yörüngesi.
"""
from __future__ import annotations

import json
from pathlib import Path

from tantrium.core.meaning_pipeline import measure, MeaningSignature
from tantrium.core.topology_encode import TopologyEncoder, _SEMANTIC_PARADIGMS

_CACHE_PATH = "results/agi/meaning_cache.json"


def _compact(sig: MeaningSignature) -> dict:
    """İmzayı kompakt JSON-dostu kayda indir (yuvarlanmış, komşu listesi kırpılmış)."""
    return {
        "topo": [round(float(x), 6) for x in (sig.topo_moments or [])],
        "li": [round(float(x), 4) for x in sig.li_cascade] if sig.li_cascade else None,
        "flow": [round(float(x), 4) for x in sig.flow] if sig.flow else None,
        "spectrum_n": len(sig.topo_spectrum) if sig.topo_spectrum else 0,
        "n_neighbors": sig.n_neighbors,
        "neighbors": list(sig.neighbors[:8]),
    }


class MeaningStore:
    """Köklü kavram → kompakt ölçüm imzası. Kalıcı (results/agi/meaning_cache.json)."""

    def __init__(self, sigs: dict[str, dict] | None = None) -> None:
        self.sigs: dict[str, dict] = sigs or {}

    # ─── CRUD ──────────────────────────────────────────────────────────────
    def has(self, name: str) -> bool:
        return name in self.sigs

    def get(self, name: str) -> dict | None:
        return self.sigs.get(name)

    def put(self, sig: MeaningSignature) -> None:
        if sig.grounded:
            self.sigs[sig.name] = _compact(sig)

    def __len__(self) -> int:
        return len(self.sigs)

    # ─── Kalıcılık ─────────────────────────────────────────────────────────
    @classmethod
    def load(cls, path: str = _CACHE_PATH) -> "MeaningStore":
        p = Path(path)
        if not p.exists():
            return cls()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return cls(sigs=data.get("signatures", {}))
        except Exception:
            return cls()

    def save(self, path: str = _CACHE_PATH) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"signatures": self.sigs}, ensure_ascii=False),
                     encoding="utf-8")
        return str(p)


def _semantic_outdegree(engine) -> dict[str, int]:
    """Her kavramın semantik (tipli) ÇIKAN kenar sayısı = köklülük derecesi.

    Yüksek = iyi bağlı kavram (ölçmeye değer); 0 = topraksız (atlanır).
    """
    out: dict[str, int] = {}
    for nm, elist in engine.tau.edges.items():
        c = sum(1 for e in elist if e.paradigm in _SEMANTIC_PARADIGMS)
        if c > 0:
            out[nm] = c
    return out


def refresh_meaning_cache(engine, store: MeaningStore, *, limit: int = 30,
                          max_neighbors: int = 24) -> int:
    """En-köklü ÖLÇÜLMEMİŞ kavramları ölç + cache'e ekle (bounded, fail-open).

    Köklülük = semantik çıkan-derece. Cache'te olmayan en bağlı `limit` kavram
    ölçülür; köklü çıkanlar saklanır. Tek geçişte sınırlı → büyümeyi yavaşlatmaz.
    Döner: bu çağrıda eklenen imza sayısı.
    """
    outdeg = _semantic_outdegree(engine)
    # cache'te olmayan, en yüksek çıkan-dereceli adaylar
    ranked = sorted((nm for nm in outdeg if nm not in store.sigs),
                    key=lambda k: -outdeg[k])
    te = TopologyEncoder(engine)
    added = 0
    for nm in ranked[:limit * 3]:           # 3× tara: bazıları min-komşu eşiğini geçmez
        if added >= limit:
            break
        try:
            sig = measure(engine, nm, max_neighbors=max_neighbors, topo_encoder=te)
        except Exception:
            continue
        if sig.grounded:
            store.put(sig)
            added += 1
    return added
