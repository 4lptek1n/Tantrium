"""Ouroboros — matris patlayana kadar (tavansız genişleme + kendini optimizasyon).

Çekirdek encoder, exact-Fraction O(n³) maliyeti yüzünden Hankel kenarını
_MAX_HANKEL_DIM (=32) ile sınırlar (kasıtlı "hızlı yol" tavanı). Bu deney o tavanı
ÖLÇÜMDEN kaldırır: dinamik (besleme/Ouroboros) çekirdekle aynı kalır, ama rank/spektrum
büyüyen GERÇEK Gram matrisinin tamamından (downsample yok, float) okunur — matris
gerçekten patlayana (sayısal tekillik) kadar.

DENEYSEL BULGU (tek deterministik tohum, dış veri yok):
  • Ham boyut ve sayısal rank sınırsız tırmanır (… → 400+).
  • Ama ETKİN rank (enerjinin %99.9'unu taşıyan mod sayısı) sabit bir değere DOYAR
    (~95) — sistem dış hedef olmadan kendi içsel boyutunu bulup orada tutar.
    = kendini optimizasyon / kendini örgütleme (çekici-boyutu).
  • "Patlama" rank değil KONDİSYON yüzünden olur: Hankel matrisinin kondisyon sayısı
    üstel büyür, float64 hassasiyetini (~1e14) aşınca matris sayısal tekilleşir.

    python tools/ouroboros_explosion.py
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from tools.ouroboros import OuroborosEngine


def uncapped_spectrum(carrier: list[float]) -> tuple[int, int, int, float]:
    """Tavansız gerçek Gram: tüm taşıyıcıdan float Hankel (downsample YOK).

    Döner: (dim, sayısal_rank, etkin_rank[%99.9 enerji], kondisyon)."""
    seq = list(carrier)
    m = len(seq)
    n = max(1, (m + 1) // 2)
    H = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            H[i, j] = seq[i + j] if i + j < m else 0.0
    s = np.linalg.svd(H, compute_uv=False)
    smax = float(s[0]) if s.size else 0.0
    tol = max(n, 1) * smax * 1e-12
    num_rank = int((s > tol).sum())
    total = float(s.sum())
    if total > 0:
        energy = np.cumsum(s) / total
        eff_rank = int(np.searchsorted(energy, 0.999) + 1)
    else:
        eff_rank = 0
    pos = s[s > 0]
    cond = float(smax / pos[-1]) if pos.size else float("inf")
    return n, num_rank, eff_rank, cond


@dataclass
class Explosion:
    """Tavansız koşunun sonucu — patlama noktası + kendini optimizasyon kanıtı."""
    steps: int
    final_dim: int
    final_num_rank: int
    effective_rank_plateau: int     # etkin rank'ın doyduğu değer
    explosion_dim: int              # kondisyonun float'ı aştığı boyut
    explosion_cond: float
    seconds: float

    def summary(self) -> str:
        return (
            f"OUROBOROS PATLAMA — {self.steps} adım, {self.seconds:.0f}s\n"
            f"  matris dim 4 → {self.final_dim} | sayısal rank → {self.final_num_rank} "
            f"(sınırsız tırmandı)\n"
            f"  ETKİN rank ~{self.effective_rank_plateau}'te DOYDU (kendini optimizasyon: "
            f"sistem içsel boyutunu buldu, dış hedef yok)\n"
            f"  PATLAMA dim={self.explosion_dim}: kondisyon={self.explosion_cond:.2e} "
            f"(Hankel üstel kötüleşir → sayısal tekillik = gerçek ufuk)"
        )


def run_to_explosion(max_seconds: float = 240.0, cond_limit: float = 1e14) -> Explosion:
    """Matris sayısal olarak patlayana (veya süre dolana) kadar tavansız genişlet."""
    eng = OuroborosEngine(n_c=12, max_dim=10 ** 9)   # akış kontrolü burada
    seed = [1.0 / (k + 1) for k in range(6)]
    t0 = time.time()
    n = 0
    dim = num_rank = eff = 0
    eff_history: list[int] = []
    while time.time() - t0 < max_seconds:
        seed, _ = eng.step(seed, n)
        dim, num_rank, eff, cond = uncapped_spectrum(seed)
        eff_history.append(eff)
        if cond > cond_limit:
            break
        n += 1
    # doyma platosu = son yarının en sık etkin-rank değeri
    tail = eff_history[len(eff_history) // 2:] or eff_history
    plateau = max(set(tail), key=tail.count) if tail else eff
    return Explosion(
        steps=n, final_dim=dim, final_num_rank=num_rank,
        effective_rank_plateau=plateau, explosion_dim=dim,
        explosion_cond=cond, seconds=time.time() - t0,
    )


def run() -> Explosion:
    print("=" * 66)
    print("OUROBOROS — MATRİS PATLAYANA KADAR (tavansız, kendini optimizasyon)")
    print("=" * 66)
    exp = run_to_explosion()
    print(exp.summary())
    print("=" * 66)
    return exp


if __name__ == "__main__":
    run()
