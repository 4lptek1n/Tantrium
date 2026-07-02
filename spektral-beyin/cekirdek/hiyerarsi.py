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
from math import comb
from domains import extract_law


# ── Kat 0: POLINOM (sonlu farklar) — en basit, en yorumlanabilir ─────────────
def polinom_uydur(s, tol=1e-9):
    """Sonlu fark tablosu: Δ^k s sabitse s, n'in k. derece polinomu.
    Doner: (derece, ilk_farklar) ya da None. Newton ileri-fark ile kesin acilir."""
    s = np.asarray(s, float)
    N = len(s)
    olcek = np.max(np.abs(s)) + 1.0
    cur = s.copy()
    firsts = [float(cur[0])]
    for k in range(1, N):
        cur = np.diff(cur)
        firsts.append(float(cur[0]))
        if len(cur) >= 2 and np.max(np.abs(cur - cur[0])) < tol * olcek:
            return k, np.array(firsts)      # Δ^k sabit -> derece k
        if len(cur) < 2:
            break
    return None


def polinom_ac(firsts, n):
    """Newton ileri-fark: s[m] = Σ_k C(m,k)·Δ^k s0. Polinom kesin acilir/genisler."""
    K = len(firsts)
    return np.array([sum(comb(m, k) * firsts[k] for k in range(K)) for m in range(n)])


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


def _sonuc(seviye, gucu, **kw):
    taban = dict(seviye=seviye, acilim_gucu=gucu, sigma=float("nan"), order=0,
                 derece=0, law=np.array([]), seed=np.array([]), holo=None,
                 poli=np.array([]))
    taban.update(kw)
    return taban


def yasa_avcisi(seq, tol_sigma=1e-9, tol_tahmin=1e-6):
    """Hiyerarsik yasa avi — KORLUK YOK: her nesne kayipsiz bir kimlige iner.

    'yasasiz' diye bir sey yoktur (Kolmogorov/Solomonoff): kimlik = veriyi
    ureten en kisa ACILABILIR programdir; en kotu ihtimalle verinin kendisidir.
    Merdiven (Occam, en basit kat kazanir); acilim_gucu = ne kadar ileri kesin:

      seviye 'polinom'   : sonlu farklar (poli)          -> acilim: sonsuz-kesin
      seviye 'c-finite'  : sabit katsayi (law+seed)       -> acilim: sonsuz-kesin
      seviye 'holonomik' : n'e bagli katsayi (holo)       -> acilim: sonsuz-kesin
      seviye 'ham'       : sikistirilamadi ama KAYIPSIZ   -> acilim: gozlem-ici-kesin
                           (veri kendi kimligidir; otesi durustce 'bilinmiyor')
    """
    s = np.asarray(seq, float)
    N = len(s)
    if N < 6:
        return _sonuc("ham", "gozlem-ici-kesin", order=N)
    hold = min(3, max(1, N // 6))
    egit, test = s[: N - hold], s[N - hold:]

    def holdout_tut(full):
        return np.max(np.abs(full[N - hold:] - test) / (np.abs(test) + 1e-12)) < tol_tahmin

    # ── Kat 0: polinom (en basit, sonlu farklar) ──
    pol = polinom_uydur(egit)
    if pol is not None:
        derece, firsts = pol
        if holdout_tut(polinom_ac(firsts, N)):
            return _sonuc("polinom", "sonsuz-kesin", order=derece, derece=derece,
                          poli=polinom_uydur(s)[1] if polinom_uydur(s) else firsts)

    # ── Kat 1: C-finite ──
    c, roots, sig, order = extract_law(egit)
    if order and np.isfinite(sig) and sig < tol_sigma and holdout_tut(_cfinite_ac(c, egit[:order], N)):
        return _sonuc("c-finite", "sonsuz-kesin", sigma=float(sig), order=int(order),
                      law=np.asarray(c), seed=np.asarray(roots))

    # ── Kat 2: holonomik (katsayilar n'e bagli) ──
    for r, d in HOLONOMIK_KATLAR:
        if len(egit) < (r + 1) * (d + 1) + r + 2:
            continue
        coef, sig = holonomik_uydur(egit, r, d)
        if sig > 1e-8:
            continue
        full = holonomik_ac(coef, s[:r], N)
        if full is not None and np.max(np.abs(full - s) / (np.abs(s) + 1e-12)) < tol_tahmin:
            return _sonuc("holonomik", "sonsuz-kesin", sigma=float(sig),
                          order=int(r), derece=int(d), holo=coef)

    # ── Kat 3: HAM — sikistirilamadi ama KAYBEDILMEDI ──
    # veri kendi kimligidir: kayipsiz saklanir, gozlem araligi kesin acilir,
    # otesi durustce 'bilinmiyor'. Bu korluk DEGIL — bilginin sinirinin durust ilani.
    return _sonuc("ham", "gozlem-ici-kesin", order=N)
