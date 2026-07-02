"""
dualite.py — EVRENSEL DUALITE MOTORU: her nesnenin iki yuzu.

asal_spektrum.py'nin genellemesi: Connes/iz-formulu fikri TUM veri turlerine.
Her nesnenin dogrudan yuzu (veri) ve dual yuzu (gizli spektrum) vardir;
motor iki yonde calisir: kesif (veri->spektrum) ve kurulum (spektrum->veri).

Dualite turleri (dogru donusum veri turune gore secilir):
  'carpimsal' : log-Fourier (Mellin) — aritmetik/merdiven yapilar
                Φ(t) = -Σ w(n)·cos(t·ln n),  w = sicramalar/√n  (asallar: Λ(n)/√n)
                KONVANSIYON: merdiven s(1..N) olarak verilir (s[0]=s(1));
                sicramalar Λ(n) ile ln(n) hizali olmalidir (off-by-one bozar).
  'toplamsal' : Fourier — zaman serileri, periyodik/dalga yapilar
  'operator'  : ozdeger spektrumu — matrisler (evrensellik dogrudan)

KALIBRASYON (5 paralel deney ailesi, olculmus):
- zeta kesfi: 10/10 sifir, max sapma 0.015 (dt=0.02 grid altinda)
- beyazlatilmis duzluk sart: rastgele yuruyus/1-f gurultu ham duzlukte 'nokta'
  gorunur (0.002-0.19!) — guc-yasasi zarfi kirilinca 0.50-0.56 (dogru 'surekli');
  saf sinus 0.0 kalir. Ek gard: lowfrac (modlarin en dusuk %10 banda yigilmasi).
- kaos (lojistik): ham duzluk 0.33 ile beyaz gurultuden (0.52) DUZ — tek metrik
  yetmez; seyreklik kapisi sart (anlamli tepe sayisi <= 15).
- gurultu tepe SNR'i (toplamsal, 20 seed): 99p=12.9, max=13.7 -> esik 15
  (gercek tonlarin SNR'i ~1e9, asla elemez).
- evrensellik sinirlari (50 seed, n=400): POISSON < 0.455 <= GOE < 0.560 <= GUE;
  n<=50'de siniflar ortusur -> guven='zayif' raporlanir (kesin etiket yalani yok).
"""
import numpy as np


# ── DUAL DONUSUMLER ──────────────────────────────────────────────────────────
def carpimsal_dual(merdiven, t_min=5.0, t_max=60.0, dt=0.02, parca=256):
    """Merdiven s(1..N) -> sicramalar w=Δs/√n -> log-Fourier guc.
    Asallarda w = Λ(n)/√n olur (ψ merdiveninin sicramalari) — ayni formul.
    Bellek icin t-parcalanmis (N=1e5'te ~GB'lik dis carpim yerine bloklar)."""
    s = np.asarray(merdiven, float)
    if len(s) < 3:
        raise ValueError("carpimsal dual icin en az 3 basamak gerekli")
    w = np.diff(s)
    n = np.arange(2, len(s) + 1, dtype=float)
    w = w / np.sqrt(n)
    w = w - w.mean()                          # DC/trend kir (sahte t→0 tepesi)
    lnn = np.log(n)
    w = w * (1.0 - lnn / lnn.max())           # Bartlett: kenar sizintisi bastir
    t = np.arange(t_min, t_max, dt)
    S = np.empty(len(t))
    for i in range(0, len(t), parca):
        tb = t[i:i + parca]
        S[i:i + parca] = -(w[None, :] * np.cos(tb[:, None] * lnn[None, :])).sum(1)
    return t, S


def toplamsal_dual(seq):
    """Zaman serisi -> Fourier guc spektrumu (DC'siz, detrend'li)."""
    s = np.asarray(seq, float)
    if len(s) < 8:
        raise ValueError("toplamsal dual icin en az 8 ornek gerekli")
    s = s - s.mean()
    x = np.arange(len(s), dtype=float)
    s = s - np.polyval(np.polyfit(x, s, 1), x)   # lineer trend kir
    F = np.fft.rfft(s)
    f = np.fft.rfftfreq(len(s))
    return f[1:], np.abs(F[1:]) ** 2             # DC atla


