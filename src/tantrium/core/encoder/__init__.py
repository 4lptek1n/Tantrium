"""Universal encoder: any input → CodexObject via spectral moments.

The encoder is domain-blind. It does not know if the input is a sentence,
a number sequence, a graph, or a physical measurement. It only does this:

    input → non-negative matrix representation A
           → spectral moments μ_k = Tr(A^k) / n
           → CodexObject with those moments

This works because:
1. Every compact-support non-negative measure is uniquely determined by its moments
   (Hamburger/Hausdorff moment problem)
2. Physical reality is bounded (finite energy = compact support)
3. Therefore every physical thing IS its moment sequence — not approximately, exactly
4. Tr(A^k)/n are the moments of the empirical spectral distribution of A
5. The empirical spectral distribution converges to the real distribution as n grows

This is the same mathematics as the RH proof (Xi function moments).
The encoder does not introduce a new mathematical layer — it IS the existing layer,
applied universally.

This package splits the original ``encoder.py`` module into logical parts while
preserving the exact public + internally-imported surface. Everything that was
importable from ``tantrium.core.encoder`` before still is.
"""
from __future__ import annotations

from ._linalg import (
    _gram,
    _mat_mul,
    _mat_pow,
    _sequence_to_hankel_matrix,
    _spectral_moments,
    _trace,
)
from ._text import (
    _AA_ALPHA,
    _CODE_MARKERS,
    _DNA_ALPHA,
    _MAX_HANKEL_DIM,
    _POWER_MOMENT_THRESHOLD,
    _RNA_ALPHA,
    _char_signature,
    _dict_to_adjacency_matrix,
    _downsample,
    _is_valid_smiles,
    _numbers_to_matrix,
    _smiles_full_eigenvalues,
    _smiles_molecular_moments,
    _smiles_to_descriptor_matrix,
    _smiles_to_graph_moments,
    _smiles_to_morgan_matrix,
    _text_extra_dims,
    _text_to_bigram_matrix,
    _text_to_signature_moments,
    _tokens_to_cooccurrence_matrix,
    _try_power_moments,
)
from ._encoder import (
    _DEFAULT_ENCODER,
    UniversalEncoder,
    _infer_name,
    encode,
    encode_smiles,
)

__all__ = [
    # public
    "UniversalEncoder",
    "encode",
    "encode_smiles",
    # linalg
    "_mat_mul",
    "_mat_pow",
    "_trace",
    "_gram",
    "_spectral_moments",
    "_sequence_to_hankel_matrix",
    # text / smiles / structured
    "_text_to_bigram_matrix",
    "_text_to_signature_moments",
    "_is_valid_smiles",
    "_char_signature",
    "_text_extra_dims",
    "_tokens_to_cooccurrence_matrix",
    "_dict_to_adjacency_matrix",
    "_downsample",
    "_numbers_to_matrix",
    "_try_power_moments",
    "_smiles_to_graph_moments",
    "_smiles_molecular_moments",
    "_smiles_full_eigenvalues",
    "_smiles_to_descriptor_matrix",
    "_smiles_to_morgan_matrix",
    "_DNA_ALPHA",
    "_RNA_ALPHA",
    "_AA_ALPHA",
    "_CODE_MARKERS",
    "_MAX_HANKEL_DIM",
    "_POWER_MOMENT_THRESHOLD",
    # encoder module
    "_infer_name",
    "_DEFAULT_ENCODER",
]
