"""SemanticBridge: theorem graph ↔ paradigm mapping.

The 22+1 Aleph-Tekin paradigms are not abstract — each one corresponds to
a specific theorem in the Tantrium proof graph. This package is the dictionary
that connects them.

When the engine certifies ZAYIN, it is certifying the LGV lemma.
When it certifies DALET, it is certifying Jensen hyperbolicity.
When it certifies TAV, it is certifying RH_CLOSURE — the proof is complete.

This bridge makes that connection explicit. It is the semantic layer
between the universal certification machinery and the specific mathematics
of the Riemann Hypothesis proof.

Without this bridge, the two worlds (universal encoder / RH proof graph) are
mechanically connected but semantically blind. With it, every certification
in the certification network is simultaneously a step in the RH proof chain.

Layout:
  _data.py    — paradigm↔theorem tables + theorem→CertifiableObject conversion
  _bridge.py  — the SemanticBridge class
"""
from __future__ import annotations

from ._bridge import SemanticBridge
from ._data import (
    PARADIGM_TO_THEOREMS,
    THEOREM_TO_PARADIGMS,
    is_proven,
    theorem_to_codex_object,
)

__all__ = [
    "SemanticBridge",
    "PARADIGM_TO_THEOREMS",
    "THEOREM_TO_PARADIGMS",
    "is_proven",
    "theorem_to_codex_object",
]
