"""
beyin.py — TEK OMURGA. Dagitik organlari tek kapali dongude birlestirir.

Vizyon (dort fiil, tek dil):
    KODLA      her domain -> operator -> ozdeger(+ozvektor) -> yasa+seed -> coord_91   (tek spektral dil)
    KOPRU      ayni grounding uzayinda domainler arasi es-kimlik                        (periyodiklik alfabeden bagimsiz)
    COZ        istenen kimlik/cep -> gecerli yeni nesne (de novo)                       (tersine tasarim)
    OUROBOROS  nesne -> kimlik -> nesne, kimligi koruyarak kapat                        (kayipsiz dongu)

Her organ zaten vardi (domains, engine, coord91, dinamik, de_novo); bu dosya
onlari TEK Kimlik tipi ve TEK cagri yuzeyi altinda birlestirir. Oyuncak olan
kimya/ilac katmani; MIMARI — dort fiilin kapali dongusu — gercek ve test edilir.

Testler: ../test_beyin.py
"""
from dataclasses import dataclass, field
from typing import Optional
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))          # cekirdek/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # spektral-beyin/ (de_novo)

from engine import gram_spectrum, prony_law
from coord91 import coord_91_temiz as _coord_full
from domains import seq_to_A, extract_law, A_molecule
from hiyerarsi import yasa_avcisi, holonomik_ac
import de_novo as dn

# ── Domain sozlukleri: alfabe -> sayi (her uzayin cekirdege inis kurali) ──────
ALFABE = {
    "dna":     {'A':2.0,'G':3.0,'C':1.0,'T':1.5},
    "rna":     {'A':2.0,'G':3.0,'C':1.0,'U':1.5},          # U=T: transkripsiyon kimligi korur
    "protein": {'A':1.8,'R':-4.5,'N':-3.5,'D':-3.5,'C':2.5,'Q':-3.5,'E':-3.5,'G':-0.4,
                'H':-3.2,'I':4.5,'L':3.8,'K':-3.9,'M':1.9,'F':2.8,'P':-1.6,'S':-0.8,
                'T':-0.7,'W':-0.9,'Y':-1.3,'V':4.2},        # Kyte-Doolittle hidropati
}
DIZI_DOMAINLERI = {"math", "dna", "rna", "protein", "finance"}
OPERATOR_DOMAINLERI = {"molecule"}


# ── TEK KIMLIK TIPI ───────────────────────────────────────────────────────────
@dataclass
class Kimlik:
    """Bir nesnenin kanonik kimligi — domain ne olursa olsun ayni tip."""
    name: str
    domain: str
    A: np.ndarray                      # operator
    lam: np.ndarray                    # ozdeger spektrumu (azalan)
    coord: np.ndarray                  # coord_91 (dinamik katli)
    V: Optional[np.ndarray] = None     # ozvektor (tam operator; yon/faz)
    law: np.ndarray = field(default_factory=lambda: np.array([]))   # yasa (Prony)
    seed: np.ndarray = field(default_factory=lambda: np.array([]))  # karakteristik kokler
    sigma: float = float("nan")        # yasalilik artigi
    order: int = 0
    seq: Optional[np.ndarray] = None   # dizi domainlerinde ham sayisal dizi
    coords3d: Optional[np.ndarray] = None  # operator domainlerinde 3D konum
    types: Optional[list] = None       # operator domainlerinde atom tipleri
    seviye: str = "yasasiz"            # 'c-finite' | 'holonomik' | 'yasasiz'
    holo: Optional[np.ndarray] = None  # holonomik yasa: p_k(n) katsayi matrisi
    derece: int = 0                    # holonomik polinom derecesi

    def kisa(self):
        if self.seviye == "yasasiz":
            yl = "yasasiz"
        else:
            yl = f"{self.seviye}(order={self.order}" + \
                 (f", derece={self.derece}" if self.seviye == "holonomik" else "") + \
                 f", σ={self.sigma:.1e})"
        return f"<{self.domain}:{self.name} | {yl} | rank={int(np.sum(self.lam>1e-9))} | coord91>"


