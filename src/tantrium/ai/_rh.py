"""Tantrium AI — RH / serbest-olasılık yüzeyi (RHMixin).

rh_criteria / rh_certificate / rh_distance / jensen / hyperbolic / bezoutian /
free_entropy / semicircle_distance / seal / verify.
"""
from __future__ import annotations

from tantrium.core.rh_criteria import RHCriteria


class RHMixin:
    """Riemann-Hipotezi türevli pozitiflik kriterleri + serbest olasılık + mühür."""

    def universe(self, seed, full: bool = True) -> "object":
        """Bir girdiden EKSİKSİZ EVRENİ doğur — yedi yüz, tek mühür.

        1 madde · 2 fizik (4 katman) · 3 geometri (NCG boyut/etki) · 6 zaman (Cosmos) ·
        7 topoloji. Tam İLİŞKİ (kuvvet+hayat+topoloji) için u.couple(other)→Relation.
        Makine = evren üreteci (üç eksen: tek operatör · ilişki · evrim).

            u = ai.universe("EGFR"); print(u.summary()); print(u.couple("CCO").summary())
        """
        from tantrium.universe import universe
        return universe(seed, full=full)

    def relate(self, a, b) -> "object":
        """İki yapı arası TAM İLİŞKİ (mimarinin İLİŞKİ ekseni, tek nesne).

        Üç eksen: TEK OPERATÖR (oku → spectral_reading), İLİŞKİ (bağla → bu), EVRİM
        (akıt → cosmos). İlişki = kuvvet + hayat (interaction) + topoloji (spectral_flow)
        tek Relation'da. Universe.couple bunu döndürür.

            print(ai.relate("CCO", "CC(=O)Oc1ccccc1C(=O)O").summary())
        """
        from tantrium.core.relation import relate as _rel
        return _rel(a, b)

    def interact(self, a, b) -> "object":
        """İki yapı arası KUVVET + HAYAT: kuplaj + dolanıklık + hibridleşme (çok-cisim).

        İlişki ekseninin yarısı (kuvvet+hayat); tam ilişki için ai.relate (topoloji dahil)."""
        from tantrium.core.interaction import interact as _it
        return _it(a, b)

    def spectral_geometry(self, query) -> "object":
        """Girdinin TANIMLADIĞI uzayın geometrisi (Connes NCG): spektral boyut + etki."""
        from tantrium.core.spectral_geometry import spectral_geometry as _sg
        return _sg(query)

    def spectral_flow(self, a, b) -> "object":
        """İki yapıyı birbirine dönüştüren YOLUN topolojik yükü (mimarinin 5. ekseni).

        Dört katman tek operatörü okur; bu, operatörler arası bir yolu okur. G_A→G_B
        morfingi boyunca net özdeğer geçişi = topolojik yük. Özdeş→0; düzgün/yakın
        dönüşüm→0 geçiş; topolojik farklı yapı→sıfırdan farklı.

            print(ai.spectral_flow("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O").summary())
        """
        from tantrium.core.spectral_flow import spectral_flow as _sf
        return _sf(a, b)

    def spectral_reading(self, query, as_spectrum: bool = False) -> "object":
        """G=A†A'nın TAM dört-katmanlı okuması — tek nesne, tek eigendecomposition.

        1 MAKRO (yoğunluk/momentler) · 2 MİKRO (⟨r⟩ korelasyon) · 3 SİMETRİ (Dyson β) ·
        4 ÖZVEKTÖR (localization/ergodiklik — makinede ilk kez). Makinenin "okuma derinliği"
        ekseni; Cosmos bunu zaman boyunca akıtır (ızgara).

            print(ai.spectral_reading("CC(=O)Oc1ccccc1C(=O)O").summary())
        """
        from tantrium.core.spectral_reading import read
        return read(query, as_spectrum=as_spectrum)

    def spectral_class(self, query, as_spectrum: bool = False) -> "object":
        """Girdi integrallenebilir mi, kaotik mi? — spektrumun seviye-aralığı ⟨r⟩.

        8 moment DEĞİL: spektrumun ince korelasyonu. Bohigas-Giannoni-Schmit
        (kaos→rastgele-matris) + Berry-Tabor (integrallenebilir→Poisson).

        as_spectrum=True: girdi GERÇEK bir seviye-dizisiyse (zeta sıfırları, özdeğerler,
        enerji seviyeleri) doğrudan oku → zeta GUE (0.62) çıkar. Varsayılan: keyfi yapıyı
        G=AᵀA'ya kodla (reel → en fazla GOE).

            ai.spectral_class([k*k for k in range(1,90)])           # integrallenebilir
            ai.spectral_class(zeta_zeros, as_spectrum=True)         # GUE
        """
        from tantrium.core.spectral_class import spectral_class as _sc
        return _sc(query, as_spectrum=as_spectrum)

    def fingerprint(self, query) -> list[float]:
        """Girdinin TAM 46-boyutlu sertifika parmak izi — makinenin asıl algı organı.

        8 moment kapıdır; bu vektör 23 paradigmanın TÜM çıktısıdır (Newton, Schur,
        τ, Li, de Bruijn-Newman Λ, cross-ratio, Achilles, serbest kümülant κ...).
        """
        from tantrium.core.metric import certificate_vector
        return certificate_vector(query)

    def compare(self, a, b) -> float:
        """İki girdiyi TAM 46-boyutlu sertifika uzayında karşılaştır — çökmeden.

        W2 (eigenvalue) ve moment-L1 alt-kümeye çöker; bu, 23 paradigmanın tüm
        çıktısı üzerinde çalışır. Ayrımı 8 boyutta değil, 46 boyutta okur.
        """
        from tantrium.core.metric import certificate_distance
        return certificate_distance(a, b)

    def self_reference(self, seed=None, max_iter: int = 64, tol: float = 1e-6) -> "object":
        """Makineyi kendi üzerine katla → öz-gönderim sabit noktası μ* (strange loop, exact).

        μ → certify_rh(μ) → öz-portre → encode (G=AᵀA, kendine) → μ_next. Sabit nokta:
        makine kendine baktığında kendini geri veren öz-tutarlı nesne. Tohumdan bağımsız
        evrensel öz-imge. (Self-modeling'in BİÇİMİ — kendisi değil; ölçen ölçtüğüdür.)
        """
        from tantrium.core.fixed_point import self_reference_orbit
        return self_reference_orbit(seed=seed, max_iter=max_iter, tol=tol)

    def zeta_operator(self, num_zeros: int = 50,
                      prime_cutoffs: tuple = (7, 30, 100, 300)) -> "object":
        """Riemann sıfırlarının operatörünü DOĞAL malzemeden kurma denemesi (fit yok).

        İskelet (asal içermez, Berry-Keating yarı-klasik = fonksiyonel denklem) sıfırların
        ortalama konumunu ~%0.7 verir; explicit-formula asal düzeltmesi (Euler çarpımı)
        eklendikçe gerçek sıfırlara monoton yakınsar. Sıfırlar yalnız SKOR için kullanılır
        — inşa dairesel değildir. Artığı kapatan sonlu operatör = Hilbert-Pólya hedefi.

            print(ai.zeta_operator().summary())
        """
        from tantrium.core.zeta_operator import probe_zeta_operator
        return probe_zeta_operator(num_zeros=num_zeros, prime_cutoffs=tuple(prime_cutoffs))

    def hilbert_polya(self, num_zeros: int = 50, prime_cutoff: int = 300) -> "object":
        """Prim-türevli zeta-operatörünü kur ve MAKİNENİN sertifika hattından geçir.

        Operatör asallardan (explicit formula) türetilir (sıfırlar yalnız skor); makine
        simetri SINIFINI okur (GUE = doğru, zaman-tersimi-kırık), spektrumu bilinen
        sıfırlara skorlar, mühürler. Doğru sınıf + sıfırlara RMS≈0.02 kilit gösterir; artık
        tabanı koşullu yakınsamada — onu kapatan sonlu operatör = Hilbert-Pólya hedefi.

            print(ai.hilbert_polya().summary())
        """
        from tantrium.core.zeta_operator import certify_hilbert_polya
        return certify_hilbert_polya(num=num_zeros, prime_cutoff=prime_cutoff)

    def compute_zeros(self, num: int = 50) -> list[float]:
        """İlk `num` Riemann zeta sıfırını ζ'den DOĞRUDAN HESAPLA (tahmin/ankraj YOK).

        Riemann-Siegel Z(t)'nin işaret değişimleri = sıfırlar. Makine durumsuz-exact:
        ÜRETMEZ/TAHMİN ETMEZ, hesaplar (deterministik, ~1e-3 lider mertebe).

            ai.compute_zeros(10)   # [14.137, 21.024, 25.018, ...]
        """
        from tantrium.core.zeta_operator import compute_zeros as _cz
        return _cz(num)

    def rh_genesis(self, depth: int = 16, max_degree: int = 4) -> "object":
        """RH pozitifliğini sonlu formda var et — tek bütün (kaynak→Jensen→Hermite→mühür).

        ξ'nin gerçek Φ-ölçüsünden (pozitifliğin kaynağı: Φ>0 ⟹ Hankel PSD bedava) Jensen-
        Pólya dizisini a_n=γ_n/(2n)! kurar; sonsuz koşul "Ξ∈Laguerre-Pólya ⟺ RH"u sonlu
        J^{d,n} hiperbolisitesine indirir; derinliği Ouroboros gibi adım adım büyütüp her
        adımı EXACT Sturm ile sertifikalar; renormalize Jensen → Hermite (= GUE) yakınsamasını,
        yani tek-kural adayını, ölçer; bütünü mühürler. Sonlu form sertifikalı; evrensel
        hiperbolisite (= RH) hedeftir, iddia edilmez.

            print(ai.rh_genesis().summary())
        """
        from tantrium.core.rh_genesis import rh_genesis as _rg
        return _rg(depth=depth, max_degree=max_degree)


    def cosmos(self, seed=None, inflation_steps: int = 40) -> "object":
        """Bir tohumun TÜM evren ömrü: T₁ yaratılış → T₁₀ son, çağ çağ, mühürlü.

        Makinenin bütün organlarını tek zaman okuna dizer (encode→Ouroboros→23
        paradigma→madde→kendini örgütleme→kritik çizgi→Achilles→mühür→serbest
        kümülant→μ*/patlama). Çıktı tek bir yaşam-döngüsü sertifikası.

        Örnek:
            print(ai.cosmos("EGFR").summary())
        """
        from tantrium.cosmos import run_cosmos
        return run_cosmos(seed=seed, inflation_steps=inflation_steps)

    def rh_criteria(self, query) -> "RHCriteria":
        """Girdinin RH-türevli pozitiflik kriterleri (τ/pivot/cross-ratio, exact Fraction).

        tce-collapse-engine ispat zincirinin moment-hesaplanabilir çekirdeği: girdiyi
        momentlerine okur, sonra Hankel determinantları τ_j, LDLᵀ pivotları d_k ve
        cross-ratio ρ_j üretir. `hamburger_certified` = geçerli (PSD) moment dizisi.

        Örnek:
            r = ai.rh_criteria("EGFR")
            print(r.summary())          # τ/pivot/cross-ratio işaretleri
            print(r.hamburger_certified)
        """
        from tantrium.core.encoder import _spectral_moments, _try_power_moments
        from tantrium.core.rh_criteria import rh_criteria as _rh
        # 16-derinlik genişletilmiş moment (encoder._extract_structure ile aynı mantık)
        ext = _try_power_moments(query, 16)
        if ext is None:
            A = self._engine.encoder._to_matrix(query)
            ext = _spectral_moments(A, 16)
        return _rh(ext)

    def rh_certificate(self, query) -> "object":
        """Girdinin TAM RH sertifikası: kriterler + Hausdorff + Turán + serbest entropi +
        yarı-daire + SHA-256 mühür (tek bütün, tce-collapse moment-matematiği)."""
        from tantrium.core.rh_certificate import certify_rh
        return certify_rh(self._ext_moments(query), name=str(query)[:64], heavy=True)

    def rh_distance(self, a, b) -> float:
        """İki nesne arası TAM RH-sertifika mesafesi (rank+pivot+κ+Hausdorff+entropi).

        Saf moment-L1'in göremediği yüksek-yapı farkını yakalar — momentleri yakın ama
        Sturm-pivot/Stieltjes/Hausdorff profili farklı nesneleri ayırır.
        """
        from tantrium.core.rh_certificate import rh_distance as _rd
        return _rd(self._ext_moments(a), self._ext_moments(b))

    # ── Jensen-Pólya / Laguerre-Pólya (RH-tipi hiperbolisite) ────────────────
    def jensen(self, sequence, max_degree: int = 4) -> "object":
        """Dizinin Jensen polinomları → Laguerre-Pólya (RH-tipi) sertifikası.

        J^{d,n}(X)=Σ C(d,j)γ_{n+j}X^j hiperbolik mi (tüm kök gerçek). LP-sınıfı = RH-tipi
        koşul. NOT: momentlere uygulanmaz (log-konveks) — ξ-benzeri/log-konkav diziler için.
        """
        from tantrium.core.jensen import laguerre_polya_test
        return laguerre_polya_test(list(sequence), max_degree=max_degree)

    def hyperbolic(self, poly_coeffs) -> bool:
        """Polinom (artan kuvvet katsayıları) hiperbolik mi = tüm kökleri gerçek."""
        from tantrium.core.jensen import is_hyperbolic
        return is_hyperbolic(list(poly_coeffs))

    def bezoutian(self, poly_coeffs) -> "object":
        """Polinomun Bezoutian/Sturm analizi: gizli faktörler H_{d,j}, Lah-pivot sapması
        (ρ_j=(d−j)²), ilk-beş-pivot pozitifliği, hiperboliklik (tce-collapse math/pivots)."""
        from tantrium.core.bezoutian import analyze
        return analyze(list(poly_coeffs))

    # ── Serbest olasılık (Voiculescu) ────────────────────────────────────────
    def free_entropy(self, query) -> float:
        """Girdinin spektral ölçüsünün serbest entropisi χ (logaritmik enerji, konkav)."""
        from tantrium.core.free_probability import free_entropy as _fe
        obj = self._engine.encoder.encode(query, name=str(query)[:64])
        return _fe(list(obj.moments))

    def semicircle_distance(self, query) -> float:
        """Girdinin yarı-daireye (serbest-CLT çekici, Wigner) κ-mesafesi."""
        from tantrium.core.free_probability import semicircle_distance as _sd
        obj = self._engine.encoder.encode(query, name=str(query)[:64])
        return _sd(list(obj.moments))

    # ── Mühürlü, dışarıdan-denetlenebilir sertifika ──────────────────────────
    def seal(self, query) -> dict:
        """Girdiyi RH-kriterleriyle mühürle → SHA-256 içerik-hash'li sertifika (artifact)."""
        from tantrium.core.verifier import seal as _seal
        obj = self._engine.encoder.encode(query, name=str(query)[:64])
        crit = self.rh_criteria(query)
        return _seal(str(query)[:64], str(query), list(obj.moments), crit.as_dict())

    def verify(self, sealed: dict) -> dict:
        """Mühürlü sertifikayı bağımsız doğrula: hash + verdict tutarlılığı (tamper-tespiti)."""
        from tantrium.core.verifier import verify as _verify
        return _verify(sealed)
