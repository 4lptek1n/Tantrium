"""
test_dualite.py — EVRENSEL DUALITE MOTORU (5 paralel deney ailesiyle kalibre).
Her veri turu: kesif dogru mu, sahte-pozitif var mi, evrensellik sinifi tutuyor mu.
Calistir: python3 test_dualite.py
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from dualite import (dualite_motoru, evrensellik, rezonans_bul, beyazlat,
                     toplamsal_dual, toplamsal_kur, carpimsal_kur, HEDEF_R)

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def psi_merdiven(N):
    e = np.ones(N + 1, bool); e[:2] = False
    for i in range(2, int(N ** 0.5) + 1):
        if e[i]: e[i * i:: i] = False
    lam = np.zeros(N + 1)
    for p in np.where(e)[0]:
        m = p
        while m <= N: lam[m] = np.log(p); m *= p
    return np.cumsum(lam)[1:]        # psi(1..N), psi(1)=0 (konvansiyon)

rng = np.random.default_rng(0)

print("— 1) CARPIMSAL: zeta sifirlari asal merdiveninden (Connes) —")
d = dualite_motoru(psi_merdiven(20000), tur="carpimsal")
Z = [14.135,21.022,25.011,30.425,32.935,37.586,40.919,43.327,48.005,49.774]
sap = [min(abs(g - m) for m in d["modlar"]) for g in Z]
check("10 zeta sifiri bulundu", len(d["modlar"]) == 10, f"{len(d['modlar'])} mod")
check("max sapma < 0.02 (grid dt=0.02)", max(sap) < 0.02, f"{max(sap):.3f}")
check("spektrum turu 'nokta' (rezonanslar keskin)", d["spektrum_turu"] == "nokta")
check("evrensellik GUE (Montgomery-Odlyzko)", d["sinif"] == "GUE", f"r={d['r_ort']:.3f}")

print("— 2) TOPLAMSAL: cok-tonlu sinyal kesfi + kurulum —")
n = np.arange(1000)
iki = np.cos(2*np.pi*0.07*n) + 0.6*np.cos(2*np.pi*0.23*n)
d = dualite_motoru(iki, tur="toplamsal")
check("2 mod, tam frekans (0.07, 0.23)",
      len(d["modlar"]) == 2 and all(min(abs(f-m) for m in d["modlar"]) < 1e-3
                                    for f in (0.07, 0.23)),
      f"modlar={[round(float(m),3) for m in d['modlar']]}")
check("spektrum turu 'nokta'", d["spektrum_turu"] == "nokta")
_, R2_1 = toplamsal_kur(iki, 1); _, R2_2 = toplamsal_kur(iki, 2)
check("kurulum: K=2 mod tam kapanis (R²~1)", R2_2 > 0.999, f"R²={R2_2:.4f}")
check("kurulum: K=1 eksik (R²<0.8) — mod sayisi onemli", R2_1 < 0.8, f"R²={R2_1:.3f}")

print("— 3) EVRENSELLIK: GOE/GUE/POISSON siniflari (operator) —")
dogru = 0
for s in range(4):
    r = np.random.default_rng(s)
    A = r.standard_normal((400,400)); goe = np.linalg.eigvalsh((A+A.T)/np.sqrt(2))
    B = r.standard_normal((400,400))+1j*r.standard_normal((400,400))
    gue = np.linalg.eigvalsh((B+B.conj().T)/2)
    poi = np.sort(r.uniform(0,1,400))
    for lv, bek in [(goe,"GOE"),(gue,"GUE"),(poi,"POISSON")]:
        dogru += evrensellik(lv)[0] == bek
check("n=400: 12/12 dogru siniflama (3 sinif x 4 seed)", dogru == 12, f"{dogru}/12")
_ps, _pr, _ = evrensellik(np.sort(np.random.default_rng(9).uniform(0,1,400)))
check("Poisson ayrik (sinif=POISSON, r sonlu-ornek bandinda)",
      _ps == "POISSON" and 0.32 < _pr < 0.42, f"r={_pr:.3f}")

print("— 4) DUSMAN: sahte-pozitif YOK (kalibrasyonun kalbi) —")
rw = np.cumsum(rng.standard_normal(2000))
d = dualite_motoru(rw, tur="toplamsal")
check("rastgele yuruyus 'surekli' (SAHTE 'nokta' DEGIL)", d["spektrum_turu"] == "surekli",
      f"duzluk_w={d['duzluk']:.3f} mod={len(d['modlar'])}")
check("rastgele yuruyus 0 sahte mod", len(d["modlar"]) == 0)
onef = np.cumsum(rng.standard_normal(4000))    # kirmizi/renkli gurultu
d = dualite_motoru(onef, tur="toplamsal")
check("renkli gurultu 'surekli'", d["spektrum_turu"] == "surekli", f"duzluk={d['duzluk']:.3f}")
gur = rng.normal(50, 10, 1000)
d = dualite_motoru(gur, tur="toplamsal")
check("beyaz gurultu 'surekli' (0 sahte mod)",
      d["spektrum_turu"] == "surekli" and len(d["modlar"]) == 0)
x = 0.4; L = []
for _ in range(2000): x = 3.9*x*(1-x); L.append(x)
d = dualite_motoru(np.array(L), tur="toplamsal")
check("kaos (lojistik) 'surekli' (seyreklik kapisi)", d["spektrum_turu"] == "surekli",
      f"duzluk={d['duzluk']:.3f} mod={len(d['modlar'])}")

print("— 5) COKME KORUMASI + beyazlatma —")
check("n=1 girdi cokmuyor ('yetersiz-veri')",
      dualite_motoru(np.array([7.0]))["spektrum_turu"] == "yetersiz-veri")
check("sabit dizi cokmuyor ('surekli')",
      dualite_motoru(np.full(2000,5.0), tur="toplamsal")["spektrum_turu"] == "surekli")
f, S = toplamsal_dual(np.cumsum(rng.standard_normal(2000)))
Sw, egim = beyazlat(f, S)
check("beyazlatma: kirmizi gurultu egimi negatif (~-2)", egim < -1.0, f"egim={egim:.2f}")

print("— 6) HAM RAF: aritmetik nesneler sahte yasa uretmiyor —")
p = [1,1]                                          # boluntu (Euler pentagonal)
for nn in range(2, 60):
    tot = 0; k = 1
    while True:
        g1 = k*(3*k-1)//2; g2 = k*(3*k+1)//2
        if g1 > nn and g2 > nn: break
        sgn = (-1)**(k+1)
        if g1 <= nn: tot += sgn*p[nn-g1]
        if g2 <= nn: tot += sgn*p[nn-g2]
        k += 1
    p.append(tot)
d = dualite_motoru(np.cumsum(p), tur="carpimsal")
check("boluntu sayilari: nokta-spektrum YOK (sahte rezonans uretmiyor)",
      d["spektrum_turu"] == "surekli", f"mod={len(d['modlar'])} duzluk={d['duzluk']:.2f}")

print("— 7) GUVEN: az ornekte 'zayif', bol ornekte 'kesin' —")
_g = np.random.default_rng(7)
_M = _g.standard_normal((400,400)) + 1j*_g.standard_normal((400,400))
_gue = np.linalg.eigvalsh((_M + _M.conj().T)/2)
_sc, _rc, _gv = evrensellik(_gue)
check("n=400 GUE guven='kesin' (sinirdan 2σ uzak, 300+ r)",
      _sc == "GUE" and _gv == "kesin", f"sinif={_sc} r={_rc:.3f} guven={_gv}")
check("cok az seviye (n=12) guven='zayif' (durust belirsizlik)",
      evrensellik(np.sort(_g.uniform(0,1,12)))[2] == "zayif")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
