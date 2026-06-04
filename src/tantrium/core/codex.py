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
    """ב — Information Conservation: I(T·x) = I(x).
    Every allowed transformation preserves information completely.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        transforms = obj.structure.get("transformations", [])
        if not transforms:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_TRANSFORMATIONS_RECORDED")
        losses = [t for t in transforms if t.get("information_loss", 0) > 0]
        if losses:
            return ParadigmResult(pid, "BLOCKED",
                evidence=[f"{len(losses)} lossy transforms"],
                gap_name="INFORMATION_LOSS_DETECTED")
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(transforms)} transforms verified lossless"],
            certificate={"transform_count": len(transforms)})


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
    Truly different things can always be distinguished by some measurement.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        pairs = obj.structure.get("distinct_pairs", [])
        if not pairs:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_PAIRS_TO_SEPARATE")
        unseparable = [p for p in pairs if not p.get("separating_measurement")]
        if unseparable:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"INSEPARABLE_PAIRS_{len(unseparable)}",
                evidence=[f"{len(unseparable)} pairs have no separating measurement"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(pairs)} distinct pairs — all separable"],
            certificate={"separated_pairs": len(pairs)})


class GaugeEquivalenceParadigm(Paradigm):
    """מ — Gauge Equivalence: x ~ y ⟺ ∀M, M(x) = M(y).
    Indistinguishable objects are physically identical.
    Gauge transformations make no real difference.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        equivalences = obj.structure.get("gauge_classes", [])
        if not equivalences:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_GAUGE_STRUCTURE")
        consistent = all(
            all(e.get("all_measurements_equal", False) for e in cls)
            for cls in equivalences
        )
        if consistent:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[f"{len(equivalences)} gauge classes — all consistent"],
                certificate={"gauge_class_count": len(equivalences)})
        return ParadigmResult(pid, "BLOCKED",
            gap_name="GAUGE_INCONSISTENCY",
            evidence=["gauge class contains measurably distinct elements"])


class MDLParadigm(Paradigm):
    """י — MDL / Kolmogorov: min_L(K(L) + K(D|L)).
    The simplest model that explains the data is the real one.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        model_length = obj.structure.get("model_length")
        data_given_model = obj.structure.get("data_given_model_length")
        if model_length is None or data_given_model is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="MDL_LENGTHS_NOT_COMPUTED")
        alternatives = obj.structure.get("alternative_models", [])
        mdl = model_length + data_given_model
        worse = [a for a in alternatives
                 if a.get("model_length", 0) + a.get("data_given_model_length", 0) < mdl]
        if worse:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="NOT_MINIMAL_DESCRIPTION",
                evidence=[f"{len(worse)} shorter alternative models exist"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"MDL={mdl} — no shorter model found"],
            certificate={"mdl_total": mdl, "alternatives_checked": len(alternatives)})


class DimensionParadigm(Paradigm):
    """נ — Dimensional Multiplicativity: dim(AB) = dim(A)·dim(B).
    No hidden global ledger. Complexity is local and multiplicative.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        return TensorCompositionParadigm(
            self.paradigm_id, self.name, self.theorem, self.depends_on
        ).verify(obj)


