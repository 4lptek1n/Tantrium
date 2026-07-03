"""
gerceklik.py — GERCEKLIK YURUTME MOTORU: mevcut organlarin uzerine BILDIRIMSEL,
AMAC-KOSULLU TEK YUZEY. "Reality LLM" arka beyni: amaci DIL degil YAPI olarak acar.

Fit/egitim YOK. Sistem evrenin DISINDA degil ICINDE ayni operator cebrini KOSTURUR;
train/test ucurumu yok cunku sureci taklit etmez, isletir. Tek IR = coord_91 spektrum.

AKIS (hepsi mevcut organ CAGRISI — hicbir cekirdek matematik burada tekrarlanmaz):
  1) KODLA         herhangi domain -> Kimlik            (beyin.kodla)
  2) AMAC_KUR      cekiciyi (hedef) paketle              (beyin.kodla ile hedef Kimlik)
  3) URET          amaca dogru BUYUT/AC                  (manipule / olusum / butunlesik / domains)
  4) CANLILIK_KAPISI  kritik cizgi |z|=1 siniflandirici  (extract_law + manipule.kritiklestir
                                                          + butunlesik.yasam_kapisi)
  5) TOHUMLA       kayipsiz seed/kalitim                 (beyin.ouroboros)
  6) TASI          cross-domain tasima                   (beyin.kopru + beyin.ayni_yasa)

Iki birlestirici dataclass: durumu boru boyunca tasiyan Gerceklik ve cekiciyi
ilan eden Amac. Her fiil Gerceklik->Gerceklik (bildirimsel, in-place degil).

CANLILIK KRITIK CIZGI: |z|=1 (+-tol) -> CANLI (kendini surduren); |z|<1 -> OLU
(dengeye dusen); |z|>1 -> KACAN (patlayan). Uretici operator manipule.kritiklestir
(z->z/|z|). Olusum-tarafi analog = VALANS DOYUMU. Molekul kolunda butunlesik.
yasam_kapisi'nin 5-kosul cercevesi KULLANILIR.

DURUST SINIR:
  - ham seviye 'gozlem-ici-kesin'; canli/kesin diye PAZARLANMAZ (otesi bilinmiyor).
  - manipule.evren_kur / domains.holonomik_ac None DONEBILIR -> 'canlilik-kesildi'
    olarak ele alinir, uydurma deger yok.
  - de_novo_yasayabilir / hedefe_buk STOKASTIK -> gecerlilik/esik/monotonluk beklenir
    (rng=None ise organ ici default_rng(0) deterministik).
  - butunlesik.yasam_kapisi 'kritik_cizgi_ici' ILAC polaritesidir (|z|<1 iyi); capstone
    canlilik icin bu polarite TERSTIR (docstring: kritiklestir'in tersi). Cerceve
    yeniden yazilmaz, esik amaca-kosullu SECILIR.
  - Dogrusal-olmayan yasalar Faz-2 (kapsam disi).

Konum: spektral-beyin/cekirdek/gerceklik.py ; test: spektral-beyin/test_gerceklik.py.
"""
from dataclasses import dataclass, field, replace
from typing import Optional, Any
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                    # cekirdek/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # spektral-beyin/ (kok)

import beyin
import manipule
import olusum
import butunlesik
import domains
from domains import extract_law
from hiyerarsi import holonomik_ac, polinom_ac

Kimlik = beyin.Kimlik
TOL = 1e-6


# ── BIRLESTIRICI TIPLER ──────────────────────────────────────────────────────
@dataclass
class Amac:
    """Cekici (hedef) ilani. amac.tip BIRINCIL dispatch anahtari."""
    tip: str                                   # {'yasa','spektrum','molekul','buyume'}
    hedef_kimlik: Optional[Kimlik] = None      # beyin.kodla ile uretilmis hedef
    hedef_dict: Optional[dict] = None          # {coord91_dim: deger} — manipule bukme dili
    cep: Optional[tuple] = None                # (types_list, X_ndarray) molekul farmakoforu
    facet: str = "kritiklik"                   # skorlama acisi (kablolama.ROL anahtari)


@dataclass
class Gerceklik:
    """Durumu boru boyunca tasiyan tek nesne. Her fiil bunu alir, yenisini doner."""
    kimlik: Kimlik                             # beyin.kodla ciktisi — TEK IR (coord_91)
    amac: Optional[Amac] = None
    yapi: Any = None                           # uretilen Evren|Parca-havuz|ndarray-yol|dict
    canlilik: Optional[dict] = None            # {sinif, z_max, kritiklik_uzakligi, r}
    tohum: Optional[dict] = None               # ouroboros dict
    iz: list = field(default_factory=list)     # monoton uzaklik izi
    skor: float = float("nan")
    gecerli: bool = False

    def kisa(self):
        s = self.canlilik.get("sinif") if self.canlilik else "-"
        t = self.tohum.get("yasa_korundu") if self.tohum else None
        return (f"<GERCEKLIK {self.kimlik.kisa()} | canlilik={s} | "
                f"iz={len(self.iz)} adim | yasa_korundu={t}>")


