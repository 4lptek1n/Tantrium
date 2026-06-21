"""Öz-gönderim sabit noktası — makinenin kendine bakması (strange loop, exact).

Mimarinin atomik hareketi dışarıdaki nesneye uygulanır: girdi → G=AᵀA → moment →
23-paradigma → ~45-boyutlu imza. Bu modül o işlemi makinenin KENDİSİNE çevirir,
ve okumayı 8 momente DEĞİL, tam 45-boyutlu paradigma imzasına katlar:

    s (45-dim imza)  →  encode(s)  →  23-paradigma  →  s_next (45-dim)

Sabit nokta s*: makine kendine baktığında kendini geri veren öz-tutarlı imza.

DÜRÜST ÖLÇÜT: Bir sabit noktanın "gerçekten kapandığı" iki ayrı sorudur —
  • Stieltjes/Hamburger ✓  (ölçü gerçek, [0,∞) destekli)  — momentlerde OTOMATİK
  • Turán ≥ 0 / Laguerre-Pólya hiperbolik  — OTOMATİK DEĞİL, momentler log-konveks
    olduğundan genelde NEGATİF. Asıl RH-kriteri budur; sabit noktanın hiperbolik olup
    olmadığı ayrıca ve dürüstçe raporlanır.

ML yok, dış veri yok, deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass


def _signature(moments) -> list[float]:
    """Bir nesnenin ~45-boyutlu tam paradigma imzası (23 paradigmanın çıktıları)."""
    from tantrium.core.encoder import encode
    from tantrium.core.metric import paradigm_signature
    obj = encode(list(moments), name="self")
    return paradigm_signature(obj.structure)


def self_map(signature) -> list[float]:
    """45-dim imza → encode → 23-paradigma → yeni 45-dim imza (G=AᵀA, kendine)."""
    from tantrium.core.encoder import encode
    from tantrium.core.metric import paradigm_signature
    obj = encode(list(signature), name="self")
    return paradigm_signature(obj.structure)


def _l2(a, b) -> float:
    n = min(len(a), len(b))
    return sum((float(a[i]) - float(b[i])) ** 2 for i in range(n)) ** 0.5


@dataclass
class SelfReferenceResult:
    """Öz-gönderim yörüngesinin sonucu (45-boyutlu imza uzayında)."""
    verdict: str                      # FIXED_POINT | CYCLE(period=n) | WANDERING
    iterations: int
    fixed_signature: list[float] | None   # s* (45-dim)
    fixed_moments: list[float] | None     # encode(s*).moments — alttaki ölçü
    self_distances: list[float]
    # DÜRÜST RH durumu (sabit noktanın asıl kapanışı)
    stieltjes: bool = False           # ölçü gerçek mi (otomatik)
    turan_min: float = 0.0            # Turán marjı — ≥0 ise hiperbolik-aday
    laguerre_polya: bool = False      # Jensen hiperboliklik (ASIL RH-kriteri)
    rank: int = 0
    sealed_hash: str = ""

    def summary(self) -> str:
        return (
            f"Öz-gönderim (45-dim): {self.verdict} | {self.iterations} adım | "
            f"son öz-mesafe={self.self_distances[-1] if self.self_distances else 0:.3g}\n"
            f"  s* sertifikası: rank={self.rank} Stieltjes={'✓' if self.stieltjes else '✗'} "
            f"Turán_min={self.turan_min:+.4g} "
            f"Laguerre-Pólya(hiperbolik)={'✓' if self.laguerre_polya else '✗'} "
            f"seal={self.sealed_hash[:12]}"
        )


def self_reference_orbit(seed=None, max_iter: int = 64, tol: float = 1e-5) -> SelfReferenceResult:
    """Makineyi 45-dim imza uzayında kendi üzerine katla; sabit noktayı ara ve
    DÜRÜSTÇE hiperbolik (Laguerre-Pólya) olup olmadığını raporla."""
    from tantrium.core.encoder import encode
    from tantrium.core.jensen import laguerre_polya_test
    from tantrium.core.rh_certificate import certify_rh

    if seed is None:
        seed = [1.0 / (k + 1) for k in range(8)]
    s = _signature(seed)              # başlangıç imzası (45-dim)

    orbit = [s]
    dists: list[float] = []
    verdict = "WANDERING"
    fixed = None

    for _ in range(max_iter):
        nxt = self_map(s)
        d = _l2(s, nxt)
        dists.append(d)
        if d < tol:
            verdict, fixed = "FIXED_POINT", nxt
            orbit.append(nxt)
            break
        cycle_hit = None
        for j, prev in enumerate(orbit):
            if _l2(nxt, prev) < tol:
                cycle_hit = len(orbit) - j
                break
        orbit.append(nxt)
        if cycle_hit is not None:
            verdict, fixed = f"CYCLE(period={cycle_hit})", nxt
            break
        s = nxt

    if fixed is None:
        fixed = orbit[-1]

    # alttaki ölçü + DÜRÜST RH durumu
    obj = encode(list(fixed), name="fixed")
    mu = [float(m) for m in obj.moments]
    cert = certify_rh(mu, name="self_fixed")
    lp = laguerre_polya_test(mu, max_degree=4)

    return SelfReferenceResult(
        verdict=verdict, iterations=len(dists),
        fixed_signature=fixed, fixed_moments=mu,
        self_distances=dists,
        stieltjes=cert.criteria.stieltjes_certified,
        turan_min=cert.turan_min,
        laguerre_polya=lp.laguerre_polya,
        rank=cert.criteria.rank,
        sealed_hash=cert.sealed_hash,
    )
