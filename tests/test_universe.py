"""Universe — bir girdiden eksiksiz evren: yedi yüz tek bütünde, tek mühür."""
import tantrium
from tantrium.core.interaction import Interaction
from tantrium.core.relation import Relation
from tantrium.core.spectral_geometry import SpectralGeometry
from tantrium.core.spectral_reading import SpectralReading
from tantrium.cosmos import Lifecycle
from tantrium.universe import Universe, universe


def test_seven_faces_present():
    """Yedi yüz tek nesnede: madde, fizik, geometri, zaman+topoloji (+ kuvvet/hayat couple)."""
    u = universe("CC(=O)Oc1ccccc1C(=O)O", inflation_steps=12)
    assert u.dim >= 1 and u.rank >= 0                  # 1 MADDE
    assert isinstance(u.physics, SpectralReading)      # 2 FİZİK
    assert isinstance(u.geometry, SpectralGeometry)    # 3 GEOMETRİ
    assert isinstance(u.lifecycle, Lifecycle)          # 6 ZAMAN
    assert u.lifecycle.topology is not None            # 7 TOPOLOJİ
    assert len(u.seal) == 64


def test_geometry_defines_a_space():
    """3 GEOMETRİ: her yapı kendi boyutlu uzayını tanımlar (NCG)."""
    mol = universe("CC(=O)Oc1ccccc1C(=O)O", full=False)
    seq = universe([2, 3, 5, 7, 11, 13, 17, 19, 23, 29], full=False)
    assert mol.geometry.dimension != seq.geometry.dimension   # farklı dünyalar
    assert mol.geometry.dimension > 0


def test_couple_force_and_life():
    """İLİŞKİ ekseni: couple → Relation (4 KUVVET + 5 HAYAT + 7 TOPOLOJİ tek nesnede)."""
    u = universe("c1ccccc1", full=False)
    rel = u.couple("CC(=O)Oc1ccccc1C(=O)O")
    assert isinstance(rel, Relation)
    assert isinstance(rel.interaction, Interaction)
    assert rel.coupling > 0                             # kuvvet var
    assert rel.entanglement > 0                         # hayat: dolanık
    assert rel.flow is not None                         # topoloji: dönüşüm yolunun yükü


def test_deterministic_and_sealed():
    a = universe("CCO", inflation_steps=10)
    b = universe("CCO", inflation_steps=10)
    assert a.seal == b.seal
    assert a.geometry.dimension == b.geometry.dimension


def test_summary_seven_faces():
    u = universe("CCO", inflation_steps=10)
    s = u.summary()
    for face in ("1 MADDE", "2 FİZİK", "3 GEOMETRİ", "6 ZAMAN", "7 TOPOLOJİ"):
        assert face in s


def test_sdk_facade():
    u = tantrium.AI().universe("CCO", full=False)
    assert isinstance(u, Universe)
    it = tantrium.AI().interact("CCO", "CCCO")
    assert isinstance(it, Interaction)
    g = tantrium.AI().spectral_geometry("c1ccccc1")
    assert isinstance(g, SpectralGeometry)
