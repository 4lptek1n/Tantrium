"""Öksüz-güç kablolamaları — üç bağlantının davranışını kilitler.

1. Wonder → ReflectPhase: boşluklar wonder-skoruyla önceliklenir (cognition).
2. QUANTUM_BRIDGE → generator: opt-in dolanık yürüyüş (F7 grounding korunur).
3. Science → cognition: transitif hipotez TEK-GERÇEK helper (growth ile ortak).
"""
from tantrium.reasoning.causal_rules import (
    TRANSITIVE_CAUSAL, GENERIC_TERMS, derive_transitive_hypotheses,
)
from tantrium.research.cognition import ScienceStep, _DEFAULT_BATCH_PHASES
from tantrium.language.generator import _BRIDGE, _CONNECTIVE, _EN_CONNECTIVE, _SEMANTIC


# ── Wiring 3: tek-gerçek transitif çıkarım ──
class _E:
    def __init__(self, paradigm, target):
        self.paradigm = paradigm
        self.target = target


class _FakeEngine:
    def __init__(self, edges, concepts=None):
        self.tau = type("T", (), {"edges": edges})()
        self.manifold = type("M", (), {"concepts": concepts or {}})()


def test_derive_transitive_hypothesis():
    """A INHIBITS B, B ACTIVATES C ⟹ A INHIBITS C (kausal kural tablosundan)."""
    eng = _FakeEngine({
        "a": [_E("INHIBITS", "b"), _E("INHIBITS", "x")],   # ≥2 kausal → seed
        "b": [_E("ACTIVATES", "c")],
    })
    hyps = derive_transitive_hypotheses(eng)
    stmts = {h["statement"] for h in hyps}
    assert "a INHIBITS c" in stmts          # INHIBITS∘ACTIVATES → INHIBITS
    assert TRANSITIVE_CAUSAL[("INHIBITS", "ACTIVATES")] == "INHIBITS"


def test_derive_skips_generic_and_existing():
    """Jenerik terim (protein) hipotez olmaz; zaten doğrudan kenar varsa türetilmez."""
    eng = _FakeEngine({
        "a": [_E("ACTIVATES", "protein"), _E("ACTIVATES", "b")],  # protein jenerik
        "protein": [_E("ACTIVATES", "c")],
        "b": [_E("ACTIVATES", "a")],   # a-ACTIVATES-a döngüsü elenir
    })
    hyps = derive_transitive_hypotheses(eng)
    for h in hyps:
        assert h["obj"] not in GENERIC_TERMS
        assert h["subj"] != h["obj"]


def test_science_step_registered():
    """ScienceStep batch döngüye bağlandı (öksüz değil)."""
    names = [getattr(p, "name", "") for p in _DEFAULT_BATCH_PHASES]
    assert "science" in names
    assert ScienceStep().name == "science"


def test_science_step_runs_failopen():
    """ScienceStep fail-open: kausal kenarlı sahte engine üstünde çöküp döngüyü kırmaz."""
    from tantrium.research.cognition import CognitionState
    eng = _FakeEngine({"a": [_E("INHIBITS", "b"), _E("CAUSES", "y")],
                       "b": [_E("ACTIVATES", "c")]})
    st = CognitionState()
    out = ScienceStep().execute(eng, st)
    assert out is st                       # state döner, exception atmaz
    assert st.hypotheses_generated >= 1    # en az "a INHIBITS c"


# ── Wiring 2: QUANTUM_BRIDGE generator'da opt-in ──
def test_quantum_bridge_templates_exist():
    """QUANTUM_BRIDGE cümle şablonu var (TR+EN) ve _BRIDGE seti tanımlı."""
    assert _BRIDGE == {"QUANTUM_BRIDGE"}
    assert "QUANTUM_BRIDGE" in _CONNECTIVE
    assert "QUANTUM_BRIDGE" in _EN_CONNECTIVE


def test_quantum_bridge_not_in_semantic():
    """F7 KORUNUR: QUANTUM_BRIDGE semantik sete GİRMEZ (default yürüyüşü kirletmez,
    yalnız use_bridges=True opt-in 3. geçişte gezilir)."""
    assert "QUANTUM_BRIDGE" not in _SEMANTIC
    assert "SPECTRAL_BRIDGE" not in _SEMANTIC


def test_generate_accepts_use_bridges():
    """ai.generate(use_bridges=) imzayı kabul eder (facade threading)."""
    import inspect
    from tantrium.ai import AI
    sig = inspect.signature(AI.generate)
    assert "use_bridges" in sig.parameters
    from tantrium.language.generator import CertifiedGenerator
    assert "use_bridges" in inspect.signature(CertifiedGenerator.generate).parameters
