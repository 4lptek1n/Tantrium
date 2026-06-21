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
    assert result.grounding in ("GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED", "N/A")
    assert result.truth in ("CONSISTENT", "CONTESTED", "CONTRADICTORY", "N/A")
    assert 0.0 <= result.confidence <= 1.0
    assert result.confidence_level in ("CERTAIN", "STRONG", "MODERATE", "WEAK", "UNCERTAIN")
    assert isinstance(result.coherent, bool)
    assert isinstance(result.moments, list)
    assert len(result.moments) >= 8


def test_reconstruct_returns_measure():
    """Moment rekonstrüksiyonu ölçü döndürmeli."""
    from tantrium.core.reconstruct import reconstruct_measure, reconstruction_fidelity
    moments = [1.0, 0.5, 0.3, 0.2, 0.15, 0.12, 0.1, 0.09]
    rec = reconstruct_measure(moments)
    assert rec is not None
    fid = reconstruction_fidelity(moments)
    assert 0.0 <= fid <= 1.0


def test_confidence_calibration():
    """Tüm eksenler güçlüyse STRONG veya CERTAIN döndürmeli."""
    from tantrium.core.confidence import calibrate
    # Remote API: calibrate(coverage, margin, grounding, truth)
    conf = calibrate(coverage=0.96, margin=0.15, grounding=0.8, truth=0.9)
    assert conf.level in ("CERTAIN", "STRONG")
    assert conf.value >= 0.7


def test_canonical_distance_symmetric():
    """Kanonik mesafe simetrik olmalı."""
    from tantrium.core.metric import canonical_distance
    a = [1.0, 0.5, 0.3, 0.2, 0.15, 0.12, 0.1, 0.09]
    b = [1.0, 0.6, 0.4, 0.25, 0.18, 0.14, 0.12, 0.10]
    assert abs(canonical_distance(a, b) - canonical_distance(b, a)) < 1e-10


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


def test_grounding_cert_stashed_in_evidence(ai):
    """F2b: CoreMachine grounding sertifikasını evidence'a koyar (ask() yeniden kullanır).

    ask() çift grounding hesabı YAPMAZ — gcert tek kez CoreMachine'de hesaplanır,
    evidence['grounding_cert'] üzerinden özet metnine ulaşır.
    """
    cert = ai._engine.core.certify("EGFR")
    gcert = cert.evidence.get("grounding_cert")
    assert gcert is not None, "grounding_cert evidence'ta olmalı"
    # Sertifika verdict'i UnifiedCertificate.grounding ile tutarlı
    assert gcert.verdict == cert.grounding
    assert abs(gcert.score - cert.grounding_score) < 1e-12
    # summary() çağrılabilir (ask() bunu kullanır)
    assert isinstance(gcert.summary(), str)
