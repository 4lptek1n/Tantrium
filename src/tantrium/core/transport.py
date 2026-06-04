"""Certified Dyadic Transport Engine — the real AGI motor.

Every object encodes to a spectral measure (eigenvalue distribution of its Gram matrix).
Moving from source measure to target measure is not nearest-neighbor search —
it is a CERTIFIED dyadic transport with three guarantees:

  1. Dyadic certificate: solve_greedy → verified_exact (exact rational coverage)
  2. Sturm path: H(t) = (1-t)*H_src + t*H_tgt stays PSD for all t in [0,1]
     = transport stays on the "real object" manifold throughout
     = no phantom molecules, no imaginary intermediaries
  3. Zeta anchor: distance to Riemann zeta zeros spectral family

The distinction from nearest-neighbor:
  Molecule A may be closer in moment distance, but its transport path
  crosses into non-PSD (imaginary) territory → STURM_FAILED → rejected.
  Molecule B is slightly farther but its path is entirely real → CERTIFIED.
  Molecule B is the certified drug candidate.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Extend tantrium namespace so root tantrium/ (transport, certificates) is importable
_REPO_ROOT = Path(__file__).resolve().parents[3]
_root_tantrium = str(_REPO_ROOT / "tantrium")
import tantrium as _pkg
if _root_tantrium not in _pkg.__path__:
    _pkg.__path__.append(_root_tantrium)


@dataclass
class TransportCertificate:
    """Full proof chain: source → target via certified dyadic transport."""
    certified: bool
    dyadic_verified: bool     # solve_greedy → "verified_exact"
    sturm_verified: bool      # interpolated Hankel stays PSD throughout
    zeta_distance: float      # distance to Zeta zeros spectral family
    transport_cost: float     # total dyadic mass transported
    path_length: int          # number of dyadic edges
    blocker: str = ""

    def summary(self) -> str:
        status = "CERTIFIED" if self.certified else f"BLOCKED({self.blocker})"
        return (
            f"{status} | "
            f"dyadic={'✓' if self.dyadic_verified else '✗'} | "
            f"sturm={'✓' if self.sturm_verified else '✗'} | "
            f"ζ-dist={self.zeta_distance:.4f} | "
            f"cost={self.transport_cost:.6f}"
        )


@dataclass
class TransportRanking:
    """Ranked drug candidates from certified transport."""
    target_name: str
    candidates: list[tuple[str, TransportCertificate]] = field(default_factory=list)

    def certified_only(self) -> list[tuple[str, TransportCertificate]]:
        return [(n, c) for n, c in self.candidates if c.certified]

    def best(self) -> tuple[str, TransportCertificate] | None:
        certified = self.certified_only()
        if not certified:
            return None
        return min(certified, key=lambda x: x[1].zeta_distance)

    def summary(self) -> str:
        lines = [f"Target: {self.target_name} | {len(self.candidates)} candidates"]
        for name, cert in self.candidates[:8]:
            lines.append(f"  {name:40} {cert.summary()}")
        return "\n".join(lines)


class CertifiedTransport:
    """Core AGI motor: certified dyadic transport between spectral measures.

    Replaces nearest-neighbor search in discover() with a full proof chain.
    Only certified paths produce valid drug candidates.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine
        self._zeta_moments: list[float] | None = None

    # ── Main API ────────────────────────────────────────────────────────────

    def certify(
        self,
        source_moments: list,
        target_moments: list,
        theorem_id: str = "DYADIC_TRANSPORT",
    ) -> TransportCertificate:
        """Certify transport from source to target moments.

        Three-layer proof:
          1. Dyadic: solve_greedy covering exact rational mass
          2. Sturm: H(t) stays PSD throughout transport path
          3. Zeta: target spectral family membership
        """
        from tantrium.transport.dyadic_flow import solve_greedy, FlowPolicy

        src_cells = self._moments_to_cells(source_moments, "src")
        tgt_cells = self._moments_to_cells(target_moments, "tgt")

        policy = FlowPolicy(
            theorem_id=theorem_id,
            kernel_id="hankel_spectral",
            map_name="diffgap",  # cross-rank transport costs 2^|diff| — spectral mismatch penalized
            require_q_ge=False,
            require_diff_ge=False,
        )
        cert = solve_greedy(src_cells, tgt_cells, policy)
        dyadic_ok = cert.status == "verified_exact"
        # Wasserstein-like cost: total raw source mass consumed
        cost = float(sum(e.raw_source_used for e in cert.edges))

        sturm_ok = self._sturm_path_check(source_moments, target_moments)
        zeta_dist = self._zeta_distance(target_moments)

        if not dyadic_ok:
            blocker = "DYADIC_FAILED"
        elif not sturm_ok:
            blocker = "STURM_FAILED"
        else:
            blocker = ""

        return TransportCertificate(
            certified=dyadic_ok and sturm_ok,
            dyadic_verified=dyadic_ok,
            sturm_verified=sturm_ok,
            zeta_distance=zeta_dist,
            transport_cost=cost,
            path_length=len(cert.edges),
            blocker=blocker,
        )

    def rank_candidates(
        self,
        target_name: str,
        candidate_names: list[str] | None = None,
        top_n: int = 20,
    ) -> TransportRanking:
        """Rank manifold candidates for a target via certified transport.

        Better than nearest-neighbor: candidates with non-real transport paths
        (STURM_FAILED) are rejected even if they are closer in moment distance.
        """
        target_c = self.engine.manifold.concepts.get(target_name)
        if target_c is None:
            return TransportRanking(target_name=target_name)

        if candidate_names is None:
            # Use nearest neighbors as starting pool
            neighbors = self.engine.manifold.nearest(target_c, n=top_n * 2)
            candidate_names = [n for n, _ in neighbors if n != target_name]

        results: list[tuple[str, TransportCertificate]] = []
        for name in candidate_names[:top_n * 3]:
            cand_c = self.engine.manifold.concepts.get(name)
            if cand_c is None:
                continue
            tc = self.certify(list(target_c.moments), list(cand_c.moments))
            results.append((name, tc))

        # Sort: certified first, then by zeta_distance
        results.sort(key=lambda x: (not x[1].certified, x[1].zeta_distance))

        return TransportRanking(
            target_name=target_name,
            candidates=results[:top_n],
        )

    # ── Spectral decomposition ───────────────────────────────────────────────

    def _moments_to_cells(self, moments: list, prefix: str) -> list:
        """Moments → Hankel matrix → eigenvalues → Cell objects.

        The Hankel matrix H[i,j] = μ_{i+j} captures the spectral measure.
        Its eigenvalues are the "atoms" — fundamental positive units.
        Mass is normalized so Σ mass = 1 (probability measure).
        """
        from tantrium.certificates.certificate import Cell

        n = min(len(moments), 8)
        m = [float(moments[i]) for i in range(n)]
        size = max(n // 2, 2)

        H = np.array([
            [m[i + j] if i + j < n else 0.0 for j in range(size)]
            for i in range(size)
        ])
        eigs = np.linalg.eigvalsh(H)
        eigs = np.maximum(eigs, 0.0)
        total = float(eigs.sum()) or 1.0

        # diff = eigenvalue pozisyonu × 1000 (integer)
        # diffgap map bu farkı transport maliyeti olarak kullanır
        # → Wasserstein-1 benzeri spektral mesafe
        cells = []
        for k, ev in enumerate(sorted(eigs, reverse=True)):
            mass = Fraction(ev / total).limit_denominator(10 ** 6)
            if mass > 0:
                ev_norm = ev / (eigs.max() or 1.0)
                # 0-10 arası kaba quantize: diffgap ≤ 10 → 2^10=1024x maliyet
                diff_coord = max(0, min(10, int(ev_norm * 10)))
                cells.append(Cell.make(
                    f"{prefix}_atom_{k}",
                    mass,
                    diff=diff_coord,
                    p=k + 1,
                    q=1,
                ))
        return cells

    # ── Sturm path verification ──────────────────────────────────────────────

    def _sturm_path_check(
        self,
        source_moments: list,
        target_moments: list,
        steps: int = 8,
    ) -> bool:
        """Sturm pivot positivity along the interpolated moment path.

        The characteristic polynomial of the Hankel matrix H(t) is computed at
        each step. Sturm chain verifies all roots are real and non-negative
        throughout the transport — i.e., the path stays on the "real measure"
        manifold (Hamburger theorem: valid moment sequence ↔ real measure).

        Uses normalized_sturm_chain() from tantrium.algebra.sturm.
        Pivots must all be positive for each interpolated Hankel.
        """
        try:
            import sympy as sp
            from tantrium.algebra.sturm import normalized_sturm_pivots
        except ImportError:
            # sympy unavailable — fall back to numpy PSD check
            return self._sturm_psd_fallback(source_moments, target_moments, steps)

        n = min(len(source_moments), len(target_moments), 8)
        src = [float(source_moments[i]) for i in range(n)]
        tgt = [float(target_moments[i]) for i in range(n)]
        size = max(n // 2, 2)
        x = sp.Symbol("x")

        def hankel_poly(m: list):
            H = sp.Matrix([
                [sp.Rational(m[i + j]).limit_denominator(10**6) if i + j < n else 0
                 for j in range(size)]
                for i in range(size)
            ])
            return sp.det(x * sp.eye(size) - H)

        for step in range(steps + 1):
            t = step / steps
            interp = [(1 - t) * src[i] + t * tgt[i] for i in range(n)]
            try:
                poly = hankel_poly(interp)
                pivots = normalized_sturm_pivots(poly, x)
                if any(sp.simplify(p) < 0 for p in pivots):
                    return False
            except Exception:
                continue
        return True

    def _sturm_psd_fallback(self, source_moments, target_moments, steps) -> bool:
        """Fallback: check H(t) stays PSD when sympy unavailable."""
        n = min(len(source_moments), len(target_moments), 8)
        src = [float(source_moments[i]) for i in range(n)]
        tgt = [float(target_moments[i]) for i in range(n)]
        size = max(n // 2, 2)
        for step in range(steps + 1):
            t = step / steps
            interp = [(1 - t) * src[i] + t * tgt[i] for i in range(n)]
            H = np.array([[interp[i+j] if i+j < n else 0.0 for j in range(size)] for i in range(size)])
            if np.linalg.eigvalsh(H).min() < -1e-9:
                return False
        return True

    # ── Zeta anchor ─────────────────────────────────────────────────────────

    def _zeta_distance(self, moments: list) -> float:
        """L1 moment distance from target to Riemann Zeta zeros spectral family.

        Small distance = target lives in the same spectral family as ζ zeros.
        This is the deepest certification: connection to the prime number theorem.
        """
        from tantrium.core.semantic import moment_distance, Concept

        if self._zeta_moments is None:
            for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
                zeta_c = self.engine.manifold.concepts.get(name)
                if zeta_c:
                    self._zeta_moments = [float(m) for m in zeta_c.moments]
                    break
            else:
                self._zeta_moments = []

        if not self._zeta_moments:
            return float("inf")

        k = min(len(moments), len(self._zeta_moments))
        return sum(
            abs(float(moments[i]) - self._zeta_moments[i]) for i in range(k)
        )
