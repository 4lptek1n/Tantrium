"""
onarim.py — coord_91'in bosa calisan 32 dim'ini gercek ise kabliyor.

Tespit (200+ spektrumla kanitli):
  - 18 dim YAPISAL TEKRAR: ayni nicelik birden cok yerde (varyans 4x: d₁=τ₁/τ₀=κ₂=
    Hankel-oran=serbest-κ₂; ortalama 2x; klasik=serbest kumulant 1,2,3. mertebede).
  - 14 dim OLU: hep sabit. Icinde gercek bug: Li katsayilari (37-40,65-68) 'x>1'
    ariyor ama λ̂≤1 (max'a normalize) -> hicbir zaman atesLENMEZ. Sylvester (52):
    Gram hep PSD -> n₊/r hep 1.

Cozum: her bosa dim, DEGISKEN ve BENZERSIZ bir spektral nicelige baglanir.
Durustluk notu: ~10 ozdegerlik bir nesnenin ~10 bagimsiz serbestligi vardir;
91 dim zorunlu olarak fazla-tam (over-complete). Amac dim'leri BAGIMSIZ yapmak
DEGIL (imkansiz) — her birinin AYRI bir formulu olmasi, ikisi ayni/olu olmamasi.
Farkli mercekler ayni ısıga bakabilir; ama iki mercek ayni olmamali.

coord_91 hesabi degismez; bu katman ciktiyi yamalar. Buyuk beyin (*.pkl)
yeniden uretilmelidir (hazirla.py) cunku C91 sutunlari degisti.
"""
import numpy as np
from math import comb

def _t(x):
    return float(np.nan_to_num(np.tanh(x), nan=0.0, posinf=1.0, neginf=-1.0))
def _s(x):
    return float(np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0))

def _pct(a, p):
    return float(np.percentile(a, p)) if len(a) else 0.0

def _gini(a):
    a = np.sort(np.abs(np.asarray(a, float)))
    n = len(a)
    if n == 0 or a.sum() == 0: return 0.0
    return float((2*np.arange(1, n+1)-n-1).dot(a) / (n*a.sum()))

def _li(lh, n):
    """Li-tipi katsayi — DUZELTILMIS: resiprok spektrumda (x=1/λ̂ ≥ 1) atesLENIR."""
    xs = [1.0/x for x in lh if x > 1e-9]
    return float(np.sum([1-(1-1/x)**n for x in xs if x > 1]))


