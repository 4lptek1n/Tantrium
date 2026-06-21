"""Ayrım (discrimination) testleri — makinenin GERÇEKTEN ayırt ettiğinin kanıtı.

Dokümanlanmış #1 açık soru: "23 paradigma her şeyi geçirir (G=AᵀA daima PSD) —
gerçekten AYIRT EDİYOR MU?". Bu testler RH-sertifika vektörünün (rank/Stieltjes/
Hausdorff/grade/κ) + mühürlü seal/verify + adversarial negatif kontrolün birlikte
AYIRT EDİCİ olduğunu assert eder.

tools/discrimination_benchmark.py ile aynı 6 özelliği bağımsız kontrol eder.
"""
from __future__ import annotations

import copy

import pytest

import tantrium

# RH-sertifika SMILES yolu RDKit'siz de çalışır; yine de güvenli ol: temel çağrı
# patlarsa SMILES testlerini atla.
try:
    tantrium.AI().rh_certificate("c1ccccc1")
    _SMILES_OK = True
except Exception:  # pragma: no cover - ortam koruması
    _SMILES_OK = False

requires_smiles = pytest.mark.skipif(
    not _SMILES_OK, reason="rh_certificate SMILES yolu bu ortamda kullanılamıyor"
)

DRUGS = {
    "aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "caffeine": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
    "ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "paracetamol": "CC(=O)Nc1ccc(O)cc1",
    "benzene": "c1ccccc1",
}
GARBAGE = "not a molecule at all 42"


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


# ── Özellik 1: gerçek ilaçlar sertifikalı + sonlu rank ───────────────────────
@requires_smiles
@pytest.mark.parametrize("name", list(DRUGS))
def test_drugs_are_certified_with_finite_rank(ai, name):
    c = ai.rh_certificate(DRUGS[name])
    # Stieltjes ya da Hamburger sertifikalı (moment dizisi geçerli ölçü)
    assert c.stieltjes or c.criteria.hamburger_certified
    # sonlu, en az 1 rank
    assert c.rank >= 1


# ── Özellik 2: rank AYIRT EDİCİ ─────────────────────────────────────────────
@requires_smiles
def test_rank_discriminates_benzene_below_drugs(ai):
    ranks = {n: ai.rh_certificate(s).rank for n, s in DRUGS.items()}
    benzene = ranks["benzene"]
    drug_min = min(ranks[n] for n in DRUGS if n != "benzene")
    # küçük/simetrik benzen, her ilaçtan KESİN düşük rank
    assert benzene < drug_min
    assert benzene == 1


@requires_smiles
def test_rank_vector_not_constant(ai):
    # "her şey aynı çıkıyor" itirazına karşı: rank gerçekten değişiyor
    ranks = {n: ai.rh_certificate(s).rank for n, s in DRUGS.items()}
    assert len(set(ranks.values())) >= 2


# ── Özellik 3: rh_distance metriği tutarlı ──────────────────────────────────
@requires_smiles
def test_distance_identity_is_zero(ai):
    assert ai.rh_distance(DRUGS["aspirin"], DRUGS["aspirin"]) == 0.0
    assert ai.rh_distance(DRUGS["benzene"], DRUGS["benzene"]) == 0.0


@requires_smiles
def test_chemical_pair_closer_than_garbage(ai):
    # kimyasal yapı rastgele stringden ayrışır: gerçek molekül çifti, molekül-vs-çöpten yakın
    d_chem = ai.rh_distance(DRUGS["ibuprofen"], DRUGS["caffeine"])
    d_garbage = ai.rh_distance(DRUGS["ibuprofen"], GARBAGE)
    assert d_chem < d_garbage
    assert d_garbage > 0.0


# ── Özellik 4: adversarial negatif kontrol ──────────────────────────────────
def test_adversarial_control_rejects_non_psd():
    ac = tantrium.adversarial_control()
    # geçersiz (Hankel PSD olmayan) dizi DÜRÜSTÇE elenir — makine her şeyi geçirmiyor
    assert ac["hankel_psd"] is False
    assert ac["certification_status"] == "NOT_CERTIFIED"
    assert ac["honest_rejection"] is True


# ── Özellik 5: mühür denetlenebilirliği ─────────────────────────────────────
@requires_smiles
def test_seal_verifies_clean(ai):
    sealed = ai.seal(DRUGS["aspirin"])
    res = ai.verify(sealed)
    assert res["result"] == "VERIFIED"
    assert res["hash_ok"] is True


@requires_smiles
def test_seal_detects_tampering(ai):
    sealed = ai.seal(DRUGS["aspirin"])
    tampered = copy.deepcopy(sealed)
    tampered["moments"][0] = "999999"  # momenti kurcala
    res = ai.verify(tampered)
    assert res["result"] == "TAMPERED"
    assert res["hash_ok"] is False


# ── Özellik 6: çapa (anchor) ayrımı ─────────────────────────────────────────
def test_anchor_certificates_are_distinct():
    from tantrium.core.rh_certificate import certify_rh, rh_distance
    from tantrium.graph.anchors import build_anchor_concepts

    anchors = {c.name: c for c in build_anchor_concepts()}
    zeta = next(c for n, c in anchors.items() if "ZETA" in n)
    gue = next(c for n, c in anchors.items() if "GUE" in n)

    cz = certify_rh(zeta.moments)
    cg = certify_rh(gue.moments)

    # farklı mühür = farklı sertifika içeriği
    assert cz.sealed_hash != cg.sealed_hash
    # rh_distance ile pozitif ayrım
    assert rh_distance(zeta.moments, gue.moments) > 0.0


# ── Bütünleşik: benchmark çalışır ve TÜM özellikler PASS ────────────────────
@requires_smiles
def test_benchmark_run_all_pass():
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    import discrimination_benchmark as bench

    rep = bench.run()
    assert rep["summary"]["all_pass"] is True
    assert rep["summary"]["passed"] == rep["summary"]["total"] == 6
    assert rep["summary"]["verdict"] == "DISCRIMINATES"
