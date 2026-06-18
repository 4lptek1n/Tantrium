"""ASI §12 paradigma düzeltmesi — davranışsal kod modalitesi (yapı değil DAVRANIŞ = işlev)."""
from tantrium.core.code_behavior import (behavior_signature, behavior_signature_of,
                                         behavior_fingerprint_of, fingerprint_from_examples)
from tantrium.core.quantum_moments import FreeCumulants


def test_lossless_fingerprint_no_collapse():
    """KAYIPSIZ extensional kimlik: add/sub/mul/div ASLA çakışmaz (moment sıkıştırması değil)."""
    from fractions import Fraction
    ops = {"add": lambda a, b: a + b, "sub": lambda a, b: a - b,
           "mul": lambda a, b: a * b, "div": lambda a, b: Fraction(a, b)}
    fps = {n: behavior_fingerprint_of(f, nargs=2) for n, f in ops.items()}
    assert len(set(fps.values())) == 4               # dördü de ayrı kimlik (çakışma YOK)


def test_lossless_fingerprint_is_extensional_equivalence():
    """Aynı davranış (farklı syntax) → AYNI kayıpsız kimlik = program denkliği testi."""
    a = behavior_fingerprint_of(lambda x: x + x, nargs=1)
    b = behavior_fingerprint_of(lambda x: 2 * x, nargs=1)        # aynı işi yapar
    c = behavior_fingerprint_of(lambda x: x + 1, nargs=1)        # farklı
    assert a == b and a != c


def test_fingerprint_from_examples_lossless_hashable():
    """Örnek kümesinin tam I/O kimliği — kesme yok, hashable (Fraction tam)."""
    fp = fingerprint_from_examples([(1, 2), (2, 4), (3, 6)])
    assert hash(fp) == hash(fingerprint_from_examples([(1, 2), (2, 4), (3, 6)]))


def test_synthesized_program_carries_lossless_identity():
    """Sentezlenen program kayıpsız extensional kimliğini taşır (add≠sub kanıtlı ayrı)."""
    from tantrium.core.code_synthesis import synthesize
    add = synthesize([((1, 2), 3), ((3, 4), 7), ((5, 1), 6)])
    sub = synthesize([((1, 2), -1), ((3, 4), -1), ((5, 1), 4)])
    assert add.behavior_exact and add.behavior_exact != sub.behavior_exact


def _k(examples):
    m = behavior_signature(examples)
    return FreeCumulants.from_moments([float(x) for x in m])


def test_behavior_distinguishes_behavioral_classes():
    """AST grafının çakıştırdığı davranışları DAVRANIŞSAL imza ayırır (lineer vs nonlineer)."""
    add = _k([((1, 2), 3), ((3, 4), 7), ((5, 1), 6), ((2, 2), 4)])
    mul = _k([((1, 2), 2), ((3, 4), 12), ((5, 1), 5), ((2, 2), 4)])
    srt = _k([([3, 1, 2], [1, 2, 3]), ([5, 4], [4, 5]), ([2, 1, 3], [1, 2, 3])])
    assert add.distance(mul) > 0.0          # topla ≠ çarp (geometrik ayrım)
    assert add.distance(srt) > add.distance(mul)   # liste-işlemi daha uzak sınıf


def test_behavior_signature_deterministic():
    """Aynı spec → BİREBİR aynı davranışsal imza (random yok)."""
    ex = [((1, 2), 3), ((3, 4), 7)]
    assert behavior_signature(ex) == behavior_signature(ex)


def test_behavior_handles_any_output_type():
    """Davranış ölçüsü tip-kör: sayı/liste/metin/bool hepsi aynı moment rejimine."""
    assert behavior_signature([(("a",), "A"), (("bb",), "BB")]) is not None
    assert behavior_signature([([1, 2], 3), ([3], 3)]) is not None
    assert behavior_signature([((1,), True), ((0,), False)]) is not None


def test_behavior_signature_of_runs_program():
    """Çalıştırılabilir fonksiyon kanonik girdide KOŞULARAK ölçülür (spektrum ölçümü)."""
    sig = behavior_signature_of(lambda a, b: a * b)
    assert sig and sig[0] == 1                # Hausdorff μ0 = 1
    # zıt-davranış nonlineer vs lineer ayrılır
    lin = FreeCumulants.from_moments([float(x) for x in behavior_signature_of(lambda a, b: a + b)])
    non = FreeCumulants.from_moments([float(x) for x in sig])
    assert lin.distance(non) > 0.0


def test_certified_program_carries_behavior():
    """Sentezlenen program davranışsal moment-konumunu taşır (dekoratif AST değil)."""
    from tantrium.core.code_synthesis import synthesize
    add = synthesize([((1, 2), 3), ((3, 4), 7), ((5, 1), 6)])
    mul = synthesize([((1, 2), 2), ((3, 4), 12), ((5, 1), 5)])
    assert add.verified and mul.verified
    assert add.behavior and add.behavior != mul.behavior
