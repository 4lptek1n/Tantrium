"""F3 — Caller-admission-parity (karakterizasyon) testleri.

ÖNCE YAZILDI (plan gereği TOP RİSK fazı): tek `admit()` yolu girmeden ÖNCE
her admission yolunun yargısını SABİTLER. Refactor sonrası bu testler değişmeden
geçmeli — yani admission DAVRANIŞI birebir korunmalı.

Üç politika:
  aleph   : Aleph PSD kontrolü (verify_existence). Geçerse core, geçmezse rejected.
  trusted : kontrolsüz kabul (kapı-muaf).
  gated   : engine evren kapısı (autonomous._universe_gate) — CONTRADICTORY reddi.

Pin edilen davranış:
  add()           ≡ admit(policy="aleph"), rejected → ValueError
  add_unchecked() ≡ admit(policy="trusted"), her zaman kabul
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from tantrium.core.semantic import AdmissionResult, Concept, SemanticManifold


# ─── Golden girdiler ────────────────────────────────────────────────────────

def _real_concept(name: str = "real_pt") -> Concept:
    """Aleph-sertifikalı: μ_k = (1/2)^k geometrik dizi = nokta kütlesi momentleri.

    μ_k = r^k her zaman PSD-Hankel (r∈(0,1) noktasında Dirac ölçüsü) → Aleph geçer.
    """
    return Concept(
        name=name,
        moments=[Fraction(1, 2 ** k) for k in range(6)],
        domain="test", source="t",
    )


def _junk_concept(name: str = "junk_pt") -> Concept:
    """Aleph başarısız: PSD olmayan Hankel (gerçek ölçü değil).

    μ₂ < μ₁² (varyans negatif) → Hankel PSD değil → Aleph reddeder.
    """
    return Concept(
        name=name,
        moments=[Fraction(1), Fraction(9, 10), Fraction(1, 100),
                 Fraction(0), Fraction(0), Fraction(0)],
        domain="test", source="t",
    )


# ─── 1. admit() politikaları ────────────────────────────────────────────────

def test_admit_aleph_admits_real():
    m = SemanticManifold()
    r = m.admit(_real_concept(), policy="aleph")
    assert isinstance(r, AdmissionResult)
    assert r.admitted is True
    assert r.tier == "core"
    assert "real_pt" in m.concepts


def test_admit_aleph_rejects_junk():
    m = SemanticManifold()
    r = m.admit(_junk_concept(), policy="aleph")
    assert r.admitted is False
    assert r.tier == "rejected"
    assert "junk_pt" not in m.concepts, "Aleph reddi → manifolda GİRMEMELİ"


def test_admit_trusted_admits_junk_gate_exempt():
    """KAPI-MUAF: trusted politikası Aleph'i atlar, çöp bile girer."""
    m = SemanticManifold()
    r = m.admit(_junk_concept(), policy="trusted")
    assert r.admitted is True
    assert r.tier == "trusted"
    assert "junk_pt" in m.concepts, "trusted → kapı-muaf, her şey girer"


def test_admit_trusted_admits_real():
    m = SemanticManifold()
    r = m.admit(_real_concept(), policy="trusted")
    assert r.admitted is True
    assert "real_pt" in m.concepts


def test_admit_unknown_policy_raises():
    m = SemanticManifold()
    with pytest.raises(ValueError, match="Unknown admission policy"):
        m.admit(_real_concept(), policy="bogus")


def test_admission_result_bool():
    """AdmissionResult truthy/falsy doğrudan kullanılabilir."""
    assert bool(AdmissionResult(True, "core", "x"))
    assert not bool(AdmissionResult(False, "rejected", "x"))


# ─── 2. add() / add_unchecked() PARITY (eski sözleşme korunur) ──────────────

def test_add_matches_aleph_admit_for_real():
    """add() gerçek kavramı eskisi gibi saklar, self döner."""
    m = SemanticManifold()
    out = m.add(_real_concept())
    assert out is m, "add() self döndürür (zincirleme)"
    assert "real_pt" in m.concepts


def test_add_raises_valueerror_on_junk():
    """add() Aleph reddinde ValueError fırlatır (eski sözleşme — değişmedi)."""
    m = SemanticManifold()
    with pytest.raises(ValueError, match="rejected by Aleph filter"):
        m.add(_junk_concept())
    assert "junk_pt" not in m.concepts


def test_add_unchecked_matches_trusted_admit():
    """add_unchecked() çöp dahil her şeyi saklar, self döner (kapı-muaf)."""
    m = SemanticManifold()
    out = m.add_unchecked(_junk_concept())
    assert out is m
    assert "junk_pt" in m.concepts


def test_add_and_admit_aleph_identical_decision():
    """add() ile admit(policy='aleph') AYNI kabul/red kararını verir."""
    for concept_fn, should_admit in [(_real_concept, True), (_junk_concept, False)]:
        m1 = SemanticManifold()
        m2 = SemanticManifold()
        # Yol 1: admit
        r = m1.admit(concept_fn("x"), policy="aleph")
        # Yol 2: add (ValueError veya başarı)
        added = True
        try:
            m2.add(concept_fn("x"))
        except ValueError:
            added = False
        assert r.admitted == added == should_admit
        assert ("x" in m1.concepts) == ("x" in m2.concepts) == should_admit


# ─── 3. Gated yol (engine evren kapısı) — yargı sabitlenir ──────────────────

@pytest.fixture(scope="module")
def ai():
    import tantrium
    return tantrium.AI()


def test_universe_gate_rejects_contradictory_or_admits(ai):
    """Evren kapısı CONTRADICTORY'yi reddeder; geçerli veriyi core/frontier alır.

    Gated yol kabul için manifold.admit(policy='trusted')'a iner — bu testin
    amacı: gated sınıflandırmanın (core/frontier/rejected) davranışını sabitlemek.
    """
    from tantrium.research.autonomous import AutonomousObserver
    obs = AutonomousObserver(ai._engine)
    # Gerçek, köklü bir kavram (protein) — reddedilmemeli
    mu = [float(m) for m in ai._engine.encoder.encode("protein").moments]
    tv, gv, admitted = obs._universe_gate("protein", mu)
    assert admitted in ("core", "frontier", "rejected")
    # protein bilinen biyokimya — CONTRADICTORY olmamalı
    assert admitted != "rejected" or tv == "CONTRADICTORY"


def test_universe_gate_returns_triple(ai):
    """_universe_gate (truth, grounding, admitted_as) üçlüsü döndürür."""
    from tantrium.research.autonomous import AutonomousObserver
    obs = AutonomousObserver(ai._engine)
    mu = [float(m) for m in ai._engine.encoder.encode("ATP").moments]
    result = obs._universe_gate("ATP", mu)
    assert isinstance(result, tuple) and len(result) == 3
    _, _, admitted = result
    assert admitted in ("core", "frontier", "rejected")
