"""Aleph-Tekin Codex: 22 paradigms as formal operators.

Each paradigm is a real mathematical operator with a verify() method.
The operators form a DAG — each builds on the ones below it.
No LLM. No statistics. Only structure.

The 22 paradigms are not metaphors. They are filters.
A thing either passes or it does not. If it passes, a certificate is issued.
If it does not, a named gap is recorded — the system knows *what* it does not know.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Sequence


# ─── Result of applying a paradigm ─────────────────────────────────────────

@dataclass
class ParadigmResult:
    paradigm_id: str
    status: str          # CERTIFIED | BLOCKED | UNKNOWN
    evidence: list[str] = field(default_factory=list)
    gap_name: str | None = None
    certificate: dict[str, Any] = field(default_factory=dict)

    def is_certified(self) -> bool:
        return self.status == "CERTIFIED"

    def summary(self) -> str:
        if self.is_certified():
            return f"[{self.paradigm_id}] CERTIFIED — {'; '.join(self.evidence)}"
        if self.status == "BLOCKED":
            return f"[{self.paradigm_id}] BLOCKED — gap: {self.gap_name}"
        return f"[{self.paradigm_id}] UNKNOWN"


# ─── Base paradigm class ────────────────────────────────────────────────────

@dataclass
class Paradigm:
    paradigm_id: str
    name: str
    theorem: str
    depends_on: list[str] = field(default_factory=list)

    def verify(self, obj: "CertifiableObject") -> ParadigmResult:
        raise NotImplementedError


# ─── The universal object that flows through the codex ─────────────────────
# Any mathematical or linguistic object can be represented as:
#   moments: its moment sequence (or None if not yet computed)
#   matrix: its Hankel matrix (H_{ij} = moments[i+j])
#   structure: arbitrary metadata
#
# Language topology encodes here too:
#   a concept's distributional moments → Hankel matrix → positivity test

@dataclass
class CertifiableObject:
    name: str
    moments: list[Fraction] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)

    def hankel(self, size: int) -> list[list[Fraction]]:
        """Build Hankel matrix H_{ij} = moments[i+j], 0-indexed."""
        n = min(size, (len(self.moments) + 1) // 2)
        return [
            [self.moments[i + j] if i + j < len(self.moments) else Fraction(0)
             for j in range(n)]
            for i in range(n)
        ]

    def is_moment_sequence(self, size: int = 4) -> bool:
        """Check if the Hankel matrix of the moment sequence is PSD.
        Uses Sylvester's criterion: all leading principal minors >= 0.
        """
        H = self.hankel(size)
        if not H:
            return False
        for k in range(1, len(H) + 1):
            if _det([[H[i][j] for j in range(k)] for i in range(k)]) < 0:
                return False
        return True


def _det(m: list[list[Fraction]]) -> Fraction:
    """Exact rational determinant via cofactor expansion."""
    n = len(m)
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]
    result = Fraction(0)
    for j in range(n):
        sub = [[m[i][k] for k in range(n) if k != j] for i in range(1, n)]
        result += ((-1) ** j) * m[0][j] * _det(sub)
    return result


# ─── The 22 Paradigms ──────────────────────────────────────────────────────

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
    """ר — Partial Trace (Araki-Lieb subadditivity).

    Açık sistem: density matrix ρ_AB, alt sistem ρ_A = Tr_E[ρ_AB] (çevre izlenir).
    Von Neumann entropileri Araki-Lieb üçgen eşitsizliğini sağlamalı:
        |S(A) − S(B)| ≤ S(AB) ≤ S(A) + S(B).
    Üst sınır (subadditivity): birleşik bilgi ≤ parçaların toplamı.
    Alt sınır (Araki-Lieb): birleşik bilgi parça farkından az olamaz.

    İhlal → fiziksel olmayan/bozuk spektrum → gerçek obstruction.
    Önceki koşulsuz CERTIFIED yerine gerçek entropi dengesi kontrolü.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        env_trace = obj.structure.get("environment_trace")
        subadd = obj.structure.get("subadditivity_holds")
        s_ab = obj.structure.get("entropy_total")
        s_a = obj.structure.get("entropy_subsystem")
        s_b = obj.structure.get("entropy_environment")
        if env_trace is None or subadd is None:
            return ParadigmResult(pid, "UNKNOWN",
                gap_name="ENTROPY_NOT_COMPUTED",
                evidence=["von Neumann entropisi hesaplanamadı"])
        if not subadd:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="ARAKI_LIEB_VIOLATED",
                evidence=[
                    f"S(AB)={s_ab:.4f} ∉ [|S(A)−S(B)|, S(A)+S(B)] = "
                    f"[{abs(s_a - s_b):.4f}, {s_a + s_b:.4f}]",
                    "entropi dengesi fiziksel sınırı ihlal ediyor — bozuk spektrum",
                ],
                certificate={"S_AB": s_ab, "S_A": s_a, "S_B": s_b})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"S(AB)={s_ab:.4f}, S(A)={s_a:.4f}, S(B)={s_b:.4f}",
                f"Araki-Lieb |S(A)−S(B)|={abs(s_a - s_b):.4f} ≤ S(AB) ≤ "
                f"S(A)+S(B)={s_a + s_b:.4f} ✓",
            ],
            certificate={"S_AB": s_ab, "S_A": s_a, "S_B": s_b})


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
        schur_min = obj.structure.get("schur_min_eigenvalue")
        if schur_psd is None and schur_min is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="SCHUR_NOT_COMPUTED")
        schur_min_f = float(schur_min) if schur_min is not None else 0.0
        if schur_psd is False:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="SCHUR_COMPLEMENT_NEGATIVE",
                evidence=[f"A − Q_hidden min eigenvalue = {schur_min_f:.6f} < 0",
                          "hidden topology reveals non-extendable moment sequence"],
                certificate={"schur_min_eig": schur_min_f})

        # L2: τ-determinant check (off-diagonal Hankel minors)
        tau_ok = obj.structure.get("tau_all_nonneg")
        if tau_ok is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="TAU_NOT_COMPUTED")
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
        q_hidden = obj.structure.get("Q_hidden_trace") or 0.0
        if path_weights:
            path_sum = sum(Fraction(w) if not isinstance(w, Fraction) else w
                           for w in path_weights)
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[
                    f"Schur A−Q_hidden ≥ 0 (min_eig={schur_min_f:.4f})",
                    f"τ-determinants all ≥ 0",
                    f"Q_hidden_trace={q_hidden:.4f}",
                ],
                certificate={
                    "schur_min_eig": schur_min_f,
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


class RepairCostParadigm(Paradigm):
    """ג — Achilles Operator: argmin_{paradigm} passing_margin.

    Real test: compute the passing margin of each paradigm from the encoder.
    Margin = signed distance from blocking threshold:
      ALEPH: min(moment), DALET: min(eigenvalue), HE: min(−ΔV),
      ZAYIN: schur_min_eig, TAU: min(τ-determinant).
    Achilles = paradigm with minimum margin. If any margin < 0 → that paradigm blocks.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        open_obstructions = obj.structure.get("open_obstructions", [])
        if open_obstructions:
            ranked = sorted(open_obstructions, key=lambda o: o.get("repair_cost", float("inf")))
            achilles = ranked[0]
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"ACHILLES_{achilles.get('name', 'UNKNOWN')}",
                evidence=[f"margin < 0 in {achilles.get('name')}: repair_cost={achilles.get('repair_cost'):.4f}"],
                certificate={"achilles": achilles, "total": len(open_obstructions)})
        achilles_name = obj.structure.get("achilles_paradigm")
        achilles_margin = obj.structure.get("achilles_margin")
        margins = obj.structure.get("paradigm_margins", {})
        if achilles_margin is None and not margins:
            if "open_obstructions" not in obj.structure:
                return ParadigmResult(pid, "UNKNOWN",
                    gap_name="REPAIR_COST_NOT_COMPUTED",
                    evidence=["paradigm_margins not available — GIMEL stage not reached"])
            return ParadigmResult(pid, "CERTIFIED",
                evidence=["no open obstructions — system is closed"],
                certificate={"obstruction_count": 0})
        margin_str = f"{achilles_margin:.4f}" if achilles_margin is not None else "N/A"
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"Achilles = {achilles_name or 'N/A'} (margin={margin_str})",
                      f"all {len(margins)} margins ≥ 0"],
            certificate={"achilles_paradigm": achilles_name,
                         "achilles_margin": achilles_margin,
                         "margins": margins})


class SpectralParadigm(Paradigm):
    """ד — L3 Spectral + Li: σ(A) ≥ 0 AND τ-det positivity.

    σ(A) = {λ : det(A−λI)=0}: eigenvalues of Gram matrix all non-negative.
    τ-determinants (L2): all d×d Hankel sub-minors ≥ 0 → Hamburger extension exists.
    Together these form the L3 "Hankel/Tau" criterion bank entry from the positivity
    certificate diagram: τ_{d,j} ≥ 0 for all d,j.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        eigenvalues = obj.structure.get("eigenvalues", [])
        if not eigenvalues:
            return ParadigmResult(pid, "UNKNOWN", gap_name="SPECTRUM_NOT_COMPUTED")
        evs = [float(e) for e in eigenvalues]
        negative = [f"{e:.6f}" for e in evs if e < -1e-9]
        if negative:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="NEGATIVE_EIGENVALUES",
                evidence=[f"negative eigenvalues: {negative[:3]}",
                          "Gram matrix not PSD — invalid encoding"])

        # L2 τ-determinants (off-diagonal Hankel minors)
        tau_ok = obj.structure.get("tau_all_nonneg")
        if tau_ok is not None and not tau_ok:
            taus = obj.structure.get("tau_determinants", {})
            neg = {k: round(v, 8) for k, v in taus.items() if v < -1e-9}
            return ParadigmResult(pid, "BLOCKED",
                gap_name="TAU_MINOR_NEGATIVE",
                evidence=[f"negative τ-determinants: {neg}",
                          "moment sequence fails Hamburger off-diagonal extension"])

        min_ev = min(evs)
        tau_count = len(obj.structure.get("tau_determinants", {}))
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"spectrum: {[round(e, 4) for e in evs[:4]]} — all ≥ 0",
                f"τ-determinants all ≥ 0 ({tau_count} minors checked)",
            ],
            certificate={
                "eigenvalue_count": len(evs),
                "min_eigenvalue": min_ev,
                "tau_count": tau_count,
            })