def beyazlat(f, S):
    """Guc-yasasi zarfini kir: S_w = S / f^egim. Kirmizi/renkli gurultunun
    'az frekansta guc yigilmasi'ni duzlestirir; gercek cizgiler sivri kalir.
    (Dusman deneyiyle dogrulandi: rastgele yuruyus 0.006->0.52, sinus 0.0 kalir.)"""
    m = S > 0
    if m.sum() < 4:
        return S.copy(), 0.0
    egim = float(np.polyfit(np.log(f[m]), np.log(S[m] + 1e-300), 1)[0])
    return S / np.power(f, egim), egim


# ── KESIF: rezonanslar + spektrum turu ───────────────────────────────────────
def rezonans_bul(eksen, S, kac=10, snr_esik=4.0):
    """Dual yuzdeki ANLAMLI tepeler (SNR = (tepe−medyan)/MAD_std).
    Toplamsal gurultu kalibrasyonu: sahte tepe SNR 99p=12.9 -> esik 15 kullan."""
    ic = (S[1:-1] > S[:-2]) & (S[1:-1] > S[2:])
    ix = np.where(ic)[0] + 1
    if len(ix) == 0:
        return np.array([]), np.array([])
    taban = np.median(np.abs(S - np.median(S))) * 1.4826 + 1e-30
    snr = (S[ix] - np.median(S)) / taban
    anlamli = ix[snr > snr_esik]
    if len(anlamli) == 0:
        return np.array([]), np.array([])
    sirali = np.sort(anlamli[np.argsort(S[anlamli])[::-1][:kac]])
    return eksen[sirali], S[sirali]


def spektral_duzluk(S):
    """Wiener entropi: geometrik/aritmetik ortalama, [0,1]."""
    P = np.clip(S - S.min(), 0, None) + 1e-30
    P = P / P.sum()
    return float(np.exp(np.mean(np.log(P))) / np.mean(P))


# ── EVRENSELLIK SINIFI (ampirik sinirlar + guven) ────────────────────────────
HEDEF_R = {"POISSON": 0.386, "GOE": 0.5307, "GUE": 0.5996}
SINIR_PG, SINIR_GG = 0.455, 0.560     # olculmus karar sinirlari (50 seed, n=400)

def evrensellik(seviyeler, kenar_kirp=0.2):
    """Seviye listesi -> (sinif, ⟨r⟩, guven). Unfolding'siz r-istatistigi.
    guven='zayif': ornek az ya da sinira 2σ'dan yakin — kesin etiket yalani yok.
    (Kalibrasyon: n=400 kirp=0.2 -> 30/30; n<=50 -> siniflar ortusur.)"""
    lv = np.sort(np.asarray(seviyeler, float))
    k = int(len(lv) * kenar_kirp)
    if k > 0:
        lv = lv[k:-k]
    d = np.diff(lv)
    d = d[d > 1e-15]
    if len(d) < 3:
        return "BELIRSIZ", float("nan"), "zayif"
    r = np.minimum(d[:-1], d[1:]) / np.maximum(d[:-1], d[1:])
    r_ort = float(np.mean(r))
    sinif = "POISSON" if r_ort < SINIR_PG else ("GOE" if r_ort < SINIR_GG else "GUE")
    sigma = 0.275 / np.sqrt(len(r))           # tek-r std ~0.275 (olculdu)
    sinira_uzaklik = min(abs(r_ort - SINIR_PG), abs(r_ort - SINIR_GG))
    guven = "kesin" if (len(r) >= 10 and sinira_uzaklik > 2 * sigma) else "zayif"
    return sinif, r_ort, guven


# ── KURULUM: dualden geri kur (iki yonun kapanisi) ───────────────────────────
def toplamsal_kur(seq, kac_mod):
    """En guclu K Fourier modundan sinyali geri kur; (geri, R²) doner."""
    s = np.asarray(seq, float)
    mu = s.mean()
    F = np.fft.rfft(s - mu)
    P = np.abs(F) ** 2
    P[0] = 0
    ix = np.argsort(P)[::-1][:kac_mod]
    Fk = np.zeros_like(F)
    Fk[ix] = F[ix]
    geri = np.fft.irfft(Fk, n=len(s)) + mu
    ss_res = np.sum((s - geri) ** 2)
    ss_tot = np.sum((s - s.mean()) ** 2) + 1e-30
    return geri, float(1.0 - ss_res / ss_tot)


