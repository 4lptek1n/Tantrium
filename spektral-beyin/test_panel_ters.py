"""
test_panel_ters.py — coord_91 TERSINE CEVRILEBILIR mi? (91 dim'in ICINDEN potansiyel)
Panelin momentleri (G1 blogu) spektrumu birebir verir; gecerlilik koni sertifikasi;
hedef momentten evren insasi. Veri saklama + uzay + uzay manipule — 91 dim matematigi.
Calistir: python3 test_panel_ters.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from panel_ters import (spektrum_momentleri, spektrum_geri, spektral_olcu,
                        moment_gecerli, momentten_kur, panelden_spektrum)
from beyin import kodla

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) VERI SAKLAMA: panel momentleri spektrumu BIREBIR verir —")
for lam in [np.array([5.,3.2,2.1,1.,0.4]),
            np.array([10.,9.,8.,2.,1.,0.5,0.1])]:      # ayrik (generic) spektrumlar
    mu, lmax = spektrum_momentleri(lam)
    geri = spektrum_geri(mu, len(lam), lmax)
    gercek = np.sort(lam)[::-1]
    check(f"n={len(lam)}: spektrum momentlerden geri (hata<1e-5)",
          len(geri) == len(lam) and np.max(np.abs(gercek - geri)) < 1e-5,
          f"hata={np.max(np.abs(gercek-geri)):.1e}")
# dejenere: momentler OLCUYU (atom+agirlik) saklar, ham vektoru degil
lam = np.array([1.,1.,1.,0.5,0.5]) * 4.0            # 2 farkli atom, agirlik 3/5,2/5
mu, lmax = spektrum_momentleri(lam)
atom, agir = spektral_olcu(mu, 2)
check("dejenere spektrum: 2 farkli atom {4, 2} dogru (olcu-geri-kurma)",
      np.allclose(np.sort(atom*lmax)[::-1], [4.,2.], atol=1e-6),
      f"atomlar={np.round(atom*lmax,3)}")
check("agirliklar dogru (3/5, 2/5 katlilik)",
      np.allclose(np.sort(agir)[::-1], [0.6, 0.4], atol=1e-3), f"agirlik={np.round(agir,3)}")

print("— 2) UZAY: gecerli moment KONISI (varolabilirlik sertifikasi surekli) —")
lam = np.array([4.,2.,1.,0.3])
mu, _ = spektrum_momentleri(lam)
g, mn = moment_gecerli(mu, len(lam))
check("gercek spektrumun momentleri GECERLI (Hankel-PSD)", g, f"min_ozdeger={mn:.2e}")
# gecersiz moment: μ_2 < μ_1^2 olamaz (varyans negatif) -> koni disi
sahte = mu.copy(); sahte[2] = mu[1]**2 - 0.1
g2, mn2 = moment_gecerli(sahte, len(lam))
check("sahte moment (varyans<0) GECERSIZ (koni disi tespit)", not g2, f"min={mn2:.2e}")

print("— 3) UZAY MANIPULE: hedef momentten GECERLI spektrum insa —")
# gecersiz hedef ver -> en yakin gecerli spektruma izdusur
spek, gecerliydi = momentten_kur(sahte, len(lam))
check("gecersiz hedef -> gecerli spektruma izdusuruldu",
      not gecerliydi and np.all(spek >= -1e-9) and len(spek) == len(lam),
      f"spektrum={np.round(spek,3)}")
mu2, _ = spektrum_momentleri(spek)
g3, _ = moment_gecerli(mu2, len(lam))
check("insa edilen spektrum artik GECERLI moment koni icinde", g3)

print("— 4) OMURGA: bir Kimlik'in panelinden spektrum geri kuruluyor —")
k = kodla([1.,1.,2.,3.,5.,8.,13.,21.,34.,55.], "math", "fib")
r = panelden_spektrum(k)
check("Fibonacci Kimlik: panel -> spektrum kayipsiz (hata<1e-4)",
      r["recon_hata"] < 1e-4, f"hata={r['recon_hata']:.1e} moment={r['moment_sayisi']}")
km = kodla((['C','C','N','O','C'],
            np.array([[0,0,0],[1.5,0,0],[2.2,1.2,0],[1.5,2.4,.3],[0,1.4,.5]],float)),
           "molecule", "mol")
rm = panelden_spektrum(km)
check("Molekul Kimlik: panel -> spektrum kayipsiz (domain fark etmez)",
      rm["recon_hata"] < 1e-3, f"hata={rm['recon_hata']:.1e}")

print("— 5) KODEK + DURUST SINIR: moment-problemi kosullanmasi —")
rng = np.random.default_rng(0)
def kodek_hata(n):
    lam = np.sort(rng.uniform(0.5, 8, n))[::-1]
    mu, lmax = spektrum_momentleri(lam)
    geri = spektrum_geri(mu[:2*n], n, lmax)
    return np.max(np.abs(np.sort(lam)[::-1] - geri)) if len(geri) == n else 9.9
check("n<=6: kayipsiz kodek (hata<1e-4)", kodek_hata(6) < 1e-4, f"hata={kodek_hata(6):.1e}")
check("n=8: hala kullanilabilir (hata<1e-2)", kodek_hata(8) < 1e-2)
check("DURUSTLUK: n>=10 kosullanma duvari (hata buyur — gizlenmiyor)",
      kodek_hata(12) > 1e-2, "moment problemi ustel kotu-kosullu (klasik)")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
