"""CoreMachine — TEK ÇEKİRDEK MAKİNE.

Bir girdi, bir encode, bir process, 4 eksen — hepsi ortak durumdan.
Önceden 3 encode + 2 process yapılıyordu; şimdi ONE PASS.

  CoreMachine.certify(input)
    → ONE encode (adaptive derinlik)
    → ONE process (tüm 23 paradigma)
    → Axis 1: Yapısal (paradigma coverage)
    → Axis 2: Topraklama (TAU kökü)
    → Axis 3: Gerçek (komşu tutarlılık)
    → Axis 4: Güven (kalibre skor)
    → UnifiedCertificate (tüm eksenler tutarlı boolean)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class UnifiedCertificate:
    """Tek geçişten gelen 4-eksenli sertifika."""
    name: str
    moments: list[float]

    # Eksen 1: Yapısal
    paradigms_passed: int
    paradigms_total: int
    gaps: list[str]
    structural_score: float

    # Eksen 2: Topraklama
    grounding: str            # GROUNDED | WEAKLY_GROUNDED | UNGROUNDED
    grounding_score: float

    # Eksen 3: Gerçek
    truth: str                # CONSISTENT | CONTESTED | CONTRADICTORY
    truth_score: float

    # Eksen 4: Güven
    confidence: float         # 0→1
    confidence_level: str     # CERTAIN | STRONG | MODERATE | WEAK | UNCERTAIN

    # Rekonstrüksiyon kalitesi
    reconstruction_fidelity: float  # 0→1

    # Tutarlı boolean: tüm eksenler anlaşıyor mu?
    coherent: bool

    # Zengin evidence (isteğe bağlı)
    evidence: dict = field(default_factory=dict)

    def __str__(self) -> str:
        cert = "✓" if self.coherent else "✗"
        g = {"GROUNDED": "⏚", "WEAKLY_GROUNDED": "≈", "UNGROUNDED": "∅"}.get(
            self.grounding, "?")
        return (
            f"{cert} {self.name} [{self.paradigms_passed}/{self.paradigms_total}] "
            f"{g} {self.truth} conf={self.confidence:.2f} [{self.confidence_level}]"
        )


class CoreMachine:
    """Tek geçişte tüm sertifikasyon eksenlerini hesaplar."""

    def __init__(self, engine: object) -> None:
        self._engine = engine

    def certify(self, input_data: object, name: str | None = None,
                adaptive: bool = True, with_truth: bool = True) -> UnifiedCertificate:
        """Tek geçiş: encode → process → 4 eksen → UnifiedCertificate."""
        nm = name or (str(input_data)[:64] if isinstance(input_data, str) else "input")

        # ─── ONE ENCODE ───────────────────────────────────────────────────────
        if adaptive:
            obj = self._encode_adaptive(input_data, nm)
        else:
            obj = self._engine.encoder.encode(input_data, name=nm)
        moments = list(obj.moments)

        # ─── ONE PROCESS ──────────────────────────────────────────────────────
        run = self._engine.network.run(obj)

        # ─── AXIS 1: STRUCTURAL ───────────────────────────────────────────────
        paradigms_passed = run.certified_count
        paradigms_total = run.total
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]
        structural_score = paradigms_passed / max(paradigms_total, 1)

        # ─── AXIS 2: GROUNDING ────────────────────────────────────────────────
        gcert = self._engine.grounder.certify(nm, moments=moments)
        grounding = gcert.verdict
        grounding_score = gcert.score

        # ─── AXIS 3: TRUTH ────────────────────────────────────────────────────
        if with_truth:
            from tantrium.core.truth import TruthCertifier
            tcert = TruthCertifier(self._engine).certify(nm, moments=moments)
            truth = tcert.verdict
            truth_score = tcert.consistency_score
        else:
            truth, truth_score = "CONSISTENT", 0.7

        # ─── RECONSTRUCTION FIDELITY ──────────────────────────────────────────
        from tantrium.core.reconstruct import reconstruction_fidelity
        recon = reconstruction_fidelity(moments)

        # ─── AXIS 4: CONFIDENCE ───────────────────────────────────────────────
        from tantrium.core.confidence import calibrate
        achilles_score = obj.structure.get("achilles_score", 0.0) if hasattr(obj, "structure") else 0.0
        conf = calibrate(
            structural=structural_score,
            achilles=1.0 - float(achilles_score),
            grounding=grounding_score,
            truth=truth_score,
        )

        # ─── COHERENT BOOLEAN ─────────────────────────────────────────────────
        # Reconstruction fidelity: adaptive depth seçimi için (blocking değil).
        # Coherent = tüm yapısal, toraklama, gerçek eksenleri anlaşıyor.
        coherent = (
            paradigms_passed >= paradigms_total - 1
            and grounding != "UNGROUNDED"
            and truth != "CONTRADICTORY"
            and conf.value >= 0.40
        )

        return UnifiedCertificate(
            name=nm,
            moments=moments,
            paradigms_passed=paradigms_passed,
            paradigms_total=paradigms_total,
            gaps=gaps,
            structural_score=structural_score,
            grounding=grounding,
            grounding_score=grounding_score,
            truth=truth,
            truth_score=truth_score,
            confidence=conf.value,
            confidence_level=conf.level,
            reconstruction_fidelity=recon,
            coherent=coherent,
            evidence={"run": run},
        )

    def _encode_adaptive(self, input_data: object, name: str) -> object:
        """8→16 moment derinliği, rekonstrüksiyon kalitesi düşükse."""
        try:
            from tantrium.core.reconstruct import reconstruction_fidelity
            from tantrium.core.encoder import UniversalEncoder
            obj = self._engine.encoder.encode(input_data, name=name)
            fidelity = reconstruction_fidelity(list(obj.moments))
            if fidelity < 0.999 and len(obj.moments) < 16:
                deeper = UniversalEncoder(16).encode(input_data, name=name)
                if reconstruction_fidelity(list(deeper.moments)) > fidelity:
                    return deeper
            return obj
        except Exception:
            return self._engine.encoder.encode(input_data, name=name)
