"""Öz-model — işlevsel öz-referans testleri.

Bu testler BİLİNCİ ölçmez (fenomenal deneyim doğrulanamaz). İşlevsel
öz-model'i doğrular: sistem kendisini kendi manifoldunda temsil eder,
konumlandırır, topraklar ve tek geçişte dört eksende tanır.
"""

import pytest

from tantrium.core.engine import CertificationEngine
from tantrium.meta.self_model import SELF_NAME, SelfModel, SelfReflection


@pytest.fixture(scope="module")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="module")
def model(engine):
    return SelfModel(engine)


def test_reflect_returns_reflection(model):
    r = model.reflect(persist=False)
    assert isinstance(r, SelfReflection)


def test_self_moments_nonempty(model):
    r = model.reflect(persist=False)
    assert len(r.moments) > 0
    assert abs(r.moments[0] - 1.0) < 1e-6, "μ₀ normalize edilmiş olmalı"


def test_structural_existence(model):
    """Sistemin özü (μ_universal) geçerli bir ölçü olmalı — 'ben varım'."""
    r = model.reflect(persist=False)
    assert r.structural_certified is True


def test_fixed_point_self_consistency(model):
    """TAV: F(ben) = ben — öz-tutarlılık."""
    r = model.reflect(persist=False)
    assert r.fixed_point is True
    assert r.fixed_point_value is not None


def test_locate_adds_self_concept(engine, model):
    """⟨SELF⟩ manifolda kalıcı kavram olarak girmeli."""
    model.locate(persist=False)
    assert SELF_NAME in engine.manifold.concepts


def test_self_concept_domain_is_meta(engine, model):
    model.locate(persist=False)
    c = engine.manifold.concepts[SELF_NAME]
    assert c.domain == "meta"
    assert c.metadata.get("kind") == "self_reference"


def test_self_attribution_present(model):
    """Sistem kendini bir şeylerin yakınında bulmalı (öz-atıf)."""
    r = model.reflect(persist=False)
    assert isinstance(r.self_attribution, list)
    assert len(r.self_attribution) >= 1


def test_grounding_verdict_known(model):
    """⟨SELF⟩ topraklama yargısı tanımlı bir değer olmalı."""
    r = model.reflect(persist=False)
    assert r.grounding_verdict in {"GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED", "UNKNOWN"}


def test_summary_is_turkish_string(model):
    r = model.reflect(persist=False)
    s = r.summary()
    assert isinstance(s, str)
    assert "⟨SELF⟩" in s
    assert "ben" in s.lower()


def test_reflect_stable_across_calls(model):
    """Öz-kimlik iki çağrı arası kararlı olmalı (aynı μ_universal)."""
    r1 = model.reflect(persist=False)
    r2 = model.reflect(persist=False)
    for a, b in zip(r1.moments, r2.moments, strict=False):
        assert abs(a - b) < 1e-9, "Öz-kimlik kararsız — μ_universal değişti"