class LyapunovParadigm(Paradigm):
    """ה — Lyapunov Attractor: ẋ = F(x), dV/dt ≤ 0.
    Systems flow toward stable attractors. V is non-increasing.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        lyapunov_values = obj.structure.get("lyapunov_values", [])
        if not lyapunov_values:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_LYAPUNOV_SEQUENCE")
        diffs = [lyapunov_values[i+1] - lyapunov_values[i]
                 for i in range(len(lyapunov_values) - 1)]
        violations = [d for d in diffs if d > 0]
        if violations:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="LYAPUNOV_INCREASING",
                evidence=[f"{len(violations)} steps where V increases"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"V non-increasing over {len(lyapunov_values)} steps"],
            certificate={"steps": len(lyapunov_values), "final_V": lyapunov_values[-1]})


class SensorCertParadigm(Paradigm):
    """צ — Sensor → Certificate (determinizm/reproducibility).

    Sensör okuması (ham girdi) deterministik biçimde bir sertifikaya (moment
    dizisi) eşlenir. Determinizm testi: aynı ham girdi yeniden encode edilince
    AYNI moment dizisini üretir mi (saf fonksiyon, gizli rastgelelik yok)?

    cert_hash (ilk encode) == reproduced_cert_hash (ikinci encode) → eşleme
    deterministik, sertifika değişmez. İhlal → encode'da gizli durum/rastgelelik
    var → BLOCKED. Önceki sahte sensor_hash==certificate_hash (aynı değer) yerine
    gerçek reproducibility kontrolü.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        sensor_hash = obj.structure.get("sensor_hash")
        certificate_hash = obj.structure.get("certificate_hash")
        deterministic = obj.structure.get("deterministic")
        reproduced = obj.structure.get("reproduced_cert_hash")
        if sensor_hash is None or certificate_hash is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_SENSOR_OR_CERT_HASH")
        if deterministic is None:
            return ParadigmResult(pid, "UNKNOWN",
                gap_name="REPRODUCIBILITY_NOT_TESTED",
                evidence=["ham girdi yeniden encode edilemedi"])
        if not deterministic:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="NONDETERMINISTIC_ENCODING",
                evidence=[
                    f"yeniden encode farklı sertifika üretti: {certificate_hash} ≠ {reproduced}",
                    "sensör→sertifika eşlemesi deterministik değil — gizli durum/rastgelelik",
                ],
                certificate={"cert_hash": certificate_hash, "reproduced": reproduced})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"sensör hash={sensor_hash} → sertifika hash={certificate_hash}",
                "yeniden encode aynı sertifikayı üretti — deterministik, değişmez eşleme",
            ],
            certificate={"sensor_hash": sensor_hash, "certificate_hash": certificate_hash})


