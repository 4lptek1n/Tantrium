"""İlaç Dökümhanesi Testleri — Evren Kapanışı, 6 Eksen, Çok-Strateji, Deterministizm.

Tüm testler küçük max_steps/beam_width ile hızlı; ağ testleri skipif işaretli.
"""

from __future__ import annotations

import pytest

import tantrium
from tantrium.core.production import ProductionEngine
from tantrium.core.production_judge import (
    AxisVerdict,
    ClosureProof,
    ProductionCertificate,
    ProductionJudge,
)
from tantrium.core.quantum_moments import FreeCumulants


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


@pytest.fixture(scope="module")
def pe(ai):
    return ProductionEngine(ai.engine)


@pytest.fixture(scope="module")
def judge(ai, pe):
    return ProductionJudge(ai.engine, pe)


# ── Yardımcılar ───────────────────────────────────────────────────────────

ERLOTINIB = "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
GEFITINIB = "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1"
ETHANOL = "CCO"
ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"

KZERO = FreeCumulants([0.0] * 6)


def _egfr_setup(pe):
    kind, mu_req, profiles, ref, gap, kd, kh = pe._read_target_ext("egfr")
    assert kind == "protein"
    return mu_req, profiles, gap, kd, kh


# ── 1. Evren Kapanışı ─────────────────────────────────────────────────────


class TestClosure:
    def test_real_inhibitor_closes(self, pe, judge):
        """EGFR inhibitörü evren kapanışını sağlamalı (err < epsilon, Sturm pozitif)."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        proof = judge.close_universe(ERLOTINIB, kd, kh, mu_req, epsilon=0.5)
        assert proof.applicable is True
        assert proof.universe_closes is True
        assert proof.closure_error < 0.5
        assert proof.sturm_ok is True

    def test_gefitinib_closes(self, pe, judge):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        proof = judge.close_universe(GEFITINIB, kd, kh, mu_req, epsilon=0.5)
        assert proof.universe_closes is True

    def test_junk_does_not_close(self, pe, judge):
        """Etanol EGFR için evreni kapatmamalı."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        proof = judge.close_universe(ETHANOL, kd, kh, mu_req, epsilon=0.5)
        assert proof.universe_closes is False
        assert proof.closure_error > 0.5

    def test_closure_error_orders(self, pe, judge):
        """Erlotinib < Aspirin < Etanol (kapanış hatası sıralaması)."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        err_e = judge.close_universe(ERLOTINIB, kd, kh, mu_req).closure_error
        err_a = judge.close_universe(ASPIRIN, kd, kh, mu_req).closure_error
        err_eth = judge.close_universe(ETHANOL, kd, kh, mu_req).closure_error
        assert err_e < err_a
        assert err_a < err_eth

    def test_inapplicable_when_no_kappas(self, pe, judge):
        """κ parametreleri None ise applicable=False."""
        proof = judge.close_universe(ERLOTINIB, None, None)
        assert proof.applicable is False
        assert proof.universe_closes is False

    def test_closure_proof_fields(self, pe, judge):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        proof = judge.close_universe(ERLOTINIB, kd, kh, mu_req)
        assert isinstance(proof, ClosureProof)
        assert isinstance(proof.closure_error, float)
        assert isinstance(proof.pivot_min, float)
        assert isinstance(proof.kappa_joint, list)
        assert isinstance(proof.kappa_residual, list)


# ── 2. 6 Eksen Yargısı ───────────────────────────────────────────────────


class TestSixAxes:
    def test_six_axes_present(self, pe, judge):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        kappa_thr = pe._kappa_threshold(profiles)
        axes, _ = judge.judge_all_axes(ERLOTINIB, mu_req, profiles, kappa_thr)
        names = {a.name for a in axes}
        expected = {"structural", "transport", "quantum", "energy", "gimel", "grounding"}
        assert expected.issubset(names), f"Eksik eksenler: {expected - names}"

    def test_axis_verdict_fields(self, pe, judge):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        kappa_thr = pe._kappa_threshold(profiles)
        axes, _ = judge.judge_all_axes(ERLOTINIB, mu_req, profiles, kappa_thr)
        for a in axes:
            assert isinstance(a, AxisVerdict)
            assert isinstance(a.name, str)
            assert isinstance(a.ok, bool)
            assert isinstance(a.value, float)

    def test_coherent_inhibitor(self, pe, judge):
        """Erlotinib 5 HARD eksende tutarlı olmalı."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        kappa_thr = pe._kappa_threshold(profiles)
        ref_smiles = [smi for _, smi in pe._reference_ligands("egfr")[:4]]
        axes, coherent = judge.judge_all_axes(ERLOTINIB, mu_req, profiles, kappa_thr, ref_smiles)
        assert coherent is True

    def test_incoherent_ethanol(self, pe, judge):
        """Etanol EGFR için tutarsız (en az 1 HARD eksen geçemez)."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        kappa_thr = pe._kappa_threshold(profiles)
        _, coherent = judge.judge_all_axes(ETHANOL, mu_req, profiles, kappa_thr)
        assert coherent is False

    def test_grounding_is_soft(self, pe, judge):
        """Topraklama ekseni SOFT — coherent'i veto etmemeli."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        kappa_thr = pe._kappa_threshold(profiles)
        ref_smiles = [smi for _, smi in pe._reference_ligands("egfr")[:4]]
        axes, coherent = judge.judge_all_axes(ERLOTINIB, mu_req, profiles, kappa_thr, ref_smiles)
        next(a for a in axes if a.name == "grounding")
        # Erlotinib yeni molekül → UNGROUNDED olabilir ama coherent yine True
        hard_axes = [a for a in axes if a.name != "grounding"]
        assert all(a.ok for a in hard_axes) == coherent


