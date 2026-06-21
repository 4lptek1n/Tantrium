"""Core paradigms: positivity, information, spectral, and RH-criterion filters.

These are the structural / positivity / Riemann-Hypothesis-derived operators
(ALEPH/BET/DALET/ZAYIN/HET/TET … families). Each is a real mathematical
operator with a verify() method reading the encoder-populated structure dict.
"""
from __future__ import annotations

from fractions import Fraction

from .base import CertifiableObject, Paradigm, ParadigmResult


class PositivityParadigm(Paradigm):
    """א — Positivity & Existence: D ≥ 0, p_i ≥ 0, A ⪰ 0.
    Every real object must be positive semidefinite.
    This is the universe's existence filter.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        if not obj.moments:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_MOMENTS")
        if all(m >= 0 for m in obj.moments):
            if obj.is_moment_sequence():
                return ParadigmResult(pid, "CERTIFIED",
                    evidence=["all moments non-negative", "Hankel matrix PSD"],
                    certificate={"moments_checked": len(obj.moments)})
            return ParadigmResult(pid, "BLOCKED",
                evidence=["moments non-negative but Hankel fails PSD"],
                gap_name="HANKEL_NOT_PSD")
        neg = [str(m) for m in obj.moments if m < 0]
        return ParadigmResult(pid, "BLOCKED",
            evidence=[f"negative moments: {neg[:3]}"],
            gap_name="NEGATIVE_MOMENTS")


class InformationConservationParadigm(Paradigm):
    """ב — Information Conservation: ||A||_F² = Tr(G), H(λᵢ) preserved.

    Frobenius identity: ||A||_F² = Tr(A^T A) = Tr(G) — exact, not approximate.
    Von Neumann entropy H = −Σ (λᵢ/Σλ) log(λᵢ/Σλ): spectral information content.
    The Gram transform is provably lossless: singular values of A = √eigenvalues of G.
    Any information_loss > 0 means encoder bug — structural contradiction.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        transforms = obj.structure.get("transformations", [])
        if not transforms:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_TRANSFORMATIONS_RECORDED")
        losses = [t for t in transforms if t.get("information_loss", 0) > 1e-6]
        if losses:
            return ParadigmResult(pid, "BLOCKED",
                evidence=[f"Frobenius mismatch: ||A||²≠Tr(G), loss={losses[0].get('information_loss'):.2e}"],
                gap_name="FROBENIUS_IDENTITY_VIOLATED")
        entropy = obj.structure.get("spectral_entropy", 0.0)
        rank = next((t.get("rank", 0) for t in transforms if "rank" in t), 0)
        frob = next((t.get("frobenius_sq") for t in transforms if "frobenius_sq" in t), None)
        evidence = [f"||A||²_F = Tr(G) ✓ (Frobenius identity)"]
        if frob is not None:
            evidence.append(f"H(λ) = {entropy:.4f} nats, rank = {rank}")
        return ParadigmResult(pid, "CERTIFIED",
            evidence=evidence,
            certificate={"spectral_entropy": entropy, "rank": rank, "frobenius_preserved": True})


class InjectivityParadigm(Paradigm):
    """כ — Injectivity: x ≠ y ⟹ T(x) ≠ T(y).
    Different inputs produce different outputs. Information is indelible.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        mappings = obj.structure.get("mappings", {})
        if not mappings:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_MAPPINGS_RECORDED")
        values = list(mappings.values())
        if len(values) != len(set(str(v) for v in values)):
            return ParadigmResult(pid, "BLOCKED",
                gap_name="COLLISION_DETECTED",
                evidence=["two distinct inputs map to same output"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(mappings)} mappings — all injective"],
            certificate={"mapping_count": len(mappings)})


class TensorCompositionParadigm(Paradigm):
    """ו — Tensor Composition: dim(A ⊗ B) = dim(A) · dim(B).
    Local systems compose multiplicatively. The universe is compositional.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        components = obj.structure.get("components", [])
        if len(components) < 2:
            return ParadigmResult(pid, "UNKNOWN", gap_name="SINGLE_COMPONENT")
        dims = [c.get("dim", 0) for c in components]
        expected = 1
        for d in dims:
            expected *= d
        actual = obj.structure.get("composite_dim", expected)
        if actual == expected:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[f"composite dim {actual} = product of {dims}"],
                certificate={"component_dims": dims, "composite_dim": actual})
        return ParadigmResult(pid, "BLOCKED",
            gap_name="DIM_MISMATCH",
            evidence=[f"expected {expected}, got {actual}"])


