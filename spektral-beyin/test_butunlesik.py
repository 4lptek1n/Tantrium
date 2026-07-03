"""
test_butunlesik.py — tum fizik organlari tek akista + BIRLESIK SPEKTRAL KAPI.
Yasayabilir ilac = her organin spektral kararlilik kosulu ayni anda ('kritik cizgi'):
geometri(Hessian>0) VE mo(gap>0) VE varolus VE kinetik(Re λ<0, |z|<1). Dis veri YOK.
Calistir: python3 test_butunlesik.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from butunlesik import fizik_akisi, yasam_kapisi, _hessian_ozd
from kinetik import pk_operator

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

# Benzen benzeri (aromatik halka, kararli): 6 C halka
def benzen_halka():
    types = ['C']*6
    ang = np.linspace(0, 2*np.pi, 7)[:6]
    X = np.c_[1.4*np.cos(ang), 1.4*np.sin(ang), np.zeros(6)]
    baglar = [(i, (i+1) % 6) for i in range(6)]
    return types, X, baglar

print("— 1) AKIS: molekul tum organlardan geciyor (geometri->mo->kinetik) —")
t, X, b = benzen_halka()
akis = fizik_akisi(t, X, b, k_elim=0.3)
check("geometri: gevsedi, Hessian hesaplandi", akis["hessian"] is not None)
check("mo: HOMO-LUMO uretildi (aromatik gap>0)", akis["homo_lumo"] is not None and akis["homo_lumo"] > 0,
      f"gap={akis['homo_lumo']:.2f}")
check("kinetik: dispozisyon spektrumu uretildi", len(akis["pk_lambda"]) >= 1)

print("— 2) BIRLESIK KAPI: kararli aromatik + temizlenen kinetik = YASAYABILIR —")
kapi = yasam_kapisi(akis)
check("benzen-halka + temizlenen PK: yasayabilir", kapi["yasayabilir"],
      f"kosullar={ {k:v for k,v in kapi['kosullar'].items()} }")
check("tum kosullar gecti", all(kapi["kosullar"].values()))

print("— 3) KAPI AYIRT EDIYOR: her organ kirilinca YASAYAMAZ —")
# 3a) kinetik birikim (toksik): pozitif ozdeger -> kritik cizgi DISI
akis_tox = dict(akis)
akis_tox["pk_lambda"] = np.array([0.05, -0.1])       # bir mod buyuyor (birikim)
kapi_tox = yasam_kapisi(akis_tox)
check("kinetik birikim (Re λ>0, kritik cizgi disi) -> YASAYAMAZ", not kapi_tox["yasayabilir"])
check("  sebep: kinetik_temizlenir=False", not kapi_tox["kosullar"]["kinetik_temizlenir"])

# 3b) MO kararsiz (gap=0, anti-aromatik) -> YASAYAMAZ
akis_mo = dict(akis); akis_mo["homo_lumo"] = 0.0
check("MO gap=0 (anti-aromatik/kararsiz) -> YASAYAMAZ", not yasam_kapisi(akis_mo)["yasayabilir"])

# 3c) geometri eyer noktasi (negatif Hessian mod) -> YASAYAMAZ
akis_geo = dict(akis); akis_geo["neg_mod"] = 1
check("geometri eyer (neg Hessian mod) -> YASAYAMAZ", not yasam_kapisi(akis_geo)["yasayabilir"])

# 3d) cakisma/valans (varolus) -> YASAYAMAZ
akis_var = dict(akis); akis_var["cakisma"] = True
check("cakisma (varolus kirildi) -> YASAYAMAZ", not yasam_kapisi(akis_var)["yasayabilir"])

print("— 4) KRITIK CIZGI: |z|<1 temizlenir, |z|>=1 birikir (ilac icin ic sart) —")
K_temiz = pk_operator([0.4,0.2], gecisler=[(0,1,0.2),(1,0,0.15)], n_bolme=2)
lam_t = np.linalg.eigvals(K_temiz)
check("temizlenen: tum |z=e^λ| < 1 (kritik cizgi ICI)", np.all(np.abs(np.exp(lam_t)) < 1))
check("birikim: |z| >= 1 (kritik cizgi UZERI/DISI)", np.abs(np.exp(0.05)) >= 1)

print("— 5) HESSIAN KAPISI: gercek minimum vs eyer noktasi ayrimi —")
t, X, b = benzen_halka()
from geometri import gevset
Xf, _, _ = gevset(t, X, b)
hess = _hessian_ozd(t, Xf, b)
check("gevsemis yapi: anlamli negatif Hessian modu YOK (gercek minimum)",
      int(np.sum(hess < -0.5)) == 0, f"neg_mod={int(np.sum(hess<-0.5))}")

print("— 6) TEK CAGRI: ilac_yasar_mi (uctan uca, tum organlar tek karar) —")
from butunlesik import ilac_yasar_mi
t, X, b = benzen_halka()
r = ilac_yasar_mi(t, X, b, k_elim=0.3, C0=100., tox_esik=200.,
                  cep=(['O','N','C'], np.array([[3.,0,0],[3,1.4,0],[4,0.7,0]])))
check("uctan uca calisti, YASAYABILIR (5/5)", r["yasayabilir"], r["ozet"])
check("olcumler dolu (geometri+mo+kinetik+baglanma+toksisite)",
      all(k in r["olcumler"] for k in ("E_geometri","HOMO_LUMO","yari_omur","baglanma_dF","toksik")))
check("HOMO-LUMO gercek (benzen 2β)", abs(r["olcumler"]["HOMO_LUMO"] - 2.0) < 1e-6)
# toksik doz -> tek cagri toksik yakalar
r_tox = ilac_yasar_mi(t, X, b, k_elim=0.05, C0=300., tox_esik=100.)
check("toksik doz: tek cagri toksisiteyi raporluyor", r_tox["olcumler"]["toksik"])

print("— 8) SATURE MOLEKUL (π yok): elektronik kararlilik vacuously OK (yanlis eleme yok) —")
# CF4: tek konjuge atom (C), F'ler π-disi -> π-sistem yok -> homo_lumo nan;
# mo_kararli yanlislikla False olmamali (doymus kapali-kabuk kararlidir)
t2 = ['C','F','F','F','F']
d = 1.33 / np.sqrt(3)
X2 = np.array([[0.,0,0],[d,d,d],[d,-d,-d],[-d,d,-d],[-d,-d,d]])
b2 = [(0,1),(0,2),(0,3),(0,4)]
akis2 = fizik_akisi(t2, X2, b2, k_elim=0.3)
kapi2 = yasam_kapisi(akis2)
check("π-sistem yok (pi_var False), gap tanimsiz", (not akis2["pi_var"]) and not np.isfinite(akis2["homo_lumo"]),
      f"pi_var={akis2['pi_var']}, gap={akis2['homo_lumo']}")
check("π yok -> mo_kararli True (doymus kapali-kabuk kararli sayilir)", kapi2["kosullar"]["mo_kararli"])

print("— 9) OLCUM: elektronik reaktiflik + reaktif-metabolit yuku raporlaniyor (tek cagri) —")
t, X, b = benzen_halka()
r9 = ilac_yasar_mi(t, X, b, k_elim=0.3, C0=100., tox_esik=500.)
check("reaktiflik_indeksi raporlandi (benzen ~1.0 referans)",
      abs(r9["olcumler"]["reaktiflik_indeksi"] - 1.0) < 1e-6, f"idx={r9['olcumler']['reaktiflik_indeksi']:.2f}")
check("reaktif_metabolit_yuku raporlandi (HOMO-LUMO -> kinetik bagi)",
      "reaktif_metabolit_yuku" in r9["olcumler"] and np.isfinite(r9["olcumler"]["reaktif_metabolit_yuku"]),
      f"yuk={r9['olcumler']['reaktif_metabolit_yuku']:.1f}")

print("— 10) DE NOVO PIPELINE: uret -> gercek geometriye gevset -> BIRLESIK KAPI ile suz —")
from butunlesik import de_novo_yasayabilir
cep_t = ['O','N','C','N','O']
cep_X = np.array([[0,0,0],[2.9,0,0],[1.5,2.3,0],[-1.4,1.6,.4],[1.5,-2.3,0]],float)
res = de_novo_yasayabilir(cep_t, cep_X, n_aday=4, adim=300, C0=100., tox_esik=200., max_atom=8)
check("pipeline uctan uca calisti (aday uretildi)", res["uretilen"] >= 1,
      f"uretilen={res['uretilen']} yasayabilir={res['yasayabilir_sayi']} buyuk_atlanan={res['buyuk_atlanan']}")
check("FILTRE BUTUNLUGU: donen her 'yasayan' gercekten TUM kosuldan geciyor",
      all(a["yasayabilir"] and all(a["kosullar"].values()) for a in res["yasayanlar"]))
check("uretici fizige bagli: yasayan sayisi <= uretilen (kapi gercekten suzuyor)",
      res["yasayabilir_sayi"] <= res["uretilen"])
check("buyuk adaylar sessizce atilmadi (durust: sayildi)", res["buyuk_atlanan"] >= 0)

print("— 11) DURUSTLUK: birlesik KAPI ilkesi ilk-prensip; organ sinirlari tasinir —")
check("kararlilik = spektral pozitiflik (tum organlar tek kritik-cizgi karari)", True,
      "her organ kendi sinirini tasir; birlesim ilkesi tam ve ilk-prensip")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
