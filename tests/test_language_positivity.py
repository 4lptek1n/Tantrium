"""Dil yörüngesi = kritik hat: 'düşünmek = pozitiflik koruyarak yürümek'.

RH kanıt zincirindeki pozitiflik (Sturm-pivot ⟺ Jensen hiperbolisitesi) artık dil
üretiminin de substratı: generator adımları Sturm-pozitif geçişi + köklü hedefi tercih
eder (ilaç-gerçeklenebilirliği / rooting ile AYNI sertifika). Bu testler değişmezleri
kilitler: üretim hâlâ sertifikalı + yörüngedeki her kavram köklü (konuşulabilir).
"""
import pytest

import tantrium
from tantrium.language.generator import CertifiedGenerator, _SEMANTIC


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


def test_pe_accessor_exists(ai):
    """Generator, RH-chain pozitiflik sertifikasını (ProductionEngine) lazy taşır."""
    g = CertifiedGenerator(ai._engine)
    pe = g._pe()
    assert hasattr(pe, "_sturm_path_pivot_min")
    assert g._pe() is pe          # lazy singleton


def test_generation_still_certified(ai):
    """Pozitiflik yeniden-sıralaması üretimi bozmaz — yörünge hâlâ certified."""
    g = CertifiedGenerator(ai._engine)
    r = g.generate("protein", max_steps=4)
    assert r.certified


def test_trajectory_concepts_are_grounded(ai):
    """Kritik hat değişmezi: yörüngedeki HER kavram semantik-köklü (konuşulabilir).

    Köksüz 'karmaşık sıfır' kavramlar yörüngeye giremez — pozitiflik yolu bunu korur.
    """
    g = CertifiedGenerator(ai._engine)
    e = ai._engine
    r = g.generate("EGFR", max_steps=5)
    for step in r.steps:
        edges = e.tau.edges.get(step.concept, [])
        assert any(ed.paradigm in _SEMANTIC for ed in edges), \
            f"köksüz kavram yörüngede: {step.concept}"


def test_sturm_positive_rooted_candidate_preferred(ai, monkeypatch):
    """İki aday: biri Sturm-NEGATİF+köksüz, biri Sturm-POZİTİF+köklü → pozitif+köklü seçilir."""
    g = CertifiedGenerator(ai._engine)
    e = ai._engine
    m = e.manifold

    # gerçek momentli iki hedef + bir kaynak (encoder ile is_real garantisi)
    def _mk(name):
        if name not in m.concepts:
            from tantrium.core.semantic import Concept
            cod = e.encoder.encode(name, name=name)
            c = Concept(name=name, moments=list(cod.moments), domain="test")
            m.concepts[name] = c
        return m.concepts[name]

    cur, pos_rooted, neg_iso = _mk("zzcur_pos"), _mk("zzrooted_tgt"), _mk("zziso_tgt")

    class _E:
        def __init__(s, t, p): s.target, s.paradigm, s.distance = t, p, 0.0

    # kaynak her iki hedefe semantik kenar; pos_rooted ayrıca 3 kenarla KÖKLÜ
    e.tau.edges["zzcur_pos"] = [_E("zzrooted_tgt", "IS_A"), _E("zziso_tgt", "IS_A")]
    e.tau.edges["zzrooted_tgt"] = [_E("a", "CAUSES"), _E("b", "CAUSES"), _E("c", "ACTIVATES")]
    e.tau.edges["zziso_tgt"] = []

    # Pozitiflik derinliği: pos_rooted hedefi derin (3), izole hedef sapma (0) — momentlere göre
    rooted_mu = [float(x) for x in pos_rooted.moments]

    def fake_depth(src, tgt, **kw):
        return (3, {}) if [float(x) for x in tgt] == rooted_mu else (0, {})
    monkeypatch.setattr("tantrium.core.positivity_ladder.positivity_depth", fake_depth)

    nxt = g._next_step("zzcur_pos", list(cur.moments), None, {"zzcur_pos"}, beam=3)
    assert nxt is not None
    assert nxt[0] == "zzrooted_tgt"    # derin-pozitif+köklü, sapma-hedefe tercih edildi
