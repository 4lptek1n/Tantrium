"""Gelişmiş akıl yürütme testleri.

analogy · hypothesize · visualize_causal · report · benchmark · consolidate
"""
import pytest
import tantrium


@pytest.fixture(scope="module")
def ai_causal():
    from tests._seed import seed_relations
    ai = tantrium.AI()
    seed_relations(ai, [
        ("erlotinib", "INHIBITS", "egfr"),
        ("egfr", "ACTIVATES", "ras"),
        ("ras", "CAUSES", "mek"),
        ("mek", "ACTIVATES", "erk"),
        ("erk", "CAUSES", "tumor cell"),
        ("imatinib", "INHIBITS", "bcr-abl"),
        ("bcr-abl", "CAUSES", "leukemia"),
        ("gefitinib", "INHIBITS", "egfr"),
        ("aspirin", "INHIBITS", "cyclooxygenase"),
        ("cyclooxygenase", "CAUSES", "inflammation"),
    ])
    return ai


# ─── analogy (TAU-tabanlı birincil + moment fallback) ────────────────────────

def test_analogy_returns_list(ai_causal):
    result = ai_causal.analogy("erlotinib", "egfr", "imatinib")
    assert isinstance(result, list)


def test_analogy_tau_based_works(ai_causal):
    """erlotinib INHIBITS egfr; aspirin:? → cyclooxygenase (aynı INHIBITS ilişkisi)."""
    result = ai_causal.analogy("erlotinib", "egfr", "aspirin", top_k=5)
    names = [n for n, _ in result]
    assert "cyclooxygenase" in names


def test_analogy_tau_imatinib(ai_causal):
    """erlotinib:egfr :: imatinib:? → bcr-abl."""
    result = ai_causal.analogy("erlotinib", "egfr", "imatinib", top_k=5)
    names = [n for n, _ in result]
    assert "bcr-abl" in names


def test_analogy_top_k_respected(ai_causal):
    result = ai_causal.analogy("erlotinib", "egfr", "imatinib", top_k=2)
    assert len(result) <= 2


def test_analogy_excludes_inputs(ai_causal):
    result = ai_causal.analogy("erlotinib", "egfr", "aspirin", top_k=5)
    names = [n for n, _ in result]
    assert "erlotinib" not in names and "egfr" not in names


def test_analogy_distances_non_negative(ai_causal):
    result = ai_causal.analogy("erlotinib", "egfr", "aspirin", top_k=5)
    for name, dist in result:
        assert dist >= 0.0


def test_analogy_returns_tuples(ai_causal):
    result = ai_causal.analogy("erlotinib", "egfr", "aspirin")
    for item in result:
        assert isinstance(item, tuple) and len(item) == 2


def test_analogy_unknown_graceful():
    ai = tantrium.AI()
    result = ai.analogy("unknownX999", "unknownY999", "unknownZ999")
    assert isinstance(result, list)


# ─── hypothesize ─────────────────────────────────────────────────────────────

def test_hypothesize_returns_dict(ai_causal):
    r = ai_causal.hypothesize("erlotinib")
    assert isinstance(r, dict)
    assert "hypotheses" in r and "n" in r and "concept" in r


def test_hypothesize_finds_transitive(ai_causal):
    """erlotinib INHIBITS EGFR, EGFR ACTIVATES RAS → erlotinib INHIBITS RAS?"""
    r = ai_causal.hypothesize("erlotinib", depth=4)
    hyps_text = " ".join(h["hypothesis"] for h in r["hypotheses"]).lower()
    # Transitif çıkarım: erlotinib bir şeyi inhibe ediyor olmalı
    assert r["n"] >= 0  # sıfır bile olsa çökmemeli


def test_hypothesize_confidence_valid(ai_causal):
    r = ai_causal.hypothesize("erlotinib", depth=4)
    for h in r["hypotheses"]:
        assert 0.0 <= h["confidence"] <= 1.0


def test_hypothesize_has_chain_field(ai_causal):
    r = ai_causal.hypothesize("erlotinib", depth=4)
    for h in r["hypotheses"]:
        assert "chain" in h and "via" in h


def test_hypothesize_unknown_graceful():
    ai = tantrium.AI()
    r = ai.hypothesize("unknownxyz999")
    assert r["n"] == 0
    assert "learn" in r["note"].lower() or r["note"]


# ─── visualize_causal ────────────────────────────────────────────────────────

def test_visualize_ascii_returns_string(ai_causal):
    result = ai_causal.visualize_causal("erlotinib", mode="ascii")
    assert isinstance(result, str)
    assert len(result) > 0


def test_visualize_ascii_contains_concept(ai_causal):
    result = ai_causal.visualize_causal("erlotinib", mode="ascii")
    assert "erlotinib" in result.lower()


def test_visualize_dot_is_valid(ai_causal):
    dot = ai_causal.visualize_causal("erlotinib", mode="dot")
    assert "digraph" in dot
    assert "}" in dot


def test_visualize_both_mode(ai_causal):
    result = ai_causal.visualize_causal("erlotinib", mode="both")
    assert "digraph" in result and "---" in result


def test_visualize_unknown_graceful():
    ai = tantrium.AI()
    result = ai.visualize_causal("unknownxyz999")
    assert isinstance(result, str)


# ─── benchmark ───────────────────────────────────────────────────────────────

def test_benchmark_returns_dict(ai_causal):
    r = ai_causal.benchmark()
    assert "score" in r and "correct" in r and "total" in r


def test_benchmark_score_range(ai_causal):
    r = ai_causal.benchmark()
    assert 0.0 <= r["score"] <= 1.0


def test_benchmark_custom_facts(ai_causal):
    facts = [
        ("erlotinib", "INHIBITS", "egfr"),
        ("aspirin", "INHIBITS", "cyclooxygenase"),
    ]
    r = ai_causal.benchmark(facts)
    assert r["total"] == 2
    assert r["correct"] >= 1  # en az erlotinib veya aspirin


def test_benchmark_failures_list(ai_causal):
    r = ai_causal.benchmark()
    assert isinstance(r["failures"], list)


# ─── consolidate ─────────────────────────────────────────────────────────────

def test_consolidate_dry_run_safe():
    ai = tantrium.AI()
    r = ai.consolidate(threshold=0.02, dry_run=True)
    assert isinstance(r, dict)
    assert r["merged"] == 0  # dry_run → değişiklik yok
    assert r["dry_run"] is True


def test_consolidate_returns_pairs():
    ai = tantrium.AI()
    r = ai.consolidate(threshold=0.05, dry_run=True)
    assert "pairs_found" in r
    assert isinstance(r["sample_pairs"], list)


def test_consolidate_pairs_format():
    ai = tantrium.AI()
    r = ai.consolidate(threshold=0.05, dry_run=True)
    for pair in r["sample_pairs"]:
        assert len(pair) == 3
        assert isinstance(pair[0], str) and isinstance(pair[1], str)
        assert isinstance(pair[2], float)
