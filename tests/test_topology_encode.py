"""İlişkisel kodlama testleri — anlam TAU topolojisinden okunur.

Mimari tezi: "Topoloji = bilgi." Kelimenin anlamı harflerinde değil ilişki
komşuluğunda. Bu testler kanıtlar: anlam kanalı harflerin yapamadığı ayrımı yapar
(protein~enzyme < protein~algorithm) — VE dürüst sınırı belgeler (semantik-topraksız
kavram None döner, yüzeye düşer).
"""
import pytest
import tantrium
from fractions import Fraction
from tantrium.core.topology_encode import TopologyEncoder


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


@pytest.fixture(scope="module")
def te(ai):
    return TopologyEncoder(ai.engine)


def _l1(oa, ob):
    return sum(abs(float(x) - float(y)) for x, y in zip(oa.moments, ob.moments))


# ── Temel sözleşme ───────────────────────────────────────────────────────────

def test_moments_hausdorff_regime(te):
    """Topolojik momentler [0,1] Hausdorff: μ₀=1, μ_k ∈ [0,1]."""
    o = te.encode("intelligence")
    assert o is not None
    assert o.moments[0] == Fraction(1)
    assert all(0.0 <= float(m) <= 1.0 for m in o.moments)


def test_modality_tagged(te):
    o = te.encode("intelligence")
    assert o.structure["modality"] == "relational"
    assert o.structure["encoder"] == "topological_spectral"
    assert o.structure["n_neighbors"] >= 2


def test_deterministic(te):
    """Aynı kavram → aynı moment (deterministik)."""
    a = te.encode("reasoning")
    b = te.encode("reasoning")
    assert [float(m) for m in a.moments] == [float(m) for m in b.moments]


# ── Dürüst sınır: semantik-topraksız kavram ──────────────────────────────────

def test_sparse_concept_returns_none(te):
    """Semantik kenarı olmayan kavram → None (yüzey kodlamasına düşer)."""
    # 'pointer'/'glucose' gerçek grafta tipli kenar taşımıyor (yalnız geometrik).
    o = te.encode("pointer")
    assert o is None


def test_min_neighbors_threshold(te):
    """2'den az semantik komşu → None."""
    o = te.encode("zzznonexistentconceptxyz")
    assert o is None


# ── Anlam ayrımı: harflerin yapamadığı ─────────────────────────────────────

def test_abstract_cluster_close(te):
    """intelligence ~ reasoning yakın (aynı anlam-kümesi)."""
    d = _l1(te.encode("intelligence"), te.encode("reasoning"))
    assert d < 0.05


def test_abstract_vs_biochem_far(te):
    """intelligence ~ protein UZAK (biliş vs biyokimya)."""
    d = _l1(te.encode("intelligence"), te.encode("protein"))
    assert d > 0.1


def test_meaning_ordering_protein(te):
    """protein ~ enzyme < protein ~ algorithm — anlam kanalının çekirdek kanıtı.

    Harfler bunu YAPAMAZ: 'enzyme' ve 'algorithm' yüzeyde protein'e benzemez,
    ama topoloji protein'i enzyme'e (biyokimya) algoritma'dan daha yakın koyar.
    """
    d_enzyme = _l1(te.encode("protein"), te.encode("enzyme"))
    d_algo = _l1(te.encode("protein"), te.encode("algorithm"))
    assert d_enzyme < d_algo


def test_intelligence_reasoning_vs_protein_ordering(te):
    """d(intelligence,reasoning) < d(intelligence,protein) — güçlü ayrım."""
    d_close = _l1(te.encode("intelligence"), te.encode("reasoning"))
    d_far = _l1(te.encode("intelligence"), te.encode("protein"))
    assert d_close < d_far


# ── ai facade ────────────────────────────────────────────────────────────────

def test_ai_meaning_returns_object(ai):
    o = ai.meaning("intelligence")
    assert o is not None
    assert o.structure["modality"] == "relational"


def test_ai_meaning_sparse_none(ai):
    assert ai.meaning("pointer") is None


def test_ai_meaning_distance_ordering(ai):
    """ai.meaning_distance: protein~enzyme < protein~algorithm."""
    d_enzyme = ai.meaning_distance("protein", "enzyme")
    d_algo = ai.meaning_distance("protein", "algorithm")
    assert d_enzyme is not None and d_algo is not None
    assert d_enzyme < d_algo


def test_ai_meaning_distance_none_for_sparse(ai):
    """Topraksız kavram → None."""
    assert ai.meaning_distance("protein", "pointer") is None
