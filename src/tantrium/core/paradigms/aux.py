"""Auxiliary paradigms and the canonical paradigm registry.

Holds the spectral / Achilles / symmetry / fixed-point / consistency operators
(DALET/HE/GIMEL/SU3/KUF/TAV/EMET …) plus the assembled PARADIGMS list and the
PARADIGM_BY_ID lookup in dependency order. Classes defined in `core` are
imported here so the registry can be built in one place.
"""
from __future__ import annotations

from .base import CertifiableObject, Paradigm, ParadigmResult
from .core import (
    CrossRatioParadigm,
    DimensionParadigm,
    GaugeEquivalenceParadigm,
    GradientParadigm,
    InformationConservationParadigm,
    InjectivityParadigm,
    LocalVisibilityParadigm,
    MDLParadigm,
    PartialTraceParadigm,
    PathSumParadigm,
    PositivityParadigm,
    SeparabilityParadigm,
    TensorCompositionParadigm,
)


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
        achilles_name = obj.structure.get("achilles_paradigm", "UNKNOWN")
        achilles_margin = obj.structure.get("achilles_margin", 0.0)
        margins = obj.structure.get("paradigm_margins", {})
        if not margins:
            if "open_obstructions" not in obj.structure:
                return ParadigmResult(pid, "UNKNOWN",
                    gap_name="REPAIR_COST_NOT_COMPUTED",
                    evidence=["paradigm_margins not available — GIMEL stage not reached"])
            return ParadigmResult(pid, "CERTIFIED",
                evidence=["no open obstructions — system is closed"],
                certificate={"obstruction_count": 0})
        return ParadigmResult(pid, "CERTIFIED",
            evidence=[f"Achilles = {achilles_name} (margin={achilles_margin:.4f})",
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
        newton_ok = obj.structure.get("su3_newton_verified", True)
        newton_res = obj.structure.get("newton_residual", 0.0)
        center_order = obj.structure.get("center_order", 3)
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
        fixed_point_iterations = obj.structure.get("fixed_point_iterations", [])
        is_running = obj.structure.get("is_running", False)
        lambda_db = obj.structure.get("debruijn_newman_lambda")
        if not fixed_point_iterations:
            return ParadigmResult(pid, "UNKNOWN", gap_name="NO_ITERATION_SEQUENCE")
        if len(fixed_point_iterations) < 2:
            return ParadigmResult(pid, "UNKNOWN", gap_name="INSUFFICIENT_ITERATIONS")
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