# ── 3. _read_target_ext ────────────────────────────────────────────────────


class TestReadTargetExt:
    def test_protein_target(self, pe):
        kind, mu_req, profiles, ref, gap, kd, kh = pe._read_target_ext("egfr")
        assert kind == "protein"
        assert gap is None
        assert len(profiles) > 0
        assert all(kd.k[i] == 0.0 for i in range(len(kd.k)))  # kd = zero baseline

    def test_smiles_target(self, pe):
        kind, mu_req, profiles, ref, gap, kd, kh = pe._read_target_ext(ERLOTINIB)
        assert kind == "smiles"
        assert gap is None
        assert mu_req[0] == pytest.approx(1.0, abs=0.01)

    def test_disease_target(self, pe):
        kind, mu_req, profiles, ref, gap, kd, kh = pe._read_target_ext("alzheimer")
        assert kind == "disease"
        assert gap is not None
        assert gap >= 0.0

    def test_back_compat_read_target(self, pe):
        """_read_target (eski) hâlâ 4-tuple döndürmeli."""
        result = pe._read_target("egfr")
        assert len(result) == 4
        kind, mu_req, profiles, ref = result
        assert kind == "protein"

    def test_protein_realizability_gap_none(self, pe):
        *_, gap, kd, kh = pe._read_target_ext("egfr")
        assert gap is None

    def test_disease_realizability_gap_float(self, pe):
        *_, gap, kd, kh = pe._read_target_ext("alzheimer")
        assert isinstance(gap, float)


# ── 4. Çok-Strateji Havuzu ────────────────────────────────────────────────