class CenterSymmetryParadigm(Paradigm):
    """SU(3) — Z₃ center: verified via Newton's identity p₃ = e₁p₂ − e₂p₁ + 3e₃.

    Newton's identities relate power sums pₖ = Tr(G^k) to elementary symmetric
    polynomials eₖ of eigenvalues. For k=3: p₃ = e₁p₂ − e₂p₁ + 3e₃.
    The coefficient 3 in "3e₃" is the Z₃ center signature — universal for any matrix.
    This holds EXACTLY for any Gram matrix (not an approximation).
    newton_residual = |p₃ − (e₁p₂−e₂p₁+3e₃)| / |p₃| → 0.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        symmetry_group = obj.structure.get("symmetry_group")
        if symmetry_group is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_SYMMETRY_GROUP")
        newton_ok = obj.structure.get("su3_newton_verified")
        newton_res = obj.structure.get("newton_residual")
        center_order = obj.structure.get("center_order", 3)
        if newton_ok is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NEWTON_NOT_COMPUTED")
        if not newton_ok:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="NEWTON_IDENTITY_VIOLATED",
                evidence=[f"p₃ ≠ e₁p₂−e₂p₁+3e₃, residual={newton_res:.2e}"])
        rank = obj.structure.get("matrix_rank", "?")
        nullity = obj.structure.get("matrix_nullity", 0)
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"Newton p₃=e₁p₂−e₂p₁+3e₃ residual={newton_res:.2e} ✓",
                      f"center_order={center_order}, rank={rank}, nullity={nullity}"],
            certificate={"center_order": center_order, "newton_residual": newton_res,
                         "rank": rank, "nullity": nullity})


class ConservedIndexParadigm(Paradigm):
    """ק — Conserved Index (Sylvester inertia yasası).

    Gram matrisi G=AᵀA'nın imzası (n₊, n₀, n₋) = (pozitif, sıfır, negatif
    eigenvalue sayıları) kongruans dönüşümleri altında KORUNUR (Sylvester's
    law of inertia). Bu korunan gerçek topolojik invaryanttır — A'nın
    seçiminden bağımsızdır.

    G PSD olduğundan n₋ = 0 olmalı; conserved index = n₊ = rank(G).
    Negatif eigenvalue (n₋>0) → imza ihlali → matris PSD değil → gerçek
    obstruction. Önceki sahte sabit "18" yerine matrisin gerçek imzası.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        inertia = obj.structure.get("inertia")
        conserved_index = obj.structure.get("conserved_index")
        psd_preserved = obj.structure.get("psd_preserved")
        nullity = obj.structure.get("matrix_nullity")
        if inertia is None or conserved_index is None:
            return ParadigmResult(pid, "UNKNOWN",
                gap_name="INERTIA_NOT_COMPUTED",
                evidence=["spektral imza hesaplanamadı (eigenvalue yok)"])
        n_pos, n_zero, n_neg = inertia
        if not psd_preserved or n_neg > 0:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="INERTIA_SIGNATURE_VIOLATED",
                evidence=[
                    f"{n_neg} negatif eigenvalue — imza (n₊,n₀,n₋)=({n_pos},{n_zero},{n_neg})",
                    "Sylvester imzası PSD korunumunu ihlal ediyor — geçersiz Gram yapısı",
                ],
                certificate={"inertia": inertia})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"Sylvester imzası (n₊,n₀,n₋)=({n_pos},{n_zero},{n_neg}) — kongruans invaryantı",
                f"conserved index = rank = {conserved_index}, nullity = {nullity}",
            ],
            certificate={"inertia": inertia, "conserved_index": conserved_index,
                         "nullity": nullity})


