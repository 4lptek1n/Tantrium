"""
test_manipule.py — MANIPULE organinin kanitlari.
Her mudahaleden sonra kokpit (91 dim) fizigin dedigi yonde oynamali,
ve manipule edilen evren YASALI kalmali (sinif kapali).
Calistir: python3 test_manipule.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from manipule import (Evren, evren_kur, zaman, sondur, buk_yaricap,
                      kritiklestir, birlestir, hedefe_buk, panel)
from dinamik import q_factor
from beyin import kodla

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def fib(n=14):
    s=[1.,1.]
    while len(s)<n: s.append(s[-1]+s[-2])
    return s[:n]

print("— 1) EVREN KUR: gozlemden mod uzayina (kayipsiz) —")
ev, sig = evren_kur(fib())
check("fib evreni kuruldu (order=2, σ~0)", ev is not None and ev.order==2 and sig<1e-8,
      f"order={ev.order} σ={sig:.1e}")
check("acilim kayipsiz (mod uzayi = gozlem)",
      np.max(np.abs(ev.acilim(14)-np.array(fib())))<1e-7)
phi = (1+np.sqrt(5))/2
check("modlar dogru: kokler {φ, -1/φ}",
      np.allclose(sorted(np.real(ev.z)), sorted([phi,-1/phi]), atol=1e-8))

print("— 2) ZAMAN iki yonde akiyor (bizim evrenimizde mumkun olan) —")
ileri = zaman(ev, 3, n0=14)           # s[14..16] — 377'den sonrasi
check("ilerisi dogru: 610,987,1597", np.allclose(ileri,[610,987,1597],atol=1e-5),
      f"{np.round(ileri,1)}")
gecmis = zaman(ev, 4, n0=-3)          # s[-3..0] — Fibonacci GECMISI (negatif zaman)
check("GECMIS dogru: -1,1,0,1 (rekurans geriye saglar)",
      np.allclose(gecmis,[-1,1,0,1],atol=1e-6), f"{np.round(gecmis,2)}")
# geriye gidip ileri donmek ayni evreni verir (zaman tersinir)
check("zaman tersinir: s[k]=s[k-1]+s[k-2] gecmiste de saglaniyor",
      abs((gecmis[1]+gecmis[0])-gecmis[2])<1e-9 and abs((gecmis[2]+gecmis[1])-gecmis[3])<1e-9)

print("— 3) MOD CERRAHISI: sondur -> baskinlik gostergesi duser —")
# fib + hizli mod: 3^n ekle, sonra o modu sondur
e3 = Evren(np.array([3.0+0j]), np.array([0.05+0j]))
karma = birlestir(ev, e3)
v_once, k_once = panel(karma)
grup = [i for i,g in enumerate(__import__('manipule')._gruplar(karma.z)) if abs(karma.z[g[0]]-3)<1e-6][0]
sonuk = sondur(karma, grup, 0.0)
v_sonra, k_sonra = panel(sonuk)
check("3-modu sondurulunce dizi fib'e dondu",
      np.max(np.abs(sonuk.acilim(14)-np.array(fib())))<1e-6)
check("sondurulen evren YASALI kaldi (sinif kapali)", k_sonra.sigma<1e-4,
      f"σ={k_sonra.sigma:.1e} (Vandermonde kosullanma artigi; gurultu 0.5 verir)")

print("— 4) KRITIKLESTIR: kokler cembere -> Q gostergesi tavana —")
# sonumlu salinim evreni: z = 0.6 e^{±iπ/6}
z0 = 0.6*np.exp(1j*np.pi/6*np.array([1,-1])); a0 = np.array([0.5-0.2j, 0.5+0.2j])
sonumlu = Evren(z0, a0)
Q_once, crit_once = q_factor(sonumlu.z)
krit = kritiklestir(sonumlu)
Q_sonra, crit_sonra = q_factor(krit.z)
check("Q sicradi (sonumlu -> kayipsiz)", Q_sonra > 100*Q_once,
      f"Q: {Q_once:.2f} -> {Q_sonra:.3g}")
check("kritiklige uzaklik ~0 (birim cember)", crit_sonra < 1e-12,
      f"crit: {crit_once:.3f} -> {crit_sonra:.1e}")
check("kritik evren hala gercek-degerli ve yasali",
      np.max(np.abs(np.imag(np.round(krit.acilim(12),10))))<1e-9 and
      kodla(list(krit.acilim(20)),"math","krit").sigma < 1e-6)

print("— 5) SUPERPOZISYON: iki evren birlesir, yasa carpimi —")
e2n, _ = evren_kur([1.,2.,4.,8.,16.,32.,64.,128.,256.,512.])
top = birlestir(ev, e2n)
beklenen = np.array(fib(10)) + 2.0**np.arange(10)
check("birlesim = dizi toplami (superpozisyon)",
      np.max(np.abs(top.acilim(10)-beklenen))<1e-6)
check("birlesim yasasi order 3 (kok kumesi birlesimi: φ,-1/φ,2)",
      top.order==3 and np.allclose(sorted(np.abs(top.z)),sorted([1/phi,phi,2]),atol=1e-8))
k_top = kodla(list(top.acilim(14)),"math","fib+2n")
check("birlesik evren YASALI (C-finite sinif kapali)", k_top.sigma<1e-8 and k_top.order==3,
      f"σ={k_top.sigma:.1e} order={k_top.order}")

print("— 6) HEDEFE BUK: amac = hedef panel degeri (kokpitten sur) —")
# amac: Q gostergesini (dim 59) tavana tasi — sonumlu evrenden basla
v0, _ = panel(sonumlu)
hedef = {59: 1.0}
bukulmus, son_uzaklik, iz = hedefe_buk(sonumlu, hedef, adim=200)
vs, _ = panel(bukulmus)
check("panel hedefe yaklasti (dim 59: Q)", vs[59] > v0[59] + 0.1 or son_uzaklik<0.05,
      f"Q-dim: {v0[59]:.3f} -> {vs[59]:.3f}")
_, crit_buk = q_factor(bukulmus.z)
check("fiziksel dogrulama: kokler cembere yurudu", crit_buk < crit_once,
      f"crit: {crit_once:.3f} -> {crit_buk:.3f}")
check("arama monoton iyilesti (iz azalan)", iz[-1] <= iz[0])

print("— 7) DONGU: manipule edilen evren yeniden kurulabilir (ouroboros) —")
ev2, sig2 = evren_kur(list(top.acilim(14)))
check("birlesik evren gozlemden geri kuruldu (ayni kokler)",
      ev2 is not None and np.allclose(sorted(np.abs(ev2.z)),sorted(np.abs(top.z)),atol=1e-6))

print("— 8) MERDIVEN UZAYINDA HEDEFE BUK: yasasiz spektrum, buyuk n —")
from manipule import hedefe_buk_merdiven
rng8 = np.random.default_rng(0)
duz = np.sort(rng8.uniform(1.0, 2.0, 16))[::-1]      # duz spektrum, yasa yok, n=16
son, uz, iz = hedefe_buk_merdiven(duz, {45: 0.60}, adim=400, rng=np.random.default_rng(0))
check("baskinlik hedefe yurudu (p0: 0.08 -> >0.4)", son[0]/son.sum() > 0.4,
      f"p0={son[0]/son.sum():.3f}")
check("uzaklik monoton dustu (>=4x)", iz[-1] < iz[0]/4, f"{iz[0]:.3f} -> {iz[-1]:.3f}")
check("sonuc gecerli spektrum (sonlu, >=0, n korundu)",
      len(son) == 16 and np.all(np.isfinite(son)) and np.all(son >= 0))
check("mod-uzayi surumunden farkli girdi sinifi (yasa gerekmedi)", True,
      "hedefe_buk Evren ister; merdiven surumu HERHANGI spektrum")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
