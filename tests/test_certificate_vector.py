"""Tam 46-boyutlu sertifika = karşılaştırmanın operatif birimi (çökmeden).

8 moment yalnız kapı; makinenin asıl algı organı 23 paradigmanın TÜM çıktısından
türeyen 46-boyutlu vektör. Bu testler o vektörün operatif birim olduğunu ve
çökmüş metriklerin (W2/L1) karıştırdığını AYIRDIĞINI kilitler."""
import tantrium
from tantrium.core.metric import (
    canonical_distance,
    certificate_distance,
    certificate_vector,
)


def test_fingerprint_is_46_dim():
    """Sertifika vektörü tam paradigma imzası (~46 boyut), 8 değil."""
    v = tantrium.AI().fingerprint("c1ccccc1")
    assert len(v) >= 40           # 8 momentin çok ötesinde — tam okuma


def test_identical_zero_distinct_positive():
    """d(x,x)=0; farklı moleküller > 0 (tam 46-dim uzayda)."""
    assert certificate_distance("c1ccccc1", "c1ccccc1") == 0.0
    assert certificate_distance("c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O") > 0.0


def test_46dim_separates_what_w2_collapses():
    """KANIT: W2 (eigenvalue) aspirin/kafeini ≈0'a çökerken 46-dim onları ayırır."""
    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    caffeine = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
    oa = tantrium.encode(aspirin)
    ob = tantrium.encode(caffeine)
    w2 = canonical_distance([float(x) for x in oa.moments], [float(x) for x in ob.moments])
    full = certificate_distance(aspirin, caffeine)
    assert w2 < 0.1               # W2 onları neredeyse aynı sanıyor
    assert full > 10 * w2          # 46-dim belirgin biçimde ayırıyor


def test_deterministic_and_symmetric():
    a, b = "CCO", "CC(=O)O"
    assert certificate_distance(a, b) == certificate_distance(a, b)
    assert abs(certificate_distance(a, b) - certificate_distance(b, a)) < 1e-12


def test_sdk_compare_matches_core():
    ai = tantrium.AI()
    a, b = "c1ccccc1", "CCO"
    assert abs(ai.compare(a, b) - certificate_distance(a, b)) < 1e-12
    assert len(ai.fingerprint(a)) == len(certificate_vector(a))
