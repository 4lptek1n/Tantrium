"""Pozitiflik Merdiveni — "düşünmek = doğru yolda (kritik hatta) yürümek".

RH kanıt zincirinin pozitiflik basamakları bir düşünce/geçiş için bir DERİNLİK verir:
kavram-geçişi merdivenin kaç basamağını geçiyorsa o kadar "kritik hat üzerinde" =
o kadar az halüsinasyon. Sapan adım pozitifliği bozar → geometrik olarak engellenir.

DÜRÜST KAPSAM: yalnız bir kavram-geçişine GERÇEKTEN hesaplanabilen basamaklar var:

  1. HANKEL/τ PSD (Aleph)        — varış momentleri geçerli bir ölçü mü (H ⪰ 0)
  2. NEWTON moment pozitifliği  — log-konkavlık μ_k² ≥ μ_{k-1}·μ_{k+1} (hiperbolik şekil)
  3. STURM-pivot ⟺ JENSEN       — Hankel TÜM konveks yol (src→tgt) boyunca PSD kalıyor mu

D-pozitiflik / A-pozitiflik (Vandermonde) kanıt-İÇİ soyut basamaklardır; tek bir
kavram-geçişine dürüstçe haritalanmaz → UYDURULMAZ (merdivene dahil edilmez).

Merdiven KÜMÜLATİF: geçerli ölçü olmadan Jensen-hiperbolik olmak anlamsız → derinlik
alttan yukarı en yüksek KESİNTİSİZ basamak (0–3). 3 = tam kritik hatta.
"""

from __future__ import annotations

_EPS = -1e-6


def _hankel_min_eig(mu: list[float], size: int | None = None) -> float:
    """Momentlerden Hankel matrisi kurup en küçük özdeğerini döner (PSD ⟺ ≥ 0)."""
    import numpy as np

    n = min(len(mu), 8)
    if n < 2:
        return float("-inf")
    if size is None:
        size = max(n // 2, 2)
    H = np.array(
        [[mu[i + j] if i + j < n else 0.0 for j in range(size)] for i in range(size)], dtype=float
    )
    return float(np.linalg.eigvalsh(H).min())


def _newton_log_concave(mu: list[float], tol: float = 1e-6) -> bool:
    """Newton/log-konkavlık: iç indekslerde μ_k² ≥ μ_{k-1}·μ_{k+1} (hiperbolik dizi şekli)."""
    n = min(len(mu), 8)
    if n < 3:
        return True
    for k in range(1, n - 1):
        if mu[k] * mu[k] + tol < mu[k - 1] * mu[k + 1]:
            return False
    return True


def _path_hankel_min_eig(src: list[float], tgt: list[float], steps: int = 8) -> float:
    """Konveks yol (1-t)·src + t·tgt boyunca en küçük Hankel özdeğeri (Sturm pivot vekili)."""
    import numpy as np

    n = min(len(src), len(tgt), 8)
    if n < 2:
        return float("-inf")
    a = [float(src[i]) for i in range(n)]
    b = [float(tgt[i]) for i in range(n)]
    size = max(n // 2, 2)
    worst = float("inf")
    for step in range(steps + 1):
        t = step / steps
        interp = [(1 - t) * a[i] + t * b[i] for i in range(n)]
        H = np.array(
            [[interp[i + j] if i + j < n else 0.0 for j in range(size)] for i in range(size)],
            dtype=float,
        )
        worst = min(worst, float(np.linalg.eigvalsh(H).min()))
    return worst


def positivity_depth(src: list[float], tgt: list[float], *, eps: float = _EPS) -> tuple[int, dict]:
    """Bir kavram-geçişinin pozitiflik DERİNLİĞİ (0–3) + basamak raporu.

    Kümülatif: rung_k yalnız altındakiler de geçtiyse sayılır. 3 = tam kritik hatta
    (geçerli ölçü + Newton-hiperbolik + tüm yol boyunca Sturm-pozitif). 0 = sapma.
    """
    rungs = {"hankel": False, "newton": False, "sturm": False}
    try:
        if not tgt:
            return 0, rungs
        rungs["hankel"] = _hankel_min_eig(tgt) >= eps
        rungs["newton"] = _newton_log_concave(tgt)
        if src:
            rungs["sturm"] = _path_hankel_min_eig(src, tgt) >= eps
    except Exception:
        return 0, rungs
    depth = 0
    if rungs["hankel"]:
        depth = 1
        if rungs["newton"]:
            depth = 2
            if rungs["sturm"]:
                depth = 3
    return depth, rungs
