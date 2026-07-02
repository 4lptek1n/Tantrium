"""
sinir.py — SINIR / DEGISIM-NOKTASI organi (Tantrium'un spektral kapanisi).

Proje 'sistemin nerede kirildigini bul' diye basladi (Boundary Engine).
Arka beyin bunu SPEKTRAL yapar: bir seri boyunca kayan pencerede yasa uydur;
yasanin/duzenliligin BOZULDUGU nokta = sinir. Anomali + degisim + tahmin, tek organ.

Birlesim (yeni matematik yok):
  yasa-avcisi (hiyerarsi) × kayan pencere  -> her konumda 'yasalilik' skoru σ
  σ patlamasi                              -> degisim noktasi / sinir
  yasa oncesi                              -> guvenli rejim (safe envelope)
  bir-adim tahmin vs gercek                -> anomali (tek nokta sapmasi)

Iki kip:
  segment_sinirlari : yasa DEGISEN noktalar (rejim gecisleri)
  anomali_noktalari : yasaya UYMAYAN tek noktalar (aykiri degerler)
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hiyerarsi import yasa_avcisi, _cfinite_ac, polinom_ac, holonomik_ac


def _pencere_yasalilik(pencere):
    """Bir pencerenin yasalilik skoru: [0,1], 1=tam yasali. Seviye + σ birlesik."""
    av = yasa_avcisi(pencere)
    if av["seviye"] == "ham":
        return 0.0, av
    # sonsuz-kesin yasa: σ'yi skora cevir (küçük σ -> yüksek skor)
    sig = av["sigma"] if np.isfinite(av["sigma"]) else 1.0
    return float(np.exp(-sig * 20)), av


def segment_sinirlari(seri, pencere=8, esik=0.5):
    """Yasa DEGISEN noktalari bul (rejim gecisleri = sinirlar).

    Kayan pencerede yasalilik profili cikar; profil DUSTUGU yerler sinir.
    Doner: dict(sinirlar=[idx...], profil=[...], segmentler=[(bas,son,seviye)...])
    """
    s = np.asarray(seri, float)
    N = len(s)
    if N < 2 * pencere:
        return dict(sinirlar=[], profil=[], segmentler=[(0, N, "belirsiz")])
    profil, seviyeler = [], []
    for i in range(N - pencere + 1):
        skor, av = _pencere_yasalilik(s[i:i + pencere])
        profil.append(skor)
        seviyeler.append(av["seviye"] if skor > esik else "ham")
    profil = np.array(profil)
    # sinir: yuksek->dusuk gecisi (yasa bozuluyor) ya da seviye degisimi
    sinirlar = []
    for i in range(1, len(profil)):
        dustu = profil[i - 1] > esik and profil[i] <= esik
        seviye_degisti = (seviyeler[i] != seviyeler[i - 1]
                          and profil[i] > esik and profil[i - 1] > esik)
        if dustu or seviye_degisti:
            sinirlar.append(i + pencere // 2)      # pencere ortasina hizala
    # segmentler
    segmentler, bas = [], 0
    for b in sinirlar:
        segmentler.append((bas, b, seviyeler[min(bas, len(seviyeler) - 1)]))
        bas = b
    segmentler.append((bas, N, seviyeler[min(bas, len(seviyeler) - 1)]))
    return dict(sinirlar=sinirlar, profil=profil.tolist(), segmentler=segmentler)


def _ac(av, ilk, n):
    """Yasa seviyesine gore diziyi ac (tahmin icin)."""
    if av["seviye"] == "polinom":
        return polinom_ac(av["poli"], n)
    if av["seviye"] == "c-finite":
        return _cfinite_ac(av["law"], ilk[:av["order"]], n)
    if av["seviye"] == "holonomik":
        return holonomik_ac(av["holo"], ilk[:av["order"]], n)
    return None


def _ransac_law(s, o):
    """Robust sabit-katsayili rekurans: her ardisik minimal denklem kumesi bir
    aday law verir; kirli denklemler AZINLIKTA kalir, bilesenlerin MEDYANI saglam.
    Doner: law (uzunluk o) ya da None."""
    N = len(s)
    if N < 2 * o + 1:
        return None
    adaylar = []
    for i in range(o, N - o + 1):
        H = np.array([s[i + r - 1::-1][:o] for r in range(o)])   # o×o
        y = np.array([s[i + r] for r in range(o)])
        try:
            c = np.linalg.solve(H, y)
        except np.linalg.LinAlgError:
            continue
        if np.all(np.isfinite(c)):
            adaylar.append(c)
    if len(adaylar) < 2:
        return None
    return np.median(np.array(adaylar), axis=0)


def anomali_noktalari(seri, esik=4.0):
    """Yasaya UYMAYAN tek noktalar (aykiri deger tespiti).

    Robust rekurans (RANSAC-medyan) ile sabit-katsayili yasayi tek bozuk noktaya
    ragmen cikar; sonra bir-adim-ileri artik. En SEYREK anomali veren order secilir
    (Occam: gercek yasa en az noktayi 'aykiri' gosterir). Ilk indeks = kok anomali.
    """
    s = np.asarray(seri, float)
    N = len(s)
    en_iyi = None
    for o in (1, 2, 3):
        law = _ransac_law(s, o)
        if law is None:
            continue
        art = np.zeros(N)
        for n in range(o, N):
            art[n] = s[n] - float(np.dot(law, s[n - o:n][::-1]))
        mad = np.median(np.abs(art - np.median(art))) * 1.4826 + 1e-12
        z = np.abs(art) / mad
        idx = np.where(z > esik)[0]
        # skor: az sayida ama keskin anomali tercih (gercek yasa)
        skor = (len(idx), -float(np.max(z)) if len(z) else 0)
        if en_iyi is None or skor < en_iyi[0]:
            en_iyi = (skor, o, idx, z)
    if en_iyi is None or en_iyi[0][0] >= max(2, N // 2):
        # hicbir yasa seyrek anomali vermedi -> gercekten yasasiz: robust-z
        med = np.median(s)
        mad = np.median(np.abs(s - med)) * 1.4826 + 1e-12
        z = np.abs(s - med) / mad
        idx = np.where(z > esik)[0]
        return dict(indeksler=idx.tolist(), sapmalar=np.round(z[idx], 2).tolist(),
                    yasa="ham", yontem="robust-z")
    _, o, idx, z = en_iyi
    return dict(indeksler=idx.tolist(), sapmalar=np.round(z[idx], 2).tolist(),
                yasa=f"rekurans-order-{o}", yontem="ransac-bir-adim")


def sinir_raporu(seri, pencere=8):
    """Tantrium-tarzi butun rapor: guvenli rejim + ilk kirilma + surucu + tahmin.
    Cekirdek fiillerin birlesimiyle orijinal urunun spektral hali."""
    s = np.asarray(seri, float)
    seg = segment_sinirlari(s, pencere=pencere)
    anom = anomali_noktalari(s)
    ilk_kirilma = seg["sinirlar"][0] if seg["sinirlar"] else None
    # guvenli rejim = ilk segmentin yasasi
    b0, s0, sev0 = seg["segmentler"][0]
    guvenli_av = yasa_avcisi(s[b0:s0]) if s0 - b0 >= 6 else {"seviye": "belirsiz"}
    # tahmin: son segmentin yasasindan bir adim
    bl, sl, sevl = seg["segmentler"][-1]
    son_av = yasa_avcisi(s[bl:sl]) if sl - bl >= 6 else {"seviye": "ham"}
    otesi = None
    if son_av.get("seviye") not in ("ham", "belirsiz"):
        uz = _ac(son_av, s[bl:sl], sl - bl + 1)
        if uz is not None:
            otesi = float(uz[-1])
    return dict(
        guvenli_rejim=guvenli_av["seviye"],
        ilk_kirilma=ilk_kirilma,
        kirilma_sayisi=len(seg["sinirlar"]),
        segmentler=seg["segmentler"],
        anomali_indeksleri=anom["indeksler"],
        sonraki_tahmin=otesi,
    )
