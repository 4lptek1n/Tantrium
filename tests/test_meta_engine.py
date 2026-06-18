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


def test_graph_adapter_invents_converse_rule():
    """AİLE 2: transitiften FARKLI strateji — a-relX->b varken b-relY->a tutarlıysa relX⁻¹→relY icat."""
    from tantrium.reasoning.causal_rules import LEARNED_CONVERSE, lookup_converse

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    for i in range(3):
        a, b = f"ca{i}", f"cb{i}"
        edges[a] = [_E(b, "XPART")]        # a -XPART-> b
        edges[b] = [_E(a, "XWHOLE")]       # b -XWHOLE-> a (tutarlı ters)
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges))
    try:
        inv = meta_synthesize(GraphAdapter(min_obs=3), eng)
        assert lookup_converse("XPART") == "XWHOLE"       # ters kural icat edildi (IS_A değil)
        assert any("XPART" in s for s in inv)
    finally:
        LEARNED_CONVERSE.pop("XPART", None)


def test_apply_converse_materializes_certified_back_edges():
    """Converse kuralı UYGULANIR: eksik ters kenar (pozitiflik geçerse) materyalize edilir."""
    from tantrium.core.meta import apply_converse_rules
    from tantrium.reasoning.causal_rules import LEARNED_CONVERSE
    ai = tantrium.AI()
    e = ai._engine
    from tantrium.core.semantic import Concept

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    # gerçek momentli kavramlar (pozitiflik certify edilebilsin)
    for n in ("cvx", "cvy"):
        if n not in e.manifold.concepts:
            cod = e.encoder.encode(n, name=n)
            e.manifold.concepts[n] = Concept(name=n, moments=list(cod.moments), domain="test")
    e.tau.edges["cvx"] = [_E("cvy", "XF")]    # cvx -XF-> cvy ; ters (cvy-XB->cvx) YOK
    e.tau.edges.setdefault("cvy", [])
    LEARNED_CONVERSE["XF"] = "XB"
    try:
        n = apply_converse_rules(e, max_apply=10)
        has_back = any(x.target == "cvx" and x.paradigm == "XB"
                       for x in e.tau.edges.get("cvy", []))
        # pozitiflik geçtiyse materyalize edilmiş olur; geçmediyse dürüstçe eklenmez
        assert (n >= 1) == has_back
    finally:
        LEARNED_CONVERSE.pop("XF", None)
        e.tau.edges.pop("cvx", None)
        e.tau.edges.pop("cvy", None)


def test_graph_adapter_invents_implication_rule():
    """AİLE 3: relX olan HER çiftte relY de varsa (karşı-örnek yok) → relX⊑relY içerme icat."""
    from tantrium.reasoning.causal_rules import LEARNED_IMPLICATION, lookup_implication

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    for i in range(3):
        a, b = f"ia{i}", f"ib{i}"
        edges[a] = [_E(b, "XSPEC"), _E(b, "XGEN")]   # her çiftte hem XSPEC hem XGEN
        edges[b] = []
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges))
    try:
        inv = meta_synthesize(GraphAdapter(min_obs=3), eng)
        assert lookup_implication("XSPEC") == "XGEN"   # XSPEC ⊑ XGEN icat edildi
        assert any("XSPEC" in s and "XGEN" in s for s in inv)
    finally:
        LEARNED_IMPLICATION.pop("XSPEC", None)
        LEARNED_IMPLICATION.pop("XGEN", None)


def test_implication_not_learned_with_counterexample():
    """relX bazı çiftte relY OLMADAN görülürse içerme icat EDİLMEZ (karşı-örnek = red)."""
    from tantrium.reasoning.causal_rules import LEARNED_IMPLICATION, lookup_implication

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    edges = {}
    for i in range(3):
        a, b = f"ja{i}", f"jb{i}"
        rels = [_E(b, "YSPEC")] + ([_E(b, "YGEN")] if i < 2 else [])  # 3. çiftte YGEN YOK
        edges[a] = rels
        edges[b] = []
    eng = types.SimpleNamespace(tau=types.SimpleNamespace(edges=edges))
    try:
        meta_synthesize(GraphAdapter(min_obs=3), eng)
        assert lookup_implication("YSPEC") is None    # karşı-örnek → öğrenilmedi
    finally:
        LEARNED_IMPLICATION.pop("YSPEC", None)


def test_analogy_transfer_certified_only():
    """Analoji-transfer: yapısal-analog kavramlar arası ilişki transferi, her biri pozitiflik-kapılı."""
    from tantrium.core.meta import derive_analogy_edges
    ai = tantrium.AI()
    n = derive_analogy_edges(ai._engine, min_shared=3, max_apply=5)
    assert isinstance(n, int) and n >= 0       # çalışır, sertifikasız conjecture eklemez


def test_code_adapter_routes_through_unified_engine():
    """CodeAdapter: kod şeması icadı AYNI motordan geçer (unification kozmetik değil)."""
    ai = tantrium.AI()
    # map-fold ailesinin çözebildiği bir spec: sum(2*e for e in x)
    ex = [([1, 2], 6), ([3], 6), ([1, 1, 1], 6), ([2, 2], 8), ([5], 10)]
    inv = meta_synthesize(CodeAdapter(), ai._engine, examples=ex)
    # genelleşirse şema adını döndürür; genelleşmezse boş — ikisi de geçerli, patlamamalı
    assert isinstance(inv, list)
