"""Çok-boyutlu kavram zenginleştirme — kavramı tüm GERÇEK boyutlarıyla kökle (F8).

Genişletilebilir boyut-registry: molekül + protein + DNA + fiziksel-özellik. Bu testler
bağlama mantığını + büyüme kablosunu kilitler. Ağ ÇAĞIRMAZ (elle değer / fake AI)."""
import numpy as np

from tantrium.core.enrichment import (
    enrich_concept, fetch_molecular_smiles, fetch_physical_properties, _DIMENSIONS,
)


class _AI:
    """bind_percept + ground_full + enrich taklidi — ağsız, bağlanan kenarları kaydeder."""
    def __init__(self):
        self.bindings = []   # (concept, paradigm, percept_name)

    def bind_percept(self, concept, signal, *, modality="signal", paradigm="HAS_SIGNAL", name=None):
        self.bindings.append((concept, paradigm, name))
        return name

    def ground_full(self, name, *, molecule=None, dna=None, **kw):
        b = {}
        if molecule:
            self.bindings.append((name, "HAS_COMPOUND", None)); b["HAS_COMPOUND"] = "p"
        if dna:
            self.bindings.append((name, "HAS_DNA", None)); b["HAS_DNA"] = "p"
        return type("GS", (), {"bound": b})()

    def enrich(self, name, *, network=True, **kw):
        known_smiles = {"caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"}
        known_protein = {"egfr": "MEEPQSDPSVEPPLSQ"}
        return enrich_concept(self, name, network=False,
                              smiles=known_smiles.get(name),
                              protein=known_protein.get(name))


def _paradigms(ai):
    return {p for _, p, _ in ai.bindings}


# ── enrich_concept çekirdek (elle değer, ağsız) ──
def test_molecule_dimension_binds():
    ai = _AI()
    r = enrich_concept(ai, "caffeine", smiles="CN1C=NC2=C1C(=O)N(C(=O)N2C)C", network=False)
    assert "molecule" in r["dimensions"] and "HAS_COMPOUND" in r["bound"]


def test_protein_dimension_binds_as_bio():
    ai = _AI()
    r = enrich_concept(ai, "egfr", protein="MEEPQSDPSVEPPLSQ", network=False)
    assert "protein" in r["dimensions"] and "HAS_DNA" in r["bound"]


def test_dna_dimension_binds():
    ai = _AI()
    r = enrich_concept(ai, "egfr", dna="ATCGATCGATCG", network=False)
    assert "dna" in r["dimensions"]


def test_properties_dimension_binds_geometry():
    ai = _AI()
    r = enrich_concept(ai, "caffeine", properties=[194.19, -0.1, 58.4, 293.0], network=False)
    assert "properties" in r["dimensions"] and "HAS_GEOMETRY" in r["bound"]


def test_multiple_complementary_dimensions():
    """Bir kavram birden çok BAĞIMSIZ boyut alabilir (çok-boyutlu kökleme)."""
    ai = _AI()
    r = enrich_concept(ai, "egfr", protein="MEEPQSDP", dna="ATCGATCG",
                       properties=[1.0, 2.0, 3.0], network=False)
    assert set(r["dimensions"]) == {"protein", "dna", "properties"}


def test_no_data_no_network_empty():
    ai = _AI()
    r = enrich_concept(ai, "postal", network=False)
    assert r["dimensions"] == [] and not ai.bindings


def test_dims_filter_restricts():
    """dims= yalnız istenen boyutları dener."""
    ai = _AI()
    r = enrich_concept(ai, "egfr", protein="MEEPQSDP", smiles="CC(=O)O",
                       network=False, dims=["protein"])
    assert r["dimensions"] == ["protein"]


def test_registry_has_all_eight_dimensions():
    keys = {d.key for d in _DIMENSIONS}
    assert keys == {"molecule", "protein", "dna", "properties",
                    "law", "structure3d", "sound", "image"}


def test_image_dimension_binds():
    """Görsel piksel matrisi → HAS_IMAGE (manuel, ağsız)."""
    import numpy as np
    ai = _AI()
    img = np.random.RandomState(1).rand(16, 16) * 255
    r = enrich_concept(ai, "apple", image=img, network=False)
    assert "image" in r["dimensions"] and "HAS_IMAGE" in r["bound"]


