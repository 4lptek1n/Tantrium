"""Aleph-Tekin Codex: 22+1 paradigms as formal operators.

Each paradigm is a real mathematical operator with a verify() method.
The operators form a DAG — each builds on the ones below it.
No LLM. No statistics. Only structure.

The paradigms are not metaphors. They are filters.
A thing either passes or it does not. If it passes, a certificate is issued.
If it does not, a named gap is recorded — the system knows *what* it does not know.

This package was split from a single module; the public import surface is
preserved bit-for-bit:  `from tantrium.core.paradigms import X` continues to
resolve every previously public symbol (base types, all paradigm classes,
PARADIGMS and PARADIGM_BY_ID).
"""
from __future__ import annotations

from .base import (
    CertifiableObject,
    Paradigm,
    ParadigmResult,
    _det,
)
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
from .aux import (
    PARADIGM_BY_ID,
    PARADIGMS,
    CenterSymmetryParadigm,
    ConservedIndexParadigm,
    ConsistencyParadigm,
    FixedPointParadigm,
    LyapunovParadigm,
    OptimalActionParadigm,
    RepairCostParadigm,
    SemanticMappingParadigm,
    SensorCertParadigm,
    SpectralParadigm,
)

__all__ = [
    # base types
    "CertifiableObject",
    "Paradigm",
    "ParadigmResult",
    "_det",
    # core paradigms
    "CrossRatioParadigm",
    "DimensionParadigm",
    "GaugeEquivalenceParadigm",
    "GradientParadigm",
    "InformationConservationParadigm",
    "InjectivityParadigm",
    "LocalVisibilityParadigm",
    "MDLParadigm",
    "PartialTraceParadigm",
    "PathSumParadigm",
    "PositivityParadigm",
    "SeparabilityParadigm",
    "TensorCompositionParadigm",
    # aux paradigms
    "CenterSymmetryParadigm",
    "ConservedIndexParadigm",
    "ConsistencyParadigm",
    "FixedPointParadigm",
    "LyapunovParadigm",
    "OptimalActionParadigm",
    "RepairCostParadigm",
    "SemanticMappingParadigm",
    "SensorCertParadigm",
    "SpectralParadigm",
    # registries
    "PARADIGMS",
    "PARADIGM_BY_ID",
]