def carpimsal_kur(modlar, x_max):
    """Kritik modlardan merdiveni kur (acik formul bicimi; asal ornegi:
    asal_spektrum.psi_spektral). Modlar kritik cizgide varsayilir (Re=1/2)."""
    xs = np.arange(2, x_max + 1, dtype=float)
    g = np.asarray(modlar, float)
    ra, rg = np.sqrt(0.25 + g ** 2), np.arctan2(g, 0.5)
    S = xs - np.array([(2 * np.sqrt(x) * np.cos(g * np.log(x) - rg) / ra).sum()
                       for x in xs])
    return xs, S


# ── TEK KAPI: her veri turu icin otomatik dualite ────────────────────────────
def dualite_motoru(seq, tur="auto", kac=10):
    """Evrensel giris: nesne -> dual kimlik.
    Doner: dict(tur, modlar, spektrum_turu, duzluk, sinif, r_ort, guven, egim).

    Karar mantigi (kalibrasyonla kilitli):
      toplamsal: BEYAZLATILMIS duzluk < 0.35  VE  1<=mod<=15 (SNR>15, beyaz yuzde)
                 VE lowfrac<0.6 (modlar dusuk banda yigilmamis)  -> nokta
                 (rastgele yuruyus / 1-f / kaos / beyaz gurultu -> surekli)
      carpimsal: SNR>4 anlamli rezonans var -> nokta (zeta 10/10; boluntu/trend 0)
      sinif: nokta+mod>=4 -> evrensellik; nokta+mod<4 -> 'NOKTA-AZ-MOD';
             surekli -> 'SUREKLI-SPEKTRUM' (bu da kimliktir, kusur degil).
    """
    s = np.asarray(seq, float)
    if len(s) < 8:
        return dict(tur="belirsiz", modlar=np.array([]), spektrum_turu="yetersiz-veri",
                    duzluk=float("nan"), sinif="BELIRSIZ", r_ort=float("nan"),
                    guven="zayif", egim=float("nan"))
    if tur == "auto":
        artan = bool(np.all(np.diff(s) >= -1e-12) and s[-1] > s[0])
        tur = "carpimsal" if artan else "toplamsal"

    if tur == "carpimsal":
        eksen, S = carpimsal_dual(s)
        duzluk = spektral_duzluk(S)
        egim = float("nan")
        modlar, _ = rezonans_bul(eksen, S, kac=kac, snr_esik=4.0)
        st = "nokta" if len(modlar) >= 1 else "surekli"
    else:
        eksen, S = toplamsal_dual(s)
        Sw, egim = beyazlat(eksen, S)
        duzluk = spektral_duzluk(Sw)             # beyazlatilmis duzluk (dusman-onayli)
        modlar, _ = rezonans_bul(eksen, Sw, kac=max(kac, 16), snr_esik=15.0)
        lowfrac = (float(np.mean(modlar < eksen[0] + 0.1 * (eksen[-1] - eksen[0])))
                   if len(modlar) else 0.0)
        st = "nokta" if (duzluk < 0.35 and 1 <= len(modlar) <= 15
                         and lowfrac < 0.6) else "surekli"
        modlar = modlar[:kac]

    if st == "nokta" and len(modlar) >= 4:
        sinif, r_ort, guven = evrensellik(modlar, kenar_kirp=0.0)
    elif st == "nokta":
        sinif, r_ort, guven = "NOKTA-AZ-MOD", float("nan"), "kesin"
    else:
        sinif, r_ort, guven = "SUREKLI-SPEKTRUM", float("nan"), "kesin"
    return dict(tur=tur, modlar=modlar, spektrum_turu=st, duzluk=duzluk,
                sinif=sinif, r_ort=r_ort, guven=guven, egim=egim)
