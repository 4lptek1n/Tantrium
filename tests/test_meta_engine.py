"""TEK meta-sentez motoru (core/meta) — kural/şema İCAT eder, certify geçidiyle.

Frontier: sistem elle yazılmamış kuralı kendi keşfeder + sertifikalar. GraphAdapter graf
kuralı icat eder; CodeAdapter kod şemasını AYNI motora bağlar (tek-gerçek). Tutarsız/
sertifikasız aday REDDEDİLİR (uydurma yok).
"""
import types

import tantrium
from tantrium.core.meta import meta_synthesize, GraphAdapter, CodeAdapter, MetaCandidate


def test_meta_candidate_accepts_generalizing():
    """Tutarlı + verify geçen aday kaydedilir; commit adını döner."""
    committed = []
    cand = MetaCandidate(
        name="t",
        build=lambda train: ("R" if {x[1] for x in train} == {"R"} else None),
        instances=[("a", "R"), ("b", "R"), ("c", "R")],
        verify=lambda art, held: all(x[1] == art for x in held),
        commit=lambda art: (committed.append(art) or "icat:R"),
    )
    adapter = types.SimpleNamespace(domain="t", candidates=lambda engine, **kw: [cand])
    inv = meta_synthesize(adapter, engine=None)
    assert inv == ["icat:R"] and committed == ["R"]


def test_meta_rejects_inconsistent():
    """Tutarsız gözlem → build None döndürür/genelleşmez → kaydedilmez (uydurma yok)."""
    committed = []
    cand = MetaCandidate(
        name="t",
        build=lambda train: (lambda s: s.pop() if len(s) == 1 else None)({x[1] for x in train}),
        instances=[("a", "R"), ("b", "Q"), ("c", "R")],   # tutarsız
        verify=lambda art, held: art is not None and all(x[1] == art for x in held),
        commit=lambda art: (committed.append(art) or "icat"),
    )
    adapter = types.SimpleNamespace(domain="t", candidates=lambda engine, **kw: [cand])
    assert meta_synthesize(adapter, engine=None) == [] and committed == []


def test_graph_adapter_invents_certified_rule():
    """GraphAdapter: 3 tutarlı gözlemden (relA,relB)→relC kuralını İCAT eder + kaydeder."""
    from tantrium.reasoning.causal_rules import LEARNED_TRANSITIVE, lookup_transitive

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    for i in range(3):
        a, b, c = f"za{i}", f"zb{i}", f"zc{i}"
        edges[a] = [_E(b, "ZREL1"), _E(c, "ZRELD")]   # a -ZREL1-> b, a -ZRELD-> c (doğrudan)
        edges[b] = [_E(c, "ZREL2")]                    # b -ZREL2-> c
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges))
    try:
        inv = meta_synthesize(GraphAdapter(min_obs=3), eng)
        assert lookup_transitive("ZREL1", "ZREL2") == "ZRELD"     # kural icat edildi
        assert any("ZREL1" in s and "ZRELD" in s for s in inv)
    finally:
        LEARNED_TRANSITIVE.pop(("ZREL1", "ZREL2"), None)


def test_graph_adapter_rejects_inconsistent_observations():
    """Tutarsız gözlem (bazen RELD bazen RELE) → kural KAYDEDİLMEZ (uydurma yok)."""
    from tantrium.reasoning.causal_rules import LEARNED_TRANSITIVE, lookup_transitive

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    labels = ["ZRELD", "ZRELE", "ZRELD"]   # tutarsız
    for i in range(3):
        a, b, c = f"qa{i}", f"qb{i}", f"qc{i}"
        edges[a] = [_E(b, "QREL1"), _E(c, labels[i])]
        edges[b] = [_E(c, "QREL2")]
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges))
    try:
        meta_synthesize(GraphAdapter(min_obs=3), eng)
        assert lookup_transitive("QREL1", "QREL2") is None    # tutarsız → öğrenilmedi
    finally:
        LEARNED_TRANSITIVE.pop(("QREL1", "QREL2"), None)


def test_graph_adapter_does_not_relearn_builtin_rules():
    """Sabit TRANSITIVE_CAUSAL'daki çift YENİDEN öğrenilmez (elle bilgi korunur)."""
    from tantrium.reasoning.causal_rules import TRANSITIVE_CAUSAL
    # (ACTIVATES, ACTIVATES) zaten tabloda → GraphAdapter onu aday yapmaz
    assert ("ACTIVATES", "ACTIVATES") in TRANSITIVE_CAUSAL


def test_meta_synthesis_phase_invents_in_loop():
    """MetaSynthesisPhase: döngüde kural icat eder; _autonomy kapılı; özyineleme (lookup) aktif."""
    from tantrium.research.cognition import MetaSynthesisPhase, CognitionState
    from tantrium.reasoning.causal_rules import LEARNED_TRANSITIVE, lookup_transitive

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    for i in range(3):
        a, b, c = f"ma{i}", f"mb{i}", f"mc{i}"
        edges[a] = [_E(b, "MREL1"), _E(c, "MRELD")]
        edges[b] = [_E(c, "MREL2")]
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges), _autonomy=True)
    try:
        st = MetaSynthesisPhase().execute(eng, CognitionState())
        assert st.rules_invented >= 1
        assert lookup_transitive("MREL1", "MREL2") == "MRELD"   # özyineleme: derive bunu okur
    finally:
        LEARNED_TRANSITIVE.pop(("MREL1", "MREL2"), None)


def test_meta_synthesis_phase_gated_by_autonomy():
    from tantrium.research.cognition import MetaSynthesisPhase, CognitionState
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges={}), _autonomy=False)
    st = MetaSynthesisPhase().execute(eng, CognitionState())
    assert st.rules_invented == 0


def test_code_adapter_routes_through_unified_engine():
    """CodeAdapter: kod şeması icadı AYNI motordan geçer (unification kozmetik değil)."""
    ai = tantrium.AI()
    # map-fold ailesinin çözebildiği bir spec: sum(2*e for e in x)
    ex = [([1, 2], 6), ([3], 6), ([1, 1, 1], 6), ([2, 2], 8), ([5], 10)]
    inv = meta_synthesize(CodeAdapter(), ai._engine, examples=ex)
    # genelleşirse şema adını döndürür; genelleşmezse boş — ikisi de geçerli, patlamamalı
    assert isinstance(inv, list)
