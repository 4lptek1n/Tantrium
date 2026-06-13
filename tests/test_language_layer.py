"""Dil katmanı testleri: bind_percept, meaning_compose, generate(use_meaning).

Kademe 3-5 doğrulama:
- bind_percept: kavrama çok-modal TAU kenarı bağlar
- meaning_compose: cümle → semantik centroid → CompositeSignature
- generate(use_meaning): hibrit skor → farklı yörünge
"""
import numpy as np
import pytest

import tantrium
from tantrium.language.generator import CertifiedGenerator, GenerationResult


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


# ─── bind_percept ──────────────────────────────────────────────────────────────

def test_bind_percept_returns_percept_name(ai):
    sig = np.random.default_rng(42).standard_normal(500)
    name = ai.bind_percept("protein", sig, modality="signal", paradigm="HAS_SIGNAL")
    assert "protein" in name
    assert "signal" in name or "percept" in name


def test_bind_percept_creates_tau_edge(ai):
    sig = np.random.default_rng(7).standard_normal(500)
    pname = ai.bind_percept("caffeine", sig, modality="signal", paradigm="HAS_SIGNAL")
    edges = ai._engine.tau.edges.get("caffeine", [])
    hs = [e for e in edges if e.paradigm == "HAS_SIGNAL" and e.target == pname]
    assert len(hs) >= 1, "HAS_SIGNAL kenarı oluşmadı"


def test_bind_percept_custom_name(ai):
    sig = np.random.default_rng(99).standard_normal(300)
    name = ai.bind_percept("apple", sig, modality="signal",
                           paradigm="HAS_SIGNAL", name="apple_crunch")
    assert name == "apple_crunch"
    edges = ai._engine.tau.edges.get("apple", [])
    targets = [e.target for e in edges if e.paradigm == "HAS_SIGNAL"]
    assert "apple_crunch" in targets


def test_bind_percept_has_compound(ai):
    sig = np.random.default_rng(11).standard_normal(400)
    name = ai.bind_percept("apple", sig, modality="signal",
                           paradigm="HAS_COMPOUND", name="apple_ethylene")
    edges = ai._engine.tau.edges.get("apple", [])
    paradigms = {e.paradigm for e in edges if e.target == name}
    assert "HAS_COMPOUND" in paradigms


def test_bind_percept_concept_in_manifold(ai):
    sig = np.random.default_rng(55).standard_normal(600)
    pname = ai.bind_percept("dopamine", sig, modality="signal", paradigm="HAS_SIGNAL")
    assert pname in ai._engine.manifold.concepts


# ─── meaning_compose ───────────────────────────────────────────────────────────

def test_meaning_compose_returns_signature(ai):
    cs = ai.meaning_compose("protein inhibits tumor growth")
    assert cs is not None


def test_meaning_compose_has_components(ai):
    cs = ai.meaning_compose("EGFR inhibitor reduces tumor")
    assert cs is not None
    assert len(cs.components) >= 2


def test_meaning_compose_moments_in_range(ai):
    """Moment imzası [0,1] aralığında olmalı (μ₀=1, diğerleri ≤ 1)."""
    cs = ai.meaning_compose("protein kinase inhibitor")
    assert cs is not None
    assert float(cs.moments[0]) == pytest.approx(1.0, abs=1e-9)
    for m in cs.moments[1:]:
        assert 0.0 <= float(m) <= 1.0, f"Moment {float(m)} aralık dışı"


def test_meaning_compose_nearest_returns_list(ai):
    cs = ai.meaning_compose("enzyme that activates signaling")
    assert cs is not None
    result = cs.nearest(n=3)
    assert isinstance(result, list)
    assert len(result) >= 1


def test_meaning_compose_to_produce_target(ai):
    cs = ai.meaning_compose("receptor tyrosine kinase")
    assert cs is not None
    target = cs.to_produce_target()
    assert isinstance(target, list)
    assert len(target) == len(cs.moments)
    assert target == cs.moments


def test_meaning_compose_n_surface_tracking(ai):
    """Anlam kanalı bulunmayan bileşenler n_surface'e sayılmalı."""
    cs = ai.meaning_compose("protein that crosses barrier")
    assert cs is not None
    assert cs.n_surface >= 0  # fallback'lar sayılıyor
    assert cs.n_surface <= len(cs.components)


def test_meaning_compose_str(ai):
    cs = ai.meaning_compose("EGFR inhibitor")
    assert cs is not None
    s = str(cs)
    assert "CompositeSignature" in s
    assert "μ₁=" in s


def test_meaning_compose_none_for_empty(ai):
    # Tüm stopword'ler — anlamlı bileşen çıkmayabilir ya da fallback
    # Not: mantıklı fallback'la bile CompositeSignature döner; None nadirdir
    cs = ai.meaning_compose("the and for")
    # None veya boş components olabilir — en az crash olmamalı
    if cs is not None:
        assert isinstance(cs.components, list)


# ─── generate(use_meaning=True) ────────────────────────────────────────────────

def test_generate_default_works(ai):
    g = CertifiedGenerator(ai._engine)
    r = g.generate("protein")
    assert isinstance(r, GenerationResult)
    assert r.certified


def test_generate_use_meaning_returns_result(ai):
    g = CertifiedGenerator(ai._engine)
    r = g.generate("protein", use_meaning=True)
    assert isinstance(r, GenerationResult)
    assert r.certified


def test_generate_use_meaning_via_ai_facade(ai):
    r = ai.generate("EGFR", use_meaning=True)
    assert r.certified
    assert len(r.text) > 0


def test_generate_use_meaning_false_default(ai):
    r1 = ai.generate("inhibitor", use_meaning=False)
    assert r1.certified


def test_generate_results_differ_with_meaning(ai):
    """use_meaning=True ve False farklı yörünge üretebilir (garanti yok ama olası)."""
    g = CertifiedGenerator(ai._engine)
    r_surf = g.generate("EGFR", max_steps=4, use_meaning=False)
    r_mean = g.generate("EGFR", max_steps=4, use_meaning=True)
    # İkisi de geçerli olmalı
    assert r_surf.certified
    assert r_mean.certified
    # Metinlerin en az biri üretilmeli
    assert len(r_surf.text) > 0
    assert len(r_mean.text) > 0


# ─── generator _CONNECTIVE kapsamı ─────────────────────────────────────────────

def test_generator_connective_has_new_paradigms():
    from tantrium.language.generator import _CONNECTIVE, _EN_CONNECTIVE, _SEMANTIC
    new_paradigms = {"COMPONENT_OF", "HAS_SIGNAL", "HAS_COMPOUND", "HAS_IMAGE",
                     "INHIBITS", "CAUSES", "ACTIVATES"}
    for p in new_paradigms:
        assert p in _CONNECTIVE, f"{p} _CONNECTIVE'de yok"
        assert p in _EN_CONNECTIVE, f"{p} _EN_CONNECTIVE'de yok"
        assert p in _SEMANTIC, f"{p} _SEMANTIC'de yok"


def test_generator_en_lang(ai):
    g = CertifiedGenerator(ai._engine, lang="en")
    r = g.generate("protein", max_steps=3)
    assert r.lang == "en"
    assert r.certified
