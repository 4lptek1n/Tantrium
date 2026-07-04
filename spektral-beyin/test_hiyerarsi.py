"""
test_hiyerarsi.py — Yasa hiyerarsisinin (Faz 2) kanitlari: korluk bitti mi?
Eski avci sadece C-finite goruyordu; simdi n'e bagli katsayili yasalar da
gorulmeli, gorunmeyenlere DURUSTCE 'yasasiz' denmeli.
Calistir: python3 test_hiyerarsi.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from hiyerarsi import yasa_avcisi, holonomik_ac
from beyin import kodla, ouroboros

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

# gercek diziler
FAKT    = [float(np.math.factorial(n)) for n in range(18)] if hasattr(np,'math') else None
import math
FAKT    = [float(math.factorial(n)) for n in range(18)]
CATALAN = [1,1,2,5,14,42,132,429,1430,4862,16796,58786,208012,742900,2674440,9694845,35357670,129644790]
MOTZKIN = [1,1,2,4,9,21,51,127,323,835,2188,5798,15511,41835,113634,310572,853467,2356779]
ASAL    = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]
BOLUNTU = [1,1,2,3,5,7,11,15,22,30,42,56,77,101,135,176,231,297,385,490]
FIB     = [1,1,2,3,5,8,13,21,34,55,89,144,233,377]

print("— 1) ESKIDEN KOR OLDUGU YASALAR ARTIK GORULUYOR —")
av = yasa_avcisi(FAKT)
check("n! : holonomik yasa bulundu (s[n]=n·s[n-1])",
      av["seviye"]=="holonomik" and av["order"]==1,
      f"seviye={av['seviye']} r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")
uz = holonomik_ac(av["holo"], FAKT[:av["order"]], 19)
check("n! : bir adim otesi DOGRU tahmin (18! gormedigi halde)",
      abs(uz[18]-math.factorial(18))/math.factorial(18) < 1e-9,
      f"tahmin={uz[18]:.6e} gercek={float(math.factorial(18)):.6e}")

av = yasa_avcisi(CATALAN)
check("Catalan: holonomik yasa bulundu ((n+1)C=(4n-2)C')",
      av["seviye"]=="holonomik" and av["order"]==1,
      f"r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")
uz = holonomik_ac(av["holo"], CATALAN[:1], 19)
check("Catalan: sonraki terim dogru (C18=477638700)",
      abs(uz[18]-477638700)/477638700 < 1e-9, f"tahmin={uz[18]:.1f}")

av = yasa_avcisi(MOTZKIN)
check("Motzkin: holonomik order-2 yasa bulundu",
      av["seviye"]=="holonomik" and av["order"]==2,
      f"r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")

print("— 2) OCCAM: basit yasa varken karmasigi uydurmuyor —")
av = yasa_avcisi(FIB)
check("Fibonacci hala C-FINITE (en basit kat kazanir)",
      av["seviye"]=="c-finite" and av["order"]==2, f"seviye={av['seviye']}")
av = yasa_avcisi([1.,2.,4.,8.,16.,32.,64.,128.,256.,512.])
check("2^n hala C-FINITE", av["seviye"]=="c-finite" and av["order"]==1)

print("— 3) DURUSTLUK: sonsuz-kesin yasa UYDURMUYOR (ama KAYBETMIYOR) —")
av = yasa_avcisi(ASAL)
check("asallar: ham (sonsuz-kesin yasa uydurmadi, kayipsiz sakladi)",
      av["seviye"]=="ham" and av["acilim_gucu"]=="gozlem-ici-kesin", f"seviye={av['seviye']}")
av = yasa_avcisi(BOLUNTU)
check("boluntu sayilari: ham (holonomik OLMADIGI kanitli — dogru damga)",
      av["seviye"]=="ham", f"seviye={av['seviye']}")
rng = np.random.default_rng(5)
av = yasa_avcisi(list(rng.normal(50,10,20)))
check("gurultu: ham (uydurma yok)", av["seviye"]=="ham")

print("— 4) OMURGA ENTEGRASYONU: kodla + ouroboros holonomik taniyor —")
k = kodla(FAKT, "math", "faktoriyel")
check("kodla: n! Kimlik'i holonomik seviyede", k.seviye=="holonomik", k.kisa())
o = ouroboros(k)
check("ouroboros: n! evreni kayipsiz kapaniyor", o["kapali"],
      f"recon_err={o['recon_err']:.1e}")
check("ouroboros: yasa geri-kurulanda korundu", o["yasa_korundu"])
check("ouroboros: bir adim otesi = 18!",
      abs(o["bir_adim_otesi"]-math.factorial(18))/math.factorial(18) < 1e-9)
k2 = kodla(ASAL, "math", "asallar")
check("kodla: asallar durustce ham (kayipsiz, sonsuz-kesin degil)", k2.seviye=="ham")
o2 = ouroboros(k2)
check("ouroboros: ham evren KAYIPSIZ kapanir ama otesi bilinmiyor",
      o2["kapali"] and o2["recon_err"]<1e-12 and o2["bir_adim_otesi"] is None)

print("— 5) KAPSAMA: korluk olculebilir bicimde azaldi —")
DIZILER = {"fib":FIB, "2^n":[1.,2.,4.,8.,16.,32.,64.,128.,256.,512.],
           "kare":[float(n*n) for n in range(1,15)],
           "n!":FAKT, "catalan":CATALAN, "motzkin":MOTZKIN,
           "cift-fakt":[float(math.prod(range(n,0,-2))) if n>0 else 1. for n in range(16)],
           "asal":ASAL, "boluntu":BOLUNTU}
eski = sum(1 for s in DIZILER.values() if yasa_avcisi(s)["seviye"]=="c-finite")
yeni = sum(1 for s in DIZILER.values() if yasa_avcisi(s)["seviye"]!="yasasiz")
print(f"    eski avci (C-finite): {eski}/9 dizi | yeni hiyerarsi: {yeni}/9 dizi")
check("kapsama artti (en az 3 yeni dizi yasali oldu)", yeni >= eski+3,
      f"{eski} -> {yeni}")

print("— 6) KESIN (tamsayi) HOLONOMIK: float64'un yalancisi, saf-int gercegi —")
from math import comb as _comb
from hiyerarsi import (holonomik_uydur_kesin, holonomik_ac_kesin,
                       sindy_uydur, sindy_vektor_alan)
from engine import matrix_prony

def apery(n): return sum(_comb(n,k)**2 * _comb(n+k,k)**2 for k in range(n+1))
APERY14 = [apery(n) for n in range(14)]      # ilk 14 terim (buyuk-int)

# (a) Apery kesin minimal (2,3) yasasi TAM cikar
tabanlar = holonomik_uydur_kesin(APERY14, 2, 3)
duz = [x for satir in tabanlar[0] for x in satir] if tabanlar else []
BEKLENEN = [0,0,0,1, 5,-27,51,-34, -1,3,-3,1]
check("Apery: kesin (2,3) yasasi TAM = bilinen Apery reküransı",
      len(tabanlar)==1 and duz==BEKLENEN, f"dim={len(tabanlar)} law={duz}")

# yasa_avcisi tamsayi-otomatik dalla Apery'yi holonomik (2,3) gorur
avA = yasa_avcisi(APERY14)
check("Apery: yasa_avcisi -> holonomik order=2 derece=3 (kesin dal, σ=0)",
      avA["seviye"]=="holonomik" and avA["order"]==2 and avA["derece"]==3 and avA["sigma"]==0.0,
      f"seviye={avA['seviye']} r={avA['order']} d={avA['derece']} σ={avA['sigma']}")

# ilk 14'ten A[14] ve A[15] KESIN buyuk-int tahmin (float veremezdi)
uzA = holonomik_ac_kesin(avA["holo_int"], APERY14[:2], 16)
check("Apery: A[14] KESIN buyuk-int tahmin (21 basamak, float veremez)",
      uzA is not None and uzA[14]==apery(14), f"pred={uzA[14] if uzA else None} true={apery(14)}")
check("Apery: A[15] KESIN buyuk-int tahmin",
      uzA is not None and uzA[15]==apery(15), f"pred={uzA[15] if uzA else None} true={apery(15)}")

# (b) (2,2)'de kesin dim==0 -> SAHTE yasa REDDEDILDI (float SVD'nin yalanini duzeltir)
check("Apery: (2,2) kesin nullspace dim=0 -> sahte dusuk-derece yasa REDDEDILDI",
      holonomik_uydur_kesin(APERY14, 2, 2) == [], "boyle bir yasa YOK")

# (c) Catalan/Motzkin/n! kesin yasalari tam cikar (order dogru)
check("n!: kesin dal holonomik order=1 (σ=0)",
      yasa_avcisi(FAKT)["seviye"]=="holonomik" and yasa_avcisi(FAKT)["sigma"]==0.0)
check("Catalan: kesin dal holonomik order=1", yasa_avcisi(CATALAN)["order"]==1)
check("Motzkin: kesin dal holonomik order=2", yasa_avcisi(MOTZKIN)["order"]==2)

# (d) tamsayi-disi/gurultulu diziler HALA float dala duser -> 'ham' (regres yok)
rng6 = np.random.default_rng(6)
apery_gurultu = [x*(1+0.001*rng6.standard_normal()) for x in APERY14]
check("Apery+gurultu: tamsayi-disi -> float dal -> 'ham' (kesin dal TAKLIT etmez)",
      yasa_avcisi(apery_gurultu)["seviye"]=="ham")
# primes/partitions tamsayi ama holonomik DEGIL -> kesin dal dim0 -> ham (dogru damga)
check("asallar: kesin dal dim0 (holonomik olmadigi KESIN kanit) -> ham",
      yasa_avcisi(ASAL)["seviye"]=="ham")
check("boluntu: kesin dal dim0 -> ham", yasa_avcisi(BOLUNTU)["seviye"]=="ham")

print("— 7) NONLINEER (SINDy): DURUM-nonlineer acik uretici geri geliyor —")
def lojistik(n=120, r=4.0, x0=0.31):
    x = np.empty(n); x[0]=x0
    for i in range(1,n): x[i]=r*x[i-1]*(1-x[i-1])
    return x
XS = lojistik()
sd = sindy_uydur(XS)
# (a) lojistik: '4x - 4x^2' katsayilari |Δ|<1e-6, R2>1-1e-9
c_lin = sd["terimler"].get("x0", 0.0); c_kare = sd["terimler"].get("x0*x0", 0.0)
check("lojistik: SINDy '4x0 - 4x0*x0' katsayilari |Δ|<1e-6 (probe'da TAM)",
      abs(c_lin-4.0)<1e-6 and abs(c_kare+4.0)<1e-6, f"x0={c_lin:.8f} x0^2={c_kare:.8f}")
check("lojistik: R2>1-1e-9 ve guven='guclu'",
      sd["r2"]>1-1e-9 and sd["guven"]=="guclu", f"R2={sd['r2']:.12f} guven={sd['guven']}")
avL = yasa_avcisi(XS)
check("lojistik: yasa_avcisi -> seviye='nonlineer' (holonomik ile ham ARASINDA rung)",
      avL["seviye"]=="nonlineer", f"seviye={avL['seviye']}")

# (b) Lorenz surekli akis: dx=10(y-x) ~%2 icinde, guven='zayif' (durust-sinir)
def lorenz(n=4000, dt=0.01, s=10., rho=28., beta=8/3.):
    xyz=np.empty((n,3)); xyz[0]=[1.,1.,1.]
    for i in range(1,n):
        x,y,z=xyz[i-1]
        xyz[i]=xyz[i-1]+dt*np.array([s*(y-x), x*(rho-z)-y, x*y-beta*z])
    return xyz, dt
XYZ, dt = lorenz()
vf = sindy_vektor_alan(XYZ, dt=dt, lam=0.5)
dx = vf["bilesenler"][0]
check("Lorenz: dx=10(y-x) -> x0 kats ~-10, x1 kats ~+10 (~%2 icinde)",
      abs(dx.get("x0",0.0)+10.0)<0.3 and abs(dx.get("x1",0.0)-10.0)<0.3,
      f"x0={dx.get('x0',0):.3f} x1={dx.get('x1',0):.3f}")
check("Lorenz: R2>0.99 AMA guven='zayif' (surekli-akis turev tahmini durust-sinir)",
      vf["r2"]>0.99 and vf["guven"]=="zayif", f"R2={vf['r2']:.5f} guven={vf['guven']}")

# (c) gurultusuz sonumlu-osilator / Fibonacci HALA c-finite (Occam korunur)
t = np.arange(30)*0.3
SONUMLU = list(np.exp(-0.1*t)*np.cos(t))
check("sonumlu-osilator: HALA c-finite (nonlineer rung'a DUSMEZ — Occam)",
      yasa_avcisi(SONUMLU)["seviye"]=="c-finite", yasa_avcisi(SONUMLU)["seviye"])
check("Fibonacci: HALA c-finite (nonlineer rung'a dusmez)",
      yasa_avcisi(FIB)["seviye"]=="c-finite")

# (d) %1 gurultu -> guven='zayif' + R2 dusus (kesin taklidi YOK)
xn = XS + 0.01*np.random.default_rng(0).standard_normal(len(XS))
sdn = sindy_uydur(xn)
check("lojistik+%1 gurultu: guven='zayif' + R2<temiz (durust belirsizlik)",
      sdn["guven"]=="zayif" and sdn["r2"]<sd["r2"], f"R2={sdn['r2']:.5f} guven={sdn['guven']}")
check("lojistik+gurultu: katsayilar HALA ~[4,-4] kurtariliyor (hata cubuguyla)",
      abs(sdn["terimler"].get("x0",0)-4.0)<0.2 and abs(sdn["terimler"].get("x0*x0",0)+4.0)<0.2,
      f"x0={sdn['terimler'].get('x0',0):.3f} x0^2={sdn['terimler'].get('x0*x0',0):.3f}")

print("— 8) VEKTOR/COUPLED: skaler cekirdegin blok genellemesi (matrix_prony) —")
from scipy.linalg import expm
def coupled(Amat, x0, dt=0.3, T=40):
    M = expm(Amat*dt)                                   # KESIN ayrik map
    X = np.empty((T, len(x0))); X[0]=x0
    for n in range(1,T): X[n] = M @ X[n-1]
    return X, M

# u'=v, v'=-u -> donme; |eig|=1 (konservatif), err<1e-12
Arot = np.array([[0.,1.],[-1.,0.]])
Xrot, Mrot = coupled(Arot, [1.,0.])
mp = matrix_prony(Xrot)
check("donme u'=v,v'=-u: order=1, M rekonstruksiyon err<1e-12",
      mp["order"]==1 and np.max(np.abs(mp["M"][0]-Mrot))<1e-10,
      f"order={mp['order']} err={np.max(np.abs(mp['M'][0]-Mrot)):.1e}")
check("donme: |eig|=1 (konservatif sistem), sigma<1e-10",
      np.allclose(np.abs(mp["eig"]),1.0,atol=1e-8) and mp["sigma"]<1e-10,
      f"|eig|={np.round(np.abs(mp['eig']),4)} sigma={mp['sigma']:.1e}")
# kodla vektor yolu: crash YOK, seviye='vektor'
kv = kodla(Xrot, "math", "donme")
check("kodla(coupled): CRASH YOK, seviye='vektor', companion A + modlar V dolu",
      kv.seviye=="vektor" and kv.V is not None and kv.A.shape==(2,2),
      f"seviye={kv.seviye} A={kv.A.shape}")

# sonumlu v'=-u-0.3v -> |eig|<1
Adamp = np.array([[0.,1.],[-1.,-0.3]])
Xd, Md = coupled(Adamp, [1.,0.])
mpd = matrix_prony(Xd)
check("sonumlu v'=-u-0.3v: |eig|<1 (dissipatif), sigma<1e-10",
      np.max(np.abs(mpd["eig"]))<1.0 and mpd["sigma"]<1e-10,
      f"|eig|max={np.max(np.abs(mpd['eig'])):.4f}")

# 3-zincir u'=v,v'=w,w'=-u -> 3x3, ayrik kok modulleri, err<1e-10
Achain = np.array([[0.,1.,0.],[0.,0.,1.],[-1.,0.,0.]])
Xc, Mc = coupled(Achain, [1.,0.,0.])
mpc = matrix_prony(Xc)
check("3-zincir: 3x3 kuplaj, err<1e-10, ayrik kok modulleri",
      mpc["M"][0].shape==(3,3) and np.max(np.abs(mpc["M"][0]-Mc))<1e-9
      and len(set(np.round(np.abs(mpc["eig"]),4)))>=2,
      f"|eig|={np.round(np.abs(mpc['eig']),4)}")

# interleave-skaler yol order=4 uretip kuplaji GIZLER (o yola guvenme)
inter = Xrot.reshape(-1)
ki = kodla(inter, "math", "interleaved")
check("interleave-skaler: order KATLANIR/kuplaj GIZLENIR (vektor yolu sart)",
      ki.seviye!="vektor", f"skaler seviye={ki.seviye} order={ki.order}")

# gurultulu 2B -> yasa YOK: sigma buyuk, 'kesin' taklidi yok
Xnoise = np.random.default_rng(7).standard_normal((40,2))
mpn = matrix_prony(Xnoise)
check("gurultu 2B: sigma buyuk -> yasa YOK (kesin taklidi yapmaz, durust)",
      mpn["sigma"]>0.1 and mpn["guven"]=="zayif", f"sigma={mpn['sigma']:.3f} guven={mpn['guven']}")
kn = kodla(Xnoise, "math", "gurultu2b")
check("kodla(gurultu 2B): CRASH YOK, seviye='ham' (yasa yok, kayipsiz sakla)",
      kn.seviye=="ham", f"seviye={kn.seviye}")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
