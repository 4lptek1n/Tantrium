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
