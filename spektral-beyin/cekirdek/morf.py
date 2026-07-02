"""
morf.py — UZAY MANIPULE: iki evren arasi surekli gecis (panel-uzayi morphing).

91 dim matematiginin ICINDEN: gecerli momentler bir KONVEKS koni olusturur
(Hankel-PSD kumesi konvekstir). Dolayisiyla iki gecerli nesnenin momentlerini
DOGRUSAL interpole edince — μ(t) = (1−t)μ_A + t·μ_B — ara momentler HER t'de
gecerli kalir. Yani panel-uzayindaki dogru parcasi bastan sona GECERLI nesneler
uretir; her ara adim gercek bir spektrum. Bu, morphing'in kayipsiz garantisidir.

Iki morphing koordinati (ayni evrenin iki yuzu):
  panel-uzayi (moment)  : morf_panel — konveks, her adim garantili gecerli
  mod-uzayi (kok+genlik) : morf_mod  — yasali nesneler icin (manipule.py ustune)

Fark: panel morphing her spektrum icin calisir (yasa gerekmez); mod morphing
yasa+seed tasiyan nesnelerde 'zaman/dinamik' anlamli gecis verir.

Iliski: panel_ters (moment<->spektrum) + moment koni konveksligi. Yeni matematik
yok — mevcut iki gercegin birlesimi. (manipule.hedefe_buk TEK hedefe buker;
bu A→B YORUNGESI verir — farkli sey, duplikasyon degil.)
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_ters import spektrum_momentleri, spektrum_geri, moment_gecerli


def morf_panel(spek_A, spek_B, adim=11, kac_moment=None):
    """Panel-uzayinda A→B morphing: momentleri interpole et, her adimda spektrum kur.
    Konveks koni: her ara adim GECERLI. Doner: dict(yol=[spektrum...], gecerli_hepsi).
    Uzunluklar esitse atom-atom; degilse ortak n=min uzerinden."""
    A = np.sort(np.clip(np.asarray(spek_A, float), 0, None))[::-1]
    B = np.sort(np.clip(np.asarray(spek_B, float), 0, None))[::-1]
    n = min(len(A), len(B))
    A, B = A[:n], B[:n]
    K = kac_moment if kac_moment is not None else 2 * n + 1
    muA, lA = spektrum_momentleri(A, K)
    muB, lB = spektrum_momentleri(B, K)
    yol, gecerli_hepsi = [], True
    for t in np.linspace(0.0, 1.0, adim):
        mu = (1 - t) * muA + t * muB
        lmax = (1 - t) * lA + t * lB
        g, _ = moment_gecerli(mu, n)
        gecerli_hepsi = gecerli_hepsi and g
        yol.append(spektrum_geri(mu, n, lmax))
    return dict(yol=yol, gecerli_hepsi=bool(gecerli_hepsi), n=n)


def morf_mod(evren_A, evren_B, adim=11):
    """Mod-uzayinda A→B morphing: kok ve genlikleri interpole et (eslesik moda gore).
    Yasali nesneler icin 'dinamik' gecis (evren yavasca B'ye donusur).
    NOT: temiz eslesme AYNI mertebe (mod sayisi) nesneler icindir; farkli mertebede
    ortak min mod'a kirpilir (uclar tam A/B olmaz — panel morphing'i tercih et).
    evren_A, evren_B: manipule.Evren. Doner: [Evren...] yol."""
    from manipule import Evren
    zA, aA = np.sort_complex(evren_A.z), evren_A.a
    zB, aB = np.sort_complex(evren_B.z), evren_B.a
    m = min(len(zA), len(zB))
    # en yakin-mod eslesmesi (basit: buyukluge gore sirala, ilk m)
    zA, aA = zA[:m], aA[:m]; zB, aB = zB[:m], aB[:m]
    yol = []
    for t in np.linspace(0.0, 1.0, adim):
        z = (1 - t) * zA + t * zB
        a = (1 - t) * aA + t * aB
        yol.append(Evren(z, a))
    return yol


def morf_kimlik(kimlik_A, kimlik_B, adim=11):
    """Iki Kimlik arasi panel-morphing + her ara nesnenin evrensellik sinifini izle.
    'A'dan B'ye giderken sistem hangi rejimlerden geciyor?' — uzay-yolu analizi."""
    from dualite import evrensellik
    r = morf_panel(kimlik_A.lam, kimlik_B.lam, adim=adim)
    siniflar = []
    for spek in r["yol"]:
        s = spek[spek > 1e-12]
        siniflar.append(evrensellik(s)[0] if len(s) >= 4 else "AZ-MOD")
    return dict(yol=r["yol"], gecerli_hepsi=r["gecerli_hepsi"], sinif_yolu=siniflar)
