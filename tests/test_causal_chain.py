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

# ─── causal_chain testleri ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def ai_with_causal():
    import tantrium
    from tests._seed import seed_relations

    # İZOLE adlar (gerçek 107k manifoldla çakışmasın) — erlotinib/egfr gerçek düğümler,
    # kendi gerçek kenarlarıyla BFS'i kirletirdi. Uydurma adlar yalnız tohumlanan zinciri verir.
    ai = tantrium.AI()
    seed_relations(
        ai,
        [
            ("zdrugx", "INHIBITS", "zgenea"),
            ("zgenea", "ACTIVATES", "zpathb"),
            ("zpathb", "CAUSES", "zkinc"),
            ("zkinc", "CAUSES", "zkind"),
            ("zkind", "CAUSES", "zdiseasee"),
            ("zaspirinx", "INHIBITS", "zcoxy"),
        ],
    )
    return ai


def test_causal_chain_single_hop(ai_with_causal):
    ai = ai_with_causal
    r = ai.causal_chain("zcoxy", depth=4)
    assert r["n_paths"] >= 1
    assert any("zaspirinx" in str(a) for a in r["actionable"])


def test_causal_chain_multi_hop(ai_with_causal):
    """En az 1 çok-adımlı (depth>=3) zincir bulunmalı."""
    r = ai_with_causal.causal_chain("zdiseasee", depth=8)
    assert r["n_paths"] >= 1
    # BFS en kısa zinciri önce döndürür; çok-adımlı zincir listede bir yerdedir
    assert any(ch["depth"] >= 3 for ch in r["chains"])


def test_causal_chain_finds_root_intervention(ai_with_causal):
    r = ai_with_causal.causal_chain("zdiseasee", depth=8)
    assert "zdrugx" in r["actionable"]


def test_causal_chain_empty_for_unknown(ai_with_causal):
    r = ai_with_causal.causal_chain("nonexistent_disease_xyz_999", depth=4)
    assert r["n_paths"] == 0


def test_causal_chain_case_insensitive(ai_with_causal):
    r1 = ai_with_causal.causal_chain("ZDISEASEE", depth=8)
    r2 = ai_with_causal.causal_chain("zdiseasee", depth=8)
    # Her ikisi de en az 1 yol bulmalı (case-normalized aynı hedef)
    assert r1["n_paths"] >= 1
    assert r2["n_paths"] >= 1


def test_causal_chain_returns_dict_keys(ai_with_causal):
    r = ai_with_causal.causal_chain("zkind", depth=4)
    assert {"goal", "chains", "actionable", "n_paths", "note"}.issubset(set(r.keys()))


def test_multiple_intervention_points():
    """Ayrı bir AI nesnesiyle izolasyon sağla."""
    import tantrium
    from tests._seed import seed_relations

    ai = tantrium.AI()
    seed_relations(
        ai,
        [
            ("drugalpha", "INHIBITS", "targetx"),
            ("targetx", "ACTIVATES", "targety"),
            ("targety", "CAUSES", "diseasez"),
            ("drugbeta", "INHIBITS", "targetw"),
            ("targetw", "CAUSES", "targety"),
        ],
    )
    r = ai.causal_chain("diseasez", depth=8)
    # En az 2 müdahale noktası: DrugAlpha ve DrugBeta
    assert len(r["actionable"]) >= 2
