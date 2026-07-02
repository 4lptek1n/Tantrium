"""
hiyerarsi.py — YASA HIYERARSISI (Faz 2): korlugun bitisi.

Eski avci (Prony) tek raf goruyordu: SABIT katsayili lineer rekurans (C-finite).
Evrendeki kurallarin cogu POZISYONA BAGLI katsayili (holonomik / P-recursive):
    n!      : s[n] = n·s[n-1]
    Catalan : (n+1)·s[n] = (4n-2)·s[n-1]
    Motzkin : (n+2)·s[n] = (2n+1)·s[n-1] + 3(n-1)·s[n-2]
Genel bicim:  Σ_k p_k(n)·s[n-k] = 0,  p_k = polinom (derece d, mertebe r).
Kritik icgoru: s verildiginde bilinmeyen katsayilar LINEERDIR -> SVD ile kesin
cozulur (en kucuk tekil vektor). Cebirsel uretec fonksiyonlari da holonomik
kapsamdadir; rasyonel UF = C-finite. Yani iki raf cok sey kapsar.

Merdiven (Occam: en basit kat kazanir):
    1) C-finite   (Prony)             — en basit
    2) HOLONOMIK  (r,d taramasi)      — n'e bagli katsayilar
    3) YASASIZ    (durust damga)      — asallar, boluntu sayilari buraya

DURUSTLUK MEKANIZMASI: uydurma egitim kismindadir; son terimler SAKLANIR
(holdout) ve yasa onlari GORMEDEN tahmin etmek zorundadir. Tahmin tutmazsa
kat reddedilir. SVD kucuk artik bulur ama gelecegi bilemezse yasa degildir.
"""
import numpy as np
from domains import extract_law


def _cfinite_ac(law, ilk, n):
    o = len(law)
    s = list(np.asarray(ilk, float)[:o])
    for _ in range(n - o):
        s.append(float(np.dot(law, s[-o:][::-1])))
    return np.array(s[:n])


def holonomik_uydur(s, r, d):
    """Σ_k p_k(n)·s[n-k] = 0 uydur. Katsayilar lineer -> SVD (homojen LS).
    Doner: coef[(r+1),(d+1)], sigma (goreli artik: min/max tekil deger)."""
    s = np.asarray(s, float)
    N = len(s)
    rows = []
    for n in range(r, N):
        row = [(float(n) ** j) * s[n - k] for k in range(r + 1) for j in range(d + 1)]
        rows.append(row)
    A = np.array(rows)
    rn = np.max(np.abs(A), axis=1, keepdims=True)
    rn[rn == 0] = 1.0
    A = A / rn                                   # satir normalizasyonu (kosullanma)
    U, S, Vt = np.linalg.svd(A, full_matrices=False)
    coef = Vt[-1].reshape(r + 1, d + 1)
    sigma = float(S[-1] / (S[0] + 1e-300))
    return coef, sigma


def holonomik_ac(coef, ilk, n_top):
    """Holonomik yasa + ilk terimler -> evreni ac (geri kur + otesini uret)."""
    r = coef.shape[0] - 1
    d1 = coef.shape[1]
    s = list(np.asarray(ilk, float)[:r])
    for n in range(r, n_top):
        p = [sum(coef[k, j] * float(n) ** j for j in range(d1)) for k in range(r + 1)]
        if abs(p[0]) < 1e-14:
            return None                          # yasa bu noktada tekil
        s.append(-sum(p[k] * s[n - k] for k in range(1, r + 1)) / p[0])
    return np.array(s[:n_top])


# holonomik taramada denenen (mertebe r, derece d) katlari — basit -> karmasik
HOLONOMIK_KATLAR = [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)]


def yasa_avcisi(seq, tol_sigma=1e-9, tol_tahmin=1e-6):
    """Hiyerarsik yasa avi. Doner: dict(seviye, sigma, order, derece, ...).

    seviye 'c-finite'  : law (katsayilar) + seed (kokler)  — mod uzayi acik
    seviye 'holonomik' : holo (coef matrisi)                — n'e bagli yasa
    seviye 'yasasiz'   : hicbir kat holdout'u tahmin edemedi (DURUST damga)
    """
    s = np.asarray(seq, float)
    N = len(s)
    if N < 6:
        return dict(seviye="yasasiz", sigma=1.0, order=0, derece=0,
                    law=np.array([]), seed=np.array([]), holo=None)
    hold = min(3, max(1, N // 6))
    egit, test = s[: N - hold], s[N - hold:]

    # ── Kat 1: C-finite (Occam — en basit aciklama once) ──
    c, roots, sig, order = extract_law(egit)
    if order and np.isfinite(sig) and sig < tol_sigma:
        full = _cfinite_ac(c, egit[:order], N)
        err = np.max(np.abs(full[N - hold:] - test) / (np.abs(test) + 1e-12))
        if err < tol_tahmin:
            return dict(seviye="c-finite", sigma=float(sig), order=int(order),
                        derece=0, law=np.asarray(c), seed=np.asarray(roots), holo=None)

    # ── Kat 2: holonomik (katsayilar n'e bagli) ──
    for r, d in HOLONOMIK_KATLAR:
        if len(egit) < (r + 1) * (d + 1) + r + 2:
            continue
        coef, sig = holonomik_uydur(egit, r, d)
        if sig > 1e-8:
            continue
        full = holonomik_ac(coef, s[:r], N)      # ilk r terimden TUM diziyi kur
        if full is None:
            continue
        err = np.max(np.abs(full - s) / (np.abs(s) + 1e-12))
        if err < tol_tahmin:                     # holdout dahil hepsi tutmali
            return dict(seviye="holonomik", sigma=float(sig), order=int(r),
                        derece=int(d), law=np.array([]), seed=np.array([]), holo=coef)

    # ── Kat 3: durust damga ──
    return dict(seviye="yasasiz", sigma=float(sig) if np.isfinite(sig) else 1.0,
                order=0, derece=0, law=np.array([]), seed=np.array([]), holo=None)
