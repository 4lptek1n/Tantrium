"""SpectralFlow — operatör yolunun topolojik yükü (mimarinin 5. ekseni).

Tek operatörün değil, operatörler arası YOLUN değişmezi; transport ve Cosmos
yörüngesine entegre."""
import tantrium
from tantrium.core.spectral_flow import SpectralFlow, spectral_flow


def test_identical_zero_flow():
    """Özdeş girdi → topolojik yük 0, geçiş yok (yol sabit)."""
    f = spectral_flow("c1ccccc1", "c1ccccc1")
    assert f.net_flow == 0
    assert f.crossings == 0
    assert f.smooth is True


def test_similar_is_smooth():
    """Yakın yapılar (küçük alkoller) → düzgün morfing, topolojik engel yok."""
    f = spectral_flow("CCO", "CCCO")
    assert f.crossings == 0
    assert f.smooth is True


def test_distinct_has_topological_charge():
    """Topolojik farklı yapılar → sıfırdan farklı geçiş (modlar yeniden örgütlenir)."""
    f = spectral_flow("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O")
    assert f.crossings > 0
    assert not f.smooth


def test_deterministic():
    a = spectral_flow("c1ccccc1", "CCO")
    b = spectral_flow("c1ccccc1", "CCO")
    assert a.net_flow == b.net_flow and a.crossings == b.crossings


def test_cosmos_has_topology_axis():
    """5. eksen Cosmos'a entegre: yaşam-döngüsü topolojik yük taşır."""
    from tantrium.cosmos import run_cosmos
    life = run_cosmos(inflation_steps=12)
    assert isinstance(life.topology, SpectralFlow)
    assert "5. eksen: TOPOLOJİ" in life.summary()


def test_sdk_facade():
    f = tantrium.AI().spectral_flow("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O")
    assert isinstance(f, SpectralFlow)
    assert "topolojik yük" in f.summary()
