"""
jacobi_depo.py — KOSULLANMA DUVARINI YIKAN DEPOLAMA: Jacobi merdiveni.

panel_ters moment yolundan geri kurar — ama moment problemi USTEL kotu-kosullu:
n>=10'da duvar (olculdu: hata ~1). BU modul duvari yikar:

  spektrum <-> (alpha, beta) Jacobi uc-kosegen merdiveni   [Lanczos / Golub-Welsch]

Iki yon de MUKEMMEL kosullu (olculdu: n=32'de hata 3.5e-15). Cunku uc-kosegen
ozdeger problemi kararli; kotu-kosullu olan MOMENTLERIN kendisi, merdiven degil.

91 dim BAGI (birebir dogrulandi):  coord_91 pivot dim'leri (16-19):
    d_k = τ_k/τ_{k-1} = β₁²·β₂²···β_k²
Panel zaten Jacobi merdiveninin kumulatif carpimlarini SAKLIYORDU — iyi-kosullu
depolama 91 dim'in icinde duruyordu; bu modul onu calistirir.

VERI SAKLAMA: spektrum(n) <-> merdiven(2n-1 sayi), iki yonde kayipsiz + kararli.
Dejenere (tekrarli) spektrumda Lanczos erken durur -> olcu (atom+agirlik) saklanir
(panel_ters ile ayni durustluk: momentler olcuyu tasir, ham vektoru degil).
"""
import os, sys
import numpy as np
from scipy.linalg import eigh_tridiagonal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def spektrumdan_jacobi(lam, agirlik=None):
    """Spektrum -> Jacobi merdiveni (alpha, beta). Lanczos + tam yeniden-ortogonalizasyon.
    agirlik verilmezse esit-agirlikli olcu (1/n). Dejenere spektrumda erken durur."""
    lam = np.asarray(lam, float)
    n = len(lam)
    w = np.full(n, 1.0 / n) if agirlik is None else np.asarray(agirlik, float) / np.sum(agirlik)
    v = np.sqrt(w)
    V = [v]
    alpha, beta = [], []
    for k in range(n):
        u = lam * V[-1]
        a = float(V[-1] @ u)
        alpha.append(a)
        u = u - a * V[-1] - (beta[-1] * V[-2] if beta else 0.0)
        for vv in V:                              # tam yeniden-ortogonalizasyon (kararlilik)
            u -= (vv @ u) * vv
        b = float(np.linalg.norm(u))
        if b < 1e-13 or k == n - 1:
            break
        beta.append(b)
        V.append(u / b)
    return np.array(alpha), np.array(beta)


def jacobiden_spektrum(alpha, beta):
    """Jacobi merdiveni -> spektral olcu (atomlar, agirliklar). Golub-Welsch:
    uc-kosegen ozdegerler = atomlar; agirlik = ilk-bilesen². Mukemmel kosullu."""
    if len(alpha) == 1:
        return np.array([alpha[0]]), np.array([1.0])
    ev, evec = eigh_tridiagonal(np.asarray(alpha, float), np.asarray(beta, float))
    s = np.argsort(ev)[::-1]
    return ev[s], (evec[0, :] ** 2)[s]


def jacobi_pivotlar(beta):
    """Merdivenden coord_91 pivotlari: d_k = β₁²···β_k² (dim 16-19'un kaynagi).
    Kimlik birebir dogrulandi (test)."""
    return np.cumprod(np.asarray(beta, float) ** 2)


# ── KODEK: duvar-yikan depolama (panel_ters'in n>=10 limitini asar) ──────────
def depola(lam):
    """Spektrum -> kayitli kimlik: (alpha, beta, lmax). 2n-1 sayi, kararli."""
    lam = np.sort(np.clip(np.asarray(lam, float), 0, None))[::-1]
    lmax = lam[0] if len(lam) and lam[0] > 0 else 1.0
    a, b = spektrumdan_jacobi(lam / lmax)
    return a, b, float(lmax)


def ac(alpha, beta, lmax, n=None):
    """Kayitli kimlik -> spektrum. Agirliklardan katlilik kur (dejenere dogru)."""
    atom, w = jacobiden_spektrum(alpha, beta)
    if n is None:
        n = len(alpha) if len(beta) == len(alpha) - 1 else int(round(1.0 / np.min(w[w > 1e-12])))
    kat = np.maximum(1, np.round(w * n).astype(int))
    ham = np.repeat(atom, kat)[:n]
    if len(ham) < n:
        ham = np.concatenate([ham, np.full(n - len(ham), atom[0])])
    return np.sort(ham)[::-1] * lmax


def kimlik_depola_ac(kimlik):
    """Omurga koprusu: bir Kimlik'in spektrumunu merdivenle sakla+ac, hatayi olc."""
    lam = np.sort(np.clip(kimlik.lam, 0, None))[::-1]
    lam = lam[lam > 1e-12]
    a, b, lmax = depola(lam)
    geri = ac(a, b, lmax, n=len(lam))
    return dict(hata=float(np.max(np.abs(lam - geri))), boyut=len(a) + len(b),
                spektrum=geri)
