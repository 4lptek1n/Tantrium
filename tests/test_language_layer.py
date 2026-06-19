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


# ─── ground_full: çok-boyutlu grounding ────────────────────────────────────────

def test_ground_full_returns_signature(ai):
    sig = ai.ground_full("apple", law="fibonacci numbers")
    from tantrium.ai import GroundingSignature
    assert isinstance(sig, GroundingSignature)
    assert sig.concept == "apple"


def test_ground_full_sound_creates_tau_edge(ai):
    rng = np.random.default_rng(123)
    sound = rng.standard_normal(800)
    sig = ai.ground_full("apple", type_hint="fruit", sound=sound)
    edges = ai._engine.tau.edges.get("apple", [])
    has_signal = [e for e in edges if e.paradigm == "HAS_SIGNAL"]
    assert len(has_signal) >= 1


def test_ground_full_dna_creates_tau_edge(ai):
    sig = ai.ground_full("apple", type_hint="fruit", dna="ATCGATCGATCG")
    edges = ai._engine.tau.edges.get("apple", [])
    has_dna = [e for e in edges if e.paradigm == "HAS_DNA"]
    assert len(has_dna) >= 1


def test_ground_full_molecule_creates_tau_edge(ai):
    sig = ai.ground_full("apple", type_hint="fruit", molecule="CC(O)C")
    edges = ai._engine.tau.edges.get("apple", [])
    has_cmp = [e for e in edges if e.paradigm == "HAS_COMPOUND"]
    assert len(has_cmp) >= 1


def test_ground_full_law_edge(ai):
    sig = ai.ground_full("apple", law="golden ratio")
    edges = ai._engine.tau.edges.get("apple", [])
    governed = [e for e in edges if e.paradigm == "IS_GOVERNED_BY" and e.target == "golden ratio"]
    assert len(governed) >= 1


def test_ground_full_multi_dim_bound(ai):
    rng = np.random.default_rng(77)
    sig = ai.ground_full(
        "apple",
        type_hint="fruit",
        dna="GCTAGCTAGCTA",
        sound=rng.standard_normal(600),
        law="natural selection",
    )
    assert "HAS_DNA" in sig.bound
    assert "HAS_SIGNAL" in sig.bound
    assert "IS_GOVERNED_BY" in sig.bound


def test_ground_full_kappa_moments_nonempty(ai):
    rng = np.random.default_rng(55)
    sig = ai.ground_full("apple", type_hint="fruit", sound=rng.standard_normal(500))
    assert len(sig.kappa_moments) >= 2


def test_ground_full_str(ai):
    sig = ai.ground_full("apple", law="fibonacci numbers")
    s = str(sig)
    assert "GroundingSignature" in s
    assert "apple" in s


def test_ground_full_summary(ai):
    rng = np.random.default_rng(88)
    sig = ai.ground_full("apple", type_hint="fruit", sound=rng.standard_normal(400), law="gravity")
    summary = sig.summary()
    assert "apple" in summary
    assert "Grounding" in summary


def test_new_paradigms_in_connective():
    from tantrium.language.generator import _CONNECTIVE, _EN_CONNECTIVE, _SEMANTIC
    new = {"HAS_DNA", "HAS_GEOMETRY", "HAS_TOPOLOGY", "IS_GOVERNED_BY"}
    for p in new:
        assert p in _CONNECTIVE, f"{p} TR connective'de eksik"
        assert p in _EN_CONNECTIVE, f"{p} EN connective'de eksik"
        assert p in _SEMANTIC, f"{p} _SEMANTIC'de eksik"


def test_new_paradigms_in_speaker():
    from tantrium.language.speaker import Speaker
    new = {"HAS_DNA", "HAS_GEOMETRY", "HAS_TOPOLOGY", "IS_GOVERNED_BY"}
    for p in new:
        assert p in Speaker._TR_VERB, f"{p} _TR_VERB'de eksik"


def test_new_paradigms_in_topology_encode():
    from tantrium.core.topology_encode import _SEMANTIC_PARADIGMS
    new = {"HAS_DNA", "HAS_GEOMETRY", "HAS_TOPOLOGY", "IS_GOVERNED_BY"}
    for p in new:
        assert p in _SEMANTIC_PARADIGMS, f"{p} _SEMANTIC_PARADIGMS'de eksik"


def test_converse_topic_extraction():
    """Sorudan ana konu çıkarılmalı (stopword'ler atılır)."""
    import tantrium
    ai = tantrium.AI()
    assert ai._converse_topic("EGFR nedir?") == "egfr"
    assert ai._converse_topic("photosynthesis nasıl çalışır") == "photosynthesis"


def test_converse_known_topic_grounded():
    """Bilinen konu → köklü (grounded) akıcı cevap, halüsinasyon yok."""
    import tantrium
    ai = tantrium.AI()
    r = ai.converse("egfr nedir?", learn_if_unknown=False)
    assert r["topic"] == "egfr"
    assert r["grounded"] is True
    assert len(r["answer"]) > 10 and r["answer"][0].isupper()


def test_converse_unknown_honest_when_offline():
    """Bilmediği + öğrenme kapalı → dürüstçe 'bilmiyorum' (uydurmaz)."""
    import tantrium
    ai = tantrium.AI()
    r = ai.converse("qzxwvbnonsenseword nedir?", learn_if_unknown=False)
    assert r["grounded"] is False
    assert "bilgim yok" in r["answer"]


# ───────── Üretken-dilbilgisi (Kademe F48): DETERMİNİSTİK + uyum-duyarlı ─────────

def test_grammar_deterministic():
    """random YOK: aynı (topic, facts) → BİREBİR aynı cümle (sertifikalanabilirlik)."""
    from tantrium.language.fluent import narrate
    facts = {"IS_A": ["kinase inhibitor"], "INHIBITS": ["egfr", "her2"]}
    a = narrate("lapatinib", facts)
    b = narrate("lapatinib", facts)
    assert a == b and len(a) > 10


def test_grammar_class_agreement():
    """Çoğul/İngilizce taksonomi → 'bir X compounds' DEĞİL, 'X sınıfından bir bileşik'."""
    from tantrium.language.fluent import narrate, _is_class_term, _is_company
    assert _is_class_term("aminopyrimidines") and _is_class_term("3-pyridyl compounds")
    assert _is_company("astellas pharma") and not _is_company("kinase")
    txt = narrate("imatinib", {"IS_A": ["aminopyrimidines", "benzanilides"]})
    assert "sınıf" in txt and "bir aminopyrimidines" not in txt


def test_grammar_drops_company_isa():
    """Üretici (astellas pharma) bir SINIF değildir → IS_A'dan düşülür."""
    from tantrium.language.fluent import narrate
    txt = narrate("erlotinib", {"IS_A": ["astellas pharma"], "INHIBITS": ["egfr"]})
    assert "astellas pharma" not in txt and "egfr" in txt


def test_grammar_verb_join_not_ile():
    """İki yüklem 'A ile B' DEĞİL 'A ve B' (gen_join nesne içindir, yüklem değil)."""
    from tantrium.language.fluent import narrate
    txt = narrate("egfr", {"ACTIVATES": ["ras"], "CAUSES": ["tumor growth"]})
    assert "etkinleştirir ile" not in txt
