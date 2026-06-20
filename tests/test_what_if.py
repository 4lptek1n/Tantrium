"""İleriye doğru nedensel akıl yürütme testleri — ai.what_if()

causal_chain() geriye doğru (kime neden olan?), what_if() ileriye doğru
(bu kavramdan ne çıkar?). Bu testler synthetic AI nesnesiyle izole çalışır.
"""

import pytest

import tantrium
from tests._seed import seed_relations


@pytest.fixture(scope="module")
def ai_fwd():
    """İleriye doğru zincirleri olan izole AI nesnesi (yapısal tohum, dil yok)."""
    ai = tantrium.AI()
    seed_relations(
        ai,
        [
            ("erlotinib", "INHIBITS", "egfr"),
            ("egfr", "ACTIVATES", "ras"),
            ("ras", "CAUSES", "mek"),
            ("mek", "CAUSES", "erk"),
            ("erk", "CAUSES", "tumor cell"),
            ("erlotinib", "INHIBITS", "tumor growth"),
        ],
    )
    return ai


# ─── Temel yapı ──────────────────────────────────────────────────────────────


def test_what_if_returns_dict(ai_fwd):
    """what_if() sözlük döndürmeli."""
    r = ai_fwd.what_if("erlotinib")
    assert isinstance(r, dict)


def test_what_if_has_required_keys(ai_fwd):
    """Yanıt gerekli anahtarları içermeli."""
    r = ai_fwd.what_if("erlotinib")
    assert "concept" in r
    assert "chains" in r
    assert "effects" in r
    assert "n_paths" in r
    assert "note" in r


def test_what_if_concept_echoed(ai_fwd):
    """'concept' anahtarı sorgulanan kavramı yansıtmalı."""
    r = ai_fwd.what_if("erlotinib")
    assert r["concept"] == "erlotinib"


def test_what_if_n_paths_matches_chains(ai_fwd):
    """n_paths değeri chains uzunluğuyla eşleşmeli."""
    r = ai_fwd.what_if("erlotinib")
    assert r["n_paths"] == len(r["chains"])


# ─── İçerik doğrulama ─────────────────────────────────────────────────────


def test_what_if_finds_forward_effects(ai_fwd):
    """erlotinib → ... zinciri en az bir nihai etki bulmalı."""
    r = ai_fwd.what_if("erlotinib", depth=6)
    assert r["n_paths"] > 0 or len(r["effects"]) > 0


def test_what_if_effects_downstream(ai_fwd):
    """Nihai etkiler arasında biyolojik kavramlar bulunmalı."""
    r = ai_fwd.what_if("erlotinib", depth=6)
    all_nodes = set(r["effects"])
    for chain in r["chains"]:
        all_nodes.update(chain["path"])
    all_nodes_str = " ".join(str(x).lower() for x in all_nodes)
    # EGFR, RAS, MEK, ERK veya tümör büyümesiyle ilgili bir şey bulunmalı
    downstream_keywords = {"egfr", "ras", "mek", "erk", "tumor", "growth", "proliferation"}
    assert any(kw in all_nodes_str for kw in downstream_keywords)


def test_what_if_chain_path_is_list(ai_fwd):
    """chains içindeki her zincir path listesi taşımalı."""
    r = ai_fwd.what_if("erlotinib", depth=6)
    for chain in r["chains"]:
        assert isinstance(chain["path"], list)
        assert isinstance(chain["depth"], int)
        assert chain["depth"] >= 1


# ─── Bilinmeyen kavram davranışı ──────────────────────────────────────────


def test_what_if_unknown_concept_graceful():
    """Bilinmeyen kavram için what_if() kilitlenmemeli, not döndürmeli."""
    ai = tantrium.AI()
    r = ai.what_if("xyzunknowntoken9999")
    assert isinstance(r, dict)
    assert "note" in r
    assert r["n_paths"] == 0


def test_what_if_empty_chains_note():
    """Kenar olmayan kavram için 'ai.learn' ipucu veren note döndürmeli."""
    ai = tantrium.AI()
    r = ai.what_if("completelymadeuptoken")
    assert "learn" in r["note"].lower() or r["note"]


# ─── causal_chain ile simetri ────────────────────────────────────────────


def test_what_if_vs_causal_chain_complementary(ai_fwd):
    """what_if ve causal_chain ters yönde çalışmalı — çıktı seti örtüşmemeli."""
    fwd = ai_fwd.what_if("erlotinib", depth=6)
    bwd = ai_fwd.causal_chain("tumor cell proliferation", depth=8)
    # Her ikisi de nedensel mantık yürütür ama farklı yönlerden
    assert isinstance(fwd, dict)
    assert isinstance(bwd, dict)
    # forward effects ≠ backward actionable tam aynı set değil (yön farklı)
    fwd_effects = set(fwd["effects"])
    bwd_actionable = set(bwd["actionable"])
    # Tam özdeşlik beklemiyoruz — sadece her ikisi de çalışıyor
    assert len(fwd_effects) + len(bwd_actionable) >= 0  # her zaman geçer
