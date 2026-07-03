"""
kinetik.py — ADMET dinamigi = OPERATOR SPEKTRUMU (evren kur, zamani ilerlet, gor).

ADMET biyoloji+veri isi DEGIL (onceki degerlendirme kordu): kinetik CEKIRDEGI
—konsantrasyonun zamanla degisimi— saf ozdeger problemidir, arka beynin kalbi.

Cok-bolmeli PK: dC/dt = K·C  ->  C(t) = e^{Kt}·C₀ = Σ_i mod_i·e^{λ_i·t}
Bu, manipule.py'nin s[k]=Σ a_j·z_j^k mod-uzayinin SUREKLI hali (z=e^λ). K'nin
ozdegerleri = dispozisyon hizlari; ADMET okumalari SPEKTRUMDAN cikar:
  yari-omur = ln2/|λ|,  AUC = -K⁻¹C₀,  klerens, Cmax/Tmax.

CROSS-UZAY: ayni mod-uzayi matematigi — ister sayi dizisi, ister molekulun
elektronik modlari, ister PK bolmeleri. Toksisite: zamani ILERLET, hedef bolmede
konsantrasyon esigi asiyor mu GOR. Bu 'evren kur, amaca gore zamani sur' fiilidir.

DURUST SINIR: dinamik + tum spektral okumalar BIZIM (ilk prensip, analitik-kalibre).
Hiz sabitleri (K girdileri) fizyolojiden gelir — bir kismi kendi fizigimizden
(logP->gecirgenlik proxy), tam biyolojik esleme deneysel veri ister. Ama DINAMIGI
ve 'ne olur' kesfini tam yapariz.
"""
import numpy as np
from scipy.linalg import expm

LN2 = np.log(2.0)


def pk_operator(k_elim, gecisler=None, n_bolme=1):
    """Bolme hiz matrisi K (dC/dt=KC). k_elim: her bolmeden atilim hizi (liste/skalar).
    gecisler: [(i,j,hiz)] i->j transfer. Doner: K (n×n, kararli: ozdegerler <0)."""
    n = n_bolme
    K = np.zeros((n, n))
    ke = np.atleast_1d(np.asarray(k_elim, float))
    if len(ke) == 1:
        ke = np.full(n, ke[0])
    for i in range(n):
        K[i, i] -= ke[i]                       # atilim (kosegen)
    for (i, j, h) in (gecisler or []):
        K[i, i] -= h                           # i'den cikis
        K[j, i] += h                           # j'ye giris
    return K


def dispozisyon(K):
    """K'nin spektrumu = dispozisyon hizlari. Doner: (λ'lar, yari-omurler)."""
    w = np.linalg.eigvals(K)
    w = np.sort(w.real)                        # kararli sistemde reel<0 baskin
    yari = LN2 / np.abs(w)
    return w, yari


def profil(K, C0, t_grid):
    """Zaman profili C(t) = e^{Kt}C₀ (mod-uzayi acilimi). Her t icin bolme konsantrasyonlari."""
    C0 = np.asarray(C0, float)
    return np.array([expm(K * t) @ C0 for t in t_grid])


def admet_okumalari(K, C0, bolme=0, t_max=None, n=400):
    """Spektrumdan ADMET: yari-omur, AUC, Cmax, Tmax, klerens. bolme=gozlem (kan=0)."""
    w, yari = dispozisyon(K)
    C0 = np.asarray(C0, float)
    AUC = float((-np.linalg.inv(K) @ C0)[bolme])          # analitik ∫C dt
    if t_max is None:
        t_max = 5 * yari.max()
    tg = np.linspace(0, t_max, n)
    C = profil(K, C0, tg)[:, bolme]
    imax = int(np.argmax(C))
    return dict(yari_omur_terminal=float(yari.max()),      # en yavas mod = terminal
                dispozisyon_hizlari=w, AUC=AUC,
                Cmax=float(C[imax]), Tmax=float(tg[imax]),
                klerens=float(C0.sum() / AUC) if AUC > 0 else float("inf"))


def toksisite_zaman(K, C0, esik, bolme=0, t_max=None, n=600):
    """Zamani ILERLET, hedef bolmede konsantrasyon esigi asiyor mu GOR.
    Doner: dict(toksik, ilk_asma_zamani, esik_ustu_sure, tepe)."""
    w, yari = dispozisyon(K)
    if t_max is None:
        t_max = 6 * yari.max()
    tg = np.linspace(0, t_max, n)
    C = profil(K, C0, tg)[:, bolme]
    ustu = C > esik
    ilk = float(tg[np.argmax(ustu)]) if ustu.any() else None
    sure = float((tg[1] - tg[0]) * ustu.sum())
    return dict(toksik=bool(ustu.any()), ilk_asma_zamani=ilk,
                esik_ustu_sure=sure, tepe=float(C.max()), esik=esik)
