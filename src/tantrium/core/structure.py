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
