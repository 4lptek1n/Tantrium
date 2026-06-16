"""Anlam ölçüm boru hattı — ÖLÇTÜĞÜMÜZÜ kullanan tek yol.

Kanıt (canlı rename-invariance, test_meaning_pipeline): anlam harfte değil TAU
grafında. `access`in adını çöp harflere çevirdik, ilişkilerini koruyunca anlamı
kıpırdamadı (ΔTOPOLOJİ≈6e-5), harf imzası tamamen değişti (ΔHARF≈0.9). Bu boru
hattı o ölçümü KULLANIR — üç kat:

  yüzey (harf)    = bootstrap adresi. Yeni/yalıtık kavramı benzer-yazılışa düşürür;
                    köklendikçe körelir. `encoder._text_to_signature_moments`.
  topoloji (graf) = ANLAM. Köklü kavramda BİRİNCİL; rename-invariant (yalnız
                    `tau.edges`'e bakar, harfe değil). `TopologyEncoder`.
  RH-cascade      = topoloji Laplacian'ında Li katsayıları + akış gradyanı.
                    DARBOĞAZSIZ: harf yolundaki `A=Hankel(8moment)` sıkıştırması
                    YOK — topoloji spektrumu n≤25 gerçek özdeğer taşır, cascade
                    orada gerçek ayrım yapar (8 momentin altında değil).

Köklü kavram → modality="relational" (topoloji birincil). Yetersiz semantik
komşuluk → modality="surface" (harfe düş — dürüst sınır, TopologyEncoder None döner).

Mimari: additive. Mevcut harf-sertifikasyon yolu DEĞİŞMEZ; bu, köklü kavram için
"ne demek"i birincil ölçü yapan paralel kattır.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from tantrium.core.topology_encode import TopologyEncoder


def _li_cascade(spectrum: list[float], k: int = 4) -> list[float]:
    """RH-merdiveni Li katsayıları, TOPOLOJİ spektrumu üzerinde (darboğazsız).

    Her özdeğer λ bir spektral sıfır ρ=1/2+iλ tanımlar (pipeline.py HET ile aynı
    tanım) → λ_n = Σ_ρ [1−(1−1/ρ)^n]. Harf yolunda spektrum 8 momentten türetildiği
    için bu cascade orada yeni bilgi taşımıyordu; topoloji spektrumu (n≤25 gerçek
    özdeğer) 8-moment darboğazına tabi DEĞİL → cascade gerçek ayrım taşır.
    """
    pos = [e for e in spectrum if e > 1e-12] or [1.0]
    out: list[float] = []
    for n in range(1, k + 1):
        s = 0.0
        for lam in pos:
            mod2 = 0.25 + lam * lam
            omr = 1.0 - 0.5 / mod2          # Re(1 − 1/ρ)
            omi = lam / mod2                # Im(1 − 1/ρ)
            r = (omr * omr + omi * omi) ** 0.5
            s += 1.0 - (r ** n) * math.cos(n * math.atan2(omi, omr))
        out.append(s)
    return out


@dataclass
class MeaningSignature:
    """Bir kavramın üç-katlı ölçümü: yüzey + topoloji + RH-cascade."""

    name: str
    surface_moments: list[float]                 # harf (bootstrap adresi)
    modality: str = "surface"                    # "relational" | "surface"
    topo_moments: list[float] | None = None      # graf (anlam) — köklüyse
    topo_spectrum: list[float] | None = None     # tam Laplacian spektrumu (n≤25)
    li_cascade: list[float] | None = None        # Li katsayıları (topoloji üstünde)
    flow: list[float] | None = None              # akış gradyanı λ_{n+1}−λ_n
    n_neighbors: int = 0
    neighbors: list[str] = field(default_factory=list)

    @property
    def grounded(self) -> bool:
        return self.modality == "relational"

    def primary_moments(self) -> list[float]:
        """Karşılaştırmada kullanılacak BİRİNCİL ölçü: köklüyse topoloji, değilse harf."""
        return self.topo_moments if self.grounded else self.surface_moments


def measure(engine, name: str, *, max_neighbors: int = 24,
            topo_encoder: TopologyEncoder | None = None) -> MeaningSignature:
    """Kavramı üç katta ölç. Köklüyse topoloji birincil + RH-cascade; değilse harf.

    `topo_encoder` verilirse yeniden kurulmaz (indegree cache paylaşımı — toplu ölçüm hızlı).
    """
    surface = [float(m) for m in engine.encoder.encode(name, name=name[:64]).moments]
    te = topo_encoder or TopologyEncoder(engine)
    obj = te.encode(name, max_neighbors=max_neighbors)
    if obj is None:
        return MeaningSignature(name=name, surface_moments=surface, modality="surface")

    spectrum = [float(x) for x in obj.structure.get("eigenvalues", [])]
    li = _li_cascade(spectrum) if spectrum else None
    flow = [li[i + 1] - li[i] for i in range(len(li) - 1)] if li else None
    return MeaningSignature(
        name=name,
        surface_moments=surface,
        modality="relational",
        topo_moments=[float(m) for m in obj.moments],
        topo_spectrum=spectrum,
        li_cascade=li,
        flow=flow,
        n_neighbors=int(obj.structure.get("n_neighbors", 0)),
        neighbors=list(obj.structure.get("neighbors", [])),
    )


def _l1(a: list[float], b: list[float]) -> float:
    k = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(k))


def _cascade_distance(a: list[float], b: list[float]) -> float:
    """Li-cascade GÖRELİ mesafesi, [0,1]'e sınırlı (moment-L1 ile ölçek-uyumlu).

    Li katsayıları O(10–40) ölçekte; ham L1 [0,1] momentle harmanlanamaz. Per-katsayı
    göreli fark |a−b|/(|a|+|b|+ε) ortalaması → [0,1] sınırlı, harmanlanabilir.
    """
    k = min(len(a), len(b))
    if k == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) / (abs(a[i]) + abs(b[i]) + 1e-9) for i in range(k)) / k


def signature_distance(sa: MeaningSignature, sb: MeaningSignature, *,
                       cascade_weight: float = 0.0) -> float:
    """İki ölçümün mesafesi. İKİSİ DE köklüyse topoloji (anlam); değilse harf (yüzey).

    cascade_weight>0 ise topoloji-moment mesafesine RH-cascade'in GÖRELİ-sınırlı (Li)
    mesafesi karışır — darboğazsız spektrumun ek ayrımı, ölçek-uyumlu. Varsayılan 0
    (saf topoloji-moment, geriye dönük uyumlu meaning_distance ile aynı).
    """
    if sa.grounded and sb.grounded:
        d = _l1(sa.topo_moments, sb.topo_moments)
        if cascade_weight > 0.0 and sa.li_cascade and sb.li_cascade:
            dc = _cascade_distance(sa.li_cascade, sb.li_cascade)
            d = (1.0 - cascade_weight) * d + cascade_weight * dc
        return d
    return _l1(sa.surface_moments, sb.surface_moments)


def measure_distance(engine, a: str, b: str, *, max_neighbors: int = 24,
                     cascade_weight: float = 0.0) -> float:
    """İki kavramı ölç + anlam-birincil mesafe (köklüyse topoloji, değilse harf)."""
    te = TopologyEncoder(engine)
    sa = measure(engine, a, max_neighbors=max_neighbors, topo_encoder=te)
    sb = measure(engine, b, max_neighbors=max_neighbors, topo_encoder=te)
    return signature_distance(sa, sb, cascade_weight=cascade_weight)
