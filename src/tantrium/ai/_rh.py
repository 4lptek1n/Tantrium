"""Tantrium AI — RH / serbest-olasılık yüzeyi (RHMixin).

rh_criteria / rh_certificate / rh_distance / jensen / hyperbolic / bezoutian /
free_entropy / semicircle_distance / seal / verify.
"""
from __future__ import annotations

from tantrium.core.rh_criteria import RHCriteria


class RHMixin:
    """Riemann-Hipotezi türevli pozitiflik kriterleri + serbest olasılık + mühür."""

    def spectral_class(self, query) -> "object":
        """Girdi integrallenebilir mi, kaotik mi? — tam spektrumun seviye-aralığı ⟨r⟩.

        8 moment DEĞİL: N×N spektrumun ince korelasyonu. Bohigas-Giannoni-Schmit
        (kaos→rastgele-matris) + Berry-Tabor (integrallenebilir→Poisson). Kapalı-formlu
        diziler → Poisson; lojistik harita/rastgele → GOE.

            print(ai.spectral_class([k*k for k in range(1,90)]).summary())   # integrallenebilir
        """
        from tantrium.core.spectral_class import spectral_class as _sc
        return _sc(query)

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
