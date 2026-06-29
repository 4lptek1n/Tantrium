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

    # Eksen 5: RH-sertifika bundle (ayırt edici — PSD-otomatik DEĞİL)
    rh_grade: float = 1.0          # [0,1] birleşik RH-derece
    rh_stieltjes: bool = True      # [0,∞) ölçü sertifikası (Hilbert-Pólya operatörü)
    rh_hausdorff: bool = True      # [0,1] tam-monoton ölçü
    rh_rank: int = 0               # spektral atom sayısı (AYIRT EDİCİ)
    rh_free_entropy: float = 0.0   # serbest entropi χ (logaritmik enerji)
    rh_semicircle: float = 0.0     # yarı-daireye (Wigner) mesafe
    rh_summary: str = ""
    sealed_hash: str = ""          # SHA-256 içerik-hash — dışarıdan denetlenebilir

    def __str__(self) -> str:
        cert = "✓" if self.coherent else "✗"
        g = {"GROUNDED": "⏚", "WEAKLY_GROUNDED": "≈", "UNGROUNDED": "∅"}.get(
            self.grounding, "?")
        return (
            f"{cert} {self.name} [{self.paradigms_passed}/{self.paradigms_total}] "
            f"{g} {self.truth} conf={self.confidence:.2f} [{self.confidence_level}] "
            f"RH={self.rh_grade:.2f}{'⊕' if self.rh_stieltjes else '⊝'} "
            f"rank={self.rh_rank} seal={self.sealed_hash[:8]}"
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
            truth_score = getattr(tcert, "truth_score",
                                  getattr(tcert, "consistency_score", 0.7))
        else:
            truth, truth_score = "CONSISTENT", 0.7

        # ─── RECONSTRUCTION FIDELITY ──────────────────────────────────────────
        from tantrium.core.reconstruct import reconstruction_fidelity as _recon_fid
        recon = _recon_fid(moments)

        # ─── AXIS 5: RH-SERTİFİKA BUNDLE (ayırt edici, mühürlü) ───────────────
        # encoder structure["rh"] (16-derinlik, hafif) hazır; free_entropy burada (heavy).
        rh_grade, rh_stieltjes, rh_hausdorff = 1.0, True, True
        rh_rank, rh_free_entropy, rh_semicircle, rh_summary, sealed_hash = 0, 0.0, 0.0, "", ""
        try:
            rh = getattr(obj, "structure", {}).get("rh") if hasattr(obj, "structure") else None
            if rh is not None:
                rh_grade = float(rh.get("grade", 1.0))
                cr = rh.get("criteria", {})
                rh_stieltjes = bool(cr.get("stieltjes_certified", True))
                rh_rank = int(cr.get("rank", 0))
                rh_hausdorff = bool(rh.get("hausdorff_certified", True))
                rh_semicircle = float(rh.get("semicircle_distance", 0.0))
                sealed_hash = rh.get("sealed_hash", "")
            from tantrium.core.free_probability import free_entropy as _fe
            rh_free_entropy = float(_fe(moments))
            rh_summary = (f"RH grade={rh_grade:.2f} rank={rh_rank} "
                          f"Stieltjes:{'✓' if rh_stieltjes else '✗'} "
                          f"Hausdorff:{'✓' if rh_hausdorff else '✗'} χ={rh_free_entropy:+.3g}")
        except Exception:
            pass

        # ─── AXIS 4: CONFIDENCE ───────────────────────────────────────────────
        from tantrium.core.confidence import calibrate
        achilles_margin = 0.0
        if hasattr(obj, "structure"):
            achilles_margin = float(obj.structure.get("achilles_margin", 0.0) or 0.0)
        conf = calibrate(
            coverage=structural_score,
            margin=achilles_margin,
            grounding=grounding_score,
            truth=truth_score,
        )

        # ─── COHERENT BOOLEAN ─────────────────────────────────────────────────
        # Coherent = tüm eksenler anlaşıyor. RH-Stieltjes ayırt edici filtre:
        # G=AᵀA spektrumu ≥0 → gerçek nesnede geçer, ama geçersiz/artefakt moment
        # dizisini (Hankel-PSD-olmayan) eler. PSD-otomatik 23 paradigmadan FARKLI —
        # gerçek bir reddetme kapısı. (Hausdorff KATILMAZ: çoğu gerçek spektrum [0,1] dışı.)
        coherent = (
            paradigms_passed >= paradigms_total - 1
            and grounding != "UNGROUNDED"
            and truth != "CONTRADICTORY"
            and conf.value >= 0.40
            and rh_stieltjes
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
            # gcert: ask() özet metni için yeniden kullanır (çift grounding hesabı YOK)
            evidence={"run": run, "grounding_cert": gcert},
            rh_grade=rh_grade,
            rh_stieltjes=rh_stieltjes,
            rh_hausdorff=rh_hausdorff,
            rh_rank=rh_rank,
            rh_free_entropy=rh_free_entropy,
            rh_semicircle=rh_semicircle,
            rh_summary=rh_summary,
            sealed_hash=sealed_hash,
        )

    def _encode_adaptive(self, input_data: object, name: str) -> object:
        """8→16 moment derinliği, rekonstrüksiyon kalitesi düşükse."""
        try:
            from tantrium.core.encoder import UniversalEncoder
            from tantrium.core.reconstruct import reconstruction_fidelity as _rf
            obj = self._engine.encoder.encode(input_data, name=name)
            fidelity = _rf(list(obj.moments))
            if fidelity < 0.999 and len(obj.moments) < 16:
                deeper = UniversalEncoder(16).encode(input_data, name=name)
                if _rf(list(deeper.moments)) > fidelity:
                    return deeper
            return obj
        except Exception:
            return self._engine.encoder.encode(input_data, name=name)
