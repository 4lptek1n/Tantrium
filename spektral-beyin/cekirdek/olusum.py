"""
olusum.py — KENDILIGINDEN OLUSUM (self-assembly): tamamlayici parcalar bottom-up
kenetlenip ust olcek kurar. Atom -> molekul -> ... -> organizma, TEK yasayla.

Soru: "birbirini tamamlayan parcalar kendiliginden olusabilir mi?" — evet, tek bir
ilk-prensip yasayla, ve o yasa ISLADAN degil FIZIKTEN gelir:

  TAMAMLAYICILIK = BAGLANMA KARARLILIGI
    Iki parca, birleşince toplam ENERJI DUSERSE tamamlayicidir (bagli hal). Bag,
    sinir-orbitallerinin (HOMO/LUMO) etkilesiminden dogar — mo.py'nin Hückel'i ile
    AYNI dil: birleşik operatorun ozdegerleri = birleşik seviyeler; elektronlar en
    alta dolar; ΔE = E(birlesik) − E(A) − E(B) < 0 ise BAGLANIR (bonding stabilizasyonu).
    Tek-orbital cift icin analitik: ΔE = −2·√((Δε/2)² + t²) (H2: ε esit -> −2t).

  SONLU YAPI = VALANS DOYUMU
    Her parca sonlu 'acik slot' (valans) tasir; her bag birer slot yer. Slot bitince
    parca doyar (soygaz gibi) ve baglanmaz. Bu yuzden yapilar SONLU cikar (H2, H∞ degil)
    — dogadaki gibi. Tamamlayicilik enerjiyi, valans SAYIYI belirler.

  HIYERARSI = SPEKTRUMLARIN BIRLESIP YENI BIRIM OLMASI (olcek-bagimsiz)
    Baglanan cift, spektrumu birleşik seviyeler olan YENI bir parcadir (seviye+1). O da
    kendi sinir-orbitalleriyle daha ust birime katilir. Ayni yasa her olcekte. Panel
    (coord_91) her olusan birime kimlik verir — sayi dizisi, molekul, DNA hepsi ayni dile
    iner (beyin.kodla), dolayisiyla parcalar DOMAIN-KORÜ birleşir: bir dizi + bir molekul
    ayni tamamlayicilik yasasiyla kenetlenebilir.

DURUST SINIR: sinir-orbitali/tight-binding (FMO) modeli — YON ilk-prensip (bonding
stabilizasyonu, elektronegatiflik->orbital enerjisi, valans->sonluluk). Kupla buyuklugu
t model-birimi (mo.py Hückel β gibi); mutlak enerjiler deneysel kalibrasyon ister.
Atom seviyeleri illustratiftir; ASIL icerik YASADIR (tamamlayicilik+valans+hiyerarsi).
"""
from dataclasses import dataclass, field
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Toy element kutuphanesi: sinir-orbital enerjisi ε≈−elektronegatiflik (elektronegatif
# atom elektronu daha sikip tutar = daha dusuk/kararli orbital), valans = bag kapasitesi.
EN = {'H': 2.20, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98, 'S': 2.58, 'Ne': 4.60}
VALANS = {'H': 1, 'C': 4, 'N': 3, 'O': 2, 'F': 1, 'S': 2, 'Ne': 0}   # Ne = soygaz (doymus)


@dataclass
class Parca:
    """Bir olcek katmanindaki spektral birim: seviyeler + elektron + acik valans."""
    ad: str
    E: np.ndarray                       # enerji seviyeleri (artan)
    ne: int                             # elektron sayisi (cift dolum)
    valans: int                         # acik baglanma slotu (0 = doymus/inert)
    seviye: int = 0                     # olcek katmani (0 = atom)
    icerik: tuple = ()                  # bilesenler (alt Parca adlari) — hiyerarsi izi

    def _dolu(self):
        return self.ne // 2, self.ne % 2          # (cift-dolu seviye, tek elektron var mi)

    def homo(self):
        d, t = self._dolu()
        return int(np.clip(d - 1 + t, 0, len(self.E) - 1))

    def lumo(self):
        d, t = self._dolu()
        return int(np.clip(d + t, 0, len(self.E) - 1))

    def elektronik_enerji(self):
        d, t = self._dolu()
        e = 2.0 * float(np.sum(self.E[:d]))
        if t and d < len(self.E):
            e += float(self.E[d])
        return e

    def __repr__(self):
        return (f"<{self.ad} sv{self.seviye} E={np.round(self.E,2).tolist()} "
                f"ne={self.ne} val={self.valans}>")


def atom(sembol, ad=None):
    """Element sembolunden atom-parcasi: tek sinir-orbitali (ε=−EN), yari-dolu."""
    eps = -EN[sembol]
    return Parca(ad or sembol, np.array([eps]), ne=1, valans=VALANS[sembol],
                 seviye=0, icerik=(sembol,))


def kimlikten_parca(kimlik, ne, valans, ad=None):
    """Herhangi bir beyin.Kimlik'i (dizi/molekul/DNA) parcaya cevir — spektrumu seviye
    yapar. Ayni tamamlayicilik yasasi DOMAIN-KORÜ isler (sayi dizisi + molekul kenetlenir)."""
    E = np.sort(np.asarray(kimlik.lam, float))            # artan seviyeler
    return Parca(ad or kimlik.name, E, ne=ne, valans=valans, seviye=0,
                 icerik=(f"{kimlik.domain}:{kimlik.name}",))


def _birlesik_H(A: Parca, B: Parca, t):
    """A ve B'nin birleşik tek-parcacik Hamiltoniyeni: blok-kosegen seviyeler +
    sinir-orbitali kuplasi (HOMO_A↔LUMO_B ve LUMO_A↔HOMO_B). Doner: ozdegerler (artan)."""
    nA, nB = len(A.E), len(B.E)
    H = np.zeros((nA + nB, nA + nB))
    H[:nA, :nA] = np.diag(A.E)
    H[nA:, nA:] = np.diag(B.E)
    kanallar = {(A.homo(), B.lumo()), (A.lumo(), B.homo())}   # dedup (kovalent = tek kanal)
    for (a, b) in kanallar:
        H[a, nA + b] += t
        H[nA + b, a] += t
    return np.linalg.eigvalsh(H)


def baglanma_enerjisi(A: Parca, B: Parca, t=1.0):
    """ΔE = E_elektronik(birlesik) − E(A) − E(B). Negatif = bonding = tamamlayici.
    Doner: dict(dE, birlesik_E, ne)."""
    Ec = _birlesik_H(A, B, t)
    ne = A.ne + B.ne
    d, tk = ne // 2, ne % 2
    e = 2.0 * float(np.sum(Ec[:d])) + (float(Ec[d]) if tk and d < len(Ec) else 0.0)
    dE = e - A.elektronik_enerji() - B.elektronik_enerji()
    return dict(dE=float(dE), birlesik_E=Ec, ne=ne)


def tamamlayici(A: Parca, B: Parca, t=1.0):
    """A ve B birbirini tamamliyor mu? Bagli (dE<0) VE iki tarafta acik valans var.
    Doner: dict(tamamlayici, dE, sebep)."""
    b = baglanma_enerjisi(A, B, t)
    if A.valans <= 0 or B.valans <= 0:
        return dict(tamamlayici=False, dE=b["dE"], sebep="valans doymus (inert)")
    ok = b["dE"] < -1e-9
    return dict(tamamlayici=ok, dE=b["dE"],
                sebep="bonding (enerji dustu)" if ok else "antibonding (bagli hal yok)")


def birlestir(A: Parca, B: Parca, t=1.0):
    """Iki tamamlayici parcayi kenetle -> YENI ust-olcek parca. Spektrumu birleşik
    seviyeler; valans = valA+valB−2 (birer slot bag'a gitti); seviye = max+1."""
    b = baglanma_enerjisi(A, B, t)
    yeni_val = A.valans + B.valans - 2
    return Parca(ad=f"({A.ad}+{B.ad})", E=b["birlesik_E"], ne=b["ne"],
                 valans=max(0, yeni_val), seviye=max(A.seviye, B.seviye) + 1,
                 icerik=(A.ad, B.ad))


def kendiliginden_olus(havuz, t=1.0, max_adim=200):
    """KENDILIGINDEN OLUSUM DONGUSU: havuzdaki en tamamlayici cifti (en negatif dE)
    kenetle, yenisini havuza koy; tamamlayici cift kalmayana dek surdur.
    Tepeden tasarim YOK — parcalar kendi tamamlayanini bulur, kararlıysa baglanir,
    valans bitince durur. Doner: dict(birimler, adimlar, seviye_max, agac)."""
    havuz = list(havuz)
    adimlar = []
    for _ in range(max_adim):
        en = None
        for i in range(len(havuz)):
            for j in range(i + 1, len(havuz)):
                r = tamamlayici(havuz[i], havuz[j], t)
                if r["tamamlayici"] and (en is None or r["dE"] < en[0]):
                    en = (r["dE"], i, j)
        if en is None:
            break                                        # daha fazla tamamlayan yok -> denge
        dE, i, j = en
        A, B = havuz[i], havuz[j]
        yeni = birlestir(A, B, t)
        adimlar.append(dict(A=A.ad, B=B.ad, dE=dE, urun=yeni.ad, seviye=yeni.seviye))
        havuz = [p for k, p in enumerate(havuz) if k not in (i, j)] + [yeni]
    return dict(birimler=havuz, adimlar=adimlar,
                seviye_max=max((p.seviye for p in havuz), default=0))


def panel(parca: Parca):
    """Olusan birimin coord_91 kimligi — her olcek ayni evrensel dile iner."""
    from coord91 import coord_91_temiz
    s = np.sort(np.clip(parca.E - parca.E.min(), 0, None))[::-1]   # panel azalan >=0 bekler
    v, _ = coord_91_temiz(s)
    return v


def agac(parca: Parca, girinti=0):
    """Olusan birimin hiyerarsi agacini metin olarak ver (atomdan yukari)."""
    sat = "  " * girinti + f"sv{parca.seviye} {parca.ad}"
    return sat


if __name__ == "__main__":
    print("=" * 70)
    print(" KENDILIGINDEN OLUSUM — tamamlayici parcalar bottom-up olcek kurar")
    print("=" * 70)

    # 1) TEK BAG (analitik): H2 -> ΔE = −2t
    H1, H2 = atom('H', 'H1'), atom('H', 'H2')
    b = baglanma_enerjisi(H1, H2, t=1.0)
    print(f"\n[1] H + H:  ΔE={b['dE']:+.3f}  (analitik −2t=−2.000)  -> tamamlayici mi? "
          f"{tamamlayici(H1,H2)['tamamlayici']}")

    # 2) SOYGAZ baglanmaz (valans doymus)
    Ne = atom('Ne')
    print(f"[2] H + Ne: tamamlayici mi? {tamamlayici(atom('H'), Ne)['tamamlayici']}  "
          f"(soygaz inert — valans 0)")

    # 3) KENDILIGINDEN OLUSUM: bir atom havuzu kendi yapisini kurar
    print("\n[3] HAVUZ -> kendiliginden olusum (tepeden tasarim yok):")
    havuz = [atom('C', 'C1'), atom('O', 'O1'), atom('H', 'H1'), atom('H', 'H2'),
             atom('N', 'N1'), atom('O', 'O2')]
    print("    baslangic:", [p.ad for p in havuz])
    r = kendiliginden_olus(havuz, t=1.0)
    for a in r["adimlar"]:
        print(f"      kenetle {a['A']} + {a['B']}  (ΔE={a['dE']:+.2f})  -> {a['urun']} [sv{a['seviye']}]")
    print(f"    SONUC: {len(r['birimler'])} birim, en ust olcek = sv{r['seviye_max']}")
    for p in r["birimler"]:
        print(f"      {p}")

    # 4) HER OLUSAN BIRIM AYNI DILE INER (coord_91 kimligi)
    v = panel(r["birimler"][0])
    print(f"\n[4] olusan birimin coord_91 kimligi: shape={v.shape}, sonlu={np.all(np.isfinite(v))}")

    print("\n" + "=" * 70)
    print(" Tamamlayicilik enerjiyi, valans sonlulugu, spektrum hiyerarsi kurar.")
    print(" TEK yasa, her olcek. Domain-koru (beyin.kodla ile dizi+molekul ayni havuzda).")
    print("=" * 70)