# ── 1) KODLA ──────────────────────────────────────────────────────────────────
def _sayisallastir(veri, domain):
    """Ham veriyi sayisal diziye indir (domain'in cekirdege inis kurali)."""
    if domain == "math" or domain == "finance":
        s = np.asarray(veri, float)
        if domain == "finance":
            s = np.diff(np.log(s + 1e-12))            # log-getiri
        return s
    if domain in ALFABE:
        tbl = ALFABE[domain]
        return np.array([tbl[c.upper()] for c in veri], float)
    raise ValueError(f"dizi domaini degil: {domain}")


def kodla(veri, domain="math", name="x", **kw):
    """Her domain -> tek Kimlik. Dizi domaini raw_seq yolundan; operator domaini
    dogrudan operator ozdeger+ozvektorden gecer."""
    if domain in DIZI_DOMAINLERI:
        seq = _sayisallastir(veri, domain)
        A = seq_to_A(seq)
        _, lam, _ = gram_spectrum(A)
        av = yasa_avcisi(seq)                       # hiyerarsik av: c-finite -> holonomik -> yasasiz
        law, seed = av["law"], av["seed"]
        coord, _ = _coord_full(lam, seq=seq,
                               law=law if len(law) else None,
                               roots=seed if len(seed) else None)
        return Kimlik(name, domain, A, lam, coord, law=law, seed=seed,
                      sigma=av["sigma"], order=av["order"], seq=seq,
                      seviye=av["seviye"], holo=av["holo"], derece=av["derece"])

    if domain in OPERATOR_DOMAINLERI:
        # veri = (atoms, X)  ya da  (atoms, bonds, EN) — molekul
        if len(veri) == 2:
            atoms, X = veri
            A = dn.coulomb(atoms, np.asarray(X, float))
            coords3d = np.asarray(X, float)
        else:
            atoms, bonds, EN = veri
            A = A_molecule(atoms, bonds, EN)
            coords3d = None
        lam, V = dn.operator_identity(A)
        lam = np.sort(np.clip(lam, 0, None))[::-1]    # coord_91 azalan >=0 bekler
        coord, _ = _coord_full(lam)                 # operator domaininde dizi yok: statik+
        return Kimlik(name, domain, A, lam, coord, V=V, types=list(atoms),
                      coords3d=coords3d)

    raise ValueError(f"bilinmeyen domain: {domain}")


# ── 2) KOPRU (ortak uzay) ───────────────────────────────────────────────────────
# coord_91 tek bir mesafe DEGIL — cok-acili bir panel. Her acidan (facet) ayri
# es-kimlik sorulabilir. "Ayni yasa" bunlardan yalnizca biridir (ISKELET aci).
# Ham 91-mesafe yaniltir (bir blok boyut sayisiyla ezer); 'benzerlik' facet-ortalamasi.
#
# Facet'ler kaba blok-araligindan DEGIL, kablolama.py'den gelir: her dim TEK TEK
# gercek matematiksel rolune kablolanmistir (tam bolusum, 91 dim / 9 rol).
from kablolama import ROL as FACET, DIM as DIM_HARITA, TEKRAR, DINAMIK

def facet_mesafe(k1: Kimlik, k2: Kimlik, facet: str) -> float:
    """Tek bir acidan (facet) coord_91 mesafesi — 'hangi anlamda benzer?'"""
    idx = FACET[facet]
    return float(np.linalg.norm(k1.coord[idx] - k2.coord[idx]))

def benzerlik(k1: Kimlik, k2: Kimlik) -> dict:
    """Tam panel dokumu: her acidan mesafe + iskelet (yasa) bayragi.
    Kopru'nun asil urunu — tek skalar degil, cok-acili es-kimlik profili."""
    prof = {f: facet_mesafe(k1, k2, f) for f in FACET}
    prof["iskelet(yasa)"] = 0.0 if ayni_yasa(k1, k2) else 1.0
    return prof

