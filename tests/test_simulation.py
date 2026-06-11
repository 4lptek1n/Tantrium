"""Evren simülasyonu + protein kuantum yargısı testleri.

İki yeni motor:
  ai.simulate()      — makineyi çalıştırarak molekülü transport ile diz (hafıza yok)
  ai.judge_binding() — üretileni proteinin bilinen ligand SMILES'larına kuantum yargısı

Ana iddia: ilaç keşfi = makine self-simülasyonu + dürüst yargı, benzer arama değil.
"""
import tantrium


# ─── simulate: transport-sürücülü üretim ─────────────────────────────────────

def test_simulate_returns_report(ai):
    rep = ai.simulate(seed="CC", max_steps=4, beam_width=3)
    assert rep.seed == "CC"
    assert len(rep.lineage) >= 1
    assert rep.total_steps > 0


def test_simulate_advances_atoms(ai):
    """Makine atom ekleyerek ilerlemeli — son soy tohumdan büyük."""
    rep = ai.simulate(seed="CC", max_steps=5, beam_width=3)
    assert any(s.n_atoms > 2 for s in rep.lineage)


def test_simulate_sturm_gate(ai):
    """Her uç sturm-PSD geçidinden geçmeli (gerçek-ölçü manifoldu)."""
    rep = ai.simulate(seed="CC", max_steps=4, beam_width=3)
    assert all(s.sturm for s in rep.frontier)


def test_simulate_not_only_alkane(ai):
    """Beam çeşitliliği: üretim saf karbon zincirine çökmemeli."""
    rep = ai.simulate(seed="CC", max_steps=6, beam_width=4)
    smis = [s.smiles for s in rep.lineage] + [s.smiles for s in rep.frontier]
    # En az bir heteroatom (N/O/S/F) içeren molekül üretilmeli
    assert any(any(c in smi for c in "NOSF") for smi in smis)


def test_simulate_tracks_certified(ai):
    rep = ai.simulate(seed="CC", max_steps=4, beam_width=3)
    assert 0 <= rep.certified_steps <= rep.total_steps


# ─── judge_binding: protein kuantum yargısı ──────────────────────────────────

def test_judge_known_inhibitor_works(ai):
    """Gerçek EGFR inhibitörü 'işe yarayabilir' yargısı almalı."""
    erlotinib = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
    r = ai.judge_binding(erlotinib, "egfr")
    assert r["verdict"] == "İŞE YARAYABİLİR"
    assert r["n_refs"] >= 1


def test_judge_irrelevant_molecule_rejected(ai):
    """Alakasız molekül (etanol) EGFR için reddedilmeli — eski design hatası buydu."""
    r = ai.judge_binding("CCO", "egfr")
    assert r["verdict"] == "İŞE YARAMAZ"


def test_judge_discriminates(ai):
    """Gerçek inhibitör ile alakasız molekül FARKLI κ-mesafe almalı."""
    erlotinib = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
    real = ai.judge_binding(erlotinib, "egfr")
    junk = ai.judge_binding("CCO", "egfr")
    assert real["kappa_dist_to_nearest"] < junk["kappa_dist_to_nearest"]


def test_judge_unknown_protein_honest(ai):
    """Bilinen ligandı olmayan hedef için dürüstçe 'bilinmiyor' demeli."""
    r = ai.judge_binding("CCO", "nonexistent_protein_xyz_999")
    assert r["verdict"] == "BİLİNMİYOR"
    assert r["n_refs"] == 0


def test_judge_returns_keys(ai):
    erlotinib = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
    r = ai.judge_binding(erlotinib, "egfr")
    assert {"candidate", "protein", "verdict", "reason"}.issubset(r.keys())


# ─── Paradigma-matematik imzası: 'geçti' değil, hesaplanan SAYILAR ───────────

def test_paradigm_signature_intensive(ai):
    """Paradigma imzası farklı boyuttaki moleküller için karşılaştırılabilir vektör."""
    from tantrium.core.encoder import encode
    from tantrium.core.metric import paradigm_signature
    s1 = paradigm_signature(encode("CCO").structure)
    s2 = paradigm_signature(encode("c1ccccc1").structure)
    assert len(s1) == len(s2) and len(s1) > 10


def test_paradigm_distance_same_class_closer(ai):
    """İki kinaz inhibitörü, kinaz-dışı bir molekülden paradigma-matematik olarak yakın."""
    from tantrium.core.encoder import encode
    from tantrium.core.metric import paradigm_distance
    erlotinib = encode("C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1").structure
    gefitinib = encode("COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1").structure
    ethanol = encode("CCO").structure
    assert paradigm_distance(erlotinib, gefitinib) < paradigm_distance(erlotinib, ethanol)


def test_judge_uses_paradigm_distance(ai):
    """Yargı paradigma-matematik mesafesini raporlamalı (sertifika sayısı değil)."""
    erlotinib = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
    r = ai.judge_binding(erlotinib, "egfr")
    assert "paradigm_dist_to_nearest" in r
    assert r["paradigm_dist_to_nearest"] < ai._PARADIGM_WORKS_THR


def test_judge_generalizes_to_class(ai):
    """Referansta OLMAYAN ama aynı sınıf (imatinib) işe yarayabilir çıkmalı."""
    imatinib = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"
    r = ai.judge_binding(imatinib, "egfr")
    assert r["verdict"] == "İŞE YARAYABİLİR"


# ─── Kapalı döngü: design_drug ───────────────────────────────────────────────

def test_design_drug_unknown_protein(ai):
    r = ai.design_drug("nonexistent_protein_xyz_999", max_steps=2, beam_width=2)
    assert r["verdict"] == "BİLİNMİYOR"


def test_design_drug_resolves_refs(ai):
    """EGFR için referans ligandlar SMILES'a çözülmeli."""
    refs = ai._protein_reference_ligands("egfr")
    assert len(refs) >= 1
    assert all(isinstance(smi, str) and smi for _, smi in refs)


# ─── Ters paradigma: serbest dekonvolüsyon + cure ────────────────────────────

def test_free_deconvolution_inverts_add():
    """subtract additivity'nin tersi: (A⊞B)⊟B = A."""
    from tantrium.core.quantum_moments import FreeCumulants
    a = FreeCumulants([0.5, 0.3, 0.1, 0.05, 0.0, 0.0])
    b = FreeCumulants([0.2, 0.1, 0.05, 0.02, 0.0, 0.0])
    back = a.add(b).subtract(b)
    assert all(abs(x - y) < 1e-9 for x, y in zip(back.k, a.k))


def test_cure_runs_and_designs(ai):
    """cure() hastalıktan molekül çıkarmalı (ters paradigma hattı çalışır)."""
    r = ai.cure("c1ccc2ncnc(N)c2c1", max_steps=4, beam_width=3)
    assert r["designed_molecule"] is not None
    assert r["method"].startswith("ters paradigma")


def test_cure_reports_realizability(ai):
    """cure() gerçeklenebilirlik açığını raporlamalı — ters yön PSD kısıtına uyar."""
    r = ai.cure("c1ccc2ncnc(N)c2c1", max_steps=4, beam_width=3)
    assert "realizability_gap" in r
    assert "kappa_required" in r and len(r["kappa_required"]) >= 4