class TestMultiStrategyPool:
    def test_pool_nonempty(self, pe):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        pool = pe._build_pool("egfr", mu_req, profiles, max_steps=4, beam_width=2)
        assert len(pool) > 0

    def test_pool_dedup(self, pe):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        pool = pe._build_pool("egfr", mu_req, profiles, max_steps=4, beam_width=2)
        assert len(pool) == len(set(pool))

    def test_pool_chemically_stable(self, pe):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        pool = pe._build_pool("egfr", mu_req, profiles, max_steps=4, beam_width=2)
        for smi in pool:
            assert pe._chemically_stable(smi), f"Kararsız: {smi}"

    def test_pool_has_genesis_and_refs(self, pe):
        """Havuz en az genesis + bilinen referans ligandları içermeli."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        pool = pe._build_pool("egfr", mu_req, profiles, max_steps=4, beam_width=2)
        assert len(pool) >= 2  # en az genesis + ref ligand


# ── 5. Refine ─────────────────────────────────────────────────────────────


class TestRefine:
    def test_refine_returns_smiles(self, pe):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        scored = [{"smiles": ERLOTINIB, "kappa_fit": 1.0}]
        new_smi = pe._refine(scored, mu_req, profiles, max_steps=4, beam_width=2)
        assert isinstance(new_smi, list)

    def test_refine_bounded(self, pe, judge):
        """Refine en fazla 3 tur çalışmalı (cap=3)."""
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        cert = pe.produce("egfr", max_steps=4, beam_width=2, refine_rounds=5, inject=False, top_k=3)
        assert cert.refine_rounds_used <= 3

    def test_refine_rounds_zero_skips(self, pe):
        """refine_rounds=0 ile refine_rounds_used=0 olmalı."""
        cert = pe.produce("egfr", max_steps=4, beam_width=2, refine_rounds=0, inject=False, top_k=3)
        assert cert.refine_rounds_used == 0


# ── 6. Kombinasyon ────────────────────────────────────────────────────────


class TestCombination:
    def test_decompose_returns_pairs(self, pe):
        mu_req, profiles, gap, kd, kh = _egfr_setup(pe)
        pairs = pe._decompose_combination(mu_req, profiles, max_steps=4, beam_width=2)
        assert isinstance(pairs, list)
        for p in pairs:
            assert len(p) == 2
            assert isinstance(p[0], str)
            assert isinstance(p[1], str)

    def test_combination_off_flag(self, pe):
        """combination=False kombinasyon çifti içermemeli."""
        cert = pe.produce(
            "egfr", max_steps=4, beam_width=2, combination=False, inject=False, top_k=3
        )
        combo_partners = [c for c in cert.candidates if c.get("combination_partner")]
        assert len(combo_partners) == 0

    def test_combination_flag_default_on(self, pe):
        """combination=True (varsayılan) — sertifika alanı mevcut."""
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert isinstance(cert.combination, list)


# ── 7. Sertifika Alanları + Geriye-Uyum ──────────────────────────────────


class TestCertificate:
    def test_certificate_fields(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert isinstance(cert, ProductionCertificate)
        assert cert.target == "egfr"
        assert cert.target_kind in ("protein", "disease", "smiles")
        assert isinstance(cert.required_moments, list)
        assert cert.designed_smiles is not None
        assert cert.verdict in (
            "İŞE YARAYABİLİR",
            "İŞE YARAMAZ",
            "KISMÎ",
            "ÜRETİLEMEDİ",
            "GEÇERSİZ",
        )
        assert isinstance(cert.candidates, list)

    def test_certificate_summary(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        s = cert.summary()
        assert "Hedef" in s
        assert "YARGI" in s
        assert "Sturm" in s

    def test_to_result_backcompat(self, pe):
        """to_result() → ProductionResult (eski tip) geriye-uyum."""
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        from tantrium.core.production import ProductionResult

        old = cert.to_result()
        assert isinstance(old, ProductionResult)
        assert old.target == cert.target
        assert old.designed_smiles == cert.designed_smiles
        assert old.verdict == cert.verdict

    def test_to_design_dict(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        d = cert.to_design_dict()
        assert "protein" in d
        assert "candidates" in d
        assert "verdict" in d

    def test_to_cure_dict(self, pe):
        cert = pe.produce("alzheimer", max_steps=4, beam_width=2, inject=False, top_k=3)
        d = cert.to_cure_dict()
        assert "disease" in d
        assert "designed_molecule" in d

    def test_protein_realizability_gap_none(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert cert.realizability_gap is None

    def test_disease_realizability_gap_float(self, pe):
        cert = pe.produce("alzheimer", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert cert.realizability_gap is None or isinstance(cert.realizability_gap, float)

    def test_empty_target_still_returns_cert(self, pe):
        """Boş string bile geçerli bir sertifika döndürmeli (encoder her zaman çalışır)."""
        cert = pe.produce("", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert isinstance(cert, ProductionCertificate)
        assert cert.verdict in (
            "İŞE YARAYABİLİR",
            "İŞE YARAMAZ",
            "KISMÎ",
            "ÜRETİLEMEDİ",
            "GEÇERSİZ",
        )


# ── 8. Deterministizm ────────────────────────────────────────────────────


class TestDeterminism:
    def test_same_input_same_output(self, pe):
        """Aynı girdi → aynı SMILES, aynı pivot, aynı verdict."""

        def run():
            return pe.produce(
                "egfr", max_steps=4, beam_width=2, refine_rounds=0, inject=False, top_k=3
            )

        c1 = run()
        c2 = run()
        assert c1.designed_smiles == c2.designed_smiles
        assert c1.verdict == c2.verdict
        assert abs(c1.pivot_min - c2.pivot_min) < 1e-9

    def test_smiles_deterministic(self, pe):
        def run():
            return pe.produce(
                ERLOTINIB, max_steps=4, beam_width=2, refine_rounds=0, inject=False, top_k=3
            )

        c1 = run()
        c2 = run()
        assert c1.designed_smiles == c2.designed_smiles
        assert c1.verdict == c2.verdict


# ── 9. Enjeksiyon ─────────────────────────────────────────────────────────


class TestInjection:
    def test_inject_off(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert cert.injected_as == ""

    def test_inject_on_coherent(self, ai, pe):
        """inject=True + coherent=True → injected_as dolmalı."""
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=True, top_k=3)
        if cert.coherent:
            assert cert.injected_as != ""


# ── 10. ai.produce passthrough ───────────────────────────────────────────


class TestAIProduce:
    def test_ai_produce_passthrough(self, ai):
        """ai.produce() ProductionCertificate döndürmeli."""
        cert = ai.produce("egfr", max_steps=4, beam_width=2, refine_rounds=0, inject=False, top_k=3)
        assert isinstance(cert, ProductionCertificate)
        assert cert.target == "egfr"

    def test_ai_produce_smiles(self, ai):
        cert = ai.produce(
            ERLOTINIB, max_steps=4, beam_width=2, refine_rounds=0, inject=False, top_k=3
        )
        assert cert.target_kind == "smiles"

    def test_ai_produce_verdict_valid(self, ai):
        cert = ai.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        assert cert.verdict in (
            "İŞE YARAYABİLİR",
            "İŞE YARAMAZ",
            "KISMÎ",
            "ÜRETİLEMEDİ",
            "GEÇERSİZ",
        )


# ── 11. Sınır + Açıklama ─────────────────────────────────────────────────


class TestBoundaryAndNote:
    def test_note_states_spectral_only(self, pe):
        """Sertifika notu 'spektral zorunluluk' veya 'wet-lab' ifadesi içermeli."""
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=3)
        note_lower = (cert.note or "").lower()
        assert "spektral" in note_lower or "wet-lab" in note_lower

    def test_candidates_list_not_exceeds_top_k(self, pe):
        cert = pe.produce("egfr", max_steps=4, beam_width=2, inject=False, top_k=5)
        assert len(cert.candidates) <= 5

    def test_closure_applicable_false_for_none_kappas(self, pe, judge):
        proof = judge.close_universe(ERLOTINIB, None, None)
        assert proof.applicable is False

    @pytest.mark.skipif(True, reason="ağ testi — CI'da atla")
    def test_network_wildtype(self, pe):
        _, _, _, _, gap, kd, kh = pe._read_target_ext("egfr", network=True)
        assert kh is not None
