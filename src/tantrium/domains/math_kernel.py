"""Math Kernel → manifold köprüsü (DURUMSUZ makinede NO-OP).

Tarihsel: RH kanıt sistemindeki (theorem_graph.yaml) certified teoremleri öğrenilen
bir manifolda Concept + TAU kenarı olarak enjekte ederdi. Bu makine durumsuz olduğundan
(manifold/graf YOK) `inject_math_kernel` artık güvenli no-op döndürür; modül,
`InjectionResult` tipi ve `inject_computational_math_objects` (saf Concept üretimi) için korunur.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Teorem grafiği yolu
_GRAPH_PATH = pathlib.Path(__file__).parents[5] / "Tantrium" / "tantrium" / "theorem_graph" / "theorem_graph.yaml"
# Alternatif: working directory'den relative
_GRAPH_PATH_ALT = pathlib.Path("tantrium/theorem_graph/theorem_graph.yaml")

# Hangi status'lar certified sayılır
_CERTIFIED_STATUSES = {
    "PROVEN_BY_CERTIFICATE",
    "VERIFIED_FINITE",
    "verified_finite",
    "CERTIFIED_SCHEMA",
    "certified_local",
    "NO_STRUCTURAL_GAP",
    "proven",
    "RECURRENCE_VERIFIED_FINITE",
}

# Teorem → hangi anchor'larla köprü kurulsun
_THEOREM_ANCHORS: dict[str, list[str]] = {
    "RH_SYMBOLIC_CLOSURE":       ["ZETA_ZEROS"],
    "DYADIC_TRANSPORT":          ["ZETA_ZEROS", "PRIME_GAPS"],
    "D_POSITIVITY":              ["PRIME_GAPS", "GUE_RANDOM_MATRIX"],
    "CELL_SUPPORT_POSITIVITY":   ["PRIME_GAPS"],
    "AG_LGV_TRANSFER":           ["GUE_RANDOM_MATRIX"],
    "TAU_SUBDISCRIMINANT":       ["ZETA_ZEROS"],
    "STURM_PIVOT_POSITIVITY":    ["ZETA_ZEROS"],
    "JENSEN_HYPERBOLICITY":      ["ZETA_ZEROS", "GAUSSIAN_BELL"],
    "XI_REAL_FORM":              ["ZETA_ZEROS"],
    "GATE_A_CROSS_RATIO":        ["PERIODIC_LATTICE"],
    "GATE_B_STAIRCASE":          ["LINEAR_RAMP"],
    "RH_CLOSURE":                ["ZETA_ZEROS", "PRIME_GAPS"],
    "dyadic_transport_theorem":  ["ZETA_ZEROS"],
    "uniform_lift_lemma":        ["GUE_RANDOM_MATRIX"],
}


@dataclass
class InjectionResult:
    """Math kernel enjeksiyonunun özeti."""
    concepts_added: int
    edges_added: int
    bridges_added: int
    skipped: int

    def summary(self) -> str:
        return (
            f"Math kernel: "
            f"{self.concepts_added} kavram, "
            f"{self.edges_added} kenar, "
            f"{self.bridges_added} spektral köprü "
            f"({self.skipped} atlandı)"
        )


def inject_math_kernel(engine: "CertificationEngine") -> InjectionResult:
    """Teorem→manifold injection devre dışı (graph.* + theorem_graph silindi).

    Durumsuz saf-matematik makinesinde kalıcı manifold/TAU yok → bu köprünün
    iliştireceği hedef yok. Güvenli no-op: çağrılırsa boş sonuç döner, patlamaz.
    """
    return InjectionResult(0, 0, 0, 0)


# ── Matematiksel nesnelerin sayısal encode edilmesi ──────────────────────────

import math as _math

_RIEMANN_ZEROS_12 = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178,
    40.918720, 43.327073, 48.005151, 49.773832, 52.970321, 56.446248,
]


def _li_coefficient(n: int) -> float:
    """Li kriteri koeffisyeni λ_n = Σ_ρ [1 - (1 - 1/ρ)^n]."""
    total = 0.0
    for g in _RIEMANN_ZEROS_12:
        re, im = 0.5, g
        m2 = re**2 + im**2
        omr = 1.0 - re / m2
        omi = im / m2
        r = (omr**2 + omi**2) ** 0.5
        theta = _math.atan2(omi, omr)
        total += 1.0 - (r**n) * _math.cos(n * theta)
    return total


# Manifolddaki boş/sahte encode edilmiş matematiksel kavramlar
# → gerçek sayısal dizilerinden yeniden encode et
_MATH_OBJECT_SEQUENCES: dict[str, list[float]] = {
    # LGV transfer matrix path count = Catalan C_k
    "AG_LGV_TRANSFER": [
        _math.comb(2 * k, k) // (k + 1) if k > 0 else 1 for k in range(12)
    ],
    # Möbius cross-ratio (0,k,k+1,k+2) = 2(k+1)/(k+2) for k=0..11
    "GATE_A_CROSS_RATIO": [2 * (k + 1) / (k + 2) for k in range(12)],
    # Cross-ratio'nun ardışık farkı d_k = 2/((k+2)(k+3)) — pertürbasyon türevi
    "GATE_A_PERTURBATION": [2.0 / ((k + 2) * (k + 3)) for k in range(12)],
    # Dyadic cumulative distribution: 1 - 1/2^k
    "DYADIC_TRANSPORT": [1.0 - 1.0 / 2**k for k in range(1, 13)],
    # Triangular numbers T_j = j(j+1)/2
    "GATE_B_STAIRCASE_RAMP": [k * (k + 1) // 2 for k in range(12)],
    # Li koeffisyenleri λ_1..λ_12
    "JENSEN_HYPERBOLICITY": [_li_coefficient(n) for n in range(1, 13)],
}


def inject_computational_math_objects(engine: "CertificationEngine") -> int:
    """Boş/uniform encode edilmiş matematiksel kavramları gerçek dizilerden güncelle.

    Bu kavramlar başlangıçta uniform metin olarak encode edildi.
    Şimdi matematiksel yapılarını yansıtan sayısal dizilerden encode ediyoruz.

    Döner: güncellenen kavram sayısı.
    """
    from tantrium.core.concept import Concept

    updated = 0
    _UNIFORM_M3 = 0.125  # eski uniform encoding'in 3. momenti (1/8)
    _UNIFORM_THRESHOLD = 1e-4  # bu değerden küçük fark → uniform say

    for name, seq in _MATH_OBJECT_SEQUENCES.items():
        raw = engine.encoder.encode(seq, name=name)
        new_moments = list(raw.moments)

        existing = engine.manifold.concepts.get(name)
        if existing is not None:
            # Sadece manifold.json'dan gelen (source="saved") ya da
            # uniform encode'lu kavramları güncelle — computational olanı atla
            if existing.source == "computational":
                old_m3 = float(existing.moments[3]) if len(existing.moments) > 3 else 0.0
                new_m3 = float(new_moments[3]) if len(new_moments) > 3 else 0.0
                if abs(old_m3 - new_m3) < 1e-10:
                    continue  # Zaten doğru — atla

        concept = Concept(
            name=name,
            moments=new_moments,
            domain="math_kernel",
            source="computational",
        )
        if not concept.is_real():
            continue

        engine.manifold.concepts[name] = concept
        updated += 1

    return updated