# ── SINIFLANDIRICI (yeni matematik: yalniz |z| esik yorumu) ──────────────────
def _siniflandir(roots, tol=TOL):
    """Kritik cizgi |z|=1 siniflandirici. z_max>1 -> kacan; <1 -> olu; ~1 -> canli."""
    r = np.abs(np.asarray(roots, complex))
    if r.size == 0:
        return dict(sinif="belirsiz", z_max=float("nan"),
                    kritiklik_uzakligi=float("nan"), r=0)
    z_max = float(np.max(r))
    kdist = float(np.max(np.abs(r - 1.0)))
    if z_max > 1.0 + tol:
        sinif = "kacan"
    elif z_max < 1.0 - tol:
        sinif = "olu"
    else:
        sinif = "canli"
    return dict(sinif=sinif, z_max=z_max, kritiklik_uzakligi=kdist, r=int(r.size))


# ── 1) KODLA ─────────────────────────────────────────────────────────────────
def kodla(veri, domain="math", name="x") -> Gerceklik:
    """Herhangi domaini TEK Kimlik'e indir, Gerceklik'e sar. Kimlik ELLE kurulmaz;
    beyin.kodla coord_91/lam-azalan>=0 tutarliligini organ icinde saglar."""
    return Gerceklik(kimlik=beyin.kodla(veri, domain, name))


# ── 2) AMAC_KUR ──────────────────────────────────────────────────────────────
def amac_kur(tip, hedef_veri=None, domain=None, hedef_dict=None, cep=None,
             facet="kritiklik") -> Amac:
    """Cekiciyi paketle. hedef_veri verilirse hedef Kimlik yine beyin.kodla'dan gecer."""
    hk = beyin.kodla(hedef_veri, domain or "math", "hedef") if hedef_veri is not None else None
    return Amac(tip=tip, hedef_kimlik=hk, hedef_dict=hedef_dict, cep=cep, facet=facet)


# ── 3) URET (dispatch: molekul-vs-dizi kolu; dizi ICI seviye + hedef_dict) ───
def uret(g: Gerceklik, amac: Amac, adim=250, rng=None) -> Gerceklik:
    """Amaca dogru BUYUT/AC. Cikti g.yapi + g.iz (best-so-far uzaklik izi). Hicbir
    mod-uzayi / olusum cebri yeniden yazilmaz — sadece dispatch if/else.

    DURUST DISPATCH: amac.tip yalniz MOLEKUL-vs-DIZI kolunu secer ('molekul' ya da
    kimlik.seq is None -> molekul kolu). DIZI kolunda tip ('yasa'/'spektrum'/'buyume')
    OKUNMAZ; kararı kimlik.seviye (polinom/c-finite/holonomik/ham) + hedef_dict varligi
    verir. Yani tip 'birincil dispatch' DEGIL — kol secici."""
    k = g.kimlik
    iz = list(g.iz)
    yapi = None
    n_top = len(k.seq) + 1 if k.seq is not None else 0

    # ── MOLEKUL / MONTAJ kolu ──
    if amac.tip == "molekul" or k.seq is None:
        if amac.cep is not None:
            cep_t, cep_X = amac.cep
            # olusum + yasam_kapisi sarili tek cagri (BIRLESIK SPEKTRAL KAPI)
            yapi = butunlesik.de_novo_yasayabilir(cep_t, np.asarray(cep_X, float),
                                                  n_aday=5, adim=300, max_atom=12)
        else:
            # olusum kolu: Kimlik'i havuza sok, greedy-determinist kenetle
            p = olusum.kimlikten_parca(k, ne=2, valans=2)
            havuz = [p, olusum.atom("C"), olusum.atom("O"),
                     olusum.atom("H"), olusum.atom("H")]
            yapi = olusum.kendiliginden_olus(havuz, t=1.0)
        return replace(g, amac=amac, yapi=yapi, iz=iz)

    # ── DIZI / DINAMIK kolu (seviye ikincil dispatch) ──
    seviye = k.seviye
    if seviye == "holonomik":
        yapi = holonomik_ac(k.holo, k.seq[:k.order], n_top)      # None -> canlilik-kesildi
    elif seviye == "polinom":
        yapi = polinom_ac(k.poli, n_top)
    elif seviye == "c-finite":
        ev, sig = manipule.evren_kur(k.seq)                      # ONCE None kontrol!
        if ev is not None and amac.hedef_dict:
            yapi, son, iz = manipule.hedefe_buk(ev, amac.hedef_dict, adim=adim, rng=rng)
        elif ev is not None:
            yapi = ev
    else:  # ham / yasasiz -> ham spektrum merdiven-uzayi
        if amac.hedef_dict:
            yapi, son, iz = manipule.hedefe_buk_merdiven(k.lam, amac.hedef_dict,
                                                         adim=adim, rng=rng)
        else:
            yapi = np.asarray(k.lam, float)
    return replace(g, amac=amac, yapi=yapi, iz=iz)


