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


def test_registry_has_four_working_dimensions():
    keys = {d.key for d in _DIMENSIONS}
    assert keys == {"molecule", "protein", "dna", "properties"}


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


def test_multidim_binds_chemical_skips_noise():
    ai = _AI()
    g = _growth_like(ai, {
        "caffeine": [_E("IS_A", "stimulant")],   # bilinen → molekül bağlanır
        "postal": [_E("IS_A", "service")],        # bilinmeyen → boyut yok
        "⟨bridge:x⟩": [_E("IS_A", "y")],          # sentetik → alfabetik değil, atlanır
    })
    rep = type("R", (), {"dimensions_bound": 0})()
    g._enrich_multidim(["caffeine", "postal", "⟨bridge:x⟩"], lambda *_: None, rep)
    assert rep.dimensions_bound >= 1              # caffeine en az 1 boyut


def test_multidim_idempotent_skips_bound():
    ai = _AI()
    g = _growth_like(ai, {"caffeine": [_E("HAS_COMPOUND", "⟨percept:caffeine:molecule⟩")]})
    rep = type("R", (), {"dimensions_bound": 0})()
    g._enrich_multidim(["caffeine"], lambda *_: None, rep)
    assert rep.dimensions_bound == 0             # zaten molekül-bağlı → atlanır


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
