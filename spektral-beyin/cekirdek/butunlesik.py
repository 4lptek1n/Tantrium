"""
butunlesik.py — TUM FIZIK ORGANLARI TEK AKISTA + BIRLESIK SPEKTRAL KAPI.

Fizik organlari (geometri, mo, serbest_enerji, kinetik) birbirine baglanir; molekul
tek akista uctan uca cozulur. Ve hepsi TEK KARARDA birlesir: yasayabilir ilac =
her organin spektral kararlilik kosulu ayni anda saglanir. Bu 'kritik cizgi'nin
gercek anlami — tum ilgili ozdegerler dogru tarafta:

  GEOMETRI  : kararli minimum   ⟺ Hessian ozdegerleri > 0 (eyer degil, gercek cukur)
  MO        : elektronik kararli ⟺ HOMO-LUMO araligi > 0 (kapali kabuk)
  VAROLUS   : gecerli molekul    ⟺ valans + cakismasiz (moment/pozitiflik)
  KINETIK   : temizlenir         ⟺ dispozisyon λ'lari kritik cizgi ICINDE (Re<0,
              yani z=e^λ birim cemberin ICI |z|<1). |z|=1 UZERI = hic temizlenmez
              = sonsuz birikim = TOKSIK. Yani ilac icin manipule.kritiklestir'in TERSI.

Tek mod-uzayi tum organlari birlestirir: sayi dizisi, elektronik modlar, PK bolmeleri,
titresim (Hessian) — hepsi ayni 'operator -> spektrum -> karar' fiili.

DURUST SINIR: her organin kendi sinirini tasir (klasik MM, Hückel, kismi hiz sabiti);
ama BIRLESIK KAPI ilkesi tam ve ilk-prensip: kararlilik = spektral pozitiflik.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometri import gevset, mm_enerji
from mo import homo_lumo
from kinetik import pk_operator, dispozisyon
import kimya


def _hessian_ozd(types, X, baglar, h=1e-4):
    """Gevsemis yapinin Hessian ozdegerleri. 6 ~sifir mod (oteleme+donme) haric
    kalanlar > 0 ise gercek minimum (eyer degil)."""
    x0 = np.asarray(X, float).ravel()
    n = len(x0)
    def E(x):
        return mm_enerji(types, x.reshape(-1, 3), baglar)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            xpp = x0.copy(); xpp[i] += h; xpp[j] += h
            xpm = x0.copy(); xpm[i] += h; xpm[j] -= h
            xmp = x0.copy(); xmp[i] -= h; xmp[j] += h
            xmm = x0.copy(); xmm[i] -= h; xmm[j] -= h
            H[i, j] = H[j, i] = (E(xpp) - E(xpm) - E(xmp) + E(xmm)) / (4*h*h)
    return np.linalg.eigvalsh(H)


def _pi_komsu(types, baglar):
    """Konjuge (C/N/O) atomlar arasi baglardan Hückel π-komsu matrisi + π-elektron."""
    konj = [i for i, t in enumerate(types) if t in ('C', 'N', 'O', 'S')]
    idx = {a: k for k, a in enumerate(konj)}
    m = len(konj)
    A = np.zeros((m, m))
    for i, j in baglar:
        if i in idx and j in idx:
            A[idx[i], idx[j]] = A[idx[j], idx[i]] = 1.0
    from mo import PI_ELEKTRON
    pe = sum(PI_ELEKTRON.get(types[a], 0) for a in konj)
    return A, pe, m


def fizik_akisi(types, X, baglar, k_elim=0.2, gecisler=None, n_bolme=1,
                C0=None, tox_esik=None):
    """Molekulu TUM organlardan gecir: geometri -> mo -> kinetik. Spektrumlari topla."""
    # 1. GEOMETRI: kendi enerji minimumuna gevset
    Xf, E_geo, iz = gevset(types, X, baglar)
    hess = _hessian_ozd(types, Xf, baglar)
    neg_mod = int(np.sum(hess < -0.5))            # anlamli negatif = eyer noktasi

    # 2. VAROLUS: valans + cakisma. Molekulun kimligi BAG GRAFI (verilen topoloji);
    #    gevseme sonrasi baglari mesafeden yeniden turetmek yanlis (topolojiyi bozar,
    #    yalanci bag/valans asimi uretir). Valans verilen topolojiye gore olculur;
    #    bag mertebesi sadece o topolojinin ciftleri icin mesafeden okunur.
    if baglar:
        B = {}
        for (i, j) in baglar:
            a, b2 = (i, j) if i < j else (j, i)
            r = float(np.linalg.norm(Xf[a] - Xf[b2]))
            rc = kimya.RCOV[types[a]] + kimya.RCOV[types[b2]]
            ratio = r / rc
            B[(a, b2)] = 3 if ratio < 0.80 else (2 if ratio < 0.91 else 1)
        valans_ok = kimya.gecerli_valans(types, B)
        bag_kume = {(min(i, j), max(i, j)) for (i, j) in baglar}
    else:
        B = kimya.bag_dereceleri(types, Xf)
        valans_ok = kimya.gecerli_valans(types, B)
        bag_kume = set(B.keys())
    # cakisma: SADECE bagsiz ciftler klerens altinda (bagli ciftler zaten yakin=normal)
    cakisma = False
    if len(Xf) > 1:
        D = np.linalg.norm(Xf[:, None] - Xf[None], axis=2)
        for a in range(len(Xf)):
            for b2 in range(a + 1, len(Xf)):
                if (a, b2) not in bag_kume and D[a, b2] < 0.9:
                    cakisma = True
                    break
            if cakisma:
                break

    # 3. MO: HOMO-LUMO (π-sistem). π-sistem yoksa elektronik kararlilik VAROLUSSAL
    #    olarak saglanir (doymus kapali-kabuk = buyuk gap); sadece π varken anti-
    #    aromatik kucuk gap kararsizlik isaretidir.
    A, pe, m = _pi_komsu(types, baglar)
    pi_var = bool(m >= 2 and pe >= 2)
    hl = homo_lumo(A, pe) if pi_var else dict(gap=float("nan"), homo=None)

    # 4. KINETIK: PK operatoru, dispozisyon
    K = pk_operator(k_elim, gecisler=gecisler, n_bolme=n_bolme)
    lam_pk, yari = dispozisyon(K)

    return dict(X=Xf, E_geo=E_geo, hessian=hess, neg_mod=neg_mod,
                valans_ok=valans_ok, cakisma=cakisma,
                homo_lumo=hl.get("gap"), pi_var=pi_var,
                pk_lambda=lam_pk, yari_omur=float(yari.max()),
                C0=C0, tox_esik=tox_esik, K=K)


def yasam_kapisi(akis):
    """BIRLESIK SPEKTRAL KAPI: yasayabilir ilac mi? Her organ bir ozdeger kosulu.
    Doner: dict(yasayabilir, kosullar{...}) — hangisi gecti hangisi kaldi."""
    kos = {}
    kos["geometri_kararli"] = akis["neg_mod"] == 0            # Hessian: eyer yok
    kos["varolus"] = bool(akis["valans_ok"] and not akis["cakisma"])
    g = akis["homo_lumo"]
    # π-sistem varsa gap>0 sart; π yoksa (doymus) elektronik kararlilik vacuously OK
    kos["mo_kararli"] = bool((not akis.get("pi_var", g is not None))
                             or (g is not None and np.isfinite(g) and g > 1e-6))
    kos["kinetik_temizlenir"] = bool(np.all(akis["pk_lambda"].real < 0))     # kritik cizgi ICI
    kos["kritik_cizgi_ici"] = bool(np.all(np.abs(np.exp(akis["pk_lambda"])) < 1.0))  # |z|<1
    yasayabilir = all(kos.values())
    return dict(yasayabilir=yasayabilir, kosullar=kos)


# ── TEK CAGRI: molekul -> uctan uca fizik raporu + tek karar ─────────────────
def ilac_yasar_mi(types, X, baglar, k_elim=0.2, gecisler=None, n_bolme=1,
                  C0=None, tox_esik=None, cep=None):
    """UCTAN UCA: bir molekulu tum fizik organlarindan gecir, tek KARAR + rapor ver.

    Organlar: geometri (3D gevseme) -> mo (HOMO-LUMO) -> serbest_enerji (baglanma,
    cep verilirse) -> kinetik (PK/toksisite) -> BIRLESIK SPEKTRAL KAPI.
    Doner: dict(yasayabilir, kosullar, olcumler, ozet).
    """
    akis = fizik_akisi(types, X, baglar, k_elim=k_elim, gecisler=gecisler,
                       n_bolme=n_bolme, C0=C0, tox_esik=tox_esik)
    kapi = yasam_kapisi(akis)

    olcum = dict(
        E_geometri=akis["E_geo"],
        HOMO_LUMO=akis["homo_lumo"],
        yari_omur=akis["yari_omur"],
        dispozisyon_hizlari=[complex(z) for z in akis["pk_lambda"]],
    )
    # ELEKTRONIK REAKTIFLIK (mo.py, HSAB): sertlik/yumusaklik -> reaktif-metabolit oncusu
    if akis["homo_lumo"] is not None and np.isfinite(akis["homo_lumo"]):
        from mo import kimyasal_reaktiflik
        rx = kimyasal_reaktiflik(akis["homo_lumo"])
        olcum["reaktiflik_indeksi"] = rx["reaktiflik_indeksi"]   # benzen=1.0; >1 daha reaktif
        olcum["sertlik"] = rx["sertlik"]
    # baglanma (cep verilirse) — serbest enerji + sterik
    if cep is not None:
        from serbest_enerji import baglanma_serbest_enerji
        from dock_dogrula import sterik_itme
        cep_t, cep_X = cep
        dF = baglanma_serbest_enerji(cep_t, cep_X, types, akis["X"], beta=0.1)
        olcum["baglanma_dF"] = float(dF + sterik_itme(cep_t, cep_X, types, akis["X"]))
    # toksisite (doz+esik verilirse)
    if C0 is not None and tox_esik is not None:
        from kinetik import toksisite_zaman
        tox = toksisite_zaman(akis["K"], np.atleast_1d(C0), tox_esik)
        olcum["toksik"] = tox["toksik"]
        olcum["tox_ilk_asma"] = tox["ilk_asma_zamani"]
    # REAKTIF-METABOLIT YUKU: elektronik reaktiflik (HOMO-LUMO) × maruziyet (AUC).
    # Toksisitenin fiziksel oncusu — mo.py'nin sertligi kinetik maruziyete baglanir.
    if C0 is not None and akis["homo_lumo"] is not None and np.isfinite(akis["homo_lumo"]):
        from kinetik import reaktif_metabolit_yuku
        rm = reaktif_metabolit_yuku(akis["K"], np.atleast_1d(C0), akis["homo_lumo"])
        olcum["reaktif_metabolit_yuku"] = rm["yuk"]
        olcum["bioaktivasyon_hizi"] = rm["bioaktivasyon_hizi"]

    gecti = [k for k, v in kapi["kosullar"].items() if v]
    kaldi = [k for k, v in kapi["kosullar"].items() if not v]
    ozet = (f"{'YASAYABILIR' if kapi['yasayabilir'] else 'YASAYAMAZ'} | "
            f"gecen: {len(gecti)}/{len(kapi['kosullar'])}"
            + (f" | kalan: {kaldi}" if kaldi else ""))
    return dict(yasayabilir=kapi["yasayabilir"], kosullar=kapi["kosullar"],
                olcumler=olcum, ozet=ozet)


# ── UCTAN UCA URETIM: uret -> gercek geometriye gevset -> BIRLESIK KAPI ile suz ──
def de_novo_yasayabilir(cep_t, cep_X, n_aday=5, adim=1500, k_elim=0.2,
                        C0=None, tox_esik=None, max_atom=12):
    """Ureticiyi fizik akisina BAGLAR: cep -> ilac_v2.ara (kimya-bilincli uretim)
    -> geometri.gevset (uretici ham yapiyi GERCEK enerji minimumuna gevset)
    -> ilac_yasar_mi (BIRLESIK SPEKTRAL KAPI) -> yalniz YASAYABILIR molekulleri dondur.

    Uretici artik korlemesine skor optimize etmiyor; her aday gercek 3D'ye gevser ve
    tum organ kararlilik kosulundan (geometri+mo+varolus+kinetik) gecmek zorunda.
    Doner: dict(uretilen, yasayabilir_sayi, yasayanlar[...], tum_adaylar[...])."""
    from ilac_v2 import ara
    import kimya
    adaylar = []
    buyuk_atlanan = 0
    for _ in range(n_aday):
        e, types, X = ara(cep_t, cep_X, adim=adim)
        X = np.asarray(X, float)
        if len(types) < 2:
            continue
        if len(types) > max_atom:
            buyuk_atlanan += 1          # Hessian O(n⁴) pahali; buyuk aday elenir (durust: atlandi, gizlenmedi)
            continue
        # uretici SABIT topolojisi (bag grafi = molekulun kimligi); gevseme bunu korur,
        # yeniden algilamaz — yoksa gevseme yalanci bag/valans uretir.
        Bgen = kimya.bag_dereceleri(types, X)
        baglar = list(Bgen.keys())
        if not baglar:
            continue
        # uretici ham yapiyi SABIT topolojiyle gercek enerji minimumuna gevset
        Xf, E_geo, _ = gevset(types, X, baglar)
        r = ilac_yasar_mi(types, Xf, baglar, k_elim=k_elim, C0=C0, tox_esik=tox_esik,
                          cep=(cep_t, cep_X))
        r["types"] = list(types)
        r["X"] = Xf
        r["uretim_enerji"] = float(e)
        adaylar.append(r)
    yasayanlar = [a for a in adaylar if a["yasayabilir"]]
    return dict(uretilen=len(adaylar), yasayabilir_sayi=len(yasayanlar),
                yasayanlar=yasayanlar, tum_adaylar=adaylar,
                buyuk_atlanan=buyuk_atlanan)
