"""
geometri.py — 3D YAPI = ENERJI MINIMUMU (ilk prensip, dis araç/veri YOK).

Piyasa 3D yapiyi ogrenilmis modelle (AlphaFold) ya da dis docking'le alir.
Biz COZERIZ: bir molekulun sekli, kendi enerji operatorunun minimumudur.
Elle-yazilmis kat poz DEGIL — molekul kendi fizigine gore gevser (konformasyon).

Enerji (molekuler mekanik, kendi fizigimiz):
  bagli    : harmonik  ½k(r−r₀)²,  r₀ = kovalent yaricap toplami
  bagsiz   : Lennard-Jones + Coulomb  (sekil + elektrostatik)

Gevseme (gradyan inisi) -> yerel minimum = konformer. Cok baslangic -> konformer
toplulugu (esneklik). Bu gap #1 (3D yapi) + #4 (konformasyon) ILK PRENSIPTEN.

Dogrulama (analitik/bilinen, dis veri yok): iki atom LJ minimumu = 2^(1/6)σ;
bagli cift -> r₀; enerji gevsemede monoton duser; cakisma cozulur.

DURUST SINIR: klasik MM (kuantum bag acisi/orbital yok); nitel dogru, tam DFT
geometrisi degil. Ama ILKE — sekil = kendi enerjisinin minimumu — kanitli.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from de_novo import RCOV

EPS = {'C': 0.11, 'N': 0.17, 'O': 0.21, 'F': 0.06, 'S': 0.28, 'H': 0.03}
EN = {'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'S': 2.58, 'H': 2.20}
K_BAG = 8.0                                    # bag germe sertligi (model-birimi)


def _yukler(types):
    en = np.array([EN[t] for t in types], float)
    return en.mean() - en if len(en) else en   # yerel polarizasyon (kimsi_yuk ile ayni)


def mm_enerji(types, X, baglar):
    """Molekuler mekanik enerji: bagli harmonik + bagsiz LJ+Coulomb. Dusuk=kararli."""
    X = np.asarray(X, float)
    n = len(types)
    q = _yukler(types)
    bagli = set(tuple(sorted(b)) for b in baglar)
    E = 0.0
    for i, j in baglar:                        # bagli: harmonik
        r = np.linalg.norm(X[i] - X[j])
        r0 = RCOV[types[i]] + RCOV[types[j]]
        E += 0.5 * K_BAG * (r - r0) ** 2
    for i in range(n):                         # bagsiz: LJ + Coulomb
        for j in range(i + 1, n):
            if (i, j) in bagli:
                continue
            r = np.linalg.norm(X[i] - X[j]) + 1e-9
            sig = RCOV[types[i]] + RCOV[types[j]]
            eps = np.sqrt(EPS[types[i]] * EPS[types[j]])
            sr6 = (sig / r) ** 6
            E += 4 * eps * (sr6 ** 2 - sr6) + 3.0 * q[i] * q[j] / r
    return float(E)


def _gradyan(types, X, baglar, h=1e-5):
    g = np.zeros_like(X)
    for i in range(len(X)):
        for d in range(3):
            Xp = X.copy(); Xp[i, d] += h
            Xm = X.copy(); Xm[i, d] -= h
            g[i, d] = (mm_enerji(types, Xp, baglar) - mm_enerji(types, Xm, baglar)) / (2 * h)
    return g


def gevset(types, X, baglar, adim=1500, lr=0.02):
    """Gradyan inisiyle en yakin yerel minimuma gevset (konformer).
    Doner: (X_gevsemis, E_final, iz). Enerji monoton duser (adaptif adim)."""
    X = np.asarray(X, float).copy()
    E = mm_enerji(types, X, baglar); iz = [E]
    for _ in range(adim):
        g = _gradyan(types, X, baglar)
        gn = np.linalg.norm(g)
        if gn < 1e-6:
            break
        Xy = X - lr * g / (1 + gn)
        Ey = mm_enerji(types, Xy, baglar)
        if Ey < E:
            X, E = Xy, Ey
        else:
            lr *= 0.5                          # asti -> adimi kis
            if lr < 1e-5:
                break
        iz.append(E)
    return X, E, iz


def konformerler(types, X0, baglar, k=5, rng=None):
    """k farkli baslangictan gevset -> yerel-minimum toplulugu (esneklik).
    Doner: enerjiye gore sirali [(X, E)...]; benzersiz konformerler."""
    rng = rng or np.random.default_rng(0)
    bulunan = []
    for s in range(k):
        Xs = np.asarray(X0, float) + (0 if s == 0 else rng.normal(0, 0.6, np.shape(X0)))
        Xf, Ef, _ = gevset(types, Xs, baglar)
        bulunan.append((Xf, Ef))
    bulunan.sort(key=lambda t: t[1])
    return bulunan
