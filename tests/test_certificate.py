"""TEK geçerlilik ölçütü (core/certificate) — pozitiflik geçişi + leave-one-out genelleşme.

Meta-sentezin kabul kapısı budur; dağınık 5 kopyanın tek arayüzü. Golden: code_meta._generalizes
buna delege eder, davranış birebir korunur.
"""
from tantrium.core.certificate import (
    CertResult,
    certify_generalization,
    certify_transition,
)


def test_transition_full_path_certifies():
    """Geçerli ölçü (geometrik μ_k=0.5^k) → on_path, depth 3."""
    mu = [0.5 ** k for k in range(8)]
    r = certify_transition(mu, mu)
    assert isinstance(r, CertResult)
    assert r.on_path and r.depth == 3 and bool(r) is True


def test_transition_off_path():
    """Geçersiz Hankel → on_path False, depth 0."""
    bad = [1.0, 5.0, 0.1, 9.0]
    r = certify_transition(bad, bad)
    assert not r.on_path and r.depth == 0


def test_generalization_accepts_consistent_rule():
    """Tutarlı kural (f(x)=x+1) leave-one-out genelleşir."""
    def builder(train):
        # train'den sabit fark çıkar (hepsinde y-x aynıysa o kural)
        diffs = {y - x for x, y in train}
        return diffs.pop() if len(diffs) == 1 else None

    def verify(delta, held):
        return all(y - x == delta for x, y in held)

    inst = [(1, 2), (5, 6), (10, 11), (3, 4)]
    assert certify_generalization(builder, inst, verify) is True


def test_generalization_rejects_memorized():
    """Ezber (tutarsız) kural genelleşmez → reddedilir (uydurma yok)."""
    def builder(train):
        diffs = {y - x for x, y in train}
        return diffs.pop() if len(diffs) == 1 else None

    def verify(delta, held):
        return delta is not None and all(y - x == delta for x, y in held)

    inst = [(1, 2), (5, 99), (10, 11)]   # tutarsız → hiçbir sabit fark genelleşmez
    assert certify_generalization(builder, inst, verify) is False


def test_generalization_too_few_instances():
    """<3 örnek → güvenilir test edilemez → False (genelleşme iddia etme)."""
    assert certify_generalization(lambda t: 1, [(1, 2), (2, 3)], lambda c, h: True) is False
