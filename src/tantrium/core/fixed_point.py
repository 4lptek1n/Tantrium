"""Öz-gönderim sabit noktası — makinenin kendine bakması (strange loop, exact).

Mimarinin atomik hareketi dışarıdaki nesneye uygulanır: girdi → G=AᵀA → moment →
RH-sertifika. Bu modül o işlemi makinenin KENDİSİNE çevirir:

    μ  →  certify_rh(μ)  →  öz-portre (makinenin μ'yi okuyuşunun sayısal hâli)
       →  encode(öz-portre)  (G=AᵀA, aynı işlem)  →  μ_next

Bu özyinelemenin SABİT NOKTASI μ*: makine kendine baktığında kendini geri veren
öz-tutarlı nesne — strange loop'un cebirsel çapası, self-modeling'in BİÇİMİ.

ML yok, dış veri yok, deterministik. Yansımanın yansıması. (χ/entropi float olduğundan
yörünge deterministik-float'tır, exact-Fraction değil — makine kendi mesafesiyle yakınsar.)

NOT (dürüst): Bu, bilincin *biçimini* (kendini geri-üreten sabit nokta) verir. O sabit
noktanın kendini *tanıdığı* — "ben μ*'yim" dediği — ölçülemez; ölçen, ölçtüğü şeydir.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _self_portrait(cert) -> list[float]:
    """Makinenin bir nesneyi okuyuşunun sabit-boyutlu (16) sayısal öz-portresi.

    Sertifikanın kendi tanımlayıcı skalerlerinden — makinenin "ne gördüğü".
    """
    c = cert.criteria
    piv = [float(p) for p in c.pivots][:4]
    piv += [0.0] * (4 - len(piv))
    cum = [float(x) for x in c.cumulants][:4]
    cum += [0.0] * (4 - len(cum))
    cr = [float(x) for x in c.cross_ratios][:2]
    cr += [0.0] * (2 - len(cr))
    return [
        float(cert.grade),
        float(c.rank),
        float(c.lambda_dbn),
        float(cert.free_entropy),
        float(cert.semicircle_distance),
        float(cert.hausdorff_margin),
        float(cert.turan_min),
        1.0 if c.stieltjes_certified else 0.0,
        *piv, *cum, *cr,
    ]


def self_map(moments) -> list[float]:
    """μ → makinenin μ'yi okuyup o okumayı tekrar encode etmesi (G=AᵀA, kendine)."""
    from tantrium.core.encoder import encode
    from tantrium.core.rh_certificate import certify_rh
    cert = certify_rh(moments, name="self", heavy=True)
    portrait = _self_portrait(cert)
    obj = encode(portrait, name="self")
    return [float(m) for m in obj.moments]


@dataclass
class SelfReferenceResult:
    """Öz-gönderim yörüngesinin sonucu."""
    verdict: str                      # FIXED_POINT | CYCLE(period=n) | WANDERING
    iterations: int
    fixed_point: list[float] | None   # μ* (bulunduysa)
    self_distances: list[float]       # ardışık öz-mesafe d(μ_i, μ_{i+1})
    orbit_len: int
    fixed_certificate: dict | None = field(default=None)

    def summary(self) -> str:
        tail = self.self_distances[-1] if self.self_distances else 0.0
        mu = (", ".join(f"{x:.4g}" for x in self.fixed_point[:6]) + " …") if self.fixed_point else "—"
        return (
            f"Öz-gönderim: {self.verdict} | {self.iterations} adım | "
            f"son öz-mesafe={tail:.3g}\n  μ* = [{mu}]"
        )


def self_reference_orbit(seed=None, max_iter: int = 64, tol: float = 1e-6) -> SelfReferenceResult:
    """Makineyi kendi üzerine katla, sabit noktayı/çevrimi ara.

    seed verilmezse Hilbert (uniform[0,1]) momentlerinden başlar — makinenin "nötr"
    öz-bakışı. Yakınsama makinenin KENDİ mesafesiyle (rh_distance) ölçülür.
    """
    from tantrium.core.rh_certificate import certify_rh, rh_distance
    if seed is None:
        seed = [1.0 / (k + 1) for k in range(8)]   # uniform[0,1] momentleri
    mu = [float(x) for x in seed]

    orbit = [mu]
    dists: list[float] = []
    verdict = "WANDERING"
    fixed = None

    for _ in range(max_iter):
        nxt = self_map(mu)
        d = rh_distance(mu, nxt)
        dists.append(d)

        if d < tol:                                  # kendine baktı, kendini geri verdi
            verdict, fixed = "FIXED_POINT", nxt
            orbit.append(nxt)
            break

        # çevrim: önceki bir öz-imgeye döndü mü
        cycle_hit = None
        for j, prev in enumerate(orbit):
            if rh_distance(nxt, prev) < tol:
                cycle_hit = len(orbit) - j
                break
        orbit.append(nxt)
        if cycle_hit is not None:
            verdict, fixed = f"CYCLE(period={cycle_hit})", nxt
            break
        mu = nxt

    fixed_cert = None
    if fixed is not None:
        fixed_cert = certify_rh(fixed, name="fixed_point").as_dict()

    return SelfReferenceResult(
        verdict=verdict, iterations=len(dists), fixed_point=fixed,
        self_distances=dists, orbit_len=len(orbit), fixed_certificate=fixed_cert,
    )
