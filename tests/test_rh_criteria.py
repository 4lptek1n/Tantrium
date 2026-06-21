"""RH kriter katmanı testleri — moment dizisinden τ/pivot/cross-ratio (exact)."""
from fractions import Fraction

import tantrium
from tantrium.core.rh_criteria import RHCriteria, rh_criteria


def test_returns_rhcriteria():
    r = rh_criteria([1.0, 0.5, 0.4, 0.3, 0.25, 0.21, 0.18, 0.16])
    assert isinstance(r, RHCriteria)


def test_exact_fraction():
    """Tüm determinantlar exact Fraction — yuvarlama yok."""
    r = rh_criteria([Fraction(1), Fraction(1, 2), Fraction(1, 3),
                     Fraction(1, 4), Fraction(1, 5), Fraction(1, 6),
                     Fraction(1, 7), Fraction(1, 8)])
    assert all(isinstance(t, Fraction) for t in r.hankel_dets)
    assert all(isinstance(p, Fraction) for p in r.pivots)


def test_eight_moments_gives_four_taus():
    """8 moment → a+b≤7 → τ_0..τ_3 (4 determinant). Cross-ratio rank'a kadar."""
    r = rh_criteria([1.0, 0.6, 0.4, 0.3, 0.24, 0.2, 0.17, 0.15])
    assert len(r.hankel_dets) == 4
    assert r.max_level == 3
    # cross-ratio ve pivot rank'a kadar (degenere sınır sıfırları hariç)
    assert len(r.cross_ratios) == max(0, r.rank - 1)
    assert len(r.pivots) == r.rank + 1


def test_rank_discriminates():
    """RH-kriter rank'ı ayırt edici: simetrik/dejenere → düşük rank, zengin → yüksek."""
    import tantrium
    ai = tantrium.AI()
    benzene = ai.rh_criteria("c1ccccc1").rank   # simetrik halka → düşük rank
    aspirin = ai.rh_criteria("CC(=O)Oc1ccccc1C(=O)O").rank
    assert aspirin > benzene


def test_full_criteria_fields():
    """Genişletilmiş kriter alanları mevcut ve tutarlı."""
    import tantrium
    r = tantrium.AI().rh_criteria("aspirin")
    assert len(r.cumulants) >= 2          # κ_1..κ_4
    assert r.lambda_dbn <= 0              # de Bruijn-Newman Λ = −var₀ ≤ 0
    assert 0.0 <= r.grade() <= 1.0
    assert isinstance(r.stieltjes_certified, bool)


def test_rh_distance_discriminates():
    """rh_distance: aynı nesne 0, farklı nesne > 0."""
    import tantrium
    ai = tantrium.AI()
    assert ai.rh_distance("EGFR", "EGFR") == 0.0
    assert ai.rh_distance("EGFR", "c1ccccc1") > 0.0


def test_certify_all_has_rh_axis():
    """UnifiedCertificate RH eksenini taşır."""
    import tantrium
    c = tantrium.AI().certify_all("aspirin")
    assert hasattr(c, "rh_grade") and 0.0 <= c.rh_grade <= 1.0
    assert hasattr(c, "rh_stieltjes")


def test_hilbert_moments_are_hamburger_certified():
    """Hilbert momentleri μ_k=1/(k+1) gerçek pozitif ölçünün (uniform[0,1]) momentleri
    → Hankel PSD, tüm pivotlar pozitif → Hamburger sertifikalı."""
    mu = [Fraction(1, k + 1) for k in range(8)]
    r = rh_criteria(mu)
    assert r.hankel_psd
    assert r.pivots_positive
    assert r.hamburger_certified
    assert all(t > 0 for t in r.hankel_dets)


def test_tau0_is_mu0():
    r = rh_criteria([Fraction(1), Fraction(2), Fraction(5), Fraction(15)])
    assert r.hankel_dets[0] == Fraction(1)


def test_tau1_is_2x2_determinant():
    """τ_1 = det[[μ0,μ1],[μ1,μ2]] = μ0·μ2 − μ1²."""
    mu = [Fraction(1), Fraction(2), Fraction(5), Fraction(15)]
    r = rh_criteria(mu)
    assert r.hankel_dets[1] == mu[0] * mu[2] - mu[1] ** 2  # 1*5 - 4 = 1


def test_deterministic():
    a = rh_criteria([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    b = rh_criteria([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    assert a.hankel_dets == b.hankel_dets
    assert a.pivots == b.pivots


def test_vector_is_floats():
    r = rh_criteria([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    v = r.vector()
    assert all(isinstance(x, float) for x in v)
    assert len(v) > 0


def test_encoder_attaches_rh_criteria():
    """encode() çıktısının structure'ında rh_criteria olmalı (tüm yollar)."""
    obj = tantrium.encode([1, 1, 2, 3, 5, 8, 13, 21])
    assert "rh_criteria" in obj.structure
    assert "hamburger_certified" in obj.structure["rh_criteria"]


def test_ai_facade():
    ai = tantrium.AI()
    r = ai.rh_criteria("EGFR")
    assert isinstance(r, RHCriteria)
    assert "Hamburger" in r.summary()


def test_pivots_match_tau_ratio():
    """d_k = τ_k/τ_{k-1} özdeşliği."""
    mu = [Fraction(1, k + 1) for k in range(8)]
    r = rh_criteria(mu)
    assert r.pivots[0] == r.hankel_dets[0]                       # τ_0/1
    assert r.pivots[1] == r.hankel_dets[1] / r.hankel_dets[0]    # τ_1/τ_0