# ── 4) CANLILIK_KAPISI ───────────────────────────────────────────────────────
def canlilik_kapisi(g: Gerceklik, amac: Amac = None) -> Gerceklik:
    """Kritik cizgi |z|=1 kapisi. Dizi kolu: extract_law kokleri -> |z| siniflandirma.
    Molekul kolu: butunlesik.yasam_kapisi 5-kosul cercevesi (kimya IR). Olusum kolu:
    VALANS DOYUMU analogu (acik valans=buyur, doymus=dur/sonlu).

    DURUST: |z|=1 kritik-cizgi TANIMI YALNIZ DIZI/DINAMIK kolunun degismezidir; orada
    z_max/kritiklik_uzakligi doldurulur. Molekul ve olusum dallari FARKLI semantik
    kullanir (5-kosul kapisi / valans doyumu) ve z_max=nan doner. Birlesim ortak bir
    invariant degil, amac-kosullu DOMAIN-DISPATCH'tir — sinif etiketi kola gore degisir."""
    amac = amac or g.amac
    k = g.kimlik

    # ── MOLEKUL / MONTAJ kolu ──
    if k.seq is None or (amac is not None and amac.tip == "molekul"):
        # 3a) de_novo_yasayabilir ciktisi (butunlesik BIRLESIK KAPI zaten kostu)
        if isinstance(g.yapi, dict) and "yasayanlar" in g.yapi:
            n_yasar = g.yapi["yasayabilir_sayi"]
            canlilik = dict(sinif="canli" if n_yasar > 0 else "olu",
                            kaynak="butunlesik.de_novo_yasayabilir",
                            yasayabilir_sayi=n_yasar, uretilen=g.yapi["uretilen"],
                            z_max=float("nan"), kritiklik_uzakligi=float("nan"), r=0)
        # 3b) olusum havuzu -> valans doyumu analogu
        elif isinstance(g.yapi, dict) and "birimler" in g.yapi:
            birimler = g.yapi["birimler"]
            acik = any(p.valans > 0 for p in birimler)
            canlilik = dict(sinif="buyur" if acik else "doymus",
                            kaynak="olusum.valans_doyumu",
                            seviye_max=g.yapi["seviye_max"],
                            z_max=float("nan"), kritiklik_uzakligi=float("nan"),
                            r=len(birimler))
        # 3c) mevcut molekul IR -> butunlesik.yasam_kapisi (kimya kolu)
        elif k.types is not None and k.coords3d is not None:
            import kimya
            B = kimya.bag_dereceleri(k.types, np.asarray(k.coords3d, float))
            akis = butunlesik.fizik_akisi(k.types, np.asarray(k.coords3d, float),
                                          list(B.keys()))
            kapi = butunlesik.yasam_kapisi(akis)          # 5-kosul cerceve (ILAC polaritesi)
            canlilik = dict(sinif="yasar" if kapi["yasayabilir"] else "yasamaz",
                            kaynak="butunlesik.yasam_kapisi", kosullar=kapi["kosullar"],
                            HOMO_LUMO=akis["homo_lumo"], neg_mod=akis["neg_mod"],
                            E_geometri=akis["E_geo"],
                            z_max=float("nan"), kritiklik_uzakligi=float("nan"), r=0)
        else:
            canlilik = dict(sinif="belirsiz", z_max=float("nan"),
                            kritiklik_uzakligi=float("nan"), r=0)
        return replace(g, canlilik=canlilik)

    # ── DIZI / DINAMIK kolu ──
    # Uret KOSTU ve URETIM KESILDI (holonomik tekil p0 / evren_kur None): uydurma
    # yok, kapi durustce kesildi. (g.amac set = uret ran; standalone siniflandirmada
    # g.amac None -> kimligin kokleri her zaman siniflandirilabilir.)
    if g.amac is not None and g.yapi is None:
        canlilik = dict(sinif="canlilik-kesildi", z_max=float("nan"),
                        kritiklik_uzakligi=float("nan"), r=0)
        return replace(g, canlilik=canlilik)

    # kokler: extract_law (mevcut organ) veya k.seed
    roots = np.asarray([], complex)
    if k.seq is not None:
        _, roots, _, _ = extract_law(np.asarray(k.seq, float))
    if roots.size == 0:
        roots = np.asarray(k.seed, complex)
    return replace(g, canlilik=_siniflandir(roots))


