"""CoreMachine (4-eksenli tek geçiş) testleri."""
from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def ai():
    import tantrium
    return tantrium.AI()


def test_certify_all_returns_unified_certificate(ai):
    """certify_all() UnifiedCertificate döndürmeli."""
    from tantrium.core.unified import UnifiedCertificate
    result = ai.certify_all("EGFR")
    assert isinstance(result, UnifiedCertificate)


def test_unified_certificate_has_all_fields(ai):
    """UnifiedCertificate tüm 4 ekseni içermeli."""
    result = ai.certify_all("protein")
    assert result.paradigms_passed > 0
    assert result.paradigms_total == 23
    assert result.grounding in ("GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED")
    assert result.truth in ("CONSISTENT", "CONTESTED", "CONTRADICTORY")
    assert 0.0 <= result.confidence <= 1.0
    assert result.confidence_level in ("CERTAIN", "STRONG", "MODERATE", "WEAK", "UNCERTAIN")
    assert isinstance(result.coherent, bool)
    assert isinstance(result.moments, list)
    assert len(result.moments) >= 8


def test_ask_has_truth_and_confidence(ai):
    """ask() geriye uyumlu certified + yeni truth/confidence alanları."""
    r = ai.ask("DNA")
    assert r.certified is True  # 23/23 paradigm
    assert r.truth in ("CONSISTENT", "CONTESTED", "CONTRADICTORY")
    assert 0.0 <= r.truth_score <= 1.0
    assert 0.0 <= r.confidence <= 1.0
    assert r.confidence_level in ("CERTAIN", "STRONG", "MODERATE", "WEAK", "UNCERTAIN")
    assert isinstance(r.coherent, bool)


def test_grounded_concept_is_coherent(ai):
    """Köklü (GROUNDED) ve 23/23 olan kavram coherent olmalı."""
    r = ai.ask("protein")
    # protein manifolda mevcut ve köklü
    if r.grounding == "GROUNDED" and r.paradigms_passed == 23:
        assert r.coherent is True


def test_reconstruct_returns_atomic_measure():
    """Moment rekonstrüksiyonu atomik ölçü döndürmeli."""
    from tantrium.core.reconstruct import reconstruct_measure, reconstruction_fidelity
    moments = [1.0, 0.5, 0.3, 0.2, 0.15, 0.12, 0.1, 0.09]
    rec = reconstruct_measure(moments)
    assert len(rec.nodes) > 0
    assert len(rec.weights) == len(rec.nodes)
    assert abs(sum(rec.weights) - 1.0) < 0.01
    fid = reconstruction_fidelity(moments)
    assert 0.0 <= fid <= 1.0


def test_truth_certifier_consistent(ai):
    """Gerçek kavram CONSISTENT olmalı."""
    from tantrium.core.truth import TruthCertifier
    tc = TruthCertifier(ai._engine)
    result = tc.certify("prime")
    assert result.verdict in ("CONSISTENT", "CONTESTED")
    assert 0.0 <= result.consistency_score <= 1.0


def test_confidence_calibration():
    """Tüm eksenler güçlüyse STRONG veya CERTAIN döndürmeli."""
    from tantrium.core.confidence import calibrate
    conf = calibrate(structural=0.96, achilles=0.95, grounding=0.8, truth=0.9)
    assert conf.level in ("CERTAIN", "STRONG")
    assert conf.value >= 0.7


def test_canonical_distance_symmetric():
    """Kanonik mesafe simetrik olmalı."""
    from tantrium.core.metric import canonical_distance
    a = [1.0, 0.5, 0.3, 0.2, 0.15, 0.12, 0.1, 0.09]
    b = [1.0, 0.6, 0.4, 0.25, 0.18, 0.14, 0.12, 0.10]
    assert abs(canonical_distance(a, b) - canonical_distance(b, a)) < 1e-10


def test_manifold_distance_method(ai):
    """manifold.distance() iki kavram arasını hesaplamalı."""
    d = ai._engine.manifold.distance("prime", "energy")
    assert d >= 0.0
    assert d < float("inf")


def test_new_api_methods_exist(ai):
    """Yeni API metodları mevcut olmalı."""
    assert hasattr(ai, "certify_all")
    assert hasattr(ai, "manifold_gaps")
    assert hasattr(ai, "destiny")
    assert hasattr(ai, "genealogy")
    assert hasattr(ai, "signal")
    assert hasattr(ai, "dna")
    assert hasattr(ai, "crypto")
    assert hasattr(ai, "inject_english")


def test_engine_core_property(ai):
    """engine.core CoreMachine döndürmeli (lazy singleton)."""
    from tantrium.core.unified import CoreMachine
    core = ai._engine.core
    assert isinstance(core, CoreMachine)
    # Singleton
    assert ai._engine.core is core


def test_certify_unified_shorthand(ai):
    """engine.certify_unified() shorthand çalışmalı."""
    from tantrium.core.unified import UnifiedCertificate
    result = ai._engine.certify_unified("EGFR")
    assert isinstance(result, UnifiedCertificate)
