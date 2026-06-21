"""RH sertifika bundle testleri — birleşik moment-RH matematiği + mimari kablolama."""
from fractions import Fraction

import tantrium
from tantrium.core.metric import distance
from tantrium.core.rh_certificate import RHCertificate, certify_rh, hausdorff


def test_certify_rh_returns_bundle():
    c = certify_rh([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    assert isinstance(c, RHCertificate)
    assert c.sealed_hash  # mühür mevcut
    assert 0.0 <= c.grade <= 1.0


def test_hausdorff_uniform_certified():
    """Uniform[0,1] momentleri μ_k=1/(k+1) → tam-monoton → Hausdorff ✓."""
    mu = [Fraction(1, k + 1) for k in range(12)]
    ok, _ = hausdorff(mu)
    assert ok


def test_hausdorff_rejects_out_of_unit():
    """[0,1] dışı destekli (büyük momentler) → Hausdorff ✗ (dürüst ayrım)."""
    mu = [Fraction(1), Fraction(5), Fraction(30), Fraction(200)]
    ok, _ = hausdorff(mu)
    assert not ok


def test_bundle_has_all_fields():
    c = certify_rh([Fraction(1, k + 1) for k in range(16)], heavy=True)
    assert c.criteria.rank >= 0
    assert isinstance(c.hausdorff_certified, bool)
    assert isinstance(c.free_entropy, float)
    assert isinstance(c.semicircle_distance, float)
    assert c.turan_min <= 0 or c.turan_min == 0.0  # moment log-konveks


def test_heavy_false_skips_free_entropy():
    c = certify_rh([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15], heavy=False)
    assert c.free_entropy == 0.0


def test_deterministic_seal():
    a = certify_rh([1.0, 0.5, 0.4, 0.3, 0.25, 0.2], name="x", heavy=False)
    b = certify_rh([1.0, 0.5, 0.4, 0.3, 0.25, 0.2], name="x", heavy=False)
    assert a.sealed_hash == b.sealed_hash


def test_rh_distance_discriminates():
    ai = tantrium.AI()
    assert ai.rh_distance("EGFR", "EGFR") == 0.0
    assert ai.rh_distance("EGFR", "c1ccccc1") > 0.0


def test_metric_rh_mode():
    """metric='rh' dispatch çalışıyor."""
    a = [1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15]
    b = [1.0, 0.6, 0.45, 0.35, 0.28, 0.22, 0.19, 0.16]
    d = distance(a, b, metric="rh")
    assert d >= 0.0
    assert distance(a, a, metric="rh") == 0.0


def test_encoder_attaches_rh_bundle():
    obj = tantrium.encode([1, 1, 2, 3, 5, 8, 13, 21])
    assert "rh" in obj.structure
    assert "sealed_hash" in obj.structure["rh"]
    assert "criteria" in obj.structure["rh"]


def test_certify_all_carries_bundle():
    c = tantrium.AI().certify_all("aspirin")
    assert hasattr(c, "rh_rank")
    assert hasattr(c, "rh_hausdorff")
    assert hasattr(c, "sealed_hash") and c.sealed_hash
    assert hasattr(c, "rh_free_entropy")


def test_ai_rh_certificate():
    c = tantrium.AI().rh_certificate("EGFR")
    assert isinstance(c, RHCertificate)
    assert "Hausdorff" in c.summary()
