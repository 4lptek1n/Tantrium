"""Relation — iki operatör arası TAM ilişki (İLİŞKİ ekseni): kuvvet + hayat + topoloji.

interaction (kuvvet/dolanıklık) + spectral_flow (topoloji) tek nesnede birleşir."""
import tantrium
from tantrium.core.interaction import Interaction
from tantrium.core.relation import Relation, relate
from tantrium.core.spectral_flow import SpectralFlow


def test_relation_unifies_force_life_topology():
    """Tam ilişki üç yarısını da taşır: interaction (kuvvet+hayat) + flow (topoloji)."""
    r = relate("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O")
    assert isinstance(r, Relation)
    assert isinstance(r.interaction, Interaction)
    assert isinstance(r.flow, SpectralFlow)
    assert r.coupling > 0                               # kuvvet
    assert r.entanglement > 0                           # hayat (dolanıklık)


def test_relation_passthrough_matches_parts():
    """Relation'ın kısayolları alt-nesnelere birebir yönlendirir (kompozisyon, kopya değil)."""
    r = relate("CCO", "CCCO")
    assert r.coupling == r.interaction.coupling
    assert r.entanglement == r.interaction.entanglement
    assert r.entangled == r.interaction.entangled
    assert r.topological == (not r.flow.smooth)


def test_identical_inputs_smooth_topology():
    """Özdeş girdi → topolojik engel yok (yol sabit)."""
    r = relate("c1ccccc1", "c1ccccc1")
    assert r.flow.smooth is True
    assert r.topological is False


def test_distinct_inputs_topological():
    """Topolojik farklı yapı → ilişki yolu engelli (modlar yeniden örgütlenir)."""
    r = relate("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O")
    assert r.topological is True


def test_deterministic():
    a = relate("CCO", "c1ccccc1")
    b = relate("CCO", "c1ccccc1")
    assert a.coupling == b.coupling
    assert a.flow.net_flow == b.flow.net_flow


def test_summary_three_faces():
    s = relate("CCO", "c1ccccc1").summary()
    assert "KUVVET" in s and "HAYAT" in s and "TOPOLOJİ" in s


def test_sdk_facade():
    r = tantrium.AI().relate("CCO", "CCCO")
    assert isinstance(r, Relation)
