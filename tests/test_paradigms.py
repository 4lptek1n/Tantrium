"""Tests for paradigm definitions in tantrium.agi.core.codex."""
import pytest

from tantrium.agi.core.codex import (
    PARADIGMS,
    PARADIGM_BY_ID,
    CertifiableObject,
    ParadigmResult,
    PositivityParadigm,
    SpectralParadigm,
    FixedPointParadigm,
    ConsistencyParadigm,
)
from tantrium.agi.core.encoder import encode


# ─── PARADIGMS list ───────────────────────────────────────────────────────────

def test_paradigms_list_has_23_items():
    assert len(PARADIGMS) == 23


def test_paradigm_by_id_has_23_keys():
    assert len(PARADIGM_BY_ID) == 23


def test_paradigm_by_id_keys_match_list_ids():
    list_ids = {p.paradigm_id for p in PARADIGMS}
    dict_ids = set(PARADIGM_BY_ID.keys())
    assert list_ids == dict_ids


# ─── Paradigm object attributes ──────────────────────────────────────────────

def test_each_paradigm_has_id():
    for p in PARADIGMS:
        assert isinstance(p.paradigm_id, str)
        assert len(p.paradigm_id) > 0


def test_each_paradigm_has_name():
    for p in PARADIGMS:
        assert isinstance(p.name, str)
        assert len(p.name) > 0


def test_each_paradigm_has_theorem():
    """Paradigms store their theorem (analogous to a description) in .theorem."""
    for p in PARADIGMS:
        assert hasattr(p, "theorem")
        assert isinstance(p.theorem, str)


def test_each_paradigm_has_depends_on():
    for p in PARADIGMS:
        assert hasattr(p, "depends_on")
        assert isinstance(p.depends_on, list)


def test_known_paradigm_ids_present():
    ids = PARADIGM_BY_ID.keys()
    for expected in ("ALEPH", "DALET", "TAV", "EMET"):
        assert expected in ids, f"Expected paradigm '{expected}' not found"


# ─── ParadigmResult ───────────────────────────────────────────────────────────

def test_paradigm_result_has_status():
    obj = encode("test")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert hasattr(result, "status")


def test_paradigm_result_status_is_valid_string():
    obj = encode("test")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert result.status in ("CERTIFIED", "BLOCKED", "UNKNOWN")


def test_paradigm_result_has_gap_name():
    obj = encode("test")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert hasattr(result, "gap_name")


def test_paradigm_result_is_paradigm_result_instance():
    obj = encode("test")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert isinstance(result, ParadigmResult)


# ─── PositivityParadigm.verify ────────────────────────────────────────────────

def test_positivity_certifies_encoded_text():
    """A CertifiableObject from encode() must pass the ALEPH positivity test."""
    obj = encode("test")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert result.status == "CERTIFIED"


def test_positivity_certifies_real_word():
    obj = encode("quantum mechanics")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert result.status == "CERTIFIED"


def test_positivity_certifies_smiles():
    from tantrium.agi.core.encoder import encode_smiles
    obj = encode_smiles("CCO")
    p = PositivityParadigm("ALEPH", "Positivity", "D >= 0", [])
    result = p.verify(obj)
    assert result.status == "CERTIFIED"


# ─── Other paradigm smoke tests ───────────────────────────────────────────────

def test_spectral_paradigm_certifies_encoded_text():
    obj = encode("test")
    p = SpectralParadigm("DALET", "Spectral Theory", "sigma(A)", ["ALEPH"])
    result = p.verify(obj)
    # The encoder fills eigenvalues, all non-negative → CERTIFIED
    assert result.status == "CERTIFIED"


def test_fixed_point_paradigm_certifies_encoded_text():
    obj = encode("test")
    p = FixedPointParadigm("TAV", "Fixed Point", "L* = F(L*)", ["HE", "YOD"])
    result = p.verify(obj)
    assert result.status == "CERTIFIED"


def test_consistency_paradigm_certifies_encoded_text():
    obj = encode("test")
    p = ConsistencyParadigm("EMET", "Consistency", "no contradiction", ["TAV", "TSADI"])
    result = p.verify(obj)
    assert result.status == "CERTIFIED"


def test_aleph_paradigm_from_codex_by_id():
    """Look up ALEPH from the dict and verify it works."""
    p = PARADIGM_BY_ID["ALEPH"]
    obj = encode("RNA polymerase")
    result = p.verify(obj)
    assert result.status == "CERTIFIED"