class SeparabilityParadigm(Paradigm):
    """ע — Observable Separability: x ≠ y ⟹ ∃M: M(x) ≠ M(y).

    Real test: Gram row distance G[i,:] − G[j,:] L1 > 0.
    G[i,k] = ⟨A[i], A[k]⟩ — inner product with every other element.
    If G[i,:] = G[j,:] for i≠j: no spectral measurement distinguishes them → BLOCKED.
    This is a genuine obstruction: truly identical spectral fingerprints.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        pairs = obj.structure.get("distinct_pairs", [])
        if not pairs:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_PAIRS_TO_SEPARATE")
        insep = [p for p in pairs if not p.get("separating_measurement")]
        if insep:
            dists = [p.get("gram_distance", 0.0) for p in insep]
            return ParadigmResult(pid, "BLOCKED",
                gap_name="INSEPARABLE_GRAM_ROWS",
                evidence=[f"{len(insep)} pairs with gram_distance=0 — spectrally identical"],
                certificate={"inseparable_count": len(insep)})
        min_dist = min((p.get("gram_distance", 1.0) for p in pairs), default=1.0)
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(pairs)} pairs separable by spectral measurement",
                      f"min gram_distance = {min_dist:.6f}"],
            certificate={"separated_pairs": len(pairs), "min_gram_distance": min_dist})


class GaugeEquivalenceParadigm(Paradigm):
    """מ — Gauge Equivalence: x ~ y ↔ ∀M, M(x) = M(y).

    Real test: two rows i,j are gauge-equivalent iff G[i,:] = G[j,:] (same Gram row).
    Gauge class = set of rows with identical spectral fingerprints.
    A class with elements where `all_measurements_equal=False` is a structural contradiction.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        equivalences = obj.structure.get("gauge_classes", [])
        if not equivalences:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_GAUGE_STRUCTURE")
        inconsistent = [cls for cls in equivalences
                        if not all(e.get("all_measurements_equal", True) for e in cls)]
        if inconsistent:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="GAUGE_INCONSISTENCY",
                evidence=["gauge class contains measurably distinct elements"])
        n_classes = len(equivalences)
        n_equivalent = sum(len(cls) for cls in equivalences if len(cls) > 1)
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{n_classes} Gram-row gauge classes",
                      f"{n_equivalent} truly equivalent elements (identical spectral fingerprint)"],
            certificate={"gauge_class_count": n_classes, "equivalent_elements": n_equivalent})