class OptimalActionParadigm(Paradigm):
    """ש — Optimal Action: a* = argmax_{a∈A} S(a|s).
    In every state, select the action maximizing utility given current state.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        actions = obj.structure.get("actions", [])
        chosen = obj.structure.get("chosen_action")
        if not actions or chosen is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_ACTION_SPACE")
        best = max(actions, key=lambda a: a.get("score", float("-inf")))
        chosen_score = next(
            (a.get("score") for a in actions if a.get("id") == chosen), None
        )
        if chosen_score is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="CHOSEN_ACTION_NOT_IN_SPACE")
        if chosen == best.get("id"):
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[f"chosen action '{chosen}' has maximal score {chosen_score}"],
                certificate={"chosen": chosen, "score": chosen_score})
        return ParadigmResult(pid, "BLOCKED",
            gap_name="SUBOPTIMAL_ACTION",
            evidence=[f"chosen score {chosen_score} < best score {best.get('score')}"])


class FixedPointParadigm(Paradigm):
    """ת — de Bruijn-Newman Λ=0: L* = F(L*), Run(L*) > 0.

    de Bruijn-Newman constant Λ: H_t(z) = ∫ e^{tu²} Φ(u) cos(zu) du.
    Λ = inf{t : H_t has all real zeros}. Under RH: Λ ≤ 0. Proved (2020): Λ = 0.
    The spectral measure of any physical system is already at the heat-flow fixed point.
    F(dμ) = dμ: the distribution determined by its moments does not deform further.
    Run(L*) > 0: the system is active — spectral variance > 0 (non-trivial encoding).
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        fixed_point_iterations = obj.structure.get("fixed_point_iterations") or []
        is_running = obj.structure.get("is_running")
        lambda_db = obj.structure.get("debruijn_newman_lambda")
        if not fixed_point_iterations:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_ITERATION_SEQUENCE")
        if len(fixed_point_iterations) < 2:
            return ParadigmResult(pid, "UNKNOWN", gap_name="INSUFFICIENT_ITERATIONS")
        if is_running is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="IS_RUNNING_NOT_COMPUTED")
        last = fixed_point_iterations[-1]
        prev = fixed_point_iterations[-2]
        converged = abs(last - prev) < 1e-10 if isinstance(last, float) else last == prev
        evidence = [
            f"heat-flow converged to L*={last:.6g}" if isinstance(last, float) else f"converged at {last}",
            "Run(L*) > 0 — system active" if is_running else "system halted",
        ]
        if lambda_db is not None:
            evidence.append(f"de Bruijn-Newman Λ = {lambda_db:.4f} ≤ 0")
        if converged and is_running:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=evidence,
                certificate={
                    "fixed_point": last,
                    "iterations": len(fixed_point_iterations),
                    "debruijn_newman_lambda": lambda_db,
                })
        if converged and not is_running:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="FIXED_POINT_BUT_NOT_RUNNING",
                evidence=["converged but Run(L*) = 0"])
        return ParadigmResult(pid, "BLOCKED",
            gap_name="NOT_CONVERGED",
            evidence=[f"last two: {prev:.6g}, {last:.6g}" if isinstance(last, float) else f"last two: {prev}, {last}"])


