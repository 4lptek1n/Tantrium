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
from math import comb, gcd
from fractions import Fraction
from itertools import combinations_with_replacement
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
    # Δ^0 (dizinin kendisi) zaten sabit mi? -> derece 0 (sabit polinom).
    # Yoksa sabit diziler k=1'de yakalanip yanlislikla 'derece 1' etiketlenir.
    if N >= 2 and np.max(np.abs(cur - cur[0])) < tol * olcek:
        return 0, np.array(firsts)
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


# ── KESIN (tamsayi) holonomik yol — float SVD'nin saf-int muadili ────────────
# Felsefe rademacher._p_int ile birebir ayni: float64 hizli-buyuyen tamsayi
# dizilerinde (Apery ~1e20) 2^53 tavani ustunde KESIN degildir; SVD sigma~0
# gorup VAR OLMAYAN dusuk-derece yasa uydurabilir. Girdi tamsayi-degerliyse
# satirlari Fraction ile kur, KESIN homojen nullspace coz -> sigma=0 sertifika
# + tam-int yasa. Gurultulu/tamsayi-disi girdi float dalinda kalir (durust
# belirsizlik). Ayni cekirdek ileride extract_law/prony_law'a da beslenebilir.

def _tamsayi_dizi(seq):
    """seq (temsil edilebilir) tamsayi-degerliyse buyuk-int KORUNARAK list[int]
    dondur; degilse None. Python int listesi / numpy int dizisi TAM saklanir
    (float'a inip 2^53 kaybi yasamaz); float girdi ancak yuvarlama tutarsa gecer."""
    try:
        arr = np.asarray(seq)
    except (ValueError, TypeError):
        return None
    if arr.ndim != 1:
        return None
    if np.issubdtype(arr.dtype, np.integer):
        return [int(x) for x in seq]
    out = []
    for x in seq:
        if isinstance(x, (int, np.integer)):
            out.append(int(x)); continue
        xf = float(x)
        if not np.isfinite(xf):
            return None
        xr = round(xf)
        if abs(xf - xr) > 1e-6 * (abs(xf) + 1.0):
            return None
        out.append(int(xr))
    return out


