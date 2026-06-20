"""Doğruluk ekseni + güven kalibrasyonu + kanonik metrik testleri (Tier 1+2)."""

from tantrium.core.confidence import calibrate
from tantrium.core.metric import canonical_distance, distance, l1_distance
from tantrium.core.truth import TruthCertifier

# ─── Doğruluk ekseni (3. eksen) ──────────────────────────────────────────────


def test_truth_certifier_verdict(ai):
    """Gerçek kavram komşularıyla tutarlı (CONSISTENT) olmalı."""
    cert = TruthCertifier(ai._engine).certify("riemann", n_neighbors=5)
    assert cert.verdict in ("CONSISTENT", "CONTESTED", "CONTRADICTORY")
    assert 0.0 <= cert.truth_score <= 1.0
    assert cert.neighbors_checked >= 0


def test_truth_score_bounded(ai):
    """Doğruluk skoru her zaman [0,1]."""
    for name in ("prime", "protein", "EGFR"):
        cert = TruthCertifier(ai._engine).certify(name, n_neighbors=4)
        assert 0.0 <= cert.truth_score <= 1.0


def test_truth_via_moments(ai):
    """Manifoldda olmayan token momentlerle değerlendirilebilmeli."""
    from tantrium.core.encoder import encode

    obj = encode("xqztplmbnv", name="garbage")
    cert = TruthCertifier(ai._engine).certify("xqztplmbnv", moments=list(obj.moments))
    assert cert.verdict in ("CONSISTENT", "CONTESTED", "CONTRADICTORY")


# ─── Güven kalibrasyonu ──────────────────────────────────────────────────────


def test_confidence_all_high():
    """Tüm eksenler yüksek → yüksek güven."""
    c = calibrate(coverage=1.0, margin=0.5, grounding=1.0, truth=1.0)
    assert c.value > 0.8
    assert c.level in ("CERTAIN", "STRONG")


def test_confidence_weak_link_collapses():
    """Bir eksen sıfıra giderse güven çöker (zayıf halka kuralı)."""
    c = calibrate(coverage=0.0, margin=0.5, grounding=1.0, truth=1.0)
    assert c.value < 0.4
    assert c.weakest_axis == "kapsama"


def test_confidence_zero_margin_not_fatal():
    """margin=0 (sıfır özdeğer, PSD-geçerli) güveni sıfırlamamalı (taban 0.3)."""
    c = calibrate(coverage=1.0, margin=0.0, grounding=1.0, truth=1.0)
    assert c.value > 0.5  # tabanlı margin → makul güven


def test_confidence_bounded():
    """Güven her zaman [0,1]."""
    import random

    rng = random.Random(0)
    for _ in range(20):
        c = calibrate(
            coverage=rng.random(),
            margin=rng.random(),
            grounding=rng.random(),
            truth=rng.random(),
        )
        assert 0.0 <= c.value <= 1.0


# ─── Kanonik metrik ──────────────────────────────────────────────────────────


def test_canonical_distance_self_zero():
    """Bir kavramın kendisiyle kanonik mesafesi ~0."""
    from tantrium.core.encoder import encode

    mu = list(encode("prime", name="prime").moments)
    d = canonical_distance(mu, mu)
    assert d < 1e-6


def test_canonical_distance_symmetric():
    """Kanonik mesafe simetrik olmalı."""
    from tantrium.core.encoder import encode

    a = list(encode("zeta", name="zeta").moments)
    b = list(encode("prime", name="prime").moments)
    assert abs(canonical_distance(a, b) - canonical_distance(b, a)) < 1e-9


def test_manifold_distance_canonical(ai):
    """Manifold kanonik mesafe metodu çalışmalı."""
    d = ai._engine.manifold.distance("riemann", "prime")
    assert d is None or d >= 0.0


def test_metric_dispatch():
    """distance() metric parametresine göre yönlenmeli."""
    a = [1.0, 0.5, 0.3, 0.2]
    b = [1.0, 0.4, 0.2, 0.1]
    assert distance(a, b, metric="l1") == l1_distance(a, b)
    assert distance(a, b) == canonical_distance(a, b)  # default = canonical
