"""
Spektral Genotip Motoru — çekirdek
A -> G = AᵀA (PSD) -> spektrum λ -> yasa L (Prony) -> σ (residual)
+ coord vektörünün ELDEKİ 47 boyutu (modüler, kalan bloklar eklenebilir)

NOT: Bazı semboller (newton_res, Q, τ_ref, Λ, ρ, ∇, κ_free) kullanıcı
tanımına göre netleşecek. Standart/makul karşılıklar varsayıldı, hepsi
ayrı fonksiyonda — kullanıcı düzeltince tek yerden değişir.
"""
import numpy as np
from numpy.polynomial import polynomial as P

# ----------------------------------------------------------------------
# 1. A -> G -> spektrum
# ----------------------------------------------------------------------
def gram_spectrum(A, tol=1e-10):
    """G = AᵀA (PSD garantili). Özdeğerler reel, >=0; azalan sırada döner."""
    A = np.asarray(A, dtype=float)
    G = A.T @ A
    w = np.linalg.eigvalsh(G)          # simetrik -> reel
    w = np.clip(w, 0.0, None)          # PSD: negatif sayısal artıkları kırp
    w = np.sort(w)[::-1]
    r = int(np.sum(w > tol * (w[0] if w[0] > 0 else 1)))  # rank
    return G, w, r

# ----------------------------------------------------------------------
# 2. Yasa: Prony — bir diziyi üreten lineer rekürans
#    s[n] = c1 s[n-1] + ... + cp s[n-p]
# ----------------------------------------------------------------------
def prony_law(seq, order):
    """
    Diziye en iyi 'order' mertebeli lineer reküransı uydurur.
    Döner: katsayılar c (uzunluk=order), karakteristik kökler (seed özdeğerleri),
            residual sigma.
    """
    seq = np.asarray(seq, dtype=float)
    N = len(seq)
    if N < 2 * order:
        order = N // 2
    # Hankel sistemi: [s_{n-1..n-p}] c = s_n
    rows = N - order
    H = np.empty((rows, order))
    b = np.empty(rows)
    for i in range(rows):
        H[i, :] = seq[i:i + order][::-1]   # s_{i+order-1} ... s_i
        b[i] = seq[i + order]
    c, *_ = np.linalg.lstsq(H, b, rcond=None)
    pred = H @ c
    sigma = float(np.sqrt(np.mean((pred - b) ** 2)) / (np.std(seq) + 1e-12))
    # karakteristik kökler: x^p - c1 x^{p-1} - ... - cp = 0
    char = np.empty(order + 1)
    char[0] = 1.0
    char[1:] = -c
    roots = np.roots(char)
    return c, roots, sigma

