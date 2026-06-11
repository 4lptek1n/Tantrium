"""Kausal çıkarım katmanı testleri.

Kapsam: _extract_relations, _normalize_entity, causal_chain() API.
"""
import pytest


# ─── _normalize_entity testleri ─────────────────────────────────────────────

def test_normalize_strips_pathway():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("ras pathway") == "ras"


def test_normalize_strips_activation():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("mek activation") == "mek"


def test_normalize_strips_enzyme():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("cox enzyme") == "cox"


def test_normalize_strips_kinase():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("egfr kinase") == "egfr"


def test_normalize_strips_proliferation():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("tumor cell proliferation") == "tumor cell"


def test_normalize_unchanged_short():
    from tantrium.research.autonomous import _normalize_entity
    assert _normalize_entity("ras") == "ras"
    assert _normalize_entity("egfr") == "egfr"


# ─── _extract_relations testleri ────────────────────────────────────────────

def test_extract_inhibits():
    from tantrium.research.autonomous import _extract_relations
    rels = _extract_relations("Erlotinib inhibits EGFR kinase.")
    assert any(r[0] == "erlotinib" and r[1] == "INHIBITS" and r[2] == "egfr" for r in rels)


def test_extract_activates():
    from tantrium.research.autonomous import _extract_relations
    rels = _extract_relations("EGFR activates RAS pathway.")
    assert any(r[0] == "egfr" and r[1] == "ACTIVATES" and r[2] == "ras" for r in rels)


def test_extract_causes():
    from tantrium.research.autonomous import _extract_relations
    rels = _extract_relations("RAS causes tumor cell proliferation.")
    assert any(r[0] == "ras" and r[1] == "CAUSES" and r[2] == "tumor cell" for r in rels)


def test_extract_multi_sentence():
    from tantrium.research.autonomous import _extract_relations
    text = "Aspirin inhibits COX enzyme. COX causes inflammation."
    rels = _extract_relations(text)
    assert len(rels) >= 2


def test_extract_and_split():
    from tantrium.research.autonomous import _extract_relations
    text = "Aspirin inhibits COX and ibuprofen activates inflammation."
    rels = _extract_relations(text)
    assert len(rels) >= 1  # en az 1 ilişki (kısa entity'ler filtrelenebilir)


# ─── causal_chain testleri ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ai_with_causal():
    import tantrium
    ai = tantrium.AI()
    ai.learn(
        "Erlotinib inhibits EGFR. EGFR activates RAS. "
        "RAS causes MEK activation. MEK causes ERK activation. "
        "ERK causes tumor cell proliferation."
    )
    return ai


def test_causal_chain_single_hop(ai_with_causal):
    ai = ai_with_causal
    ai.learn("Aspirin inhibits COX enzyme.")
    r = ai.causal_chain("COX", depth=4)
    assert r["n_paths"] >= 1
    assert any("aspirin" in str(a) for a in r["actionable"])


def test_causal_chain_multi_hop(ai_with_causal):
    r = ai_with_causal.causal_chain("tumor cell proliferation", depth=8)
    assert r["n_paths"] >= 1
    best = r["chains"][0]
    assert best["depth"] >= 3


def test_causal_chain_finds_erlotinib(ai_with_causal):
    r = ai_with_causal.causal_chain("tumor cell proliferation", depth=8)
    assert "erlotinib" in r["actionable"]


def test_causal_chain_empty_for_unknown(ai_with_causal):
    r = ai_with_causal.causal_chain("nonexistent_disease_xyz_999", depth=4)
    assert r["n_paths"] == 0


def test_causal_chain_case_insensitive(ai_with_causal):
    r1 = ai_with_causal.causal_chain("TUMOR CELL PROLIFERATION", depth=8)
    r2 = ai_with_causal.causal_chain("tumor cell proliferation", depth=8)
    # Her ikisi de en az 1 yol bulmalı (case-normalized aynı hedef)
    assert r1["n_paths"] >= 1
    assert r2["n_paths"] >= 1


def test_causal_chain_returns_dict_keys(ai_with_causal):
    r = ai_with_causal.causal_chain("tumor cell", depth=4)
    assert set(["goal", "chains", "actionable", "n_paths", "note"]).issubset(set(r.keys()))


def test_multiple_intervention_points():
    """Ayrı bir AI nesnesiyle izolasyon sağla."""
    import tantrium
    ai = tantrium.AI()
    ai.learn(
        "DrugAlpha inhibits TargetX. TargetX activates TargetY. "
        "TargetY causes DiseaseZ."
    )
    ai.learn(
        "DrugBeta inhibits TargetW. TargetW causes TargetY."
    )
    r = ai.causal_chain("DiseaseZ", depth=8)
    # En az 2 müdahale noktası: DrugAlpha ve DrugBeta
    assert len(r["actionable"]) >= 2
