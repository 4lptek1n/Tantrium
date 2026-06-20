"""Emanasyon testleri — Kabbalistik 23 sefirot → Malkuth cascade."""

import pytest


@pytest.fixture(scope="module")
def ai():
    import tantrium

    return tantrium.AI()


def test_emanate_returns_emanation_result(ai):
    from tantrium.meta.synthesis import EmanationResult

    result = ai.emanate("protein")
    assert isinstance(result, EmanationResult)


def test_emanate_has_light(ai):
    result = ai.emanate("protein")
    assert isinstance(result.light, dict)
    assert len(result.light) > 0


def test_emanate_light_has_spectrum_or_li(ai):
    result = ai.emanate("enzyme")
    assert "spectrum" in result.light or "li_coefficients" in result.light


def test_emanate_light_has_li_coefficients(ai):
    result = ai.emanate("DNA")
    li = result.light.get("li_coefficients", [])
    assert isinstance(li, list)
    assert len(li) > 0


def test_emanate_debruijn_lambda_non_positive(ai):
    result = ai.emanate("protein")
    lam = result.light.get("debruijn_lambda")
    if lam is not None:
        assert lam <= 0.0


def test_emanate_certified_paradigms_count(ai):
    result = ai.emanate("protein")
    assert 0 <= result.certified_paradigms <= 23


def test_emanate_grounding_field(ai):
    result = ai.emanate("protein")
    assert result.grounding in ("GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED")


def test_emanate_known_concept_high_certified(ai):
    result = ai.emanate("protein")
    assert result.certified_paradigms >= 18


def test_emanate_summary_contains_name(ai):
    result = ai.emanate("enzyme")
    s = result.summary()
    assert "enzyme" in s or "EMANASYON" in s


def test_emanate_manifested_in_manifold(ai):
    from tantrium.core.engine import CertificationEngine
    from tantrium.meta.synthesis import ConceptSynthesizer

    engine = CertificationEngine()
    synth = ConceptSynthesizer(engine)
    result = synth.emanate("test_emanate_unique_9876")
    if result.manifested:
        assert result.descended_to in engine.manifold.concepts


def test_emanate_light_debruijn_lambda_present(ai):
    result = ai.emanate("riemann")
    assert "debruijn_lambda" in result.light


def test_genesis_discover_mode(ai):
    report = ai.genesis(max_gaps=2)
    assert hasattr(report, "concepts_created")
    assert hasattr(report, "manifold_growth")


def test_ai_emanate_api_exists():
    import tantrium

    ai = tantrium.AI()
    assert hasattr(ai, "emanate")
    assert callable(ai.emanate)
