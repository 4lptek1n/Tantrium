"""GapFinder — 4 boşluk-tespit sinyalinin TEK dispatcher'ı (#10 dedup).

Manifold boşluğu 4 farklı yöntemle tespit ediliyordu, her biri FARKLI algoritma,
dönüş tipi ve çağıran (gerçek ayrım — naif birleştirme gücü öldürür):

  geometric → NecessityEngine.find_manifold_gaps  (teorem midpoint geometrisi)
  anchor    → MetaParadigm.blind_spots            (çapa SPECTRAL_BRIDGE bağlantı zayıflığı)
  recorded  → Explorer.scan_frontier              (geçmiş kayıtlı boşluklar)
  grid      → MomentTopology.analyze              (boş moment-grid hücreleri)

GapFinder bu 4 metoda DOKUNMAZ — hepsi native çağrılabilir kalır. Yalnız ADDITIVE
bir yüz ekler: tek `find(signal=)` girişi + normalize `Gap` görünümü. Her Gap orijinal
nesneyi `raw` alanında taşır → güç KAYBOLMAZ, sadece tek kapı arkasına toplanır.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_SIGNALS = ("geometric", "anchor", "recorded", "grid")


@dataclass
class Gap:
    """4 sinyalin ortak normalize yüzü. `raw` orijinal nesneyi taşır (güç korunur)."""

    signal: str  # geometric | anchor | recorded | grid
    name: str  # kanonik etiket
    description: str  # insan-okunur
    location: list[float] | None = None  # moment-uzayı koordinatı (varsa)
    priority: float = 0.0  # araştırma önceliği (yüksek=önce)
    raw: object = None  # ManifoldGap / dict / ExplorationObjective / MathRegion


class GapFinder:
    """4 boşluk-tespit sinyalini tek dispatcher arkasına alan additive facade."""

    def __init__(self, engine: CertificationEngine) -> None:
        self.engine = engine

    def find(self, signal: str = "all", **kw) -> list[Gap]:
        """Boşlukları normalize Gap listesi olarak döndür.

        signal: "geometric" | "anchor" | "recorded" | "grid" | "all".
        **kw ilgili alt-metoda geçer (örn. domain, threshold, grid_n, n_gaps).
        "all" → 4 sinyal birleşik, priority azalan sıralı.
        """
        if signal == "all":
            gaps: list[Gap] = []
            for s in _SIGNALS:
                try:
                    gaps.extend(self._dispatch(s, kw))
                except Exception:
                    continue  # bir sinyal düşse diğerleri akar (fail-open)
            gaps.sort(key=lambda g: g.priority, reverse=True)
            return gaps
        if signal not in _SIGNALS:
            raise ValueError(f"Unknown gap signal: {signal!r} (expected {_SIGNALS} or 'all')")
        return self._dispatch(signal, kw)

    def _dispatch(self, signal: str, kw: dict) -> list[Gap]:
        if signal == "geometric":
            return self._geometric(kw)
        if signal == "anchor":
            return self._anchor(kw)
        if signal == "recorded":
            return self._recorded(kw)
        return self._grid(kw)

    # ── 4 sinyal adaptörü (orijinal metotlar DEĞİŞMEZ) ─────────────────────

    def _geometric(self, kw: dict) -> list[Gap]:
        from tantrium.reasoning.necessity import NecessityEngine

        domain = kw.get("domain", "math_kernel")
        raw_gaps = NecessityEngine(self.engine).find_manifold_gaps(
            domain=domain,
            n_gaps=kw.get("n_gaps", 5),
            max_pairs=kw.get("max_pairs", 40),
        )
        out = []
        for g in raw_gaps:
            near = "+".join(c.replace("theorem:", "") for c in g.nearest_concepts[:2])
            out.append(
                Gap(
                    signal="geometric",
                    name=f"GEOM[{near}]",
                    description=g.description,
                    location=list(g.centroid),
                    priority=10.0,  # geometrik zorunluluk yüksek öncelik
                    raw=g,
                )
            )
        return out

    def _anchor(self, kw: dict) -> list[Gap]:
        from tantrium.meta.paradigm import MetaParadigm

        threshold = kw.get("threshold", 5)
        raw_gaps = MetaParadigm(self.engine).blind_spots(threshold=threshold)
        out = []
        for d in raw_gaps:
            cnt = d.get("count", 0)
            out.append(
                Gap(
                    signal="anchor",
                    name=d.get("anchor", "UNKNOWN"),
                    description=(
                        f"{d.get('anchor')} zayıf temsil: {cnt} köprü "
                        f"(< {threshold}). Anahtarlar: {', '.join(d.get('keywords', [])[:3])}"
                    ),
                    location=None,
                    # az komşu = yüksek öncelik (threshold − count)
                    priority=float(max(threshold - cnt, 0)),
                    raw=d,
                )
            )
        return out

    def _recorded(self, kw: dict) -> list[Gap]:
        from tantrium.research.explorer import Explorer

        objectives = Explorer(self.engine).scan_frontier()
        out = []
        for o in objectives:
            out.append(
                Gap(
                    signal="recorded",
                    name=f"{o.gap_paradigm}:{o.source_object}",
                    description=f"{o.gap_name} ({o.gap_paradigm}) kaynak={o.source_object}",
                    location=None,
                    priority=float(o.priority),
                    raw=o,
                )
            )
        return out

    def _grid(self, kw: dict) -> list[Gap]:
        from tantrium.meta.topology import MomentTopology

        regions = MomentTopology(self.engine).analyze(grid_n=kw.get("grid_n", 12))
        out = []
        for r in regions:
            if not r.is_unknown:
                continue  # yalnız boş bölgeler boşluk
            out.append(
                Gap(
                    signal="grid",
                    name=r.named_unknown or r.region_id,
                    description=(
                        f"Boş moment bölgesi {r.region_id} "
                        f"({r.density_class}); sertifikalanabilir={r.certifiable}"
                    ),
                    location=list(r.center),
                    # frontier (komşulu boşluk, certifiable) > void (izole)
                    priority=3.0 if r.certifiable else 1.0,
                    raw=r,
                )
            )
        return out
