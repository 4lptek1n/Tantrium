"""Yargı = üretimle aynı eksen — Sturm pivot pozitifliği + yapısal/χ fit mixin.

_judge_on_axis / _spectral_fit / _structural_kappa_distance / _sturm_path_pivot_min.
Sıralama ekseni (κ-fit + spektral W2 + χ-tiebreaker) ile transport pivot vekili burada.
"""
from __future__ import annotations

from ._types import _FREE_ENTROPY_WEIGHT, _SPECTRAL_FIT_WEIGHT


class _JudgeMixin:
    # ── Yargı = üretimle aynı eksen ────────────────────────────────────────

    def _judge_on_axis(self, smiles: str, mu_req: list[float]
                       ) -> tuple[bool, float, float, float]:
        """Pipeline aşaması: adayın TEK imzasından AK → Sturm pivot + yapısal fit + χ.

        Aday imzadan okunur (bir kez encode); κ/spektrum/χ imzada lazy+cache.
        YAPISAL FİT = κ₂₋₄ (düşük-derece şekil) + tam özdeğer W2 (yüksek-derece yapı).
        χ-uyumu (serbest entropi) AYRI döner → sıralamada TIEBREAKER (birincil κ/yapı
        sinyalini EZMEZ; yalnız κ+spektrum eşitken termodinamik yayılımı ayırır). Böylece
        defter ilkesi: gerçek ayrım korunur, χ küçük-molekül eşleştirmesiyle gerçek ilacı
        geçemez ama ölçü bilgisi skora girer.
        """
        import math
        sig = self._signature(smiles)
        if not sig.mu:
            return False, float("-inf"), float("inf"), float("inf")
        ok, pmin = self._sturm_path_pivot_min(sig.mu, mu_req)
        kfit = self._structural_kappa_distance(sig.mu, mu_req)
        # Spektral W2: adayın CACHE'li spektrumu vs hedef spektrumu (bir kez hesaplanır).
        sfit = 0.0
        try:
            from tantrium.domains.spectral import spectral_distance, moments_to_spectral
            if getattr(self, "_target_spec_mu", None) != mu_req:
                self._target_spec = moments_to_spectral(list(mu_req))
                self._target_spec_mu = list(mu_req)
            sfit = float(spectral_distance(sig.spectral, self._target_spec))
        except Exception:
            pass
        # Serbest entropi uyumu: adayın χ'si hedefin χ'sine ne kadar yakın (lazy, cache).
        efit = 0.0
        try:
            from tantrium.core.quantum_moments import free_entropy
            if getattr(self, "_target_chi_mu", None) != mu_req:
                self._target_chi = float(free_entropy(list(mu_req)))
                self._target_chi_mu = list(mu_req)
            cand_chi = sig.free_entropy
            if math.isfinite(cand_chi) and math.isfinite(self._target_chi):
                efit = _FREE_ENTROPY_WEIGHT * abs(cand_chi - self._target_chi)
        except Exception:
            pass
        fit = kfit + _SPECTRAL_FIT_WEIGHT * sfit
        return ok, pmin, fit, efit

    @staticmethod
    def _spectral_fit(mu_a: list[float], mu_b: list[float]) -> float:
        """Tam özdeğer-dağılımı W2 mesafesi — `domains/spectral` (TEK spektral motor).

        moment→özdeğer (Gauss kuadratür/Golub-Welsch) → sıralı-özdeğer W2. κ₂₋₄'ün
        kaçırdığı yüksek-derece yapıyı yakalar (yapıcı Hamburger'in mesafe yüzü).
        """
        try:
            from tantrium.domains.spectral import moments_to_spectral, spectral_distance
            sa = moments_to_spectral(list(mu_a))
            sb = moments_to_spectral(list(mu_b))
            return float(spectral_distance(sa, sb))
        except Exception:
            return 0.0

    @staticmethod
    def _structural_kappa_distance(mu_a: list[float], mu_b: list[float]) -> float:
        """Yapısal κ₂,κ₃,κ₄ mesafesi — kanonik bounded_kappa_distance'a delege.

        Merkez κ₁ hariç (include_mean=False): yol-fit ekseni. Tek imza L0'da.
        """
        from tantrium.core.quantum_moments import bounded_kappa_distance
        return bounded_kappa_distance(mu_a, mu_b, include_mean=False)

    def _sturm_path_pivot_min(self, src: list[float], tgt: list[float],
                              steps: int = 8) -> tuple[bool, float]:
        """Konveks yol boyunca en küçük Hankel özdeğeri (Sturm pivot vekili)."""
        import numpy as np
        n = min(len(src), len(tgt), 8)
        if n < 2:
            return False, float("-inf")
        a = [float(src[i]) for i in range(n)]
        b = [float(tgt[i]) for i in range(n)]
        size = max(n // 2, 2)
        worst = float("inf")
        for step in range(steps + 1):
            t = step / steps
            interp = [(1 - t) * a[i] + t * b[i] for i in range(n)]
            H = np.array([[interp[i + j] if i + j < n else 0.0
                           for j in range(size)] for i in range(size)])
            lo = float(np.linalg.eigvalsh(H).min())
            worst = min(worst, lo)
        return worst >= self._transport_epsilon, worst
