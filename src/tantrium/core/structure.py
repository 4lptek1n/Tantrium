"""Ham yapısal ayrışma — Kronecker/Prony: gözlemin GERÇEK üreten yapısı.

EVRENE TERSİNE MÜHENDİSLİĞİN matematiksel çekirdeği. Bir gözlem dizisi x[0..N] için
Hankel matrisi H_{ij}=x[i+j] kurulur; Kronecker teoremi: H SONLU rank r ⟺ x, r üstelin
toplamı (= r 'mod' / gizli operatörün r özdeğeri). Yapılı sinyal düşük rank (tekil-değerler
çöker); gürültü tam rank (düz); manipülasyon rank'ı FIRLATIR (sahtelik/anomali yapıdan okunur).

Encoder'ın 8-moment sıkıştırması bunu siler (8 moment hep ~4 atoma çöker) — bu modül HAM
veriden okur, içeriğe bakmadan. Saf numpy.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StructuralReading:
    n: int                       # gözlem uzunluğu
    rank: int                    # üreten mod sayısı = GERÇEK karmaşıklık (Hankel rank)
    modes: list = field(default_factory=list)        # üreten poller (Prony özdeğerleri)
    singular_values: list = field(default_factory=list)  # normalize tekil-değer spektrumu
    structured: bool = False     # rank ≪ n/2 → gizli düzen var
    sv_gap: float = 0.0          # rank'taki spektral boşluk (kesinlik göstergesi)


def structural_decomposition(samples, tol: float = 1e-6,
                             max_modes: int | None = None) -> "StructuralReading":
    """Ham gözlemden üreten yapıyı çıkar: Hankel rank + Prony modları + tekil-değer spektrumu.

    rank = üreten mod sayısı (Kronecker). structured = rank gözlem boyutunun yarısından
    belirgin küçükse (gizli düzen). sv_gap = rank'taki tekil-değer düşüşü (kesinlik).
    """
    import numpy as np

    x = np.asarray([float(s) for s in samples], dtype=float)
    N = len(x)
    if N < 4:
        return StructuralReading(n=N, rank=N, modes=[], singular_values=[1.0] * N)
    m = N // 2
    H = np.array([[x[i + j] for j in range(m)] for i in range(m)], dtype=float)
    try:
        sv = np.linalg.svd(H, compute_uv=False)
    except Exception:
        return StructuralReading(n=N, rank=m, modes=[], singular_values=[])
    s0 = sv[0] if sv[0] > 0 else 1.0
    svn = (sv / s0).tolist()
    rank = int(np.sum(np.asarray(svn) > tol))
    rank = max(1, min(rank, m))
    # rank'taki spektral boşluk: çöküş ne kadar keskin (kesin yapı göstergesi)
    sv_gap = float(svn[rank - 1] - (svn[rank] if rank < len(svn) else 0.0))
    structured = bool(rank < m * 0.75)   # tam-rank'ın belirgin altı = gizli düzen

    # Prony modları: shifted Hankel genelleştirilmiş özdeğer (rank-kesilmiş)
    modes: list = []
    try:
        r = rank if max_modes is None else min(rank, max_modes)
        H0 = np.array([[x[i + j] for j in range(r)] for i in range(r)], dtype=float)
        H1 = np.array([[x[i + j + 1] for j in range(r)] for i in range(r)], dtype=float)
        M = np.linalg.pinv(H0) @ H1
        eigs = np.linalg.eigvals(M)
        modes = [complex(round(e.real, 6), round(e.imag, 6)) for e in eigs]
    except Exception:
        modes = []

    return StructuralReading(
        n=N, rank=rank, modes=modes, singular_values=[round(v, 6) for v in svn],
        structured=structured, sv_gap=round(sv_gap, 6),
    )


def fit_recurrence(samples, order: int | None = None, max_order: int = 12):
    """Gürültü-DAYANIKLI lineer yineleme (AR) tahmini — en küçük kareler (denoise).

    x[n] ≈ Σ c_i x[n-i] sistemini TÜM n üzerinde aşırı-belirli çözer → gürültü ortalanır
    (exact Prony tek pencere; bu hepsini kullanır). order None → tekil-değer en-büyük-düşüş
    (sinyal/gürültü sınırı) ile otomatik. Döner: (c, order, residual_std).
    """
    import numpy as np
    x = np.asarray([float(s) for s in samples], dtype=float)
    N = len(x)
    if N < 4:
        return [], 0, 0.0
    if order is None:
        sd = structural_decomposition(x.tolist(), tol=1e-9)
        sv = np.asarray(sd.singular_values, dtype=float) if sd.singular_values else np.array([1.0])
        order = 1
        if len(sv) > 2:
            ratios = sv[:-1] / np.maximum(sv[1:], 1e-12)
            order = int(np.argmax(ratios[:max_order])) + 1
    p = max(1, min(int(order), max_order, N // 2 - 1))
    rows = [x[n - p:n][::-1] for n in range(p, N)]
    b = x[p:N]
    try:
        c, *_ = np.linalg.lstsq(np.array(rows), b, rcond=None)
        resid = b - np.array(rows) @ c
        return [float(v) for v in c], p, float(np.std(resid))
    except Exception:
        return [], p, 0.0


def forecast(samples, steps: int = 8, order: int | None = None):
    """Keşfedilen yasayla GELECEĞİ tahmin et. Döner: (forecast, coeffs, residual_std)."""
    c, p, sigma = fit_recurrence(samples, order)
    seq = [float(s) for s in samples]
    out: list = []
    for _ in range(int(steps)):
        if not c:
            break
        nxt = sum(ci * seq[-(i + 1)] for i, ci in enumerate(c))
        seq.append(nxt)
        out.append(nxt)
    return out, c, sigma


def anomaly_scan(samples, order: int | None = None, z: float = 3.0):
    """ANOMALİ/SAHTELİK tespiti — global yasaya karşı yerel sapma. 'Normal'i bilmeden.

    Veriyi yöneten yineleme bulunur; her nokta yasayla tahmin edilir; |kalıntı| > z·σ olan
    noktalar yapısal ANOMALİ (arıza/manipülasyon/olağandışı olay). Yer + şiddet döner.
    Döner: (anomalies[{index,residual,z}], residual_std).
    """
    import numpy as np
    c, p, sigma = fit_recurrence(samples, order)
    if not c:
        return [], 0.0
    x = [float(s) for s in samples]
    resids = [x[n] - sum(ci * x[n - (i + 1)] for i, ci in enumerate(c))
              for n in range(p, len(x))]
    s = float(np.std(resids)) or 1.0
    anomalies = [{"index": k + p, "residual": round(r, 5), "z": round(abs(r) / s, 2)}
                 for k, r in enumerate(resids) if abs(r) > z * s]
    return anomalies, s