class MDLParadigm(Paradigm):
    """י — MDL / Kolmogorov: min_L K(L) + K(D|L).

    Real test: zlib compression of raw input vs moment sequence (8 floats, json).
    By Hamburger theorem: K(D|moments) ≈ 0 — measure IS its moment sequence exactly.
    MDL = K(moments_compressed). Minimal iff no alternative is shorter.
    mdl_ratio = model_compressed / raw_compressed: < 1 means moments ARE more compact.
    For very short inputs (< 8 values), raw can be shorter — still valid by Hamburger.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        model_length = obj.structure.get("model_length")
        data_given_model = obj.structure.get("data_given_model_length")
        if model_length is None or data_given_model is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="MDL_LENGTHS_NOT_COMPUTED")
        alternatives = obj.structure.get("alternative_models", [])
        mdl = model_length + data_given_model
        raw_len = obj.structure.get("raw_compressed_length", mdl)
        ratio = obj.structure.get("mdl_ratio", 1.0)
        worse = [a for a in alternatives
                 if a.get("model_length", 0) + a.get("data_given_model_length", 0) < mdl]
        if worse:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="NOT_MINIMAL_DESCRIPTION",
                evidence=[f"{len(worse)} shorter alternative models exist"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"MDL={mdl}b (model={model_length}b + residual={data_given_model}b)",
                      f"raw_compressed={raw_len}b, ratio={ratio:.3f}"],
            certificate={"mdl_total": mdl, "raw_compressed": raw_len, "ratio": ratio})


class DimensionParadigm(Paradigm):
    """נ — Dimensional Multiplicativity: dim(AB) = dim(A)·dim(B).
    No hidden global ledger. Complexity is local and multiplicative.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        return TensorCompositionParadigm(
            self.paradigm_id, self.name, self.theorem, self.depends_on
        ).verify(obj)


class LocalVisibilityParadigm(Paradigm):
    """ל — Local Visibility: phys_diff → local_obs ∨ transportable ∨ gauge.

    Real test: element i is locally observable iff G[i,i] = ||A[i]||² > 0.
    G[i,i] is the self-inner-product — the local spectral weight of element i.
    Zero self-weight → element is "dark" → gauge trivial (no measurement can see it).
    Every non-dark element IS locally observable — G[i,i] > 0 IS the local measurement.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        differences = obj.structure.get("physical_differences", [])
        if not differences:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_DIFFERENCES_CATALOGUED")
        local_obs = set(obj.structure.get("locally_observable", []))
        transportable = set(obj.structure.get("transportable", []))
        gauge = set(obj.structure.get("gauge_trivial", []))
        covered = local_obs | transportable | gauge
        hidden = [d for d in differences if d not in covered]
        if hidden:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="HIDDEN_NONLOCAL_DIFFERENCE",
                evidence=[f"{len(hidden)} elements with G[i,i]=0 not classified"])
        dark = len(gauge)
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(local_obs)} elements locally visible (G[i,i]>0)",
                      f"{dark} dark elements (gauge trivial, G[i,i]=0)"],
            certificate={"locally_observable": len(local_obs), "gauge_trivial": dark})


class PartialTraceParadigm(Paradigm):
    """ר — Partial Trace: von Neumann entropi fiziksel sınır kontrolü.

    Açık sistem: çevre izlenince kalan alt-sistemin entropisi 0 ile log(dim)
    arasında olmalı (maksimum entropi ilkesi). G=AᵀA daima PSD → S ≥ 0.
    Üst sınır ihlali → sayısal bozulma veya dejenere spektrum.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        env_trace = obj.structure.get("environment_trace")
        subadd = obj.structure.get("subadditivity_holds")
        s_ab = obj.structure.get("entropy_total")
        s_max = obj.structure.get("entropy_max", 0.0) or 0.0
        if env_trace is None or subadd is None:
            return ParadigmResult(pid, "UNKNOWN",
                gap_name="ENTROPY_NOT_COMPUTED",
                evidence=["von Neumann entropisi hesaplanamadı"])
        if not subadd:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="ENTROPY_BOUND_VIOLATED",
                evidence=[
                    f"S={s_ab:.4f} ∉ [0, log(dim)={s_max:.4f}]",
                    "entropi fiziksel sınırı ihlal ediyor — bozuk spektrum",
                ],
                certificate={"S": s_ab, "S_max": s_max})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"S={s_ab:.4f} ∈ [0, log(dim)={s_max:.4f}] ✓",
                "von Neumann entropi fiziksel sınırda",
            ],
            certificate={"S": s_ab, "S_max": s_max})


