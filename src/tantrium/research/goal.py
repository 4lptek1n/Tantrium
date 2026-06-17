"""Hedef Temsili — Goal ve GoalManifold.

Her hedef manifold'da Aleph-sertifikalı bir kavramdır (canonical byte encoding).
GoalManifold.pursue() → hedefe en yakın TAU yolu = sonraki eylem adayları.

Tav döngüsü: goal encode → TAU walk → action candidates → execute → progress → Tav.

Aleph garantisi: Goal.to_concept() Hankel PSD filtreden geçer.
Kısıt: Goal sahte metin kabul eder ama encode sonrası certify edilmelidir.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

from tantrium.core.semantic import Concept

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_GOAL_DIR = "results/agi/goals"
# Açık-sözlük: geometrik OLMAYAN her tip (kausal + öğrenilen yeni tipler dahil) anlamdır.
from tantrium.graph.knowledge_graph import SEMANTIC_PARADIGMS as _SEMANTIC_PARADIGMS


@dataclass
class Goal:
    """Bir hedef — manifold'da sertifikalı kavram olarak temsil edilir."""

    name: str                          # "diffusion modellerini öğren" vb.
    moments: list[float]               # canonical byte encoding → 8 spectral moment
    priority: float = 1.0              # 0.0–1.0
    active: bool = True
    progress: float = 0.0             # 0.0 = başlamadı, 1.0 = tamamlandı
    action_trace: list[str] = field(default_factory=list)
    created: str = field(default_factory=_now)

    def to_concept(self) -> Concept:
        return Concept(
            name=f"goal:{self.name}",
            moments=[Fraction(m).limit_denominator(10 ** 9) for m in self.moments],
            domain="goal",
            source="goal_manifold",
        )

    def distance_to(self, concept_moments: list) -> float:
        k = min(len(self.moments), len(concept_moments))
        return sum(abs(self.moments[i] - float(concept_moments[i])) for i in range(k))

    def update_progress(self, concept_names: list[str], engine: "CertificationEngine") -> float:
        """Bilinen kavramların hedefe manifold uzaklığına göre progress güncelle.

        Mesafe ölçeği: manifold moment_distance (~30-60 arası tipik değer).
        progress = max(0, 1 - min_dist / scale)  scale=35 (ortanca mesafe).
        """
        from tantrium.core.semantic import moment_distance
        goal_c = self.to_concept()
        distances = []
        for name in concept_names:
            c = engine.manifold.concepts.get(name)
            if c is not None:
                d = float(moment_distance(goal_c, c))
                distances.append(d)
        if not distances:
            return self.progress
        min_dist = min(distances)
        # scale: manifold NN mesafeleri ~30-35 → 0 mesafe = 100% ilerleme
        proximity = max(0.0, 1.0 - min_dist / 35.0)
        self.progress = max(self.progress, proximity)
        return self.progress


