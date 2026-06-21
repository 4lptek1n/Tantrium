"""ProductionEngine çekirdeği — __init__ + produce + produce_math.

Tüm yardımcı metot grupları mixin olarak birleşir (_targets/_pool/_judge/_helpers/
_cross). Çekirdek: tek-giriş produce() (çok-stratejili → evren-kapanışı → 6 eksen) ve
saf-matematik produce_math() (harf yok). Public yüzey production.__init__ ile korunur.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ._cross import _CrossMixin
from ._helpers import _HelpersMixin
from ._judge import _JudgeMixin
from ._pool import _PoolMixin
from ._targets import _TargetReadingMixin
from ._types import MathDrug, MoleculeSignature

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


class ProductionEngine(_TargetReadingMixin, _PoolMixin, _JudgeMixin,
                       _CrossMixin, _HelpersMixin):
    """Çok-stratejili ilaç dökümhanesi.

    Üretim ve yargı bölünmez — ikisi de referans→molekül konveks yolunun Sturm
    pivot pozitifliği (RH'nin H_{d,j}≥0 kriteri). Strateji bütçesi hedefe göre
    büyür; deterministik fixed-point refine kapatana kadar ilerler.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine
        # Transport Sturm pivot eşiği. Kanonik sıkı (-1e-9); ispat sonrası genişler.
        # _sync_transport_epsilon() theorem graph'taki Sturm sertifikasını okur,
        # qjr_degree_j_shift + qjr_degree_r_step kanıtlanınca -1e-5'e yükselir.
        self._transport_epsilon: float = -1e-9
        # TEK İMZA PIPELINE: her molekül bir kez encode → {μ, κ, özdeğer} (lazy).
        # Tüm üretim aşamaları (ranking·judge·closure) AYNI imzadan okur — yeniden
        # encode YOK (CoreMachine "tek geçiş" ilkesi). produce() başında temizlenir.
        self._sig_cache: dict[str, "MoleculeSignature"] = {}
        # De-novo (stage 6-7) aday kümesi — sıralamada proven-first için işaretlenir.
        self._denovo_smiles: set[str] = set()

    # ── Ana üretici ───────────────────────────────────────────────────────

    def produce(self, target: "str | list[float]", max_steps: int = 16, beam_width: int = 6,
                out_dir: str = "results/molecules", refine_rounds: int = 2,
                combination: bool = True, network: bool = False, inject: bool = True,
                epsilon: float = 0.5, top_k: int = 10) -> "ProductionCertificate":
        """Tek giriş: çok-stratejili üret → evren-kapat → sertifikala.

        target:
          • SMILES / protein / hastalık-adı (str) — bilinen hedefe tasarım
          • moment listesi (list[float]) — meaning_compose().to_produce_target()
          • ÖLÇÜLEN BULGU (list[str]) — hastalığın bulgusu: dysregüle metabolit/DNA/
            dizi/biyobelirteç sinyalleri. κ_disease bulgudan serbest-toplamla hesaplanır
            (AD aranmaz), ilaç = κ_healthy ⊟ κ_disease'i kapatan M. Bellekte OLMAYAN
            hastalık için tek dürüst giriş — yakın ad söylemek DEĞİL, kendi bulgusu ölçülür.
        """
        from tantrium.core.production_judge import ProductionJudge, ProductionCertificate
        from tantrium.core.quantum_moments import FreeCumulants

        self._sync_transport_epsilon()
        self._sig_cache = {}   # TEK imza pipeline: her produce() taze cache (re-encode yok)
        self._denovo_smiles = set()
        judge = ProductionJudge(self.engine, self)

        self._disease_label = None
        # ÖLÇÜLEN BULGU yolu: liste ama sayısal DEĞİL → hastalık bulguları (ölçülmüş
        # moleküler sinyaller). κ_disease bulgudan hesaplanır, AD aranmaz. Bellekte
        # olmayan hastalık için tek dürüst giriş: kendi bulgusu (bkz. _read_findings).
        if isinstance(target, (list, tuple)) and not all(
                isinstance(x, (int, float)) for x in target):
            kind, mu_req, profiles, ref_name, gap, kd, kh = self._read_findings(list(target))
            if kind == "invalid":
                return ProductionCertificate(
                    target="⟨bulgu⟩", target_kind="invalid",
                    verdict="GEÇERSİZ", note="Bulgu sinyalleri encode edilemedi.")
            self._disease_label = "ölçülen bulgu"
            target_str = "⟨disease:measured⟩"
        # Moment listesi doğrudan verildi (meaning_compose entegrasyonu)
        elif isinstance(target, (list, tuple)):
            mu_req = [float(x) for x in target]
            if not mu_req or mu_req[0] <= 0:
                return ProductionCertificate(
                    target="⟨moment_query⟩", target_kind="invalid",
                    verdict="GEÇERSİZ", note="Moment listesi boş veya geçersiz.")
            kzero = FreeCumulants([0.0] * 6)
            kh = FreeCumulants.from_moments(mu_req)
            kind, profiles, ref_name, gap, kd = "moments", [mu_req], "moment sorgusu", 0.0, kzero
            target_str = "⟨moment_query⟩"
        else:
            target_str = target
            # HASTALIK → birincil druggable sürücüye çöz: tüm pipeline (scaffold stratejisi
            # dahil) sürücünün GERÇEK ilaç-kimyasını kullansın. Eskiden "pancreatic cancer"
            # adıyla scaffold bulunamıyor → jenerik molekül (kafein). Şimdi egfr'ye çözülür
            # → gefitinib-sınıfı. Hastalığın matematiksel yapısı = sürücüsünün kimyası.
            drivers = self._disease_drivers(target) if isinstance(target, str) else []
            if drivers:
                primary = max(drivers, key=lambda d: len(self._reference_ligands(d)),
                              default=drivers[0])
                if self._reference_ligands(primary):
                    self._disease_label = target
                    target_str = primary
            kind, mu_req, profiles, ref_name, gap, kd, kh = self._read_target_ext(
                target_str, network=network)
            if self._disease_label:
                ref_name = f"{self._disease_label} → birincil sürücü {target_str}"
            if kind == "invalid":
                return ProductionCertificate(
                    target=target, target_kind="invalid",
                    verdict="GEÇERSİZ", note="Hedef encode edilemedi.")

        kappa_thr = self._kappa_threshold(profiles)

        # ── 1. Çok-stratejili havuz ─────────────────────────────────────
        pool = self._build_pool(target_str, mu_req, profiles, max_steps, beam_width)

        # ── 2. Yargı + sırala ──────────────────────────────────────────
        # proven-first: kanıtlanmış stratejilerden (1-5) gelen aday, de-novo yedeğinden
        # (6-7) ÖNCE sıralanır — druggable hedef de-novo'nun küçük-molekül eşleştiricisine
        # kapılmaz; de-novo yalnız kanıtlanmış aday yoksa öne çıkar.
        denovo_set = getattr(self, "_denovo_smiles", set())
        scored: list[dict] = []
        for smi in pool:
            ok, pmin, fit, efit = self._judge_on_axis(smi, mu_req)
            scored.append({"smiles": smi, "sturm_ok": ok, "pivot_min": pmin,
                           "kappa_fit": fit, "entropy_fit": efit,
                           "coherent": False, "axes": [],
                           "_denovo": smi in denovo_set})
        scored.sort(key=lambda r: (r["_denovo"], not r["sturm_ok"],
                                   r["kappa_fit"], r["entropy_fit"]))

        # ── 3. Evren kapanışı (ters hedefte) ───────────────────────────
        if kd is not None and kh is not None:
            for c in scored[:top_k]:
                proof = judge.close_universe(c["smiles"], kd, kh, mu_req, epsilon)
                c["closure"] = {
                    "applicable": proof.applicable,
                    "universe_closes": proof.universe_closes,
                    "closure_error": round(proof.closure_error, 4),
                    "epsilon": proof.epsilon,
                    "pivot_min": round(proof.pivot_min, 4),
                    "sturm_ok": proof.sturm_ok,
                }
            # öne al: kapananlar önce (proven-first korunur, χ tiebreaker)
            scored.sort(key=lambda r: (
                not r.get("closure", {}).get("universe_closes", False),
                r.get("_denovo", False),
                not r["sturm_ok"], r["kappa_fit"], r.get("entropy_fit", 0.0)))

        # ── 4. Refine (kapatan yoksa) ───────────────────────────────────
        closes_count = sum(
            1 for c in scored if c.get("closure", {}).get("universe_closes", False))
        refine_used = 0
        for _rnd in range(min(refine_rounds, 3)):
            if closes_count >= 1:
                break
            new_smi = self._refine(scored, mu_req, profiles, max_steps, beam_width)
            for smi in new_smi:
                if smi not in {c["smiles"] for c in scored}:
                    ok, pmin, fit, efit = self._judge_on_axis(smi, mu_req)
                    c = {"smiles": smi, "sturm_ok": ok, "pivot_min": pmin,
                         "kappa_fit": fit, "entropy_fit": efit,
                         "coherent": False, "axes": []}
                    if kd is not None and kh is not None:
                        proof = judge.close_universe(smi, kd, kh, mu_req, epsilon)
                        c["closure"] = {
                            "applicable": proof.applicable,
                            "universe_closes": proof.universe_closes,
                            "closure_error": round(proof.closure_error, 4),
                            "epsilon": proof.epsilon,
                            "pivot_min": round(proof.pivot_min, 4),
                            "sturm_ok": proof.sturm_ok,
                        }
                        if proof.universe_closes:
                            closes_count += 1
                    scored.append(c)
            refine_used += 1
        scored.sort(key=lambda r: (
            not r.get("closure", {}).get("universe_closes", False),
            r.get("_denovo", False),
            not r["sturm_ok"], r["kappa_fit"], r.get("entropy_fit", 0.0)))

        # ── 5. Kombinasyon (hâlâ kapanmıyorsa) ────────────────────────
        combo_pairs: list[tuple[str, str]] = []
        if combination and closes_count == 0 and kd is not None and kh is not None:
            combo_pairs = self._decompose_combination(mu_req, profiles,
                                                      max_steps, beam_width)
            for s1, s2 in combo_pairs[:3]:
                from tantrium.core.quantum_moments import FreeCumulants
                mu1 = self._encode(s1)
                mu2 = self._encode(s2)
                if mu1 and mu2:
                    kc1 = FreeCumulants.from_moments(mu1)
                    kc2 = FreeCumulants.from_moments(mu2)
                    kj = kd.add(kc1).add(kc2)
                    import math
                    combo_err = sum(
                        abs(math.tanh(kj.k[i]) - math.tanh(kh.k[i]))
                        for i in range(min(4, len(kj.k), len(kh.k))))
                    mu_joint = kj.to_moments_approx()
                    mu_h_app = kh.to_moments_approx()
                    sturm_ok, pmin = self._sturm_path_pivot_min(mu_joint, mu_h_app)
                    if combo_err < epsilon and sturm_ok:
                        closes_count += 1
                    scored.insert(0, {
                        "smiles": s1, "sturm_ok": sturm_ok,
                        "pivot_min": pmin, "kappa_fit": combo_err,
                        "coherent": False, "axes": [],
                        "combination_partner": s2,
                        "closure": {"applicable": True,
                                    "universe_closes": combo_err < epsilon and sturm_ok,
                                    "closure_error": round(combo_err, 4),
                                    "epsilon": epsilon, "pivot_min": round(pmin, 4),
                                    "sturm_ok": sturm_ok}})

        # ── 6. 6 eksen yargısı (top-K adayda) ─────────────────────────
        ref_smiles_list = []
        for _, smi in self._reference_ligands(target_str)[:4]:
            ref_smiles_list.append(smi)
        # SMILES hedef: kütüphanede referans yok → hedefin kendisi yapisal kıyaslama
        if kind == "smiles" and not ref_smiles_list and self._is_smiles(target_str):
            ref_smiles_list = [target_str]

        for c in scored[:top_k]:
            axes_obj, coherent = judge.judge_all_axes(
                c["smiles"], mu_req, profiles, kappa_thr, ref_smiles_list,
                structural_soft=(kind in ("disease", "findings")))
            c["axes"] = [{"name": a.name, "ok": a.ok, "value": round(a.value, 4),
                          "threshold": a.threshold, "detail": a.detail}
                         for a in axes_obj]
            c["_axes_obj"] = axes_obj   # AxisVerdict nesneleri sertifika için
            c["coherent"] = coherent

        # ── 7. Hüküm ───────────────────────────────────────────────────
        best_closes = next(
            (c for c in scored if c.get("closure", {}).get("universe_closes", False)
             and c.get("coherent")), None)
        best_coherent = next(
            (c for c in scored if c.get("coherent")), None)
        best = best_closes or best_coherent or (scored[0] if scored else None)

        # ── LGV/DPP ÇEŞİTLİLİK SERTİFİKASI (kazanan DEĞİŞMEZ) ────────────
        # Aday havuzunun kesişmezliği = imza Gram-determinantı (DPP hacmi). Büyük = havuz
        # gereksiz-değil (gerçek strateji çeşitliliği); küçük = adaylar birbirinin kopyası.
        # Total pozitiflik / nonintersecting-path determinantının üretimde uygulamalı yüzü
        # (deep-research: generatif döngüde sömürülmemiş). Raporlanan alternatifler de
        # çeşitliliğe göre yeniden dizilir — yakın-kopya israfı biter. best KORUNUR.
        pool_diversity = 0.0
        try:
            from tantrium.core.diversity import diversity_volume, diverse_select
            judged = scored[:top_k]
            sigs = [self._signature(c["smiles"]).mu for c in judged]
            pool_diversity = float(diversity_volume(sigs))
            if best is not None and len(judged) > 2:
                rest = [c for c in judged if c is not best]
                rvecs = [self._signature(c["smiles"]).mu for c in rest]
                order = diverse_select(rvecs, len(rest),
                                       prefilter=[c.get("kappa_fit", 0.0) for c in rest])
                scored = [best] + [rest[i] for i in order] + scored[top_k:]
        except Exception:
            pass

        if best is None:
            return ProductionCertificate(
                target=target_str, target_kind=kind, required_moments=mu_req,
                reference=ref_name, realizability_gap=gap,
                verdict="ÜRETİLEMEDİ",
                note="Havuz boş veya tüm adaylar elendi.")

        smi_best = best["smiles"]
        ok_best = best["sturm_ok"]
        pmin_best = best["pivot_min"]
        fit_best = best["kappa_fit"]
        coh_best = best.get("coherent", False)
        closes_best = best.get("closure", {}).get("universe_closes", False)

        if kind in ("disease",):
            works = closes_best and coh_best
            verdict = ("İŞE YARAYABİLİR" if works
                       else "KISMÎ" if coh_best
                       else "İŞE YARAMAZ")
        else:
            works = ok_best and fit_best <= kappa_thr and coh_best
            verdict = "İŞE YARAYABİLİR" if works else "İŞE YARAMAZ"

        # ── 8. 3D (tutarlı tüm adaylara) ─────────────────────────────
        sdf = ""
        if coh_best:
            os.makedirs(out_dir, exist_ok=True)
            try:
                from tantrium.core.inverse import InverseTransport
                inv3d = InverseTransport(self.engine)
                sdf = inv3d._make_3d(smi_best, f"produce_{target[:10]}", out_dir)
                # En iyi adayın SDF yolunu candidates içine de yaz
                for c in scored[:top_k]:
                    if c["smiles"] == smi_best:
                        c["sdf_path"] = sdf
                # Diğer tutarlı adaylara da 3D üret (en fazla 4)
                n_extra = 0
                for i, c in enumerate(scored[:top_k]):
                    if c["smiles"] == smi_best or not c.get("coherent"):
                        c.setdefault("sdf_path", "")
                        continue
                    if n_extra >= 4:
                        c.setdefault("sdf_path", "")
                        continue
                    try:
                        c["sdf_path"] = inv3d._make_3d(
                            c["smiles"], f"cand_{target[:8]}_{i}", out_dir)
                        n_extra += 1
                    except Exception:
                        c["sdf_path"] = ""
            except Exception:
                pass

        # ── 9. Enjeksiyon ─────────────────────────────────────────────
        injected_as = ""
        if inject and coh_best:
            injected_as = self._inject_manifold(smi_best, target_str)

        # ── 10. Sertifika ─────────────────────────────────────────────
        from tantrium.core.production_judge import ClosureProof
        closure_obj = None
        if "closure" in best:
            cl = best["closure"]
            closure_obj = ClosureProof(
                applicable=cl.get("applicable", False),
                closure_error=cl.get("closure_error", float("inf")),
                epsilon=cl.get("epsilon", epsilon),
                pivot_min=cl.get("pivot_min", float("-inf")),
                sturm_ok=cl.get("sturm_ok", False),
                universe_closes=cl.get("universe_closes", False))

        return ProductionCertificate(
            target=target_str, target_kind=kind, reference=ref_name,
            required_moments=mu_req, realizability_gap=gap,
            designed_smiles=smi_best, n_atoms=self._n_atoms(smi_best),
            combination=[c.get("combination_partner", "") for c in scored
                         if c.get("combination_partner")] or [],
            axes=best.get("_axes_obj", []),
            coherent=coh_best, closure=closure_obj,
            sturm_path_ok=ok_best, pivot_min=pmin_best, signature_fit=fit_best,
            refine_rounds_used=refine_used,
            injected_as=injected_as, sdf_path=sdf,
            candidates=scored[:top_k], pool_diversity=pool_diversity, verdict=verdict,
            note=("Üretim ve yargı tek Sturm-pozitiflik ekseni (RH'nin H_{d,j}≥0 "
                  "kriteri). Sistem tahmin etmez — matematiksel sertifika üretir. "
                  "Wet-lab onayı ayrıdır."),
        )

    # ── SAF MATEMATİK kapanışı (harf yok) ─────────────────────────────────

    def produce_math(self, disease, build: bool = False, healthy=None) -> "MathDrug":
        """Hastalık → ilaç, TAMAMEN matematik (harf/SMILES yok). RH parçalarının zinciri.

        disease:
          • moment listesi (list[float]) — ÖLÇÜLEN hastalık imzası (lab cihazı/spektrum,
            saf sayı). En dürüst giriş: hastalık bir KÜME sayı.
          • bulgu listesi (list[str]) — ölçülen moleküler sinyaller; her biri κ'ya çekilip
            serbest-toplanır (yine sayıya iner, isim aranmaz).

        Akış (her adım bir RH parçası, hepsi sayı uzayında):
          κ_disease → κ_healthy ⊟ κ_disease = κ_drug → μ_drug → özdeğer ölçüsü (ilaç) →
          Hankel-PSD (D-poz) ∧ Sturm pivot (Jensen) = gerçeklenebilirlik (RH sertifikası).

        build=True: SON ADIM — düzeltici spektruma (μ_drug) en yakın gerçeklenebilir YAPIYI
          (molekül) kur (genesis/havuz + Sturm yargısı). Harf yalnız burada çıkar. Böylece
          ölçülen hastalık (sayı) → gerçek ilaç (yapı) baştan sona TEK akış.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        from tantrium.core.reconstruct import reconstruct_measure
        from tantrium.core.paradigms import CertifiableObject
        from fractions import Fraction

        # κ_disease: saf sayıdan (moment) ya da ölçülen bulgudan (serbest-toplam)
        if isinstance(disease, (list, tuple)) and disease and all(
                isinstance(x, (int, float)) for x in disease):
            mu_d = [float(x) for x in disease]
            kd = FreeCumulants.from_moments(mu_d)
        elif isinstance(disease, (list, tuple)):
            kd = FreeCumulants([0.0] * 6)
            for f in disease:
                mu = self._encode(str(f))
                if mu:
                    kd = kd.add(FreeCumulants.from_moments(mu))
            mu_d = kd.to_moments_approx()
        else:                                   # tek string → encode (geriye-uyum)
            mu_d = self._encode(str(disease))
            kd = FreeCumulants.from_moments(mu_d) if mu_d else FreeCumulants([0.0] * 6)

        # Sağlıklı taban: KİŞİSELLEŞTİRME — None → genel ζ; DNA/moment → BU kişinin imzası.
        if healthy is None:
            kh = self._canonical_kappa()
        elif isinstance(healthy, (list, tuple)) and healthy and all(
                isinstance(x, (int, float)) for x in healthy):
            kh = FreeCumulants.from_moments([float(x) for x in healthy])
        else:                                    # ad/dizi → kanonik sağlıklı denge
            kh = self._canonical_kappa()
        # κ_drug = κ_healthy ⊟ κ_disease (serbest dekonvolüsyon) + gerçeklenebilir μ'ye düş
        mu_drug, gap = self._deconvolve_to_target(kd, kh)
        k_drug = FreeCumulants.from_moments(mu_drug)

        # İlacın KENDİSİ = özdeğer ölçüsü (Hamburger/Gauss kuadratür) — saf spektrum
        rec = reconstruct_measure(mu_drug, max_atoms=4)

        # RH pozitiflik TANILARI: Hankel-PSD (D-poz/Aleph) — ham düzeltici imza tam moment
        # dizisi mi (işaretli farkın temizliği); Sturm pivot (Jensen) — yol gerçek-ölçü mü.
        obj = CertifiableObject(
            name="⟨math_drug⟩",
            moments=[Fraction(x).limit_denominator(10 ** 9) for x in mu_drug])
        hankel_psd = obj.is_moment_sequence(size=4)
        sturm_ok, pmin = self._sturm_path_pivot_min(mu_d, mu_drug)

        # GERÇEKLENEBİLİR: düzeltici imzaya en yakın ATOMİK ölçü (reconstruct) geçerli mi
        # (ağırlıklar ≥ 0 = gerçek molekül-ölçüsü) VE açık küçük mü. Ham κ-farkı genelde
        # tek molekül değildir (işaretli); gerçek ilaç bu projeksiyondur, açık = uzaklığı.
        weights_valid = bool(rec.weights) and all(w >= -1e-9 for w in rec.weights)
        gap_val = float(gap if gap is not None else 0.0)
        realizable = bool(weights_valid and gap_val < 0.05)

        out = MathDrug(
            kappa_disease=list(kd.k),
            kappa_healthy=list(kh.k),
            kappa_drug=list(k_drug.k),
            moments=list(mu_drug),
            eigenvalues=list(rec.support),
            weights=list(rec.weights),
            hankel_psd=hankel_psd,
            sturm_pivot=float(pmin),
            realizable=realizable,
            realizability_gap=gap_val,
        )

        # SON ADIM: düzeltici spektruma (μ_drug) en yakın gerçeklenebilir YAPIYI kur.
        # produce(μ_drug) = moment-hedef yolu → havuz (genesis/inverse/morph) + Sturm yargısı.
        # Harf (SMILES) yalnız burada; çekirdek baştan sona sayıydı.
        if build:
            try:
                cert = self.produce(list(mu_drug), inject=False)
                out.designed_smiles = getattr(cert, "designed_smiles", "") or ""
                out.n_atoms = int(getattr(cert, "n_atoms", 0) or 0)
                out.structure_coherent = bool(getattr(cert, "coherent", False))
            except Exception:
                pass

        return out
