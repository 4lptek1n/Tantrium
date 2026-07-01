"""
manipule.py — MANIPULE organi: kurulan evreni AMACA gore bukmek.

Arka beyin evreni yasa+seed olarak kurar/saklar. Bu organ evreni MOD UZAYINDA
tutar:  s[k] = Re( Σ_j a_j · z_j^k )   —  z: kokler (moda), a: genlikler.
Mod uzayinda bizim evrenimizin izin verdigi isler dogal operator olur:

  ZAMAN        z^k her tamsayi k icin tanimli -> zaman IKI YONDE akar
  SUPERPOZISYON iki evrenin birlesimi = mod kumelerinin birlesimi (yasa carpimi)
  MOD CERRAHISI bir modu sondur/guclendir (a_j), yavaslat/hizlandir (|z_j|)
  KRITIKLESTIR  kokleri birim cembere tasi (|z|=1) — kayipsiz/sonsuz-omur rejimi
  HEDEFE BUK    amac = hedef panel degerleri (91 dim) -> kok/genlik uzayinda ara

Panel (coord_91) kokpittir: her mudahaleden sonra gostergeler fizigin dedigi
yonde oynamali — testler tam bunu olcer. Manipule edilen evren yine yasa+seed
olarak saklanir (sinif kapali: C-finite evren C-finite kalir).

DURUSTLUK: bu organ C-finite evren sinifinde calisir (lineer rekurans dunyasi).
Dogrusal-olmayan evrenler yasa hiyerarsisini bekler (ARCHITECTURE.md Faz 2).
"""
from dataclasses import dataclass
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from domains import extract_law


# ── EVREN: mod uzayi temsili ─────────────────────────────────────────────────
@dataclass
class Evren:
    z: np.ndarray     # kokler (kompleks) — evrenin modlari
    a: np.ndarray     # genlikler (kompleks) — modlarin agirligi

    @property
    def order(self):
        return len(self.z)

    def yasa(self):
        """Koklerden rekurans katsayilari: x^p - c1 x^{p-1} - ... - cp."""
        pol = np.real_if_close(np.poly(self.z))
        return -np.real(pol[1:])

    def acilim(self, n, n0=0):
        """Evreni [n0, n0+n) zaman penceresinde ac. n0<0 = GECMISE git."""
        ks = np.arange(n0, n0 + n)
        S = (self.a[None, :] * self.z[None, :] ** ks[:, None]).sum(1)
        return np.real(S)

    def kopya(self):
        return Evren(self.z.copy(), self.a.copy())


def evren_kur(seq, max_order=8):
    """Gozlenen diziden evreni kur: yasa -> kokler -> genlikler (Vandermonde)."""
    s = np.asarray(seq, float)
    c, roots, sigma, order = extract_law(s, max_order=max_order)
    if order == 0:
        return None, sigma
    z = np.asarray(roots, complex)[:order]
    V = z[None, :] ** np.arange(len(s))[:, None]          # V[k,j] = z_j^k
    a, *_ = np.linalg.lstsq(V, s.astype(complex), rcond=None)
    return Evren(z, a), float(sigma)


# ── mod gruplari: reel kok tek, eslenik cift birlikte (gerceklik korunur) ────
def _gruplar(z, tol=1e-9):
    gruplar, kullanildi = [], set()
    for i in range(len(z)):
        if i in kullanildi:
            continue
        if abs(z[i].imag) < tol:
            gruplar.append([i]); kullanildi.add(i)
        else:
            es = None
            for j in range(i + 1, len(z)):
                if j not in kullanildi and abs(z[j] - np.conj(z[i])) < 1e-6:
                    es = j; break
            gruplar.append([i, es] if es is not None else [i])
            kullanildi.add(i)
            if es is not None:
                kullanildi.add(es)
    return gruplar


# ── MANIPULASYON OPERATORLERI ────────────────────────────────────────────────
def zaman(e: Evren, n, n0=0):
    """Zaman evrimi — n0 negatifse gecmis. Mod uzayinda iki yon de bedava."""
    return e.acilim(n, n0)

def sondur(e: Evren, grup_no, oran=0.0):
    """Bir modu sondur/kis: genligi oranla carp (0 = tam sondurme)."""
    y = e.kopya()
    for i in _gruplar(y.z)[grup_no]:
        y.a[i] *= oran
    return y

def buk_yaricap(e: Evren, grup_no, oran):
    """Bir modu yavaslat/hizlandir: |z| -> |z|·oran (aci korunur, gerceklik korunur)."""
    y = e.kopya()
    for i in _gruplar(y.z)[grup_no]:
        y.z[i] *= oran
    return y

def kritiklestir(e: Evren):
    """Tum kokleri birim cembere tasi: |z|=1 — kayipsiz/sonsuz-omur rejimi."""
    y = e.kopya()
    r = np.abs(y.z)
    y.z = np.where(r > 1e-12, y.z / r, y.z)
    return y

def birlestir(e1: Evren, e2: Evren, tol=1e-8):
    """SUPERPOZISYON: iki evrenin mod birlesimi. Dizi toplami; yasa = poly carpimi."""
    z = np.concatenate([e1.z, e2.z]); a = np.concatenate([e1.a, e2.a])
    # ayni mod iki evrende varsa genlikler toplanir
    zt, at = [], []
    for zi, ai in zip(z, a):
        for k, zk in enumerate(zt):
            if abs(zi - zk) < tol:
                at[k] += ai; break
        else:
            zt.append(zi); at.append(ai)
    return Evren(np.array(zt), np.array(at))


# ── HEDEFE BUK: amac = hedef panel degerleri ─────────────────────────────────
def panel(e: Evren, n=24):
    """Evreni ac, yeniden kodla, kokpiti oku -> (coord_91, Kimlik)."""
    from beyin import kodla
    k = kodla(list(e.acilim(n)), "math", "evren")
    return k.coord, k

def hedefe_buk(e: Evren, hedef: dict, adim=250, n=24, rng=None):
    """Amaca gore evreni buk: hedef = {dim_index: istenen_deger}.
    Kok yaricaplari + genlikleri uzerinde rastgele yerel arama; panel hedefe
    yaklasana kadar. Doner: (yeni_evren, son_uzaklik, iz)."""
    rng = rng or np.random.default_rng(0)
    def uzaklik(ev):
        v, _ = panel(ev, n)
        return float(np.sqrt(sum((v[i] - t) ** 2 for i, t in hedef.items())))
    en = (uzaklik(e), e.kopya()); iz = [en[0]]
    for _ in range(adim):
        aday = en[1].kopya()
        g = _gruplar(aday.z)
        gi = int(rng.integers(len(g)))
        if rng.random() < 0.6:      # yaricap buk (yavaslat/hizlandir)
            oran = float(np.exp(rng.normal(0, 0.08)))
            for i in g[gi]:
                yeni = aday.z[i] * oran
                if abs(yeni) < 1.4:            # tasma korumasi
                    aday.z[i] = yeni
        else:                        # genlik buk
            oran = float(np.exp(rng.normal(0, 0.15)))
            for i in g[gi]:
                aday.a[i] *= oran
        d = uzaklik(aday)
        if d < en[0]:
            en = (d, aday)
        iz.append(en[0])
    return en[1], en[0], iz
