"""
test_beyin.py — TEK OMURGA'nin uctan uca kanitlari.
Dort fiil (kodla/kopru/coz/ouroboros) tek Kimlik tipinde tutarli calisiyor mu?
Her test bir mimari iddiayi olcer. Calistir: python3 test_beyin.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from beyin import (kodla, mesafe, ham_mesafe, facet_mesafe, benzerlik,
                   ayni_yasa, kopru, coz, ouroboros, Kimlik, FACET, DIZI_DOMAINLERI)

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def fib(n=12):
    s=[1.,1.]
    while len(s)<n: s.append(s[-1]+s[-2])
    return s[:n]

CEP = [(np.array([0.,0.,0.]),'N'),(np.array([1.4,0.2,0.]),'C'),
       (np.array([2.6,1.,0.]),'O'),(np.array([1.2,2.2,.4]),'C'),(np.array([0.,1.6,.3]),'C')]

print("— 1) KODLA: her domain tek Kimlik tipine iniyor —")
kinds = {
    "math":    kodla(fib(), "math", "fib"),
    "dna":     kodla("ATGCGTACGTTGCACG", "dna", "dna1"),
    "rna":     kodla("AUGCGUACGUUGCACG", "rna", "rna1"),
    "protein": kodla("MKWVTFISLLFLFSSAYS", "protein", "prot1"),
    "finance": kodla([100,101,103,102,105,108,107,110,113,111,115], "finance", "fin1"),
}
for d,k in kinds.items():
    check(f"{d}: Kimlik + 91-dim sonlu coord",
          isinstance(k,Kimlik) and k.coord.shape==(91,) and np.all(np.isfinite(k.coord)))
mol = kodla((['C','C','N','O','C'],
             np.array([[0,0,0],[1.5,0,0],[2.2,1.2,0],[1.5,2.4,.3],[0,1.4,.5]],float)),
            "molecule","mol1")
check("molecule: tam operator (ozvektor V dolu)", mol.V is not None and mol.V.shape[0]==5)

print("— 2) KODLA: yasali/yasasiz dogru ayriliyor —")
check("Fibonacci C-finite: σ ~ 0", kinds["math"].sigma < 1e-8, f"σ={kinds['math'].sigma:.1e}")
noise = kodla(list(np.random.default_rng(1).normal(50,10,20)), "math", "noise")
check("Gurultu: σ buyuk (yasasiz)", noise.sigma > 0.05, f"σ={noise.sigma:.3f}")

print("— 3) KOPRU: periyot-3 domainler ARASI ayni yasa (cross-space cekirdek) —")
p3 = {u: kodla(seq, u, f"p3-{u}") for u,seq in {
        "math":[1.,5.,2.]*7, "dna":"ATG"*7, "rna":"AUG"*7, "protein":"GPA"*7}.items()}
check("dna ~ math  (ayni kanonik yasa)",  ayni_yasa(p3["dna"], p3["math"]))
check("dna ~ protein (ayni kanonik yasa)", ayni_yasa(p3["dna"], p3["protein"]))
check("rna ~ math  (ayni kanonik yasa)",  ayni_yasa(p3["rna"], p3["math"]))

print("— 4) KOPRU: transkripsiyon DNA->RNA kimligi TAM korur (d~0) —")
dna = "ATGCGTACGTTGCACGATCG"; rna = dna.replace("T","U")
kd, kr = kodla(dna,"dna","d"), kodla(rna,"rna","r")
check("DNA->RNA coord mesafe ~ 0", mesafe(kd,kr) < 1e-9, f"d={mesafe(kd,kr):.1e}")
check("DNA->RNA ayni yasa", ayni_yasa(kd,kr))

print("— 5) KOPRU: aperiyodik UZAK, periyodik YAKIN (ayirt ediyor) —")
d_in  = mesafe(p3["protein"], p3["dna"])
d_out = mesafe(p3["protein"], kodla("MKWVTFISLLFLFSSAYS","protein","aper"))
check("d(periyot3 prot, periyot3 dna) < d(periyot3 prot, aperiyodik)",
      d_in < d_out, f"{d_in:.3f} < {d_out:.3f}")

print("— 6) KOPRU: domain-asan sorgu (en yakin kimlik, domain fark etmez) —")
havuz = [p3["math"], kodla(fib(),"math","fib"), p3["dna"], noise]
en_yakin = kopru(p3["rna"], havuz, k=1)[0]
check("rna periyot-3 sorgusu -> periyot-3 komsu buluyor",
      ayni_yasa(en_yakin, p3["rna"]), f"bulunan={en_yakin.name}")

print("— 6b) KABLOLAMA: 91 dim tek tek dogru role, tam bolusum —")
from kablolama import dogrula, ROL, DIM, DINAMIK, ONARILDI
from coord91 import coord_91_temiz
check("kablolama tam bolusum (91 dim, her biri TAM BIR rol)", dogrula())
check("her dim 0..90 tam bir kez kabloli",
      sorted(i for idxs in ROL.values() for i in idxs) == list(range(91)))
check("dinamik dim'ler dogru isaretli (50,59,69-71,80-82)",
      sorted(DINAMIK) == [50,59,69,70,71,80,81,82])
check("32 bosa dim onarildi (tekrar+olu -> gercek is)", len(ONARILDI) == 32,
      f"onarildi={len(ONARILDI)}")
# ONARIM KANITI: eski tekrar (74-76 ≡ 20-22) artik AYRISIYOR
_vd = p3["dna"].coord
check("onarim dogrulandi: coord[74:77] ARTIK != coord[20:23]",
      not np.allclose(_vd[74:77], _vd[20:23]), "TET tekrari cozuldu")
# 500 spektrumda ne olu ne tekrar (statik uzay, dinamik disi)
_rng = np.random.default_rng(11); _dyn = set(DINAMIK)
_V = np.array([coord_91_temiz(np.sort(_rng.uniform(0.05,8,_rng.integers(5,14)))[::-1])[0]
               for _ in range(500)])
_dead = [i for i in range(91) if i not in _dyn and np.std(_V[:,i])<1e-9]
_dup = [(i,j) for i in range(91) if i not in _dyn and np.std(_V[:,i])>1e-9
        for j in range(i+1,91) if j not in _dyn and np.std(_V[:,j])>1e-9
        and np.allclose(_V[:,i],_V[:,j],atol=1e-8)]
check("500 spektrumda OLU dim yok (statik)", _dead == [], f"olu={_dead}")
check("500 spektrumda TEKRAR dim yok", _dup == [], f"tekrar={_dup}")
# Li bug'i duzeldi: eski Li hep 0'di; simdi atesLENIyor
check("Li katsayilari artik atesLENIyor (eski bug: λ̂≤1 -> hep 0)",
      np.std(_V[:,37]) > 1e-6, f"std(L1)={np.std(_V[:,37]):.3f}")

print("— 6c) KOPRU cok-acili: 91 dim yasadan FAZLASINI, rol-bazli —")
prof = benzerlik(p3["dna"], p3["protein"])
aper = kodla("MKWVTFISLLFLFSSAYS","protein","aper")
# dna~protein periyot-3: cogu rol ozdes; ayrilik icerik-tasiyan rollerde toplaniyor
es_roller = sum(1 for r in ("varolabilirlik","kaos","dinamik","kritiklik","yapi") if prof[r] < 0.06)
check("dna~protein: yapisal roller es (>=4/5 rol < 0.06)", es_roller >= 4,
      f"es_rol={es_roller}/5")
check("dna~protein: ayrilik icerik rollerinde (karmasiklik+baskinlik en buyuk)",
      max(prof, key=lambda k: prof[k] if k!='iskelet(yasa)' else -1) in ("karmasiklik","baskinlik"),
      f"karmasiklik={prof['karmasiklik']:.2f} baskinlik={prof['baskinlik']:.2f}")
check("kalibre mesafe < ham mesafe (tek rol domine etmiyor)",
      mesafe(p3["dna"],p3["protein"]) < ham_mesafe(p3["dna"],p3["protein"]),
      f"kalibre={mesafe(p3['dna'],p3['protein']):.2f} ham={ham_mesafe(p3['dna'],p3['protein']):.2f}")
check("'kaos' rolu: periyot-3 protein, aperiyodikten periyot-3 dna'ya daha yakin",
      facet_mesafe(p3["protein"],p3["dna"],"kaos") < facet_mesafe(p3["protein"],aper,"kaos"),
      f"p3={facet_mesafe(p3['protein'],p3['dna'],'kaos'):.3f} aper={facet_mesafe(p3['protein'],aper,'kaos'):.3f}")
check("'varolabilirlik' rolu aperiyodigi ayiriyor (yasa+varolus farkli)",
      facet_mesafe(p3["protein"],aper,"varolabilirlik") > 0.5,
      f"d={facet_mesafe(p3['protein'],aper,'varolabilirlik'):.2f}")

print("— 7) COZ: cep -> gecerli yeni molekul (de novo) —")
r = coz(CEP, adim=3000)
check("uretilen molekul gecerli (valans+bag)", r["gecerli"], f"skor={r['skor']:.2f}")
check("uretilen Kimlik operator (ozvektor dolu)", r["kimlik"].V is not None)
check("cep tamamlayiciligi anlamli (skor > yarim cep)", r["skor"] > len(CEP)/2)

print("— 8) OUROBOROS: dizi domaini kayipsiz kapaniyor + otesini uretiyor —")
o = ouroboros(kodla(fib(),"math","fib"))
check("fib: dongu kapali (recon_err ~ 0)", o["kapali"] and o["recon_err"]<1e-6,
      f"err={o['recon_err']:.1e}")
check("fib: yasa geri-kurulanda korundu", o["yasa_korundu"])
_fib = fib(); _sonraki = _fib[-1] + _fib[-2]        # gercek sonraki Fibonacci
check(f"fib: bir adim otesi dogru ({_fib[-1]:.0f}->{_sonraki:.0f})",
      abs(o["bir_adim_otesi"]-_sonraki)<1e-6, f"otesi={o['bir_adim_otesi']:.1f}")

print("— 9) OUROBOROS: operator domaini kayipsiz (tam operator -> 3D) —")
om = ouroboros(r["kimlik"])
check("molekul: dongu kapali (RMSD ~ 0)", om["kapali"] and om["rmsd"]<1e-6,
      f"rmsd={om['rmsd']:.1e}")
check("molekul: spektrum geri-kurulanda korundu", om["spektrum_farki"]<1e-6,
      f"Δλ={om['spektrum_farki']:.1e}")

print("— 10) DURUSTLUK: yasasiz nesne ouroboros'ta SAHTE basari vermiyor —")
on = ouroboros(noise)
check("gurultu: dongu kapanmiyor (recon_err buyuk ya da yasa korunmuyor)",
      (not on["kapali"]) or (not on.get("yasa_korundu", True)),
      f"kapali={on['kapali']} err={on['recon_err']:.2f}")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