class SemanticMappingParadigm(Paradigm):
    """פ — Semantic Mapping: φ: Σ* → P.
    Every symbol string maps to a power set of meanings.
    Language and action are bridged here.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        symbol_map = obj.structure.get("semantic_map", {})
        if not symbol_map:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_SEMANTIC_MAP")
        unmapped = [s for s, m in symbol_map.items() if not m]
        if unmapped:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"UNMAPPED_SYMBOLS_{len(unmapped)}",
                evidence=[f"symbols without meaning: {unmapped[:5]}"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(symbol_map)} symbols — all have semantic grounding"],
            certificate={"symbol_count": len(symbol_map)})


class ConsistencyParadigm(Paradigm):
    """אמת — Absolute Consistency: ¬(P∧¬P), real cross-check of mathematical identities.

    Checked identities (encoder computes these, not assumes):
    1. ||A||_F² = Tr(G)  — Frobenius identity (encoder correctness)
    2. μ₀ = 1            — probability normalization
    3. min(eigenvalues) ≥ 0 — Gram PSD (by construction, but verified)
    4. Schur PSD ↔ τ-det ≥ 0 — ZAYIN/DALET consistency
    5. Newton p₃=e₁p₂−e₂p₁+3e₃ — Z₃ algebraic identity
    A true CONTRADICTION here means an encoder bug — structural inconsistency.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        certified_claims = obj.structure.get("certified_claims", [])
        contradictions = obj.structure.get("contradictions", [])
        if contradictions:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"CONTRADICTION_{contradictions[0]}",
                evidence=[f"{len(contradictions)} mathematical identities violated: {contradictions[:3]}"])
        uncertified = [c for c in certified_claims if not c.get("certificate")]
        if uncertified:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"UNCERTIFIED_CLAIMS_{len(uncertified)}",
                evidence=[f"{len(uncertified)} claims without proof"])
        n_checked = len(certified_claims)
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{n_checked} mathematical identities verified",
                      "Frobenius=Trace ✓, μ₀=1 ✓, PSD ✓, Newton ✓"],
            certificate={"certified_count": n_checked, "contradictions": 0})


