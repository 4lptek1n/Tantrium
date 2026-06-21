"""Sealed-certificate verifier testleri — bağımsız, kurcalama-tespitli mühür çekirdeği.

tce-collapse-engine:tools/independent_verifier.py'nin izole dürüstlük özelliği:
SHA-256 içerik-hash mührü, kurcalama tespiti ve kasıtlı NEGATİF kontrol.
"""
from fractions import Fraction

import tantrium
from tantrium.core.encoder import encode
from tantrium.core.rh_criteria import rh_criteria
from tantrium.core.verifier import (
    seal,
    verify,
    adversarial_control,
    tamper_test,
    _recompute_criteria,
)


def _seal_egfr():
    obj = encode("EGFR")
    crit = rh_criteria(obj.moments)
    return obj, crit, seal("EGFR", "EGFR", obj.moments, crit.as_dict())


def test_seal_shape():
    """seal() beklenen kanonik şemayı döner."""
    _, _, s = _seal_egfr()
    for key in ("name", "moments", "rh_criteria", "content_hash", "version"):
        assert key in s
    assert isinstance(s["content_hash"], str) and len(s["content_hash"]) == 64
    assert all(isinstance(m, str) for m in s["moments"])  # exact-Fraction str


def test_seal_deterministic_same_input_same_hash():
    """Aynı girdi → bit-bit aynı content_hash (tekrarlanabilir)."""
    obj = encode("EGFR")
    crit = rh_criteria(obj.moments)
    s1 = seal("EGFR", "EGFR", obj.moments, crit.as_dict())
    s2 = seal("EGFR", "EGFR", obj.moments, crit.as_dict())
    assert s1["content_hash"] == s2["content_hash"]


def test_seal_different_input_different_hash():
    """Farklı girdi → farklı hash (ayırt edicilik)."""
    _, _, s_egfr = _seal_egfr()
    objb = encode("c1ccccc1")
    critb = rh_criteria(objb.moments)
    s_benzene = seal("benzene", "c1ccccc1", objb.moments, critb.as_dict())
    assert s_egfr["content_hash"] != s_benzene["content_hash"]


def test_verify_verified():
    """Bozulmamış mühür → VERIFIED (hash + recompute tutarlı)."""
    _, _, s = _seal_egfr()
    assert verify(s)["result"] == "VERIFIED"
    rep = verify(s, recompute_fn=_recompute_criteria)
    assert rep["hash_ok"] is True
    assert rep["verdicts_consistent"] is True
    assert rep["result"] == "VERIFIED"


def test_tamper_detected():
    """Momenti kurcala → verify TAMPERED döner."""
    _, _, s = _seal_egfr()
    assert tamper_test(s) is True
    # doğrudan kurcalama
    bad = dict(s)
    bad["moments"] = list(s["moments"])
    bad["moments"][0] = bad["moments"][0] + "1"
    assert verify(bad)["result"] == "TAMPERED"


def test_adversarial_control_honest_rejection():
    """Kasıtlı NEGATİF kontrol: geçersiz dizi DÜRÜSTÇE NOT_CERTIFIED işaretlenir."""
    ac = adversarial_control()
    assert ac["result"] == "PASS"
    assert ac["certification_status"] == "NOT_CERTIFIED"
    assert ac["hankel_psd"] is False
    assert ac["hamburger_certified"] is False
    assert ac["honest_rejection"] is True
    # mühür yine de kurcalanmamış (sadece içerik geçersiz, hash tutarlı)
    assert ac["seal_verify_result"] == "VERIFIED"


def test_adversarial_moments_are_invalid():
    """Negatif kontrol dizisi gerçekten Hankel-PSD-olmayan (det<0)."""
    invalid = [Fraction(1), Fraction(0), Fraction(-1), Fraction(0),
               Fraction(-1), Fraction(0), Fraction(-1), Fraction(0)]
    crit = rh_criteria(invalid)
    assert crit.hankel_psd is False
    assert crit.hamburger_certified is False


def test_empty_moments_seal_verify():
    """Boş moment listesi ile bile mühür tutarlı doğrulanır (prescribed yol)."""
    r = rh_criteria([])
    s = seal("empty", "empty", [], r.as_dict())
    assert verify(s)["result"] == "VERIFIED"
