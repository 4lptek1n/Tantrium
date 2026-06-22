"""SpectralFlow — bir operatör YOLUNUN topolojik değişmezi (mimarinin 5. ekseni).

Dört katman (SpectralReading) tek operatörü okur; bu, operatörler arası bir YOLU okur.
Bir özeşlenik aile G_t boyunca bir referans seviyeyi net kaç özdeğerin geçtiği —
spektral akış — yolun topolojik yüküdür (hiçbir tek okumanın göremediği global değişmez;
Atiyah-Singer indeksinin aile hali).

Makine iki tür yol kurar, ikisi de bu eksene sahip:
  • transport: iki yapı arası G_t = (1−t)G_A + t·G_B  → dönüşümün topolojik yükü
  • Cosmos:    yaşam-döngüsü yörüngesi (doğuş → son)   → evrenin topolojik yükü

net_flow=0 ∧ crossings=0 → topolojik engel yok (düzgün, sürekli deforme edilebilir).
crossings>0 → modlar yeniden örgütleniyor (avoided crossings — Berry fazı/konik kesişim).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SpectralFlow:
    """Bir operatör yolunun topolojik okuması."""
    net_flow: int          # net özdeğer geçişi (topolojik yük; işaretli)
    crossings: int         # toplam geçiş (mod yeniden-örgütlenmesi)
    n_levels: int
    smooth: bool           # crossings==0 → topolojik engel yok

    def summary(self) -> str:
        eng = "düzgün (topolojik engel YOK)" if self.smooth \
            else f"{self.crossings} mod yeniden-örgütlenmesi (avoided crossing)"
        return (f"SpectralFlow — topolojik yük (net akış) = {self.net_flow:+d} | "
                f"{eng} | {self.n_levels} seviye")


def _pad(M: np.ndarray, n: int) -> np.ndarray:
    P = np.zeros((n, n))
    P[:M.shape[0], :M.shape[1]] = M
    return P


def flow_between(g_a: np.ndarray, g_b: np.ndarray, steps: int = 400) -> SpectralFlow:
    """İki özeşlenik (PSD) operatör arası doğrusal yolun spektral akışı.

    G_t = (1−t)G_A + t·G_B; referans = yol boyunca özdeğerlerin medyanı; net akış =
    referansı yukarı geçen − aşağı geçen özdeğer sayısı."""
    n = max(g_a.shape[0], g_b.shape[0])
    ga, gb = _pad(np.asarray(g_a, float), n), _pad(np.asarray(g_b, float), n)
    ts = np.linspace(0.0, 1.0, steps)
    sample = np.concatenate([np.linalg.eigvalsh((1 - t) * ga + t * gb) for t in ts[::40]])
    ref = float(np.median(sample))
    prev = np.sort(np.linalg.eigvalsh(ga)) - ref
    net = crossings = 0
    for t in ts[1:]:
        cur = np.sort(np.linalg.eigvalsh((1 - t) * ga + t * gb)) - ref
        for i in np.where(np.sign(cur) * np.sign(prev) < 0)[0]:
            crossings += 1
            net += 1 if cur[i] > prev[i] else -1
        prev = cur
    return SpectralFlow(net_flow=int(net), crossings=int(crossings),
                        n_levels=n, smooth=(crossings == 0))


def _gram(query) -> np.ndarray:
    from tantrium.core.encoder import UniversalEncoder
    A = np.asarray(UniversalEncoder()._to_matrix(query), dtype=float)
    return A.T @ A


def spectral_flow(a, b, steps: int = 400) -> SpectralFlow:
    """İki girdiyi birbirine dönüştüren yolun topolojik yükü (5. eksen).

    G_A → G_B morfingi boyunca özdeğer geçişleri. Özdeş girdi → 0; düzgün/yakın
    dönüşüm → 0 geçiş; topolojik olarak farklı yapı → sıfırdan farklı net akış.
    """
    return flow_between(_gram(a), _gram(b), steps=steps)
