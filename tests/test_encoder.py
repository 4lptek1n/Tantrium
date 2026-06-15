"""Tests for the UniversalEncoder in tantrium.core.encoder."""
from fractions import Fraction

import pytest

from tantrium.core.encoder import encode, encode_smiles
from tantrium.core.codex import CertifiableObject


# ─── encode() ────────────────────────────────────────────────────────────────

def test_encode_text_returns_certifiable_object():
    obj = encode("hello world")
    assert isinstance(obj, CertifiableObject)


def test_encode_text_has_eight_moments():
    obj = encode("hello world")
    assert len(obj.moments) == 8


def test_encode_text_moments_are_fractions():
    obj = encode("hello world")
    for m in obj.moments:
        assert isinstance(m, Fraction)


def test_encode_text_moments_non_negative():
    """ALEPH = positivity: all spectral moments must be ≥ 0."""
    obj = encode("hello world")
    assert all(m >= 0 for m in obj.moments)


def test_encode_text_has_structure_dict():
    obj = encode("hello world")
    assert isinstance(obj.structure, dict)
    assert len(obj.structure) > 0


def test_encode_text_structure_has_eigenvalues():
    obj = encode("hello world")
    assert "eigenvalues" in obj.structure


def test_encode_text_structure_has_real_determinant():
    """real_determinant key must be present (ZAYIN real det fix)."""
    obj = encode("hello world")
    assert "real_determinant" in obj.structure


def test_encode_text_structure_has_fixed_point():
    """TAV Picard iteration must produce a fixed_point key."""
    obj = encode("hello world")
    assert "fixed_point" in obj.structure


# ─── encode_smiles() ─────────────────────────────────────────────────────────

def test_encode_smiles_ethanol_returns_object():
    obj = encode_smiles("CCO")
    assert isinstance(obj, CertifiableObject)


def test_encode_smiles_ethanol_has_eight_moments():
    obj = encode_smiles("CCO")
    assert len(obj.moments) == 8


def test_encode_smiles_benzene_returns_object():
    obj = encode_smiles("c1ccccc1")
    assert isinstance(obj, CertifiableObject)


def test_encode_smiles_moments_non_negative():
    """ALEPH positivity: Morgan-fingerprint moments must be ≥ 0."""
    for smiles in ("CCO", "c1ccccc1"):
        obj = encode_smiles(smiles)
        assert all(m >= 0 for m in obj.moments), f"Negative moment in {smiles}"


def test_encode_smiles_ethanol_has_real_determinant():
    obj = encode_smiles("CCO")
    assert "real_determinant" in obj.structure


def test_ethanol_benzene_have_different_eigenvalues():
    """DALET is real: different molecules must produce different eigenvalues."""
    eth = encode_smiles("CCO")
    benz = encode_smiles("c1ccccc1")
    assert eth.structure["eigenvalues"] != benz.structure["eigenvalues"]


def test_ethanol_benzene_have_different_fixed_points():
    """TAV is real: different molecules must converge to different fixed points."""
    eth = encode_smiles("CCO")
    benz = encode_smiles("c1ccccc1")
    assert eth.structure["fixed_point"] != benz.structure["fixed_point"]


# ─── Edge cases ───────────────────────────────────────────────────────────────

def test_encode_empty_string_returns_valid_object():
    """Empty string must not raise and must return a valid CertifiableObject."""
    obj = encode("")
    assert isinstance(obj, CertifiableObject)
    assert len(obj.moments) == 8
    # Moments must all be non-negative even for empty input
    assert all(m >= 0 for m in obj.moments)


def test_encode_name_propagates():
    obj = encode("test input", name="my_concept")
    assert obj.name == "my_concept"


def test_encode_smiles_name_propagates():
    obj = encode_smiles("CCO", name="ethanol")
    assert obj.name == "ethanol"


# ─── Encoder collision KÖK çözüm (F1/F5: pozisyon+codepoint imza) ────────────

def _l1(a: str, b: str) -> float:
    ma = [float(m) for m in encode(a).moments]
    mb = [float(m) for m in encode(b).moments]
    return sum(abs(x - y) for x, y in zip(ma, mb))


