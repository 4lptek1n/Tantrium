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


# ── Native özerklik kablolamaları (9 adet) ──
from tantrium.research.cognition import (
    SchedulePhase, CuriosityPhase, CodeGrowthPhase, GoalPhase, CognitionState,
    _DEFAULT_BATCH_PHASES, CognitionReport,
)


def test_all_autonomy_phases_registered():
    """9 kablolamanın faz-seviyesi olanları varsayılan döngüde (öksüz değil)."""
    names = [p.name for p in _DEFAULT_BATCH_PHASES]
    for need in ("schedule", "curiosity", "code_growth", "goal", "science", "verify", "flywheel"):
        assert need in names, need
    assert names[0] == "schedule"   # meta-kontrol ilk


def test_schedule_phase_sets_focus_and_budget():
    """SchedulePhase #8/#9: zayıf-eksenden odak + koridordan üretim-beam."""
    eng = _FakeEngine({})
    st = CognitionState()
    st.benchmark_score = 0.5            # dış-hata yüksek
    st.transport_corridor = -1e-5       # geniş koridor
    out = SchedulePhase().execute(eng, st)
    assert out.focus == "verify"
    assert out.prod_budget == 8         # geniş koridor → büyük beam


def test_autonomy_phases_noop_without_flag():
    """Ağ/ağır fazlar (#3,#6) _autonomy YOKKEN no-op — batch-test yavaşlamaz, çökmez."""
    eng = _FakeEngine({})               # _autonomy yok, _ai yok
    st = CognitionState()
    assert CuriosityPhase().execute(eng, st) is st
    assert CodeGrowthPhase().execute(eng, st) is st
    assert st.curiosity_researched == 0 and st.code_grown == 0


def test_auto_goal_clean_concept_filter():
    """#1 auto-goal yalnız temiz kavram seçer (sentetik/markup/paradigma değil)."""
    assert GoalPhase._clean_goal_concept("egfr")
    assert not GoalPhase._clean_goal_concept("⟨bridge:x⟩")
    assert not GoalPhase._clean_goal_concept("ALEPH:DYADIC_TRANSPORT")
    assert not GoalPhase._clean_goal_concept("oeis:A102283")


def test_auto_goal_failopen_on_minimal_engine():
    """#1 auto-goal fail-open: encoder'sız sahte engine'de çökmez (None döner)."""
    eng = _FakeEngine({})
    st = CognitionState()
    st.open_gap_names = ["egfr", "⟨bridge:x⟩"]
    g, gm = GoalPhase()._auto_goal(eng, st)   # encode_goal sahte engine'de başarısız → None
    assert g is None and gm is None           # fail-open, exception yok


def test_report_has_autonomy_fields():
    """CognitionReport 9-kablolama sayaçlarını taşır (raporlanabilir)."""
    r = CognitionReport(mode="batch", total_cycles=1, concepts_added=0, edges_added=0,
                        gaps_found=0, proofs_completed=0, elapsed_s=0.0)
    for f in ("relearned", "contradictions_resolved", "curiosity_researched",
              "hypotheses_tested", "artifacts_reingested", "code_grown",
              "hypotheses_generated"):
        assert hasattr(r, f), f