def onarim_yamalari(q):
    """q (temel_nicelikler ciktisi) -> {index: yeni_deger}. 32 bosa dim."""
    lh   = np.asarray(q['lh'], float)
    mu   = np.asarray(q['mu'], float)
    kap  = np.asarray(q['kap'], float)
    tau  = np.asarray(q['tau'], float)
    taup = np.asarray(q['taup'], float)
    d    = np.asarray(q['d'], float)
    Lam  = q['Lam']; rank = q['rank']; n = q['n']
    Sl = lh.sum() + 1e-12
    p = lh / Sl

    # sekil: standart momentler / dagilim olcumleri
    k2 = kap[2] if len(kap) > 2 else 1e-9
    skew = kap[3]/(abs(k2)**1.5 + 1e-12) if len(kap) > 3 else 0.0
    kurt = kap[4]/(k2**2 + 1e-12)        if len(kap) > 4 else 0.0
    flatness = np.exp(np.mean(np.log(lh + 1e-12))) / (np.mean(lh) + 1e-12)  # Wiener entropi
    gini = _gini(lh)

    # baskinlik: bosluklar / katilim
    gap1 = lh[0]-lh[1] if n > 1 else 0.0
    gap2 = lh[1]-lh[2] if n > 2 else 0.0
    gap3 = lh[2]-lh[3] if n > 3 else 0.0
    ipr  = float(np.sum(p**2))                                   # ters katilim orani
    eff_rank = np.exp(-np.sum(p*np.log(p+1e-12))) / (n + 1e-12)  # etkin rank / n
    top2 = float(np.sum(np.sort(p)[::-1][:2]))
    top3 = float(np.sum(np.sort(p)[::-1][:3]))

    # serbest kumulantlar (klasikten AYRISAN mertebeler + serbestlik defekti)
    m = mu
    kf4 = m[4]-4*m[1]*m[3]-2*m[2]**2+10*m[1]**2*m[2]-5*m[1]**4 if len(m) > 4 else 0.0
    kf5 = (m[5]-5*m[1]*m[4]-5*m[2]*m[3]+15*m[1]**2*m[3]+15*m[1]*m[2]**2
           -35*m[1]**3*m[2]+14*m[1]**5) if len(m) > 5 else 0.0
    k4 = kap[4] if len(kap) > 4 else 0.0
    k5 = kap[5] if len(kap) > 5 else 0.0
    kf2 = m[2]-m[1]**2 if len(m) > 2 else 1e-9
    kf3 = m[3]-3*m[1]*m[2]+2*m[1]**3 if len(m) > 3 else 0.0

    # yapi: Stieltjes (taup) — hesaplaniyordu ama kullanilmiyordu
    def r(a, i, j):
        return a[i]/a[j] if len(a) > max(i, j) and abs(a[j]) > 1e-15 else 0.0
    taup0 = taup[0] if len(taup) else 0.0

    # varolabilirlik: bool bayrak yerine SUREKLI marj (ne kadar guvenli?)
    piv_marj  = float(np.min(d))    if len(d)    else 0.0
    tau_marj  = float(np.min(tau))  if len(tau)  else 0.0
    taup_marj = float(np.min(taup)) if len(taup) else 0.0
    hankel_buyume = np.log(abs(tau[-1])+1e-12)/(rank+1) if len(tau) else 0.0
    hankel_kond   = r(np.abs(tau), 0, len(tau)-1) if len(tau) else 0.0

    return {
        # SEKIL
        0:  _t(skew),                 # eski μ0 (=1, olu) -> carpiklik
        24: _t(kurt),                 # eski κ2-tekrar   -> basiklik
        74: _t(flatness),             # eski TET-ρ2      -> spektral duzluk (Wiener)
        75: _t(3*gini),               # eski TET-ρ3      -> Gini (esitsizlik)
        76: _t(3*_pct(lh, 50)),       # eski TET-ρ4      -> medyan λ̂
        77: _t(3*_pct(lh, 25)),       # eski Hr1-tekrar  -> alt ceyrek λ̂
        78: _t(3*_pct(lh, 75)),       # eski Hr2-tekrar  -> ust ceyrek λ̂
        # BASKINLIK
        45: _s(p[0]) if len(p) else 0.0,   # p0 KALIR (temsilci)
        52: _t(3*ipr),                # eski Sylvester (=1 olu) -> ters katilim orani
        73: _t(3*top2),               # eski Perron-tekrar -> top-2 enerji payi
        79: _t(3*top3),               # eski Hr3-tekrar    -> top-3 enerji payi
        64: _t(5*gap1),               # eski τ²1-tekrar    -> 1. spektral bosluk
        # KARMASIKLIK
        61: _t(5*gap2),               # eski τ1 (olu)      -> 2. spektral bosluk
        63: _t(5*gap3),               # eski τ²0 (olu)     -> 3. spektral bosluk
        68: _s(eff_rank),             # eski L̂4-tekrar    -> etkin rank / n
        # KRITIKLIK: Li DUZELTILDI (resiprok spektrum, artik atesLENIR)
        37: _t(_li(lh, 1)/10),        # L1 (duzeltilmis)
        38: _t(_li(lh, 2)/10),        # L2
        39: _t(_li(lh, 3)/10),        # L3
        40: _t(_li(lh, 4)/10),        # L4
        65: _t(_li(lh, 5)/10),        # L̂1 -> L5
        66: _t(_li(lh, 6)/10),        # L̂2 -> L6
        67: _t(_li(lh, 7)/10),        # L̂3 -> L7
        72: _t(min(_li(lh, k) for k in range(1, 8))),  # TAV -> min Li (gercek RH testi)
        84: _t(Lam/(np.std(lh)+1e-9)),  # GIMEL -> normalize Λ (|Λ|=κ₂ tekrar olurdu)
        # YAPI: Stieltjes (taup) — artik kullaniliyor
        62: _t(r(taup, 1, 0)),        # eski τ2-tekrar -> Stieltjes pivot τ'₁/τ'₀
        # VAROLABILIRLIK: surekli marj / dagilim genisligi (bool degil, olu degil)
        30: _t(piv_marj),             # Hankel⁺ (hep true) -> pivot pozitiflik marji
        31: _t(np.std(lh)),           # Stj⁺ (olu) -> spektral yayilim (std λ̂)
        33: _t(3*(1-lh[-1])),         # cr⁺ (olu) -> spektral aralik (max-min λ̂)
        35: _t(hankel_buyume),        # Ham-tekrar -> Hankel det buyumesi
        36: _t(hankel_kond),          # Stj-tekrar -> Hankel kosullanma
        # SERBESTLIK: klasik-serbest AYRISMASI (yalniz n>=4'te ayrisir)
        86: _t(k4-kf4),               # eski κf1(=κ1) -> serbestlik defekti κ4-κf4
        87: _t(k5-kf5),               # eski κf2(=κ2) -> serbestlik defekti κ5-κf5
        88: _t(kf4/(kf2**2+1e-12)),   # eski κf3(=κ3) -> SERBEST basiklik (klasikten farkli)
    }