def mesafe(k1: Kimlik, k2: Kimlik, facet=None) -> float:
    """Kalibre panel mesafesi: facet-ortalamasi (blok domine edemez).
    facet verilirse yalniz o aciyi olcer; None ise tum acilarin ortalamasi.
    Ham 91-oklit icin 32. dim... degil — kasitli olarak facet-ortalamasi."""
    if facet is not None:
        return facet_mesafe(k1, k2, facet)
    return float(np.mean([facet_mesafe(k1, k2, f) for f in FACET]))

def ham_mesafe(k1: Kimlik, k2: Kimlik) -> float:
    """Ham 91-oklit (paradigma blogu domine eder — kiyas/teshis icin)."""
    return float(np.linalg.norm(k1.coord - k2.coord))

def ayni_yasa(k1: Kimlik, k2: Kimlik, tol=1e-6) -> bool:
    """ISKELET acisi: iki nesne ayni kanonik yasaya mi iniyor? (facet'lerden biri)"""
    a, b = np.asarray(k1.law, float), np.asarray(k2.law, float)
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return False
    return bool(np.max(np.abs(a - b)) < tol)

def kopru(hedef: Kimlik, aday_kimlikler, k=1, facet=None):
    """Ortak uzayda hedefe en yakin adaylar — domain fark etmez.
    facet=None: kalibre panel-ortalamasi. facet='kaos'/'kritiklik'/...: o acidan.
    Cok-acili sorgu: 'kritiklikte ayni' ile 'kaosta ayni' farkli komsu dondurebilir."""
    sirali = sorted(aday_kimlikler, key=lambda a: mesafe(hedef, a, facet=facet))
    return sirali[:k]


# ── 3) COZ (de novo — tersine tasarim) ──────────────────────────────────────────
def coz(cep, adim=4000, name="denovo"):
    """Istenen cep/farmakofor -> gecerli 3D nesne -> Kimlik. Ters yon + arama."""
    sc, types, X = dn.de_novo(cep, adim=adim)
    ok, baglar = dn.gecerli(types, X)
    kim = kodla((types, X), domain="molecule", name=name)
    return dict(kimlik=kim, skor=float(sc), gecerli=bool(ok),
                bag_sayisi=len(baglar), types=types, X=X)


# ── 4) OUROBOROS (kapali dongu — kimligi koruyarak geri kur) ─────────────────────
def ouroboros(k: Kimlik):
    """Nesne -> kimlik -> nesne. Kimlik korunuyor mu? Yilan kuyrugunu yiyor mu?

    Dizi domaini : yasa+seed -> diziyi geri kur (+ genislet). Metrik: recon_err.
    Operator dom.: tam operator (Gram=ozdeger+ozvektor) -> MDS -> 3D. Metrik: RMSD.
    """
    if k.domain in DIZI_DOMAINLERI:
        if k.seviye == "holonomik":
            # n'e bagli yasa: ilk r terimden diziyi + bir adim otesini kur
            uz = holonomik_ac(k.holo, k.seq[:k.order], len(k.seq) + 1)
            if uz is None:
                return dict(kapali=False, sebep="yasa tekil", recon_err=float("inf"))
            rebuilt, otesi = uz[:len(k.seq)], float(uz[-1])
            rel = float(np.max(np.abs(rebuilt - k.seq) / (np.abs(k.seq) + 1e-12)))
            k2 = kodla(rebuilt, domain="math", name=k.name + "'")
            return dict(kapali=rel < 1e-6, recon_err=rel,
                        yasa_korundu=(k2.seviye == "holonomik" and k2.order == k.order),
                        bir_adim_otesi=otesi)
        if k.order == 0 or k.law.size == 0:
            return dict(kapali=False, sebep="yasasiz", recon_err=float("inf"))
        o = k.order
        s = list(k.seq[:o])
        for _ in range(len(k.seq) - o):
            s.append(float(np.dot(k.law, s[-o:][::-1])))
        rebuilt = np.array(s[:len(k.seq)])
        err = float(np.max(np.abs(rebuilt - k.seq)))
        genis = [float(np.dot(k.law, (list(rebuilt) + s)[-o:][::-1]))]  # bir adim otesi
        # geri kurulandan kimligi yeniden cikar: yasa korunuyor mu?
        k2 = kodla(rebuilt, domain="math", name=k.name + "'")
        return dict(kapali=err < 1e-6, recon_err=err,
                    yasa_korundu=ayni_yasa(k, k2, tol=1e-4),
                    bir_adim_otesi=genis[0])

    if k.domain in OPERATOR_DOMAINLERI:
        if k.coords3d is None:
            return dict(kapali=False, sebep="3D konum yok")
        D = np.linalg.norm(k.coords3d[:, None] - k.coords3d[None], axis=2)
        Xrec = dn.mds(D)                              # tam operator -> 3D
        rmsd = float(dn.hizala(k.coords3d, Xrec))
        # geri kurulandan kimligi yeniden cikar
        k2 = kodla((k.types, Xrec), domain="molecule", name=k.name + "'")
        spek_fark = float(np.max(np.abs(np.sort(k.lam) - np.sort(k2.lam))))
        return dict(kapali=rmsd < 1e-6, rmsd=rmsd, spektrum_farki=spek_fark)

    return dict(kapali=False, sebep="bilinmeyen domain")


