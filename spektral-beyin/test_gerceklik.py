"""
test_gerceklik.py — GERCEKLIK YURUTME MOTORU'nun kanitlari.

Testler GROUND-TRUTH'a karsi: ya ANALITIK (H2 dE=-2t, benzen gap=2.0, Fibonacci φ,
kritiklestir |z|=1) ya da MEVCUT-ORGAN davranisi (cross-domain ayni_yasa, ouroboros
recon~0, hedefe_buk monotonlugu). Uydurma veri yok, tahminci yok. Her fiil mevcut
organa iner; capstone yalniz dispatch + |z| esik + dict paketleme ekler.

Calistir: python3 test_gerceklik.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from dataclasses import replace

from gerceklik import (Gerceklik, Amac, kodla, amac_kur, uret, canlilik_kapisi,
                       tohumla, tasi, calistir)
import manipule
import olusum
from domains import extract_law

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))


print("— 1) KODLA idempotent/shape: tek IR coord_91, lam azalan>=0 —")
g = kodla([1., 2., 3., 4.], "math")
check("coord_91 shape (91,)", g.kimlik.coord.shape == (91,))
lam = g.kimlik.lam
check("lam azalan (diff<=1e-12)", np.all(np.diff(lam) <= 1e-12), f"maxdiff={np.max(np.diff(lam)):.1e}")
check("lam >=0 (clip'li)", float(np.min(lam)) >= -1e-12, f"min={np.min(lam):.1e}")
g2 = kodla([1., 2., 3., 4.], "math")
check("idempotent: iki cagri ayni coord", np.allclose(g.kimlik.coord, g2.kimlik.coord))


print("— 2) YASA/Fibonacci: c-finite, kokler φ~1.618, canlilik='kacan' (|z|>1) —")
fib = [1., 1., 2., 3., 5., 8., 13., 21., 34.]
gf = kodla(fib, "math", "fib")
check("seviye=='c-finite'", gf.kimlik.seviye == "c-finite", gf.kimlik.seviye)
_, roots, _, _ = extract_law(np.array(fib))
phi = (1 + np.sqrt(5)) / 2
check("max|z| ~ φ (altin oran, analitik)", abs(np.max(np.abs(roots)) - phi) < 1e-6,
      f"max|z|={np.max(np.abs(roots)):.6f} φ={phi:.6f}")
gf = canlilik_kapisi(gf, amac_kur("yasa"))
check("canlilik sinif=='kacan' (|z|>1)", gf.canlilik["sinif"] == "kacan",
      f"z_max={gf.canlilik['z_max']:.4f}")


print("— 3) KRITIKLESTIR -> CANLI: kokler birim cembere, all(||z|-1|<1e-9) —")
ev, sig = manipule.evren_kur(fib)
check("evren_kur None DEGIL (c-finite yasali)", ev is not None and sig < 1e-8)
kr = manipule.kritiklestir(ev)
check("kritiklestir: all(||z|-1|<1e-9) (analitik z->z/|z|)",
      np.all(np.abs(np.abs(kr.z) - 1) < 1e-9), f"max={np.max(np.abs(np.abs(kr.z)-1)):.1e}")
# kritik evreni yeniden kodla -> canlilik kapisi (kokler |z|=1)
gk = canlilik_kapisi(kodla(list(kr.acilim(24)), "math", "krit"), amac_kur("yasa"))
check("canlilik sinif=='canli' (kritik cizgi ustunde)", gk.canlilik["sinif"] == "canli",
      f"kritiklik_uzakligi={gk.canlilik['kritiklik_uzakligi']:.1e}")


print("— 4) CANLILIK siniflari (analitik/deterministik) —")
# saf periyodik |z|=1 -> canli
per = [np.sin(2 * np.pi * i / 5.0) for i in range(12)]
gp = canlilik_kapisi(kodla(per, "math", "sin"), amac_kur("yasa"))
check("saf periyodik/sinus -> 'canli' (|z|=1)", gp.canlilik["sinif"] == "canli",
      f"z_max={gp.canlilik['z_max']:.4f}")
# sonumlu geometrik r=0.5 -> olu
geo = [0.5 ** i for i in range(10)]
gg = canlilik_kapisi(kodla(geo, "math", "geo"), amac_kur("yasa"))
check("sonumlu geometrik r=0.5 -> 'olu' (|z|<1)", gg.canlilik["sinif"] == "olu",
      f"z_max={gg.canlilik['z_max']:.4f}")
# Fibonacci φ>1 -> kacan (tekrar, sinif dogrulamasi)
check("Fibonacci φ>1 -> 'kacan'", gf.canlilik["sinif"] == "kacan")


print("— 5) MOLEKUL kapi/benzen: butunlesik.yasam_kapisi, HOMO_LUMO==2.0, neg_mod==0 —")
ang = np.linspace(0, 2 * np.pi, 7)[:6]
Xb = np.c_[1.4 * np.cos(ang), 1.4 * np.sin(ang), np.zeros(6)]
gb = canlilik_kapisi(kodla((['C'] * 6, Xb), "molecule", "benzen"), amac_kur("molekul"))
check("benzen HOMO_LUMO == 2.0 (analitik 2β)", abs(gb.canlilik["HOMO_LUMO"] - 2.0) < 1e-6,
      f"gap={gb.canlilik['HOMO_LUMO']:.6f}")
check("benzen neg_mod == 0 (gercek minimum, eyer yok)", gb.canlilik["neg_mod"] == 0)
check("yasam_kapisi 5-kosul cercevesi kullanildi", "kosullar" in gb.canlilik and
      len(gb.canlilik["kosullar"]) == 5)


print("— 6) OLUSUM/H2 analitik: dE=-2t; hetero -2√((Δε/2)²+t²) —")
bH2 = olusum.baglanma_enerjisi(olusum.atom('H'), olusum.atom('H'), t=1.0)
check("H2 dE == -2t == -2.000 (analitik)", abs(bH2["dE"] - (-2.0)) < 1e-9, f"dE={bH2['dE']:.4f}")
bHF = olusum.baglanma_enerjisi(olusum.atom('H'), olusum.atom('F'), t=1.0)
bek = -2.0 * np.sqrt(((-olusum.EN['H'] + olusum.EN['F']) / 2.0) ** 2 + 1.0 ** 2)
check("H-F hetero -2√((Δε/2)²+t²) formule uyuyor", abs(bHF["dE"] - bek) < 1e-9,
      f"dE={bHF['dE']:.4f} bek={bek:.4f}")


print("— 7) CROSS-DOMAIN TASIMA (KANIT): periyot-3 dna/rna/protein ayni_yasa —")
g_dna = kodla("ATG" * 7, "dna", "dna")
adaylar = [kodla("AUG" * 7, "rna", "rna"), kodla("GPA" * 7, "protein", "prot")]
yakin = tasi(g_dna, adaylar, k=2)
check("tasi 2 komsu dondurdu", len(yakin) == 2)
check("periyot-3 dna=rna=protein ayni_yasa==True (iskelet facet)",
      all(a.canlilik["ayni_yasa"] for a in yakin),
      str([(a.kimlik.name, a.canlilik["ayni_yasa"]) for a in yakin]))


print("— 8) TOHUM/ouroboros: c-finite tohumla yasa_korundu, recon_err<1e-6 —")
gt = tohumla(kodla(fib, "math", "fib"))
check("tohum.get('yasa_korundu')==True (kayipsiz seed)", gt.tohum.get("yasa_korundu") is True)
check("recon_err < 1e-6", gt.tohum.get("recon_err", 1.0) < 1e-6,
      f"recon_err={gt.tohum.get('recon_err'):.1e}")


print("— 9) hedefe_buk iz YAPISAL: best-so-far, TUM trace boyunca azalmaz —")
amac_b = amac_kur("buyume", hedef_dict={59: 1.0})   # Q gostergesini (dim 59) tavana
gu = uret(kodla(fib, "math", "fib"), amac_b, adim=150)
check("g.iz uretildi (hedefe_buk kostu)", len(gu.iz) >= 2, f"iz uzunlugu={len(gu.iz)}")
# DURUST: bu best-so-far'in YAPISAL ozelligi (hicbir adim onceki en-iyiyi asmaz);
# optimizerin ise yaradigini KANITLAMAZ — onu Test 10 strict esikle kanitliyor.
check("iz best-so-far: hicbir adim onceki en-iyiyi asmaz (tum trace, yapisal)",
      all(gu.iz[i + 1] <= gu.iz[i] + 1e-12 for i in range(len(gu.iz) - 1)))


print("— 10) AMAC-BUYUME/cekici GERCEK ISI: anlamli bosluk -> STRICT anlamli dusum —")
# sonumlu evren (|z|=0.6, |z|=1 kritik cizgiden UZAK) -> dim-59 (Q, kritiklik) hedefi 1.0
z0 = 0.6 * np.exp(1j * np.pi / 6 * np.array([1, -1]))
a0 = np.array([0.5 - 0.2j, 0.5 + 0.2j])
sonumlu_seq = list(np.real((a0[None, :] * z0[None, :] ** np.arange(24)[:, None]).sum(1)))
gs = kodla(sonumlu_seq, "math", "sonumlu")
amac_c = amac_kur("buyume", hedef_dict={59: 1.0})
gs = uret(gs, amac_c, adim=200)
check("baslangicta ANLAMLI bosluk vardi (iz[0] > 0.05)", gs.iz[0] > 0.05, f"iz[0]={gs.iz[0]:.4f}")
# STRICT + anlamli: no-op optimizer GECEMEZ (yapisal degil, gercek iyilesme sart)
check("cekici mesafeyi ANLAMLI dusurdu (iz[-1] < 0.5*iz[0], strict)",
      gs.iz[-1] < 0.5 * gs.iz[0], f"{gs.iz[0]:.4f} -> {gs.iz[-1]:.4f}")


print("— 11) holonomik_ac None ELE ALMA: tekil p0 -> yapi=None, 'canlilik-kesildi' —")
# gercek holonomik kimlik (faktoriyel) al, holo'yu tekil-p0 katsayiyla degistir
fact = [1., 1., 2., 6., 24., 120., 720., 5040., 40320.]
gfac = kodla(fact, "math", "fact")
check("faktoriyel seviye=='holonomik'", gfac.kimlik.seviye == "holonomik", gfac.kimlik.seviye)
tekil_holo = np.array([[-5.0, 1.0], [1.0, 0.0]])   # p0(n)=n-5 -> n=5'te tekil
gfac = replace(gfac, kimlik=replace(gfac.kimlik, holo=tekil_holo, order=1))
hata = False
try:
    gfac = uret(gfac, amac_kur("yasa"))
    gfac = canlilik_kapisi(gfac, amac_kur("yasa"))
except Exception as e:
    hata = True
    print("    exception:", e)
check("uret hata FIRLATMADI (durust None)", not hata)
check("uret g.yapi is None (tekil p0)", gfac.yapi is None)
check("canlilik sinif=='canlilik-kesildi' (uydurma yok)",
      gfac.canlilik["sinif"] == "canlilik-kesildi")


print("— 12) REGRESYON: mesafe(k,k)==0; ham tohum bir_adim_otesi None; molekul de_novo —")
import beyin
check("beyin.mesafe(k,k)==0", beyin.mesafe(gf.kimlik, gf.kimlik) == 0.0)
# ham seviye: durust sinir korunur (bir_adim_otesi None)
gham = tohumla(kodla(per, "math", "ham"))
check("ham seviye tohum bir_adim_otesi is None (durust sinir)",
      gham.kimlik.seviye == "ham" and gham.tohum.get("bir_adim_otesi") is None,
      f"seviye={gham.kimlik.seviye}")
# TEK YUZEY orkestrasyon: calistir uctan uca (molekul cep kolu)
cep_t = ['O', 'N', 'C']
cep_X = np.array([[0., 0, 0], [2.9, 0, 0], [1.5, 2.3, 0]])
gmol = calistir((cep_t, cep_X), "molecule",
                amac_kur("molekul", cep=(cep_t, cep_X)), adim=200)
check("calistir molekul kolu: de_novo yasayabilir suzdu (uretilen>=1)",
      isinstance(gmol.yapi, dict) and gmol.yapi.get("uretilen", 0) >= 1,
      f"uretilen={gmol.yapi.get('uretilen') if isinstance(gmol.yapi,dict) else None}")
check("molekul canlilik sinifi belirlendi (canli/olu)",
      gmol.canlilik["sinif"] in ("canli", "olu"), gmol.canlilik["sinif"])


print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