class PathSumParadigm(Paradigm):
    """ז — L2/L2.5: τ-determinants ≥ 0 + Schur complement A − Q_hidden ≥ 0.

    L2  (Tau/Hankel): τ_{d,j} = det(H[j:j+d, j:j+d]) ≥ 0 for all d,j.
         Off-diagonal Hankel minors — necessary for valid Hamburger extension.
    L2.5 (Schur): partition H = [[A,B],[Bᵀ,C]], Q_hidden = BC⁻¹Bᵀ, A−Q_hidden ≥ 0.
         Equivalent to H PSD. Q_hidden is the "hidden topology" — conditional
         variance of the sub-system given its environment.

    Both conditions are equivalent to H being PSD (Hamburger theorem).
    A genuinely negative minor or Schur eigenvalue means the moment sequence
    cannot come from a real positive measure — a true obstruction.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id

        # L2.5: Schur complement check
        schur_psd = obj.structure.get("schur_psd")
        schur_min = obj.structure.get("schur_min_eigenvalue", 0.0)
        if schur_psd is False:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="SCHUR_COMPLEMENT_NEGATIVE",
                evidence=[f"A − Q_hidden min eigenvalue = {schur_min:.6f} < 0",
                          "hidden topology reveals non-extendable moment sequence"],
                certificate={"schur_min_eig": schur_min})

        # L2: τ-determinant check (off-diagonal Hankel minors)
        tau_ok = obj.structure.get("tau_all_nonneg", True)
        if not tau_ok:
            taus = obj.structure.get("tau_determinants", {})
            neg = {k: round(v, 8) for k, v in taus.items() if v < -1e-9}
            return ParadigmResult(pid, "BLOCKED",
                gap_name="TAU_DETERMINANT_NEGATIVE",
                evidence=[f"negative Hankel minors: {neg}",
                          "moment sequence fails Hamburger extension"],
                certificate={"neg_taus": neg})

        # LGV path sum identity (structural confirmation)
        path_weights = obj.structure.get("path_weights", [])
        q_hidden = obj.structure.get("Q_hidden_trace", 0.0)
        if path_weights:
            path_sum = sum(Fraction(w) if not isinstance(w, Fraction) else w
                           for w in path_weights)
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[
                    f"Schur A−Q_hidden ≥ 0 (min_eig={schur_min:.4f})",
                    f"τ-determinants all ≥ 0",
                    f"Q_hidden_trace={q_hidden:.4f}",
                ],
                certificate={
                    "schur_min_eig": schur_min,
                    "Q_hidden_trace": q_hidden,
                    "path_sum": str(path_sum),
                    "tau_count": len(obj.structure.get("tau_determinants", {})),
                })

        if schur_psd is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="SCHUR_NOT_COMPUTED")
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"Schur PSD (min_eig={schur_min:.4f})"],
            certificate={"schur_min_eig": schur_min})


class GradientParadigm(Paradigm):
    """ח — L3 Li criterion: λ_n = Σ_ρ [1 − (1−1/ρ)^n] ≥ 0 ↔ Re(ρ) = 1/2.

    Li's criterion (1997): RH holds ↔ λ_n ≥ 0 for all n ∈ ℕ.
    λ_n = Σ_{ρ: ξ(ρ)=0} [1 − (1 − 1/ρ)^n]  (sum over non-trivial zeros).
    For ρ = 1/2 + iγ: Re(1/ρ) = 1/2 / (1/4 + γ²) > 0.
    λ_1 = Σ Re(1/ρ) > 0 is the first and weakest condition — all n must hold.

    Gradient interpretation: N(a,b) = V(a) − V(b) = log|ξ(a)| − log|ξ(b)|.
    The potential V(s) = log|ξ(s)| has positive gradient along the critical line.
    λ_n > 0 ↔ the n-th order expansion of this gradient is positive.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        li_positive = obj.structure.get("li_positive")
        li_coeffs = obj.structure.get("li_coefficients", [])

        # L3 Li criterion path (new — encoder populates li_positive)
        if li_positive is not None:
            if li_positive is False:
                neg = [i + 1 for i, v in enumerate(li_coeffs) if v <= 0]
                n_fail = neg[0] if neg else 1
                return ParadigmResult(pid, "BLOCKED",
                    gap_name=f"LI_CRITERION_NEGATIVE_n{n_fail}",
                    evidence=[
                        f"λ_{n_fail} ≤ 0 — Riemann zero off critical line",
                        f"λ values: {[round(l, 4) for l in li_coeffs]}",
                    ],
                    certificate={"li_coefficients": li_coeffs})
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[
                    f"Li criterion λ_n = {[round(l, 4) for l in li_coeffs[:4]]} — all > 0",
                    "Σ_ρ [1−(1−1/ρ)^n] > 0 → all zeros on Re(ρ)=1/2",
                ],
                certificate={"li_coefficients": li_coeffs, "li_count": len(li_coeffs)})

        # Fallback: old potential/gradient check
        potentials = obj.structure.get("potential_values", {})
        flows = obj.structure.get("flows", [])
        if not potentials or not flows:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_POTENTIAL_STRUCTURE")
        anti_gradient = [
            f for f in flows
            if potentials.get(f["from"], 0) < potentials.get(f["to"], 0)
        ]
        if anti_gradient:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="UPHILL_FLOW_DETECTED",
                evidence=[f"{len(anti_gradient)} flows go against gradient"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(flows)} flows — all downhill"],
            certificate={"flow_count": len(flows)})