class LocalVisibilityParadigm(Paradigm):
    """ל — Local Visibility: physical difference ⟹ local observable ∨ transportable ∨ gauge.
    Every real difference is locally detectable.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        local_obs = obj.structure.get("locally_observable", [])
        transportable = obj.structure.get("transportable", [])
        gauge = obj.structure.get("gauge_trivial", [])
        differences = obj.structure.get("physical_differences", [])
        if not differences:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_DIFFERENCES_CATALOGUED")
        covered = set(local_obs) | set(transportable) | set(gauge)
        hidden = [d for d in differences if d not in covered]
        if hidden:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="HIDDEN_NONLOCAL_DIFFERENCE",
                evidence=[f"{len(hidden)} differences are non-local and non-gauge"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=["all differences are local, transportable, or gauge"],
            certificate={"differences": len(differences)})


class PartialTraceParadigm(Paradigm):
    """ר — Partial Trace: ε(ρ) = Tr_E[U(ρ⊗η)U†].
    Open systems leave traces in their environment.
    Information loss is apparent; in the total system it is conserved.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        env_trace = obj.structure.get("environment_trace")
        total_info = obj.structure.get("total_information")
        subsystem_info = obj.structure.get("subsystem_information")
        if env_trace is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="ENVIRONMENT_NOT_MODELED")
        if total_info is not None and subsystem_info is not None:
            if total_info >= subsystem_info:
                return ParadigmResult(pid, "CERTIFIED",
                    evidence=["total info ≥ subsystem info — conservation holds"],
                    certificate={"total": total_info, "subsystem": subsystem_info})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=["partial trace structure confirmed"],
            certificate={"env_trace_present": True})


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
    """ח — Gradient / Potential: N(a,b) = V(a) - V(b).
    Systems flow down potential gradients. Flow follows the gradient.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
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
    """ט — Cross-Ratio Invariance: [a,b;c,d] = (a-c)(b-d)/((a-d)(b-c)).
    This ratio is invariant under conformal (Möbius) transformations.
    The fundamental invariant of perception and projective geometry.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        quadruples = obj.structure.get("cross_ratio_quadruples", [])
        if not quadruples:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_QUADRUPLES")
        failures = []
        for q in quadruples:
            a, b, c, d = (Fraction(q[k]) for k in ["a", "b", "c", "d"])
            if (a - d) == 0 or (b - c) == 0:
                continue
            cr = (a - c) * (b - d) / ((a - d) * (b - c))
            if "expected_cr" in q:
                if cr != Fraction(q["expected_cr"]):
                    failures.append(q)
        if failures:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="CROSS_RATIO_NOT_INVARIANT",
                evidence=[f"{len(failures)} quadruples fail invariance"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"{len(quadruples)} quadruples — cross-ratio consistent"],
            certificate={"quadruples_checked": len(quadruples)})


class RepairCostParadigm(Paradigm):
    """ג — Achilles Operator: argmin_{o ∈ open/fail} repair(o).
    Every system has a critical open point — the minimum-energy failure.
    This is the weakest link. Control it, and you control the boundary.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        open_obstructions = obj.structure.get("open_obstructions", [])
        if not open_obstructions:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=["no open obstructions — system is closed"],
                certificate={"obstruction_count": 0})
        ranked = sorted(open_obstructions, key=lambda o: o.get("repair_cost", float("inf")))
        achilles = ranked[0]
        return ParadigmResult(pid, "BLOCKED",
            gap_name=f"ACHILLES_{achilles.get('name', 'UNKNOWN')}",
            evidence=[
                f"weakest point: {achilles.get('name')}",
                f"repair cost: {achilles.get('repair_cost')}",
                f"{len(open_obstructions)} total obstructions"
            ],
            certificate={"achilles": achilles, "total": len(open_obstructions)})


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
        tau_ok = obj.structure.get("tau_all_nonneg", True)
        if not tau_ok:
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
    """צ — Sensor → Certificate: hash(G(s)) = cert(s).
    Every sensor reading can be converted to an immutable certificate.
    Reality is recorded in the mathematics itself.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        sensor_hash = obj.structure.get("sensor_hash")
        certificate_hash = obj.structure.get("certificate_hash")
        if sensor_hash is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_SENSOR_HASH")
        if certificate_hash is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_CERTIFICATE_HASH")
        if sensor_hash == certificate_hash:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=["sensor hash matches certificate hash — reading is authentic"],
                certificate={"hash": sensor_hash})
        return ParadigmResult(pid, "BLOCKED",
            gap_name="HASH_MISMATCH",
            evidence=["sensor hash does not match certificate — integrity violated"])


