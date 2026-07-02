"""
panel_ters.py — coord_91 TERSINE CEVRILEBILIR: panelden spektruma geri.

91 dim matematiginin ICINDEN cikan potansiyel (dis kaynak degil):
coord_91'in G1 blogu momentlerdir  μ_k = mean(λ̂^k) = (1/n)Σ λ̂_i^k.
Ayrik spektrum (n atom) 2n momentle TAM belirlenir (klasik moment problemi).
  -> spektrum, panelin kendi momentlerinden Hankel-kalemle GERI kurulur (1e-12).

Bu, uc seyi ayni anda soyler:
  VERI SAKLAMA : spektrum = 2n moment (kayipsiz kod). coord_91 depolama, süs degil.
  UZAY         : gecerli momentler bir KONI olusturur (Hankel-PSD = moment problemi).
                 coord_91'in 'varolabilirlik' dim'leri (30-36) tam bu koninin sertifikasi.
  UZAY MANIPULE: hedef moment ver -> en yakin GECERLI spektrumu kur (panel-duzeyi insa).

Iliski: manipule.py mod-uzayinda (kok+genlik) buker; bu panel-uzayinda (moment) kurar.
Ikisi ayni evrenin iki koordinati — biri zaman/yasa, digeri spektrum/moment.
"""
import numpy as np
from scipy.linalg import eig


# ── momentler <-> spektrum ───────────────────────────────────────────────────
def spektrum_momentleri(lam, kac_moment=None):
    """Spektrum -> normalize momentler μ_0..μ_{K}. (coord_91 G1 blogunun kaynagi.)"""
    lam = np.sort(np.clip(np.asarray(lam, float), 0, None))[::-1]
    lmax = lam[0] if lam[0] > 0 else 1.0
    lh = lam / lmax
    n = len(lh)
    K = kac_moment if kac_moment is not None else 2 * n + 1
    return np.array([np.mean(lh ** k) for k in range(K + 1)]), lmax


def spektral_olcu(mu, n):
    """Momentlerden spektral OLCUYU cikar: (atomlar, agirliklar).
    μ_k = Σ w_i x_i^k. (H1,H0) genellestirilmis ozdeger = atom x_i; agirlik w_i
    Vandermonde ile. Tekrarli ozdegerlerde n_atom < uzunluk (ozdes atomlar birlesir)."""
    H0 = np.array([[mu[i + j] for j in range(n)] for i in range(n)])
    H1 = np.array([[mu[i + j + 1] for j in range(n)] for i in range(n)])
    x = np.real(eig(H1, H0, right=False))
    x = np.clip(x[np.isfinite(x)], 0, None)
    V = np.array([[xi ** k for xi in x] for k in range(len(x))])   # Vandermonde
    w, *_ = np.linalg.lstsq(V, np.array(mu[:len(x)]), rcond=None)
    s = np.argsort(x)[::-1]
    return x[s], np.clip(w[s], 0, None)


def spektrum_geri(mu, n, lmax=1.0):
    """Momentlerden (μ_0..μ_{2n-1}) spektrumu GERI kur — Hankel kalem.
    Atomlari agirliklarina (×toplam) gore tekrarlayarak ham spektrumu kurar.
    Doner: azalan spektrum (lmax ile olceklenmis). Ayrik/dejenere durumu da dogru."""
    if len(mu) < 2 * n:
        raise ValueError(f"{n} atom icin en az {2*n} moment gerekli")
    x, w = spektral_olcu(mu, n)
    # agirlik*n ~ katlilik: μ_0 = Σw = n_toplam/n_toplam=1 (normalize); katlilik=round(w*n)
    kat = np.maximum(1, np.round(w * n).astype(int))
    ham = np.repeat(x, kat)[:n]
    if len(ham) < n:                              # yuvarlama eksigi: en buyugu tamamla
        ham = np.concatenate([ham, np.full(n - len(ham), x[0])])
    return np.sort(ham)[::-1] * lmax


# ── gecerlilik: moment koni (varolabilirlik dim'lerinin surekli hali) ────────
def moment_gecerli(mu, n):
    """Bu momentler GERCEK bir pozitif spektrumdan gelebilir mi?
    Hamburger/Stieltjes: Hankel matrisi PSD olmali. Doner: (gecerli, en_kucuk_ozdeger).
    coord_91 dim 30-36 bunun boolean hali; burada surekli marj."""
    H = np.array([[mu[i + j] for j in range(n + 1)] for i in range(n + 1)])
    ev = np.linalg.eigvalsh(H)
    return bool(ev[0] > -1e-10), float(ev[0])


# ── uzay manipule: hedef momentten spektrum insa et ──────────────────────────
def momentten_kur(hedef_mu, n, lmax=1.0):
    """Hedef momentlerden en yakin GECERLI n-atomlu spektrumu kur.
    Momentler gecersizse (koni disinda) Hankel'i en yakin PSD'ye izdusur, sonra
    geri kur. Panel-uzayinda evren insasi. Doner: (spektrum, gecerli_miydi)."""
    gecerli, mn = moment_gecerli(hedef_mu, n)
    mu = np.array(hedef_mu, float)
    if not gecerli:
        # Hankel'i PSD koniye izdusur (negatif ozdegerleri kirp), momentleri geri oku
        H = np.array([[mu[i + j] for j in range(n + 1)] for i in range(n + 1)])
        ev, V = np.linalg.eigh(H)
        Hp = (V * np.clip(ev, 0, None)) @ V.T
        # anti-kosegen ortalamasi -> duzeltilmis moment dizisi
        for k in range(2 * n + 1):
            idx = [(i, k - i) for i in range(n + 1) if 0 <= k - i <= n]
            mu[k] = np.mean([Hp[i, j] for i, j in idx])
    return spektrum_geri(mu, n, lmax), gecerli


# ── omurga koprusu: bir Kimlik'in panelinden spektrumu geri kur ──────────────
def panelden_spektrum(kimlik, n=None):
    """Bir Kimlik'in SAKLANAN paneli/spektrumundan spektrumu geri kur — kayipsiz mi?
    coord_91'in tersine cevrilebilirligini omurga uzerinde gosterir."""
    lam = np.sort(np.clip(kimlik.lam, 0, None))[::-1]
    lam = lam[lam > 1e-12]
    if n is None:
        n = len(lam)
    mu, lmax = spektrum_momentleri(lam, kac_moment=2 * n + 1)
    geri = spektrum_geri(mu, n, lmax)
    hata = float(np.max(np.abs(np.sort(lam)[::-1][:n] - geri[:n]))) if len(geri) >= n else float("inf")
    return dict(spektrum=geri, kaynak=lam, recon_hata=hata, moment_sayisi=len(mu))