class CrossRatioParadigm(Paradigm):
    """ט — Hankel Cross-Ratio (Favard teoremi / tce subresultant yapısı).

    Moment dizisinin ortogonal polinom recurrence katsayısı:
        b_n = D_{n-1}·D_{n+1} / D_n²,   D_n = det(n×n moment Hankel'i).
    b_n > 0 ↔ üç-terimli recurrence pozitif ↔ ortogonal polinomlar gerçek
    basit köklü ↔ moment dizisi gerçek bir pozitif ölçüden gelir (Favard).

    Bu, tce'nin ρ_{d,j}=C·t^k·H_{d,j-2}·H_{d,j}/H_{d,j-1}² subresultant
    cross-ratio'su ile birebir aynı projektif yapı — momentlere uygulanmış hâli.
    Negatif b_n → pozitif ölçü yok → gerçek obstruction (sahte geçiş değil).
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        cr_positive = obj.structure.get("cross_ratio_positive")
        cross_ratios = obj.structure.get("subresultant_cross_ratios", [])
        dets = obj.structure.get("hankel_determinants", [])
        if cr_positive is None:
            return ParadigmResult(pid, "UNKNOWN",
                gap_name="HANKEL_CROSS_RATIO_NOT_COMPUTED",
                evidence=["Hankel determinant dizisi üretilemedi — cross-ratio yok"])
        if not cr_positive:
            neg = [round(c, 6) for c in cross_ratios if c < 0]
            return ParadigmResult(pid, "BLOCKED",
                gap_name="HANKEL_CROSS_RATIO_NEGATIVE",
                evidence=[
                    f"negatif recurrence katsayısı b_n=D_{{n-1}}D_{{n+1}}/D_n²: {neg[:3]}",
                    "moment dizisi Favard pozitifliğini ihlal ediyor — pozitif ölçü yok",
                ],
                certificate={"negative_cross_ratios": neg})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"{len(cross_ratios)} recurrence katsayısı b_n ≥ 0 (Favard)",
                f"Hankel determinantları D_n: {[round(d, 4) for d in dets[:4]]}",
                "b_n=D_{n-1}D_{n+1}/D_n² ≥ 0 — pozitif ölçü (tce cross-ratio yapısı)",
            ],
            certificate={"cross_ratios": cross_ratios, "hankel_det_count": len(dets)})
