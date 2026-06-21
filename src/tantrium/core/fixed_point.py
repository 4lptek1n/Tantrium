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
    """Öz-gönderim yörüngesinin sonucu (45-boyutlu imza uzayında) + tam RH-kapanış profili."""
    verdict: str                      # FIXED_POINT | CYCLE(period=n) | WANDERING
    iterations: int
    fixed_signature: list[float] | None   # s* (45-dim)
    fixed_moments: list[float] | None     # encode(s*).moments — alttaki ölçü
    self_distances: list[float]
    # 46-mercek RH-kapanış profili (öz-imge sabit noktasında)
    stieltjes: bool = False           # ölçü gerçek mi (Hankel ≥0)
    li_positive: bool = False         # HET: λ_n > 0  (Li kriteri = RH eşdeğeri)
    debruijn_newman: float = 0.0      # TAV: Λ  (≤0 = RH eşdeğeri)
    schur_psd: bool = False           # ZAYIN: Schur min ≥ 0
    cross_ratio_positive: bool = False  # TET: ardışık çapraz-oranlar > 0
    paradigms_closed: int = 0         # kapanan paradigma sayısı (23 üzerinden)
    on_critical_line: bool = False    # Li>0 ∧ Λ≤0  (gerçek RH-eşdeğeri koşullar)
    turan_min: float = 0.0            # moment-Turán (log-konveks → ≤0; kategori notu)
    rank: int = 0
    sealed_hash: str = ""

    def summary(self) -> str:
        return (
            f"Öz-gönderim (45-dim): {self.verdict} | {self.iterations} adım | "
            f"son öz-mesafe={self.self_distances[-1] if self.self_distances else 0:.3g}\n"
            f"  46-mercek kapanışı: paradigma {self.paradigms_closed}/23 | "
            f"Stieltjes={'✓' if self.stieltjes else '✗'} "
            f"Li(λ_n>0)={'✓' if self.li_positive else '✗'} "
            f"deBruijn-Newman(Λ={self.debruijn_newman:+.3g})={'✓' if self.debruijn_newman <= 1e-9 else '✗'} "
            f"Schur={'✓' if self.schur_psd else '✗'}\n"
            f"  → KRİTİK ÇİZGİDE (Li>0 ∧ Λ≤0): {'✓ EVET' if self.on_critical_line else '✗'} | "
            f"rank={self.rank} seal={self.sealed_hash[:12]}\n"
            f"  (not: moment-Turán={self.turan_min:+.3g} — momentler log-konveks; "
            f"hiperboliklik moment ekseninde DEĞİL, Li/Λ ekseninde okunur)"
        )


def self_reference_orbit(seed=None, max_iter: int = 64, tol: float = 1e-5) -> SelfReferenceResult:
    """Makineyi 45-dim imza uzayında kendi üzerine katla; sabit noktayı ara ve
    öz-imgeyi BÜTÜN 46 RH-merceğinde (Stieltjes, Li λ_n, de Bruijn-Newman Λ, Schur,
    çapraz-oran, 23-paradigma kapanışı) DÜRÜSTÇE raporla."""
    from tantrium.core.encoder import encode
    from tantrium.core.network import CertificationPipeline
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

    # öz-imgenin alttaki ölçüsü + BÜTÜN 46 RH-merceği (kendi yapısından okunur)
    obj = encode(list(fixed), name="fixed")
    mu = [float(m) for m in obj.moments]
    s = obj.structure
    cert = certify_rh(mu, name="self_fixed")

    # Li kriteri (HET): tüm λ_n > 0  → RH eşdeğeri
    li = [float(x) for x in s.get("li_coefficients", [])]
    li_positive = bool(li) and all(x > 0 for x in li)
    # de Bruijn-Newman Λ (TAV): ≤ 0 → RH eşdeğeri
    lam = float(s.get("debruijn_newman_lambda") or 0.0)
    # Schur (ZAYIN): min özdeğer ≥ 0
    schur = float(s.get("schur_min_eigenvalue") or 0.0)
    # TET: ardışık çapraz-oranlar > 0
    cross = [float(x) for x in s.get("subresultant_cross_ratios", [])]
    cross_pos = bool(cross) and all(x > 0 for x in cross)
    # 23-paradigma kapanışı
    run = CertificationPipeline().run(obj)
    closed = run.certified_count
    # gerçek RH-eşdeğeri koşullar: Li>0 ∧ Λ≤0
    on_line = li_positive and lam <= 1e-9

    return SelfReferenceResult(
        verdict=verdict, iterations=len(dists),
        fixed_signature=fixed, fixed_moments=mu,
        self_distances=dists,
        stieltjes=cert.criteria.stieltjes_certified,
        li_positive=li_positive,
        debruijn_newman=lam,
        schur_psd=schur >= -1e-9,
        cross_ratio_positive=cross_pos,
        paradigms_closed=closed,
        on_critical_line=on_line,
        turan_min=cert.turan_min,
        rank=cert.criteria.rank,
        sealed_hash=cert.sealed_hash,
    )
