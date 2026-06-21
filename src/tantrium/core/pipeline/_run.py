"""run_pipeline orkestratörü — L0–L7 sıralı hesap.

Aşamaları doğru bağımlılık sırasında çağırır. Stage fonksiyonları
`_stages_low` (L0.5–L3) ve `_stages_high` (L4–L6) modüllerindedir.
"""
from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any

from ._stages_low import (
    _update_bet_entropy,
    stage_l05_bet_infocon,
    stage_l15_he_lyapunov,
    stage_l2_zayin_hankel,
    stage_l25_dalet_spectrum,
    stage_l3_het_li,
)
from ._stages_high import (
    stage_ancillary,
    stage_l4_tav_heatflow,
    stage_l5_gimel_admission,
    stage_l6_emet_certificate,
)


# ─── Ana pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    raw_input: Any,
    A: list[list[Fraction]],
    G: list[list[Fraction]],
    moments: list[Fraction],
) -> dict:
    """L0–L7 pipeline'ını çalıştır ve tüm state'i döndür.

    Aşama sırası (bağımlılıklar korunur):
      1. DALET (L2.5) — eigenvalues: diğer tüm aşamalar buna bağlı
      2. BET   (L0.5) — Frobenius + von Neumann (eigenvalues güncellemesiyle)
      3. HE    (L1.5) — Lyapunov (eigenvalues gerekli)
      4. ZAYIN (L2)   — τ-det + Schur
      5. HET   (L3)   — Li kriteri (eigenvalues gerekli, input-specific!)
      6. TAV   (L4)   — Heat-flow (eigenvalues gerekli)
      7. ANCK         — Yardımcı paradigmalar
      8. GIMEL (L5)   — Achilles (tüm marjinler gerekli)
      9. EMET  (L6)   — Cross-check
    """
    state: dict = {}
    n = len(A)
    sig = hashlib.sha256(
        "|".join(str(m) for m in moments).encode()
    ).hexdigest()[:16]

    # 1. Eigenvalues önce gelir — diğer aşamalar buna bağlı
    stage_l25_dalet_spectrum(G, state)

    # 2. BET: Frobenius kimliği (eigenvalues artık mevcut → entropy doğru)
    stage_l05_bet_infocon(A, G, state)
    _update_bet_entropy(state)

    # 3. HE: Lyapunov (dominant eigenvalue kullanır)
    stage_l15_he_lyapunov(moments, state)

    # 4. ZAYIN: τ-determinantlar + Schur
    stage_l2_zayin_hankel(moments, G, state)

    # 5. HET: Li kriteri — bu objenin eigenvalue'ları, global Riemann sıfırları DEĞİL
    stage_l3_het_li(state)

    # 6. TAV: de Bruijn-Newman heat-flow
    stage_l4_tav_heatflow(state)

    # 7. Yardımcı paradigmalar
    stage_ancillary(raw_input, A, G, moments, n, state)

    # 8. GIMEL: Achilles (tüm marjinler hazır)
    stage_l5_gimel_admission(moments, state)

    # 9. EMET: Cross-check
    stage_l6_emet_certificate(A, G, moments, state, sig)

    return state
