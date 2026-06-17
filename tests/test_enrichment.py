"""Çok-boyutlu kavram zenginleştirme — kavramı GERÇEK boyutuyla kökle (F8).

'caffeine' öğrenince onun molekülünü de bağla. Bu testler bağlama mantığını + büyüme
kablosunu (kimyasal-aday seçimi, idempotentlik, sınır) kilitler. Ağ ÇAĞIRMAZ (fake AI)."""
from tantrium.core.enrichment import enrich_concept, fetch_molecular_smiles


class _GS:
    def __init__(self, bound):
        self.bound = bound


class _AI:
    """ground_full + enrich taklidi — ağsız, çağrıları kaydeder."""
    def __init__(self):
        self.calls = []

    def ground_full(self, name, *, molecule=None, dna=None, law=None, **kw):
        self.calls.append((name, molecule, dna, law))
        b = {}
        if molecule:
            b["HAS_COMPOUND"] = f"⟨percept:{name}:molecule⟩"
        if dna:
            b["HAS_DNA"] = f"⟨percept:{name}:dna⟩"
        return _GS(b)

    def enrich(self, name, *, smiles=None, dna=None, law=None, network=True):
        # kimyasal-aday simülasyonu: 'caffeine'/'aspirin' SMILES döndürür, gerisi None
        known = {"caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "aspirin": "CC(=O)Oc1ccccc1C(=O)O"}
        s = smiles or known.get(name)
        return enrich_concept(self, name, smiles=s, network=False)


# ── enrich_concept çekirdek ──
def test_enrich_with_smiles_binds_compound():
    ai = _AI()
    r = enrich_concept(ai, "caffeine", smiles="CN1C=NC2=C1C(=O)N(C(=O)N2C)C", network=False)
    assert "HAS_COMPOUND" in r["bound"]
    assert ai.calls and ai.calls[0][1].startswith("CN1")


def test_enrich_no_data_no_network_empty():
    ai = _AI()
    r = enrich_concept(ai, "postal", network=False)
    assert r["bound"] == [] and not ai.calls       # boyut yok → ground_full çağrılmaz


def test_enrich_dna_dimension():
    ai = _AI()
    r = enrich_concept(ai, "egfr", dna="ATCGATCG", network=False)
    assert "HAS_DNA" in r["bound"]


def test_enrich_protein_dimension_binds_as_bio():
    """Protein dizisi de bio-boyut olarak bağlanır (ground_full dna= üzerinden, encoder ayırır)."""
    ai = _AI()
    r = enrich_concept(ai, "egfr", protein="MEEPQSDPSVEPPLSQ", network=False)
    assert "HAS_DNA" in r["bound"]        # bio-dizi HAS_DNA kenarıyla bağlanır
    assert r["bio"] == "MEEPQSDPSVEPPLSQ"


def test_enrich_complementary_dimensions():
    """Molekül + bio aynı kavrama bağlanabilir (çok-boyutlu, tamamlayıcı)."""
    ai = _AI()
    r = enrich_concept(ai, "egfr", smiles="CC(=O)O", protein="MEEPQSDP", network=False)
    assert set(r["bound"]) == {"HAS_COMPOUND", "HAS_DNA"}


def test_fetch_rejects_non_alnum_and_empty():
    assert fetch_molecular_smiles("⟨bridge:x⟩") is None
    assert fetch_molecular_smiles("") is None


# ── growth _enrich_multidim kablosu (ağsız, fake AI) ──
class _E:
    def __init__(self, paradigm, target):
        self.paradigm = paradigm
        self.target = target


def _growth_like(ai, edges):
    """GrowthEngine._enrich_multidim'i izole çağırmak için minimal nesne."""
    from tantrium.research.growth import GrowthEngine
    obj = GrowthEngine.__new__(GrowthEngine)
    obj.engine = type("Eng", (), {"tau": type("T", (), {"edges": edges})(), "_ai": ai})()
    return obj


def test_multidim_binds_chemical_skips_noise():
    ai = _AI()
    g = _growth_like(ai, {
        "caffeine": [_E("IS_A", "stimulant")],         # kimyasal-aday → bağlanır
        "postal": [_E("IS_A", "service")],             # kimyasal değil → None
        "⟨bridge:x⟩": [_E("IS_A", "y")],               # sentetik → alfabetik değil, atlanır
    })
    logs = []
    rep = type("R", (), {"dimensions_bound": 0})()
    g._enrich_multidim(["caffeine", "postal", "⟨bridge:x⟩"], logs.append, rep)
    assert rep.dimensions_bound == 1                   # yalnız caffeine bağlandı


def test_multidim_idempotent_skips_already_bound():
    ai = _AI()
    g = _growth_like(ai, {"caffeine": [_E("HAS_COMPOUND", "⟨percept:caffeine:molecule⟩")]})
    rep = type("R", (), {"dimensions_bound": 0})()
    g._enrich_multidim(["caffeine"], lambda *_: None, rep)
    assert rep.dimensions_bound == 0                   # zaten bağlı → atlanır


def test_multidim_respects_bound_limit():
    ai = _AI()
    names = ["caffeine", "aspirin", "caffeine", "aspirin"]
    g = _growth_like(ai, {n: [_E("IS_A", "x")] for n in set(names)})
    rep = type("R", (), {"dimensions_bound": 0})()
    g._enrich_multidim(["caffeine", "aspirin"], lambda *_: None, rep, max_per_pass=1)
    assert rep.dimensions_bound <= 1                   # max_per_pass=1 sınırı