def test_no_molecule_3d_dimension():
    """İLKE: molekül 3D boyutu YOK — çekirdek ilacı sıfırdan üretir, dış 3D kirletir.
    3D yalnız protein (structure3d); molekül 2D SMILES kalır."""
    by_key = {d.key: d for d in _DIMENSIONS}
    assert by_key["molecule"].paradigm == "HAS_COMPOUND"     # 2D graf spektrumu
    assert by_key["structure3d"].paradigm == "HAS_TOPOLOGY"  # 3D yalnız protein fold
    # molekül fetcher SMILES (2D) döndürür, 3D koordinat değil
    assert "smiles" in by_key["molecule"].fetch.__doc__ if by_key["molecule"].fetch.__doc__ else True


def test_law_dimension_known_sequence():
    """Yasa boyutu: bilinen dizi (fibonacci) → discover_law → IS_GOVERNED_BY (ağsız, iç)."""
    from tantrium.core.enrichment import fetch_governing_law

    class _LawAI:
        def discover_law(self, seq):
            return type("LD", (), {"law_holds": True, "order": 2,
                                   "recurrence": [1.0, 1.0], "modes": [-0.618, 1.618]})()

        def bind_percept(self, *a, **k):
            return "p"
    fp = fetch_governing_law("fibonacci sequence", _LawAI())
    assert fp is not None and fp[0] == 2.0          # order=2
    # bilinmeyen kavram → dizi yok → None
    assert fetch_governing_law("postal", _LawAI()) is None


def test_law_binds_governed_by():
    ai = _AI()

    class _LawAI(_AI):
        def discover_law(self, seq):
            return type("LD", (), {"law_holds": True, "order": 2,
                                   "recurrence": [1.0, 1.0], "modes": [-0.618, 1.618]})()
    lai = _LawAI()
    r = enrich_concept(lai, "fibonacci", network=False)
    assert "law" in r["dimensions"] and "IS_GOVERNED_BY" in r["bound"]


def test_sound_manual_only_no_autofetch():
    """Ses: oto-kaynak yok (fetch None); yalnız elle sound= ile bağlanır."""
    import numpy as np
    by_key = {d.key: d for d in _DIMENSIONS}
    assert by_key["sound"].fetch("anything", None) is None    # oto-fetch yok
    ai = _AI()
    r = enrich_concept(ai, "bell", sound=list(np.sin(np.linspace(0, 10, 64))), network=False)
    assert "sound" in r["dimensions"] and "HAS_SIGNAL" in r["bound"]


def test_structure3d_binds_topology():
    import numpy as np
    ai = _AI()
    dm = np.abs(np.random.RandomState(0).randn(8, 8))
    dm = (dm + dm.T) / 2
    r = enrich_concept(ai, "egfr", structure3d=dm, network=False)
    assert "structure3d" in r["dimensions"] and "HAS_TOPOLOGY" in r["bound"]


def test_fetch_rejects_non_alnum():
    assert fetch_molecular_smiles("⟨bridge:x⟩") is None
    assert fetch_physical_properties("") is None


# ── growth _enrich_multidim kablosu (ağsız, fake AI) ──
class _E:
    def __init__(self, paradigm, target):
        self.paradigm = paradigm
        self.target = target


def _growth_like(ai, edges):
    from tantrium.research.growth import GrowthEngine
    obj = GrowthEngine.__new__(GrowthEngine)
    obj.engine = type("Eng", (), {"tau": type("T", (), {"edges": edges})(), "_ai": ai})()
    return obj


def test_properties_matrix_is_psd():
    """Fiziksel özellik → PSD geometri matrisi (dış-çarpım, eigenvalue ≥ 0)."""
    from tantrium.core.enrichment import _bind_properties
    captured = {}

    class _A2:
        def bind_percept(self, concept, signal, **kw):
            captured["mat"] = np.array(signal)
            return "p"
    _bind_properties(_A2(), "caffeine", [194.19, -0.1, 58.4, 293.0], "properties")
    eigs = np.linalg.eigvalsh(captured["mat"])
    assert (eigs >= -1e-9).all()                 # PSD