@dataclass
class GoalManifold:
    """Aktif hedeflerin manifoldu.

    Her hedef sertifikalı bir kavramdır. pursue() hedefe en yakın TAU
    yolunu bulur; bu kavramlar Actor'ın eylem adaylarıdır.
    """

    goals: list[Goal] = field(default_factory=list)

    # ─── CRUD ─────────────────────────────────────────────────────────────────

    def add(self, goal: Goal) -> bool:
        if any(g.name == goal.name for g in self.goals):
            return False
        self.goals.append(goal)
        return True

    def get(self, name: str) -> Goal | None:
        for g in self.goals:
            if g.name == name:
                return g
        return None

    def active_goals(self) -> list[Goal]:
        return [g for g in self.goals if g.active and g.progress < 1.0]

    # ─── TAU Walk: hedefe giden yol ───────────────────────────────────────────

    def pursue(
        self,
        goal: Goal,
        engine: "CertificationEngine",
        top_n: int = 6,
    ) -> list[tuple[str, float, str]]:
        """Hedefe en yakın kavramları bul: manifold walk + semantic edge bonus.

        Strateji:
          1. Manifold nearest-N → başlangıç adayları (ALEPH)
          2. Bu adayların semantic TAU komşuları → hedefe gerçek manifold
             mesafesiyle eklenir (inter-concept mesafe DEĞİL, goal-mesafesi)
          3. Semantic'e bonus çarpan (×0.5) — aynı mesafede semantic tercih edilir

        Döner: [(concept_name, goal_distance_scaled, paradigm), ...]
        """
        tau = getattr(engine, "tau", None)
        if tau is None or not engine.manifold.concepts:
            return []

        goal_concept = goal.to_concept()

        # ANLAM-PUSULASI: hedef köklü kavram(lar)a indirgenebiliyorsa "hedefe yakınlık"
        # yazılış değil ANLAM mesafesiyle ölçülür; değilse moment (eski davranış). dist_fn
        # no-anchor'da otomatik momente düşer → fail-open, math-hedef güvenli.
        from tantrium.core.meaning_pipeline import goal_distance_function
        dist_fn = goal_distance_function(engine, goal.name, goal_concept)

        # L1: SEED havuzu. Çapa köklüyse çapanın GRAF komşuları (anlam-havuzu); değilse
        # manifold.nearest (harf adresi). Havuz baştan doğru olmalı — sonra dist_fn sıralar.
        nearest = self._seed_candidates(goal, goal_concept, engine, top_n)
        result: dict[str, tuple[float, str]] = {}

        for seed_name, seed_dist in nearest:
            d = dist_fn(seed_name)
            if d != float("inf") and (seed_name not in result or d < result[seed_name][0]):
                result[seed_name] = (d, "ALEPH")

            # L2: seed'in semantic komşularının hedefe ANLAM mesafesi (typed-edge bonus ×0.5)
            for edge in tau.edges.get(seed_name, []):
                if edge.paradigm not in _SEMANTIC_PARADIGMS:
                    continue
                t = edge.target
                if engine.manifold.concepts.get(t) is None:
                    continue
                td = dist_fn(t)
                if td == float("inf"):
                    continue
                t_dist = td * 0.5  # semantic bonus
                if t not in result or t_dist < result[t][0]:
                    result[t] = (t_dist, edge.paradigm)

        candidates = sorted(result.items(), key=lambda x: x[1][0])
        return [(name, dist, p) for name, (dist, p) in candidates[:top_n]]

    def _seed_candidates(self, goal: Goal, goal_concept, engine, top_n: int):
        """Hedef-pursuit seed havuzu: çapa köklüyse çapanın GRAF komşuları, değilse harf-nearest.

        Çapa-grafından çekmek 'understand egfr signaling' için egfr'nin gerçek komşularını
        (akt3/kdr/grb2) verir; harf-nearest cümlenin yazılışına benzer jenerik çöp verirdi."""
        try:
            from tantrium.core.meaning_pipeline import resolve_goal_anchors, nearest_meaning
            anchors = resolve_goal_anchors(engine, goal.name)
            if anchors:
                seen: dict[str, float] = {}
                for a in anchors:
                    for nm, d, _ in nearest_meaning(engine, a, n=top_n * 2):
                        if nm not in seen and nm not in anchors:
                            seen[nm] = d
                if seen:
                    return list(seen.items())
        except Exception:
            pass
        return engine.manifold.nearest(goal_concept, n=top_n * 2)

    # ─── Kalıcılık ────────────────────────────────────────────────────────────

    def save(self, directory: str = _GOAL_DIR) -> str:
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        path = d / "goals.json"
        data = {
            "goals": [
                {
                    "name": g.name,
                    "moments": g.moments,
                    "priority": g.priority,
                    "active": g.active,
                    "progress": g.progress,
                    "action_trace": g.action_trace,
                    "created": g.created,
                }
                for g in self.goals
            ]
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    @classmethod
    def load(cls, directory: str = _GOAL_DIR) -> "GoalManifold":
        path = Path(directory) / "goals.json"
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        goals = [
            Goal(
                name=g["name"],
                moments=g["moments"],
                priority=g.get("priority", 1.0),
                active=g.get("active", True),
                progress=g.get("progress", 0.0),
                action_trace=g.get("action_trace", []),
                created=g.get("created", _now()),
            )
            for g in data.get("goals", [])
        ]
        return cls(goals=goals)

    # ─── Summary ──────────────────────────────────────────────────────────────

    def summary(self) -> str:
        active = self.active_goals()
        if not active:
            return "Aktif hedef yok."
        lines = [f"Aktif hedefler ({len(active)}):"]
        for g in sorted(active, key=lambda x: -x.priority):
            bar = "█" * int(g.progress * 10) + "░" * (10 - int(g.progress * 10))
            lines.append(
                f"  [{bar}] {g.progress:.0%}  '{g.name}'  (öncelik: {g.priority:.1f})"
            )
            if g.action_trace:
                lines.append(f"    öğrenildi: {', '.join(g.action_trace[-4:])}")
        return "\n".join(lines)


# ─── Helper ───────────────────────────────────────────────────────────────────

def encode_goal(engine: "CertificationEngine", description: str) -> Goal | None:
    """Hedefi canonical byte encoding ile encode et; Aleph certify.

    Döner: Goal (certified) ya da None (Aleph filtresi geçemedi).
    """
    obj = engine.encoder.encode(description, name=description[:64])
    run = engine.network.run(obj)
    aleph = run.nodes.get("ALEPH")
    if aleph is None or aleph.status != "CERTIFIED":
        return None
    return Goal(
        name=description,
        moments=[float(m) for m in obj.moments],
    )