# ----------------------------------------------------------------------
# 2b. Vektor/blok Prony — skaler prony_law'in DOGRUDAN blok genellemesi.
#     Coupled sistem / vektor-degerli trajektori X (T,d):
#         X[n] = M_1 X[n-1] + ... + M_p X[n-p]   (ayrik VAR(p) / Ho-Kalman)
#     Skaler Hankel-lstsq'in blok hali; M_k (d×d) kuplaj matrisleri +
#     companion ozdegerleri (mod buyuklukleri) doner. Dis-veri YOK.
# ----------------------------------------------------------------------
def matrix_prony(X, max_order=None, tol=1e-6):
    """Vektor-degerli diziye (T,d) blok-Hankel lstsq ile order-p matris rekuransi.

    Doner: dict(order, M[list of d×d], companion, eig, mod (|eig| azalan),
                V (companion ozvektorleri), sigma (holdout goreli-yeniden-kurma),
                cond (blok-Hankel kosul sayisi), guven).
    Occam: sigma<tol saglayan EN KUCUK p. DURUST: gurultuluyse sigma buyuk kalir,
    'kesin' taklidi yok — guven bayragi + mod buyukluklerine belirsizlik.

    DURUST-SINIR: ayrik map M ve BOYUTSUZ mod oranlari saf-matematikle TAM.
    Surekli-zaman uretec A=logm(M)/dt MUTLAK fiziksel oranlar icin dt ornekleme
    araligi kalibrasyonu ister -> bu organ onu URETMEZ (sahte cozmez)."""
    X = np.asarray(X, float)
    if X.ndim != 2:
        raise ValueError("matrix_prony (T,d) 2-B trajektori bekler")
    T, d = X.shape
    if max_order is None:
        max_order = max(1, min(5, (T - 2) // (d + 1)))
    hold = min(3, max(1, T // 6))
    Ttr = T - hold
    best = None
    for p in range(1, max_order + 1):
        if Ttr - p < d * p:                       # satir >= bilinmeyen blok
            continue
        satir = range(p, Ttr)
        Phi = np.array([np.concatenate([X[n - 1 - k] for k in range(p)]) for n in satir])
        Y = np.array([X[n] for n in satir])       # Y = Phi @ Coef
        Coef, *_ = np.linalg.lstsq(Phi, Y, rcond=None)
        Mk = [Coef[k * d:(k + 1) * d, :].T for k in range(p)]   # M_{k+1}
        # holdout: GERCEK gecmisle bir-adim yeniden kurma (durustluk)
        errs = []
        for n in range(Ttr, T):
            xhat = sum(Mk[k] @ X[n - 1 - k] for k in range(p))
            errs.append(np.linalg.norm(xhat - X[n]) / (np.linalg.norm(X[n]) + 1e-12))
        sigma = float(np.max(errs)) if errs else float("inf")
        # companion (dp×dp): ust blok-satir M_k, alt: kaydirma birimi
        C = np.zeros((d * p, d * p))
        for k in range(p):
            C[:d, k * d:(k + 1) * d] = Mk[k]
        if p > 1:
            C[d:, :d * (p - 1)] = np.eye(d * (p - 1))
        eig, V = np.linalg.eig(C)
        mod = np.sort(np.abs(eig))[::-1]
        cand = dict(order=p, M=Mk, companion=C, eig=eig, mod=mod, V=V,
                    sigma=sigma, cond=float(np.linalg.cond(Phi)),
                    guven="kesin" if sigma < tol else "zayif")
        if best is None or sigma < best["sigma"]:
            best = cand
        if sigma < tol:
            break
    return best

# ----------------------------------------------------------------------
# 3. coord — ELDEKİ 47 boyut (modüler bloklar)
# ----------------------------------------------------------------------
def _safe(x):
    return float(np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0))

def block_dalet(w):                       # 5: ilk 5 özdeğer şekli, pad 0
    v = list(w[:5]) + [0.0] * max(0, 5 - len(w))
    return [_safe(x) for x in v[:5]]

def block_newton(newton_res):             # 1
    return [_safe(np.tanh(10 * newton_res))]

def block_euler(n, r):                    # 1
    return [_safe(min((n - r) / (r + 1), 1.0))]

def block_sylvester(n_pos, r):            # 1: n_+ = pozitif özdeğer sayısı
    return [_safe(min(n_pos / r, 1.0)) if r else 0.0]

def block_bet(p, r):                      # 1: Shannon / log r
    S = -np.sum(p * np.log(p + 1e-12))
    return [_safe(S / (np.log(r) + 1e-12))]

def block_HE(mu, lmax):                   # 4: μ_k / λ_max^k, k=1..4
    return [_safe(mu[k - 1] / (lmax ** k + 1e-12)) for k in range(1, 5)]

def block_schur(lhat):                    # 1
    return [_safe(np.tanh(np.min(lhat)))]

def block_Q(Q):                           # 1
    return [_safe(np.tanh(Q))]

def block_tau1(tau1, tau_ref):            # 3: m=0,1,2
    return [_safe(np.tanh(tau1[m] / (tau_ref + 1e-12))) for m in range(3)]

def block_tau2(tau2, tau_ref):            # 2
    return [_safe(np.tanh(tau2[m] / (tau_ref ** 2 + 1e-12))) for m in range(2)]

def block_flow(grad):                     # 3
    return [_safe(np.tanh(grad[i])) for i in range(3)]

def block_tav(Lam):                       # 1
    return [_safe(np.tanh(Lam))]

def block_fixedpoint(w):                  # 1: λ_max / Σλ
    return [_safe(w[0] / (np.sum(w) + 1e-12))]

def block_tet(rho):                       # 3
    return [_safe(np.tanh(rho[j])) for j in range(3)]

def block_hankel_ratio(tau):              # 3: τ_i/τ_{i-1}, i=1..3
    return [_safe(np.tanh(tau[i] / (tau[i - 1] + 1e-12))) for i in range(1, 4)]

def block_resh(S_tot, S_alt, S_cev, r):   # 3: her biri / log r
    lr = np.log(r) + 1e-12
    return [_safe(S_tot / lr), _safe(S_alt / lr), _safe(S_cev / lr)]

def block_yod(r, n):                      # 1
    return [_safe(np.tanh(r / (n + 1)))]

def block_gimel(lhat, Lam):               # 1
    return [_safe(np.tanh(min(np.min(lhat), Lam)))]

def block_vav(n):                         # 1
    return [_safe(np.log(max(n, 1)) / 10)]

def block_voiculescu(kappa_free):         # 5: k=1..5
    return [_safe(np.tanh(kappa_free[k - 1])) for k in range(1, 6)]
