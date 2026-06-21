"""Moleküler Genesis — beam search ve W2 yakınsama testleri."""
import time
import pytest

try:
    from rdkit import Chem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

pytestmark = pytest.mark.skipif(not HAS_RDKIT, reason="RDKit gerekli")


@pytest.fixture(scope="module")
def engine():
    from tantrium.core.engine import CertificationEngine
    return CertificationEngine()


@pytest.fixture(scope="module")
def genesis(engine):
    from tantrium.core.molecular_derivation import MolecularGenesis
    return MolecularGenesis(engine)


def test_generate_returns_report(genesis):
    r = genesis.generate("CCCO", top_k=3, max_atoms=6, beam_width=2)
    from tantrium.core.molecular_derivation import GenesisReport
    assert isinstance(r, GenesisReport)


def test_at_least_one_candidate(genesis):
    r = genesis.generate("CCCO", top_k=3, max_atoms=6, beam_width=2)
    assert len(r.candidates) >= 1


def test_best_w2_small_for_propanol(genesis):
    r = genesis.generate("CCCO", top_k=4, max_atoms=6, beam_width=3)
    assert r.best is not None
    # Quantum skor = 0.75×W2 + 0.25×κ_mesafe (blended); CCCO hedef CCCO bulmalı
    assert r.best.smiles == "CCCO" or r.best.w2 < 0.15, \
        f"En iyi: {r.best.smiles}, W2={r.best.w2:.4f}"


def test_all_smiles_valid(genesis):
    r = genesis.generate("CCCO", top_k=4, max_atoms=6, beam_width=2)
    for c in r.candidates:
        mol = Chem.MolFromSmiles(c.smiles)
        assert mol is not None, f"Geçersiz SMILES: {c.smiles}"


def test_different_targets_different_best(genesis):
    r1 = genesis.generate("CCCO", top_k=2, max_atoms=5, beam_width=2)
    r2 = genesis.generate("CCN", top_k=2, max_atoms=5, beam_width=2)
    # Farklı hedefler farklı en iyi moleküller üretmeli (ya farklı SMILES ya farklı W2)
    if r1.best and r2.best:
        assert r1.best.smiles != r2.best.smiles or abs(r1.best.w2 - r2.best.w2) > 1e-6


def test_smiles_target_works(genesis):
    r = genesis.generate("c1ccccc1", top_k=3, max_atoms=8, beam_width=2)
    assert r is not None
    assert r.total_steps > 0


def test_text_target_works(genesis):
    r = genesis.generate("EGFR", top_k=2, max_atoms=6, beam_width=2)
    assert r is not None
    assert len(r.candidates) >= 1


def test_atom_count_within_limit(genesis):
    max_a = 6
    r = genesis.generate("CCCO", top_k=3, max_atoms=max_a, beam_width=2)
    for c in r.candidates:
        mol = Chem.MolFromSmiles(c.smiles)
        if mol:
            assert mol.GetNumAtoms() <= max_a + 2, \
                f"{c.smiles} — {mol.GetNumAtoms()} atom > {max_a}+2"


def test_total_steps_positive(genesis):
    r = genesis.generate("CCN", top_k=2, max_atoms=5, beam_width=2)
    assert r.total_steps > 0


def test_summary_returns_string(genesis):
    r = genesis.generate("CCCO", top_k=2, max_atoms=5, beam_width=2)
    s = r.summary()
    assert isinstance(s, str)
    assert "Tantrium" in s


def test_top_k_limits_candidates(genesis):
    r = genesis.generate("CCCO", top_k=2, max_atoms=5, beam_width=2)
    assert len(r.candidates) <= 2


def test_speed_under_10s(genesis):
    t0 = time.time()
    genesis.generate("CCN", top_k=2, max_atoms=6, beam_width=2)
    elapsed = time.time() - t0
    assert elapsed < 10.0, f"Genesis {elapsed:.1f}s aldı (limit: 10s)"