def _kesin_nullspace(rows):
    """rows: list[list[Fraction]]. Kesin Gauss-Jordan RREF -> homojen nullspace.
    Doner: liste; her eleman tam-int taban vektoru (LCM ile paydalar temizlenmis,
    GCD ile sadelestirilmis, ilk sifir-olmayan bilesen pozitif)."""
    if not rows:
        return []
    M = [list(r) for r in rows]
    R = len(M); C = len(M[0])
    pivots = []; pr = 0
    for pc in range(C):
        piv = None
        for i in range(pr, R):
            if M[i][pc] != 0:
                piv = i; break
        if piv is None:
            continue
        M[pr], M[piv] = M[piv], M[pr]
        inv = M[pr][pc]
        M[pr] = [x / inv for x in M[pr]]
        for i in range(R):
            if i != pr and M[i][pc] != 0:
                f = M[i][pc]
                M[i] = [a - f * b for a, b in zip(M[i], M[pr])]
        pivots.append(pc); pr += 1
        if pr == R:
            break
    pivot_set = set(pivots)
    free = [c for c in range(C) if c not in pivot_set]
    out = []
    for fcol in free:
        vec = [Fraction(0)] * C
        vec[fcol] = Fraction(1)
        for ri, pc in enumerate(pivots):
            vec[pc] = -M[ri][fcol]
        L = 1
        for x in vec:
            L = L * x.denominator // gcd(L, x.denominator)
        ints = [int(x * L) for x in vec]
        g = 0
        for x in ints:
            g = gcd(g, abs(x))
        if g > 1:
            ints = [x // g for x in ints]
        for x in ints:                                   # isaret: ilk !=0 pozitif
            if x != 0:
                if x < 0:
                    ints = [-y for y in ints]
                break
        out.append(ints)
    return out


def holonomik_uydur_kesin(seq_int, r, d):
    """Σ_k p_k(n)·s[n-k]=0 KESIN uydur (satir A[n,(k,j)] = n^j·s[n-k]).
    seq_int tam-int; float YOK. Doner: liste; her eleman (r+1)×(d+1) tam-int
    katsayi matrisi (nullspace tabani). Bos liste -> BOYLE YASA YOK (dim 0)."""
    s = [int(x) for x in seq_int]
    N = len(s)
    if N - r < (r + 1) * (d + 1):        # satir >= parametre: belirlilik (dim<=... )
        return []                         # az satir -> sahte dusuk-derece cozum riski
    rows = [[Fraction(n) ** j * s[n - k] for k in range(r + 1) for j in range(d + 1)]
            for n in range(r, N)]
    tabanlar = _kesin_nullspace(rows)
    return [[b[k * (d + 1):(k + 1) * (d + 1)] for k in range(r + 1)] for b in tabanlar]


def holonomik_ac_kesin(coef, ilk, n_top):
    """Tam-int holonomik yasa + ilk r terim -> KESIN buyuk-int extrapolasyon.
    s[n] = -Σ_{k>=1} p_k(n)·s[n-k] / p_0(n); bolme Fraction ile TAM yapilir.
    p_0(n)=0 (tekil) ya da bolunme tam-int degilse None (durust: gecersiz)."""
    r = len(coef) - 1
    d1 = len(coef[0])
    s = [int(x) for x in ilk[:r]]
    for n in range(r, n_top):
        p = [sum(coef[k][j] * (n ** j) for j in range(d1)) for k in range(r + 1)]
        if p[0] == 0:
            return None
        num = -sum(p[k] * s[n - k] for k in range(1, r + 1))
        q = Fraction(num, p[0])
        if q.denominator != 1:
            return None
        s.append(int(q))
    return s


# ── NONLINEER (SINDy/STLSQ) — c-finite'in DURUM-nonlineer genellemesi ─────────
# c-finite: x_{n+1}=lineer_harita(x).  SINDy: x_{n+1}=Σ ξ_k φ_k(x) (monom baz).
# Ayni holdout-durustluk mekanizmasi; gurultuluyse 'kesin' TAKLIT ETMEZ, R2 +
# guven bayragi verir. Lojistik x'=4x-4x^2 gibi ACIK uretici formulu geri kurar.

def _monom_kutuphane(X, derece=2):
    """Θ(X): {1, x_i, x_i x_j, ...} derece<=d (combinations_with_replacement).
    X:(m,dd) -> (Θ:(m,p), isimler)."""
    m, dd = X.shape
    sut = [np.ones(m)]; isim = ["1"]
    for deg in range(1, derece + 1):
        for combo in combinations_with_replacement(range(dd), deg):
            col = np.ones(m)
            for k in combo:
                col = col * X[:, k]
            sut.append(col)
            isim.append("*".join(f"x{k}" for k in combo))
    return np.array(sut).T, isim


def _stlsq(Theta, Y, lam=0.05, iters=12):
    """Ardisik-esikli en kucuk kareler (Brunton SINDy): seyrek katsayi."""
    Xi, *_ = np.linalg.lstsq(Theta, Y, rcond=None)
    for _ in range(iters):
        kucuk = np.abs(Xi) < lam
        Xi[kucuk] = 0.0
        for j in range(Y.shape[1]):
            buyuk = ~kucuk[:, j]
            if buyuk.sum() == 0:
                continue
            c, *_ = np.linalg.lstsq(Theta[:, buyuk], Y[:, j], rcond=None)
            Xi[buyuk, j] = c
    return Xi


def _r2(Y, P):
    Y = np.asarray(Y, float); P = np.asarray(P, float)
    ss_tot = np.sum((Y - Y.mean(axis=0)) ** 2)
    return float(1 - np.sum((Y - P) ** 2) / (ss_tot + 1e-300))


def sindy_uydur(s, derece=2, lam=0.05, hold=None, tol_kesin=1e-6):
    """1B yorunge x_{n+1}=f(x_n) icin ACIK nonlineer uretici (SINDy/STLSQ).
    Egit/holdout ayrimi + BIR-ADIM holdout (gercek girdiyle) = durustluk.
    Doner: dict(xi, isim, terimler, r2, ho_relerr, guven, nonlin_var, derece).
    guven: 'guclu' (kesin one-step) | 'zayif' (gurultu/kismi) — 'kesin' TAKLIT YOK."""
    s = np.asarray(s, float)
    N = len(s)
    if hold is None:
        hold = max(1, N // 6)
    hold = min(hold, N - 3)
    # egit uzerinde uydur
    Xtr = s[:N - hold - 1, None]; Ytr = s[1:N - hold, None]
    Th, isim = _monom_kutuphane(Xtr, derece)
    Xi_tr = _stlsq(Th, Ytr, lam)
    # bir-adim holdout: GERCEK gecmisle tahmin (kaotik uzun-ufuk degil)
    Xho = s[N - hold - 1:N - 1, None]; Yho = s[N - hold:N]
    Tho, _ = _monom_kutuphane(Xho, derece)
    pred_ho = (Tho @ Xi_tr)[:, 0]
    ho_relerr = float(np.max(np.abs(pred_ho - Yho) / (np.abs(Yho) + 1e-12)))
    # tam-fit katsayilari (rapor/acilim icin)
    Xf = s[:-1, None]; Yf = s[1:, None]
    Tf, _ = _monom_kutuphane(Xf, derece)
    Xi = _stlsq(Tf, Yf, lam)
    r2 = _r2(Yf, Tf @ Xi)
    xi = Xi[:, 0]
    nonlin_var = any(abs(xi[i]) > lam for i in range(len(isim)) if "*" in isim[i])
    terimler = {isim[i]: float(xi[i]) for i in range(len(isim)) if abs(xi[i]) > lam}
    guven = "guclu" if (r2 > 1 - 1e-9 and ho_relerr < tol_kesin) else "zayif"
    return dict(xi=xi, isim=isim, terimler=terimler, r2=r2, ho_relerr=ho_relerr,
                guven=guven, nonlin_var=nonlin_var, derece=derece)


def sindy_ac(xi, isim, x0, n):
    """Nonlineer uretici + baslangic -> yorungeyi ileri ac (harita iterasyonu).
    Kaotik sistemde uzun-ufuk hassastir; acilim 'adim-kesin' (tek adim exact)."""
    s = [float(x0)]
    for _ in range(n - 1):
        X = np.array([[s[-1]]])
        Th, _ = _monom_kutuphane(X, _derece_isimden(isim))
        s.append(float(Th[0] @ xi))
    return np.array(s[:n])


def _derece_isimden(isim):
    d = 1
    for nm in isim:
        if "*" in nm:
            d = max(d, nm.count("*") + 1)
    return d


def sindy_vektor_alan(X, dt=None, derece=2, lam=0.5):
    """Cok-degiskenli SUREKLI akis (Lorenz gibi) icin vektor alani: x'=f(x).
    Y = merkezi-fark turev (dt gerekli). DURUST-SINIR: turev tahmini kusurlu ->
    guven cogunlukla 'zayif'; mutlak fiziksel-birim degil, boyutsuz yapi + R2."""
    X = np.asarray(X, float)
    if dt is None:
        dt = 1.0
    dX = (X[2:] - X[:-2]) / (2 * dt)
    Xc = X[1:-1]
    Th, isim = _monom_kutuphane(Xc, derece)
    Xi = _stlsq(Th, dX, lam)
    r2 = _r2(dX, Th @ Xi)
    guven = "guclu" if r2 > 1 - 1e-9 else "zayif"       # akis turevi -> hemen hep 'zayif'
    bilesenler = []
    for j in range(dX.shape[1]):
        bilesenler.append({isim[i]: float(Xi[i, j])
                           for i in range(len(isim)) if abs(Xi[i, j]) > lam})
    return dict(Xi=Xi, isim=isim, bilesenler=bilesenler, r2=r2, guven=guven, derece=derece)


# holonomik taramada denenen (mertebe r, derece d) katlari — basit -> karmasik
# (2,3) EKLENDI: Apery gibi gercek minimal (2,3) yasalari taransin (kesin dalda).
HOLONOMIK_KATLAR = [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]


def _sonuc(seviye, gucu, **kw):
    taban = dict(seviye=seviye, acilim_gucu=gucu, sigma=float("nan"), order=0,
                 derece=0, law=np.array([]), seed=np.array([]), holo=None,
                 poli=np.array([]), holo_int=None, nonlin=None,
                 guven="kesin", r2=float("nan"))
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
    seq_int = _tamsayi_dizi(seq)
    if seq_int is not None:
        # KESIN DAL (tamsayi girdi): Fraction nullspace. Sahte dusuk-derece yasa
        # UYDURMAZ — (2,2) gibi katlarda dim=0 ise 'yasa yok' der (float SVD'nin
        # sigma~0 sahte raporunu duzeltir). Occam: en dusuk (r,d) kazanir.
        for r, d in HOLONOMIK_KATLAR:
            tabanlar = holonomik_uydur_kesin(seq_int, r, d)
            for coef in tabanlar:
                full = holonomik_ac_kesin(coef, seq_int[:r], N)
                if full is not None and full == list(seq_int):
                    return _sonuc("holonomik", "sonsuz-kesin", sigma=0.0,
                                  order=int(r), derece=int(d),
                                  holo=np.array(coef, float), holo_int=coef,
                                  guven="kesin")
    else:
        # FLOAT DAL (tamsayi-disi/gurultulu): SVD nullspace + holdout, durust belirsizlik.
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

    # ── Kat 2.5: NONLINEER (SINDy) — c-finite/holonomik ile ham ARASINDA ──
    # DURUM-nonlineer uretici (lojistik x'=4x-4x^2). c-finite (lineer) ve holonomik
    # (n-bagli-lineer) kacirinca burada acik nonlineer formul aranir. Occam korunur:
    # lineer/polinom yasalar zaten ustte yakalandi. DURUSTLUK: yalnizca GERCEK
    # nonlineer terim + BIR-ADIM holdout kesin tutunca terfi eder; aksi ham kalir.
    if N >= 10:
        try:
            sd = sindy_uydur(s)
            if sd["nonlin_var"] and sd["guven"] == "guclu":
                return _sonuc("nonlineer", "adim-kesin", order=len(sd["terimler"]),
                              derece=sd["derece"], nonlin=sd, guven=sd["guven"],
                              r2=sd["r2"])
        except (np.linalg.LinAlgError, ValueError):
            pass                # sadece sayisal uyum-basarisizligi -> durustce 'ham'e dus;
            #                     gercek bug'lar (TypeError vb.) maskelenmesin, yukselsin

    # ── Kat 3: HAM — sikistirilamadi ama KAYBEDILMEDI ──
    # veri kendi kimligidir: kayipsiz saklanir, gozlem araligi kesin acilir,
    # otesi durustce 'bilinmiyor'. Bu korluk DEGIL — bilginin sinirinin durust ilani.
    return _sonuc("ham", "gozlem-ici-kesin", order=N)