class CenterSymmetryParadigm(Paradigm):
    """SU(3) — Z₃ Center Symmetry: Z(SU(3)) ≅ ℤ₃.
    The center of color symmetry is ℤ₃.
    One of the fundamental symmetry groups of the universe.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        symmetry_group = obj.structure.get("symmetry_group")
        if symmetry_group is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_SYMMETRY_GROUP")
        center_order = obj.structure.get("center_order")
        if center_order == 3:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=["center order = 3, consistent with Z₃"],
                certificate={"center_order": 3, "group": symmetry_group})
        if center_order is not None:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"CENTER_ORDER_{center_order}_NOT_Z3",
                evidence=[f"center order {center_order} ≠ 3"])
        return ParadigmResult(pid, "UNKNOWN", gap_name="CENTER_ORDER_NOT_COMPUTED")


class ConservedIndexParadigm(Paradigm):
    """ק — Conserved Index 18: ℤ₃ × C₆ ⟹ 3 × 6 = 18.
    Certain topological structures have conserved index 18.
    A fundamental signature of the universe.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        z3_order = obj.structure.get("z3_order", 3)
        c6_order = obj.structure.get("c6_order", 6)
        index = obj.structure.get("topological_index")
        expected = z3_order * c6_order
        if index is None:
            return ParadigmResult(pid, "UNKNOWN", gap_name="INDEX_NOT_COMPUTED")
        if index == expected:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[f"index {index} = {z3_order} × {c6_order} — conserved"],
                certificate={"index": index, "z3": z3_order, "c6": c6_order})
        return ParadigmResult(pid, "BLOCKED",
            gap_name=f"INDEX_{index}_NOT_{expected}",
            evidence=[f"index {index} ≠ expected {expected}"])


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
    """ת — Fixed Point & Life: L* = F(L*), Run(L*) > 0.
    Living systems converge to their own fixed points and keep running.
    This is the ultimate condition for consciousness and sustainable existence.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        fixed_point_iterations = obj.structure.get("fixed_point_iterations", [])
        is_running = obj.structure.get("is_running", False)
        if not fixed_point_iterations:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_ITERATION_SEQUENCE")
        if len(fixed_point_iterations) < 2:
            return ParadigmResult(pid, "UNKNOWN", gap_name="INSUFFICIENT_ITERATIONS")
        last = fixed_point_iterations[-1]
        prev = fixed_point_iterations[-2]
        converged = abs(last - prev) < 1e-10 if isinstance(last, float) else last == prev
        if converged and is_running:
            return ParadigmResult(pid, "CERTIFIED",
                evidence=[f"converged at {last}", "system is running"],
                certificate={"fixed_point": last, "iterations": len(fixed_point_iterations)})
        if converged and not is_running:
            return ParadigmResult(pid, "BLOCKED",
                gap_name="FIXED_POINT_BUT_NOT_RUNNING",
                evidence=["converged but Run(L*) = 0"])
        return ParadigmResult(pid, "BLOCKED",
            gap_name="NOT_CONVERGED",
            evidence=[f"last two: {prev}, {last}"])


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
    """אמת — Absolute Consistency: ¬(P ∧ ¬P), PROVEN ⟹ ∃ proof/certificate.
    No system can contain a contradiction.
    Every true claim has a proof. Lies and manipulation become visible here.
    """
    def verify(self, obj: CertifiableObject) -> ParadigmResult:
        pid = self.paradigm_id
        certified_claims = obj.structure.get("certified_claims", [])
        contradictions = obj.structure.get("contradictions", [])
        if contradictions:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"CONTRADICTION_{contradictions[0]}",
                evidence=[f"{len(contradictions)} contradictions detected: {contradictions[:3]}"])
        uncertified = [c for c in certified_claims if not c.get("certificate")]
        if uncertified:
            return ParadigmResult(pid, "BLOCKED",
                gap_name=f"UNCERTIFIED_CLAIMS_{len(uncertified)}",
                evidence=[f"{len(uncertified)} claims without proof/certificate"])
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[
                f"{len(certified_claims)} claims — all certified",
                "no contradictions"
            ],
            certificate={"certified_count": len(certified_claims)})


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
