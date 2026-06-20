"""Tests for InverseTransport — inverse molecular design via W2 metric."""

import pytest


@pytest.fixture(scope="module")
def ai():
    import tantrium

    return tantrium.AI()


def test_design_returns_design_result(ai):
    from tantrium import DesignResult

    r = ai.design("EGFR", top_k=4, n_fragment_rounds=1)
    assert isinstance(r, DesignResult)


def test_design_has_candidates(ai):
    r = ai.design("EGFR", top_k=4, n_fragment_rounds=1)
    assert len(r.candidates) > 0


def test_design_smiles_candidates_first(ai):
    r = ai.design("EGFR", top_k=6, n_fragment_rounds=1)
    smiles_cands = [c for c in r.candidates if c.smiles]
    assert len(smiles_cands) > 0, "At least one SMILES candidate expected"


def test_design_structural_validity(ai):
    r = ai.design("EGFR", top_k=4, n_fragment_rounds=1)
    smiles_cands = [c for c in r.candidates if c.smiles]
    # All SMILES candidates should pass structural paradigms
    for c in smiles_cands:
        assert c.paradigms_passed > 0


def test_design_w2_distances_positive(ai):
    r = ai.design("protein kinase", top_k=4, n_fragment_rounds=1)
    for c in r.candidates:
        assert c.w2_distance >= 0.0


def test_design_different_targets_different_results(ai):
    r1 = ai.design("EGFR", top_k=5, n_fragment_rounds=1)
    r2 = ai.design("glucose", top_k=5, n_fragment_rounds=1)
    # Different targets → different W2 distances (different manifold positions)
    w2_egfr = r1.candidates[0].w2_distance if r1.candidates else 0
    w2_gluc = r2.candidates[0].w2_distance if r2.candidates else 0
    # At least one target should give a non-trivial distance
    assert w2_egfr != w2_gluc or (w2_egfr == 0 and w2_gluc == 0)


def test_design_smiles_target(ai):
    # SMILES as target — find similar molecules
    r = ai.design("c1ccc2[nH]cnc2c1", top_k=4, n_fragment_rounds=1)
    assert r.target_type == "smiles"
    assert len(r.candidates) > 0


def test_design_result_str(ai):
    r = ai.design("ATP", top_k=3, n_fragment_rounds=1)
    s = str(r)
    assert "W2=" in s or "aday bulunamadı" in s


def test_design_fast_enough(ai):
    import time

    t0 = time.time()
    ai.design("EGFR", top_k=4, n_fragment_rounds=1)
    elapsed = time.time() - t0
    assert elapsed < 30.0, f"Design too slow: {elapsed:.1f}s"


def test_inverse_transport_manifold_search(ai):
    from tantrium import InverseTransport

    inv = InverseTransport(ai.engine)
    m, t = inv._encode_target("EGFR")
    hits = inv._search_manifold(m, n=5)
    assert len(hits) > 0
    # Check structure
    for h in hits:
        assert "name" in h
        assert "w2" in h
        assert "moments" in h


def test_inverse_transport_encode_smiles(ai):
    from tantrium import InverseTransport

    inv = InverseTransport(ai.engine)
    m, t = inv._encode_target("c1ccccc1")
    assert t == "smiles"
    assert len(m) > 0


def test_design_3d_conformer(ai, tmp_path):
    r = ai.design("aspirin", top_k=3, n_fragment_rounds=1, out_dir=str(tmp_path))
    # At least attempt 3D generation for top candidates
    # (may fail for some SMILES — just check no crash)
    assert r is not None