def test_collision_all_unique_chars_separated():
    """protein/glucose (7 char, tam çeşitlilik, eski yol-grafı izomorfizmi) AYRIŞIR.

    Eski label_aware bigram L1≈0.0026 (ince). Yeni imza encoding: L1 > 0.1 (sağlam).
    """
    assert _l1("protein", "glucose") > 0.1, "tüm-farklı-karakter çakışması çözülmeli"


def test_collision_anagrams_separated():
    """Anagramlar (aynı harf kümesi, farklı sıra) AYRIŞIR — pozisyon bilgisi taşınır."""
    assert _l1("protein", "pointer") > 0.1, "anagram protein/pointer ayrışmalı"
    assert _l1("listen", "silent") > 0.1, "anagram listen/silent ayrışmalı"


def test_collision_identity_zero():
    """Aynı metin → tam sıfır mesafe (determinizm)."""
    assert _l1("protein", "protein") == 0.0


def test_signature_moments_hausdorff_range():
    """İmza momentleri [0,1] Hausdorff rejiminde (μ₀=1, azalan), SMILES ile tutarlı."""
    mu = [float(m) for m in encode("protein").moments]
    assert abs(mu[0] - 1.0) < 1e-9, "μ₀=1"
    assert all(0.0 <= m <= 1.0 for m in mu), "tüm momentler [0,1]"


def test_short_text_certifies():
    """Kısa kelimeler (DNA/ATP, az karakter) regülarizasyonla ALEPH-PSD geçer."""
    for w in ("DNA", "ATP", "RNA", "cat"):
        obj = encode(w)
        H = obj.hankel(4)
        # Sylvester: lider asal minörler ≥ 0 (PSD)
        assert obj.is_moment_sequence(), f"{w} geçerli moment dizisi (Hankel PSD) olmalı"


# ───────────── ASI §12 P1: Kod modalitesi (kod = AST grafı = topoloji) ─────────────

def test_code_strict_detection():
    """STRICT: gerçek kod True; kelime/cümle/molekül/SMILES kod DEĞİL (regresyon)."""
    from tantrium.core.encoder import _is_code_snippet
    assert _is_code_snippet("def add(a, b): return a + b")
    assert _is_code_snippet("for i in range(10):\n    total += i")
    assert not _is_code_snippet("protein")
    assert not _is_code_snippet("the cat sat on the mat")
    assert not _is_code_snippet("CC(=O)Oc1ccccc1C(=O)O")   # aspirin SMILES


def test_code_moments_valid_hausdorff():
    """Kod momentleri [0,1] Hausdorff dizisi (SMILES rejimi)."""
    from tantrium.core.encoder import _code_to_graph_moments
    m = _code_to_graph_moments("def f(x):\n    return x * 2 + 1")
    assert m is not None and m[0] == 1
    assert all(0.0 <= float(x) <= 1.0001 for x in m)


def test_code_structure_name_invariant():
    """Kod YAPISAL topolojiyle girer: isim-değişmez (refactor denkliği), yapı-duyarlı."""
    from tantrium.core.encoder import _code_to_graph_moments
    from tantrium.core.metric import l1_distance
    f = [float(x) for x in _code_to_graph_moments("def f(x):\n    return x + 1")]
    g = [float(x) for x in _code_to_graph_moments("def g(y):\n    return y + 2")]
    loop = [float(x) for x in _code_to_graph_moments(
        "for i in range(10):\n    total += i\n    print(total)")]
    assert l1_distance(f, g) < 1e-6           # aynı yapı, farklı isim → AYNI moment
    assert l1_distance(f, loop) > l1_distance(f, g)   # farklı yapı → uzak


def test_code_routes_through_encode():
    """encode() kod parçasını AST-graf yoluna yönlendirir (bigram metin değil)."""
    from tantrium.core.encoder import UniversalEncoder
    obj = UniversalEncoder().encode("def f(x):\n    return x * 2")
    assert obj.structure.get("moment_path") == "code_ast_graph"
    # kelime hâlâ metin yolunda
    w = UniversalEncoder().encode("protein")
    assert w.structure.get("moment_path") != "code_ast_graph"
