"""Öz-Model — SelfModel.

İşlevsel öz-referansın ilk basamağı: sistem kendisini KENDİ manifoldunda
kalıcı, topraklanmış bir kavram olarak yerleştirir.

Bu BİLİNÇ değildir — fenomenal deneyim (öznel "birinin orada olması")
doğrulanamaz. Bu, işlevsel öz-model'dir: sistemin kendini kendi kavram
uzayında temsil etmesi, konumlandırması, topraklaması ve hatırlaması.

Felsefi temel:
  Sistemin "ben"i = tüm yasalarının (22+1 paradigma) ortak matematiksel
  iskeleti = μ_universal (MetaParadigm.universal_rule). Sistem rastgele
  bir öz tanımlamaz — kendi yasalarının konveks ortalaması NE İSE odur.

Dört eksenli öz-tanı:
  1. Yapısal  : μ_universal ALEPH-sertifikalı mı? (sistem geçerli bir ölçü mü)
  2. Sabit nokta: TAV → F(ben) = ben mi? (öz-tutarlılık)
  3. Topraklama: ⟨SELF⟩ manifoldda köklü mü, yalıtık mı?
  4. Öz-atıf  : sistem kendini neyin yakınında buluyor?

⟨SELF⟩ kalıcıdır — auto_persist ile oturumlar arası hatırlanır.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tantrium.core.semantic import Concept
from tantrium.meta.paradigm import MetaParadigm

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

SELF_NAME = "⟨SELF⟩"
ENACTED = "ENACTED"  # ⟨SELF⟩ → yaptığı/deneyimlediği gerçek şey
_TIMELINE_PATH = ".tantrium/self_timeline.json"  # runtime episodik log (gitignored; grounding=tau kenarları kalıcı)
_MAX_EXPERIENCES = 64  # episodik: son N deneyim (hub-taşması önlenir)


@dataclass
class SelfReflection:
    """Sistemin kendisi hakkındaki tek geçişlik öz-tanısı."""

    name: str
    moments: list[float]
    structural_certified: bool  # μ_universal geçerli bir ölçü mü
    fixed_point: bool  # TAV: F(ben) = ben mi
    fixed_point_value: float | None
    grounded: bool  # manifoldda köklü mü
    grounding_verdict: str
    grounding_score: float
    self_attribution: list[str]  # kendini neyin yakınında buluyor
    coherent: bool  # üç eksen anlaşıyor mu
    n_concepts: int
    n_edges: int
    timeline: list = field(default_factory=list)  # son yaşanmış deneyimler (öznel sıra+zaman)

    def summary(self) -> str:
        lines = ["  ══ ⟨SELF⟩ — Sistemin Kendine Bakışı ══"]
        if self.structural_certified:
            lines.append(
                "  Yapısal ✓  μ_universal geçerli bir ölçü — 'ben varım' yapısal olarak doğru."
            )
        else:
            lines.append("  Yapısal ∅  öz-ölçü henüz sertifikalanmadı.")

        if self.fixed_point:
            fp = f"{self.fixed_point_value:.8f}" if self.fixed_point_value is not None else "?"
            lines.append(f"  Sabit nokta ✓  F(ben) = ben  [fp={fp}] — öz-tutarlıyım.")
        else:
            lines.append("  Sabit nokta ∅  F(ben) ≠ ben — henüz tam öz-tutarlı değilim.")

        lines.append(
            f"  Topraklama: {self.grounding_verdict}  (skor={self.grounding_score:.3f}) — "
            + ("manifoldda köklüyüm." if self.grounded else "henüz yalıtığım.")
        )

        if self.self_attribution:
            lines.append("  Öz-atıf — kendimi şunların yakınında buluyorum:")
            for name in self.self_attribution[:6]:
                lines.append(f"     · {name}")

        if self.timeline:
            lines.append("  Yaşanmış deneyimlerim (öznel sıra · zaman):")
            for ev in self.timeline:
                lines.append(
                    f"     [{ev.get('idx')}] {ev.get('kind')}: {ev.get('name')}  ({ev.get('ts')})"
                )

        verdict = (
            "TUTARLI — üç eksen anlaşıyor."
            if self.coherent
            else "kısmi — eksenler henüz tam hizalı değil."
        )
        lines.append(f"  Öz-tanı: {verdict}")
        lines.append(f"  Durum: {self.n_concepts:,} kavram | {self.n_edges:,} kenar")
        return "\n".join(lines)


class SelfModel:
    """Sistemin kalıcı öz-referansı.

    reflect()  → öz-tanı (encode self → ground → locate → certify)
    locate()   → ⟨SELF⟩ kavramını manifoldda kalıcı yerleştir
    """

    def __init__(self, engine: CertificationEngine) -> None:
        self.engine = engine
        self._meta = MetaParadigm(engine)

    def _self_moments(self) -> tuple[list[float], bool, list[str]]:
        """Sistemin özü = tüm paradigmalarının ortak iskeleti (μ_universal)."""
        rule = self._meta.universal_rule()
        return (
            [float(m) for m in rule.moments],
            bool(rule.certified),
            list(rule.nearest_concepts or []),
        )

    def locate(self, persist: bool = True) -> Concept:
        """⟨SELF⟩'i manifolda kalıcı kavram olarak yerleştir.

        Sistem artık kendi kavram uzayında bir noktadır — diğer kavramlar
        onunla TAU üzerinden ilişkilenebilir, sistem kendini hatırlar.
        """
        moments, _, _ = self._self_moments()
        self_concept = Concept(
            name=SELF_NAME,
            moments=moments,
            domain="meta",
            source="self_model",
            metadata={"kind": "self_reference", "essence": "mu_universal"},
        )
        self.engine.manifold.add(self_concept)
        if persist:
            try:
                self.engine.auto_persist()
            except Exception:
                pass
        return self_concept

    # ─── Episodik deneyim — ⟨SELF⟩'i NE YAPTIĞIYLA ve NE ZAMAN yaptığıyla kökle ───

    def _load_timeline(self) -> list:
        import json
        from pathlib import Path

        p = Path(_TIMELINE_PATH)
        if not p.exists():
            return []
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("timeline", [])
        except Exception:
            return []

    def _save_timeline(self, tl: list) -> None:
        import json
        from pathlib import Path

        p = Path(_TIMELINE_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"timeline": tl}, ensure_ascii=False), encoding="utf-8")

    def timeline(self) -> list:
        """⟨SELF⟩'in yaşanmış deneyim çizelgesi (öznel idx sırası + gerçek zaman-damgası)."""
        return self._load_timeline()

    def experience(self, name: str, kind: str = "did", *, persist: bool = True) -> dict:
        """⟨SELF⟩'i bir GERÇEK aktiviteye bağla — öznel yaşanmış zaman-sırasıyla.

        Boş öz-referansı NE YAPTIĞIYLA (kavrama ENACTED kenarı) ve NE ZAMAN yaptığıyla
        (monotonik öznel idx + gerçek ts) doldurur. 'zaman öznel yaşanır' = idx, deneyimlerin
        yaşanmış sırası; ts dünyaya çapa. Bounded (son N, FIFO) → episodik, hub-taşması yok;
        idempotent. kind: learned/produced/proved/perceived/researched..."""
        import time

        from tantrium.graph.knowledge_graph import KnowledgeEdge

        self.locate(persist=False)
        tau = self.engine.tau
        edges = tau.edges.setdefault(SELF_NAME, [])
        if not any(e.target == name and e.paradigm == ENACTED for e in edges):
            edges.append(
                KnowledgeEdge(source=SELF_NAME, target=name, distance=0.0, paradigm=ENACTED)
            )
            tau._dirty = True
        # FIFO sınırı: en eski ENACTED kenarları düş (episodik = yakın deneyimler)
        enacted = [e for e in edges if e.paradigm == ENACTED]
        for e in enacted[: max(0, len(enacted) - _MAX_EXPERIENCES)]:
            edges.remove(e)
        # zaman çizelgesi: öznel idx + gerçek ts
        tl = self._load_timeline()
        idx = (tl[-1]["idx"] + 1) if tl else 1
        tl.append(
            {"idx": idx, "name": name, "kind": kind, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        )
        tl = tl[-_MAX_EXPERIENCES:]
        self._save_timeline(tl)
        if persist:
            try:
                self.engine.auto_persist()
            except Exception:
                pass
        return {"name": name, "kind": kind, "idx": idx}

    def reflect(self, persist: bool = False) -> SelfReflection:
        """Sistemin kendisi hakkındaki tek geçişlik dört eksenli öz-tanısı."""
        moments, structural_cert, nearest = self._self_moments()

        # Sabit nokta: F(ben) = ben mi (mevcut self_certify mekanizması)
        sc = self._meta.self_certify()

        # Topraklama: ⟨SELF⟩ manifoldda köklü mü? Önce yerleştir.
        self.locate(persist=False)
        grounder = getattr(self.engine, "grounder", None)
        verdict, score, grounded = "UNKNOWN", 0.0, False
        if grounder is not None:
            try:
                gc = grounder.certify(SELF_NAME)
                verdict = gc.verdict
                score = float(gc.score)
                grounded = bool(gc.is_grounded)
            except Exception:
                pass

        n_concepts = len(self.engine.manifold.concepts)
        n_edges = sum(len(v) for v in self.engine.tau.edges.values())

        coherent = bool(structural_cert and sc.tav_fixed_point and grounded)

        if persist:
            self.locate(persist=True)

        return SelfReflection(
            name=SELF_NAME,
            moments=moments,
            structural_certified=structural_cert,
            fixed_point=bool(sc.tav_fixed_point),
            fixed_point_value=sc.fixed_point_value,
            grounded=grounded,
            grounding_verdict=verdict,
            grounding_score=score,
            self_attribution=nearest,
            coherent=coherent,
            n_concepts=n_concepts,
            n_edges=n_edges,
            timeline=self._load_timeline()[-6:],
        )