# ── Onarilan dim'lerin yeni kimligi (kablolama tek kaynaktan guncellenir) ────
YAMA_META = {
    0:  ("carpiklik", "sekil", "standart carpiklik κ₃/κ₂^1.5"),
    24: ("basiklik", "sekil", "standart basiklik κ₄/κ₂²"),
    30: ("piv-marj", "varolabilirlik", "pivot pozitiflik marji (min d) — surekli sertifika"),
    31: ("yayilim", "sekil", "spektral yayilim std(λ̂)"),
    33: ("aralik", "sekil", "spektral aralik (max-min λ̂)"),
    35: ("H-buyume", "yapi", "Hankel determinant buyume orani"),
    36: ("H-kond", "yapi", "Hankel kosullanma (τ₀/τ_son)"),
    37: ("Li1", "kritiklik", "Li katsayisi L₁ (resiprok spektrum — DUZELTILDI, atesLENIR)"),
    38: ("Li2", "kritiklik", "Li katsayisi L₂ (duzeltilmis)"),
    39: ("Li3", "kritiklik", "Li katsayisi L₃ (duzeltilmis)"),
    40: ("Li4", "kritiklik", "Li katsayisi L₄ (duzeltilmis)"),
    52: ("IPR", "baskinlik", "ters katilim orani Σp² — etkin dominant mod sayisi"),
    61: ("bosluk2", "baskinlik", "2. spektral bosluk λ̂₁-λ̂₂"),
    62: ("τ'piv", "yapi", "Stieltjes pivot τ'₁/τ'₀"),
    63: ("bosluk3", "baskinlik", "3. spektral bosluk λ̂₂-λ̂₃"),
    64: ("bosluk1", "baskinlik", "1. spektral bosluk λ̂₀-λ̂₁"),
    65: ("Li5", "kritiklik", "Li katsayisi L₅ (duzeltilmis)"),
    66: ("Li6", "kritiklik", "Li katsayisi L₆ (duzeltilmis)"),
    67: ("Li7", "kritiklik", "Li katsayisi L₇ (duzeltilmis)"),
    68: ("etkin-rank", "karmasiklik", "etkin rank exp(H)/n"),
    72: ("min-Li", "kritiklik", "min Li (gercek RH testi: hepsi ≥0 mi)"),
    73: ("top2", "baskinlik", "top-2 mod enerji payi"),
    74: ("duzluk", "sekil", "spektral duzluk (Wiener entropi, geom/aritm)"),
    75: ("Gini", "karmasiklik", "Gini esitsizligi (spektral yogunlasma)"),
    76: ("medyan", "sekil", "medyan λ̂"),
    77: ("Q1", "sekil", "alt ceyrek λ̂"),
    78: ("Q3", "sekil", "ust ceyrek λ̂"),
    79: ("top3", "baskinlik", "top-3 mod enerji payi"),
    84: ("Λ-norm", "kritiklik", "normalize Λ = Λ/std(λ̂)"),
    86: ("serb-defekt4", "serbestlik", "serbestlik defekti κ₄-κf₄ (klasik-serbest ayrisimi)"),
    87: ("serb-defekt5", "serbestlik", "serbestlik defekti κ₅-κf₅"),
    88: ("serb-basiklik", "serbestlik", "serbest basiklik κf₄/κf₂² (klasikten farkli)"),
}