# ── DEMO: dort fiil tek akista ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*70); print(" TEK OMURGA — kodla / kopru / coz / ouroboros"); print("="*70)

    # KODLA — dort domain tek dile iner
    fib = [1.,1.,2.,3.,5.,8.,13.,21.,34.,55.]
    k_math = kodla(fib, "math", "fibonacci")
    k_dna  = kodla("ATG"*7, "dna", "kodon-dna")
    k_rna  = kodla("AUG"*7, "rna", "kodon-rna")
    k_prot = kodla("GPA"*7, "protein", "kodon-protein")
    for k in (k_math, k_dna, k_rna, k_prot):
        print("  KODLA", k.kisa())

    # KOPRU — periyot-3 hepsi ayni yasada bulusuyor
    print("\n  KOPRU (cross-space, periyot-3):")
    print(f"    dna=rna yasa? {ayni_yasa(k_dna,k_rna)}   d={mesafe(k_dna,k_rna):.2e}")
    print(f"    dna=protein yasa? {ayni_yasa(k_dna,k_prot)}   d={mesafe(k_dna,k_prot):.2e}")

    # COZ — cep -> yeni molekul
    cep = [(np.array([0.,0.,0.]),'N'),(np.array([1.4,0.2,0.]),'C'),
           (np.array([2.6,1.,0.]),'O'),(np.array([1.2,2.2,.4]),'C'),(np.array([0.,1.6,.3]),'C')]
    r = coz(cep, adim=2000)
    print(f"\n  COZ (de novo): {r['types']}  skor={r['skor']:.2f}  gecerli={r['gecerli']}")
    print("       ", r["kimlik"].kisa())

    # OUROBOROS — dongu kapaniyor mu
    print("\n  OUROBOROS:")
    o_math = ouroboros(k_math)
    print(f"    math (fib): kapali={o_math['kapali']} recon_err={o_math['recon_err']:.1e} "
          f"yasa_korundu={o_math['yasa_korundu']} otesi={o_math['bir_adim_otesi']:.0f}")
    o_mol = ouroboros(r["kimlik"])
    print(f"    molecule  : kapali={o_mol['kapali']} rmsd={o_mol.get('rmsd',float('nan')):.1e} "
          f"spektrum_farki={o_mol.get('spektrum_farki',float('nan')):.1e}")
    print("\n"+"="*70); print(" Dort fiil tek omurgada. Dongu kapali."); print("="*70)