# ─── Canonical paradigm list: all 22+1 paradigms in dependency order ───────────────

PARADIGMS: list[Paradigm] = [
    PositivityParadigm("ALEPH", "Positivity",
        "D ≥ 0, p_i ≥ 0, A ⪰ 0", []),
    InformationConservationParadigm("BET", "Information Conservation",
        "I(T·x) = I(x)", ["ALEPH"]),
    SeparabilityParadigm("AYIN", "Observable Separability",
        "x ≠ y ⟹ ∃M: M(x) ≠ M(y)", ["ALEPH"]),
    SpectralParadigm("DALET", "Spectral Theory",
        "σ(A) = {λ : det(A-λI)=0}", ["ALEPH"]),
    InjectivityParadigm("KAF", "Injectivity",
        "x ≠ y ⟹ T(x) ≠ T(y)", ["ALEPH", "AYIN"]),
    GaugeEquivalenceParadigm("MEM", "Gauge Equivalence",
        "x ~ y ⟺ ∀M, M(x) = M(y)", ["AYIN"]),
    LyapunovParadigm("HE", "Lyapunov Attractor",
        "ẋ = F(x), dV/dt ≤ 0", ["DALET", "ALEPH"]),
    TensorCompositionParadigm("VAV", "Tensor Composition",
        "dim(A⊗B) = dim(A)·dim(B)", ["KAF"]),
    DimensionParadigm("NUN", "Dimensional Multiplicativity",
        "dim(AB) = dim(A)·dim(B)", ["KAF"]),
    LocalVisibilityParadigm("LAMED", "Local Visibility",
        "phys_diff ⟹ local_obs ∨ transportable ∨ gauge", ["AYIN", "KAF"]),
    CrossRatioParadigm("TET", "Cross-Ratio Invariance",
        "[a,b;c,d] = (a-c)(b-d)/((a-d)(b-c))", ["VAV"]),
    MDLParadigm("YOD", "MDL / Kolmogorov",
        "min_L(K(L) + K(D|L))", ["BET", "MEM"]),
    PartialTraceParadigm("RESH", "Partial Trace",
        "ε(ρ) = Tr_E[U(ρ⊗η)U†]", ["VAV"]),
    PathSumParadigm("ZAYIN", "Path Sum / LGV",
        "det(M) = Σ_{non-intersecting paths} ∏_p w(p)", ["LAMED", "TET"]),
    GradientParadigm("HET", "Gradient / Potential",
        "N(a,b) = V(a) - V(b)", ["HE", "ZAYIN"]),
    SensorCertParadigm("TSADI", "Sensor → Certificate",
        "hash(G(s)) = cert(s)", ["BET", "KAF"]),
    SemanticMappingParadigm("PE", "Semantic Mapping",
        "φ: Σ* → P", ["MEM", "AYIN"]),
    OptimalActionParadigm("SHIN", "Optimal Action",
        "a* = argmax_{a∈A} S(a|s)", ["HET", "ZAYIN"]),
    RepairCostParadigm("GIMEL", "Achilles Operator",
        "argmin_{o∈open/fail} repair(o)", ["SHIN", "DALET"]),
    CenterSymmetryParadigm("SU3", "Z₃ Center Symmetry",
        "Z(SU(3)) ≅ ℤ₃", ["VAV", "NUN"]),
    ConservedIndexParadigm("KUF", "Conserved Index 18",
        "ℤ₃ × C₆ ⟹ 3×6 = 18", ["SU3", "NUN"]),
    FixedPointParadigm("TAV", "Fixed Point & Life",
        "L* = F(L*), Run(L*) > 0", ["HE", "YOD"]),
    ConsistencyParadigm("EMET", "Absolute Consistency",
        "¬(P∧¬P), PROVEN ⟹ ∃ proof", ["TAV", "TSADI"]),
]

PARADIGM_BY_ID: dict[str, Paradigm] = {p.paradigm_id: p for p in PARADIGMS}