# ── 5) TOHUMLA ───────────────────────────────────────────────────────────────
def tohumla(g: Gerceklik) -> Gerceklik:
    """Kayipsiz seed/kalitim testi -> g.tohum. Doner-dict anahtarlari domaine gore
    DEGISIR (.get ile eris; ham dalinda bir_adim_otesi=None — durust)."""
    return replace(g, tohum=beyin.ouroboros(g.kimlik))


# ── 6) TASI (cross-domain) ───────────────────────────────────────────────────
def tasi(g: Gerceklik, adaylar, k=1, facet=None):
    """Bir alandaki kimlige baska alandaki en yakin k komsu; ayni_yasa ile yasa-
    korunumunu isaretle (periyot-3 dna=rna=protein)."""
    hedef = g.kimlik
    aday_k = [a.kimlik for a in adaylar]
    yakin = beyin.kopru(hedef, aday_k, k=k, facet=facet)
    sonuc = []
    for kk in yakin:
        for a in adaylar:
            if a.kimlik is kk:
                ay = beyin.ayni_yasa(hedef, kk)
                bilgi = dict(a.canlilik or {})
                bilgi["ayni_yasa"] = ay
                sonuc.append(replace(a, canlilik=bilgi))
                break
    return sonuc


# ── TEK YUZEY ORKESTRASYON ───────────────────────────────────────────────────
def calistir(veri, domain, amac: Amac, adim=250) -> Gerceklik:
    """kodla -> uret -> canlilik_kapisi -> tohumla akisini (1..5) sirayla kostur."""
    g = kodla(veri, domain)
    g = uret(g, amac, adim=adim)
    g = canlilik_kapisi(g, amac)
    g = tohumla(g)
    return g


# ── DEMO ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print(" GERCEKLIK YURUTME MOTORU — kodla/uret/canlilik/tohum/tasi tek yuzeyde")
    print("=" * 70)

    # A) Fibonacci: c-finite, kacan rejim (φ>1)
    fib = [1., 1., 2., 3., 5., 8., 13., 21., 34., 55.]
    amac = amac_kur("yasa")
    g = calistir(fib, "math", amac)
    print("\n[A] Fibonacci:", g.kisa())
    print(f"    canlilik={g.canlilik['sinif']}  z_max={g.canlilik['z_max']:.4f} (φ, kacan)")
    print(f"    tohum: yasa_korundu={g.tohum.get('yasa_korundu')} "
          f"recon_err={g.tohum.get('recon_err'):.1e}")

    # B) Kritiklestir -> canli
    ev, _ = manipule.evren_kur(fib)
    kr = manipule.kritiklestir(ev)
    gc = canlilik_kapisi(kodla(list(kr.acilim(24)), "math", "krit"), amac_kur("yasa"))
    print(f"\n[B] Kritiklestirilmis fib: canlilik={gc.canlilik['sinif']} "
          f"(|z|=1, kritiklik_uzakligi={gc.canlilik['kritiklik_uzakligi']:.1e})")

    # C) Cross-domain tasima (periyot-3)
    g_dna = kodla("ATG" * 7, "dna", "dna")
    adaylar = [kodla("AUG" * 7, "rna", "rna"), kodla("GPA" * 7, "protein", "prot")]
    yakin = tasi(g_dna, adaylar, k=2)
    print("\n[C] TASI (dna -> rna/protein):",
          [(a.kimlik.name, a.canlilik["ayni_yasa"]) for a in yakin])

    # D) Molekul kolu: benzen yasam kapisi
    ang = np.linspace(0, 2 * np.pi, 7)[:6]
    X = np.c_[1.4 * np.cos(ang), 1.4 * np.sin(ang), np.zeros(6)]
    gm = canlilik_kapisi(kodla((['C'] * 6, X), "molecule", "benzen"), amac_kur("molekul"))
    print(f"\n[D] Benzen: sinif={gm.canlilik['sinif']} "
          f"HOMO_LUMO={gm.canlilik['HOMO_LUMO']:.3f} neg_mod={gm.canlilik['neg_mod']}")

    print("\n" + "=" * 70)
    print(" Tek yuzey: her fiil mevcut organa iner. Cekirdek matematik tekrar YOK.")
    print("=" * 70)
