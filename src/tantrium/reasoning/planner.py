"""Hedef Tabanlı Planlama — Planner.

TAU graph üzerinde BFS ile mevcut bilgiden hedefe giden yolu bulur.
Her adım bir TAU semantik kenarı = öğrenilecek/ilişkilendirilecek bir kavram.

TCE matematiksel temeli:
  - Dyadic transport (D(m,ell,a)≥0): her adımda moment pozitifliği korunur
  - TAU kenarları = sertifikalı semantik geçişler
  - Manifold mesafesi = hedefe yakınlık ölçüsü
  - Greedy BFS: en çok mesafeyi azaltan kenarı seç

Çıktı: PlanStep listesi — adım adım, sıralı, certified yol.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine
    from tantrium.research.goal import Goal

_SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED",
             "CAUSES", "INHIBITS", "ACTIVATES"}


@dataclass
class PlanStep:
    """Planın tek bir adımı."""
    step_num: int
    concept: str          # bu adımda odaklanılacak kavram
    paradigm: str         # bu kavrama nasıl ulaşıldı (IS_A, USES, ...)
    from_concept: str     # hangi kavramdan bu adıma geçildi
    goal_distance: float  # bu kavramın hedefe manifold mesafesi
    action: str           # önerilen eylem: "learn", "relate", "think"

    def describe(self) -> str:
        verb = {
            "IS_A":           "türü olduğunu öğren",
            "USES":           "kullandığını öğren",
            "ACHIEVES":       "elde ettiğini öğren",
            "REQUIRES":       "gerektirdiğini öğren",
            "DEFINES":        "tanımladığını öğren",
            "COMPOSED":       "bileşenini öğren",
            "SPECTRAL_BRIDGE":"spektral köprüyü keşfet",
            "QUANTUM_BRIDGE": "kuantum köprüsünü keşfet",
            "CAUSES":         "nedenini izle",
            "INHIBITS":       "engelleyiciyi belirle",
            "ACTIVATES":      "aktivatörü takip et",
            "ALEPH":          "manifoldda konumunu bul",
        }.get(self.paradigm, "incele")
        return (
            f"  Adım {self.step_num}: '{self.concept}' — {verb}  "
            f"({self.from_concept} → {self.paradigm} → {self.concept})  "
            f"[hedefe mesafe: {self.goal_distance:.3f}]"
        )


@dataclass
class Plan:
    """Hedefe giden adım adım certified yol."""
    goal_name: str
    steps: list[PlanStep]
    initial_distance: float
    final_distance: float
    certified: bool = True

    def summary(self) -> str:
        if not self.steps:
            return f"  Hedef '{self.goal_name}' zaten ulaşılabilir durumda (mesafe: {self.initial_distance:.3f})."

        lines = [
            f"  ── Plan: '{self.goal_name}' ──────────────────────────",
            f"  Başlangıç mesafe: {self.initial_distance:.3f}  →  Tahmini son: {self.final_distance:.3f}",
            f"  {len(self.steps)} adım:",
        ]
        for step in self.steps:
            lines.append(step.describe())
        lines.append(f"  ──────────────────────────────────────────────────")
        return "\n".join(lines)

    def action_sequence(self) -> list[tuple[str, str]]:
        """(action_type, payload) listesi — Actor.execute() için hazır."""
        actions = []
        for step in self.steps:
            if step.action == "learn":
                text = f"{step.concept} {step.paradigm.lower()} {step.from_concept}"
                actions.append(("learn", text))
            elif step.action == "relate":
                text = f"{step.from_concept} {step.paradigm.lower().replace('_', ' ')} {step.concept}"
                actions.append(("relate", text))
            else:
                actions.append(("think", step.concept))
        actions.append(("progress", ""))
        actions.append(("save", ""))
        return actions


class Planner:
    """TAU graph üzerinde hedef-tabanlı BFS planlama.

    Mevcut bilgiden (known_concepts) hedefe (Goal) giden
    en kısa/verimli yolu TAU semantik kenarları üzerinden bulur.

    Kullanım:
        planner = Planner(engine)
        plan = planner.plan(goal, known_concepts=["learning", "optimization"])
        print(plan.summary())
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    def plan(
        self,
        goal: "Goal",
        known_concepts: list[str] | None = None,
        max_steps: int = 5,
        beam_width: int = 4,
    ) -> Plan:
        """Mevcut bilgiden hedefe giden adım planı üret.

        Algoritma: greedy BFS
          1. Başlangıç: known_concepts (veya son session turn'lerinden)
          2. Her adımda: frontier'daki kavramların tüm TAU komşularını genişlet
          3. Hedefe manifold mesafesini azaltan yönde ilerle (greedy)
          4. max_steps adımda dur

        PSD garantisi: her adım TAU sertifikalı kenar — D-positivity korunur.
        """
        # Başlangıç kavramları
        if not known_concepts:
            known_concepts = self._infer_known()
        known_set = set(known_concepts)

        # Hedef kavramını encode et
        goal_concept = goal.to_concept()

        # ANLAM-PUSULASI: hedef köklü kavrama indirgenebiliyorsa "yaklaştım mı?" yazılış
        # değil ANLAM mesafesiyle ölçülür; değilse moment (eski davranış). TEK tutarlı metrik.
        from tantrium.core.meaning_pipeline import goal_distance_function
        dist_fn = goal_distance_function(self.engine, goal.name, goal_concept)

        # Başlangıç mesafesini hesapla
        initial_dist = self._goal_distance(known_concepts, dist_fn)

        steps: list[PlanStep] = []
        frontier: dict[str, tuple[float, str, str]] = {}  # name → (dist, from, paradigm)

        # Frontier'ı known_concepts'ten doldur
        tau = self.engine.tau
        for src in known_concepts[:beam_width * 2]:
            for edge in tau.edges.get(src, []):
                if edge.target not in known_set and edge.target not in frontier:
                    tc = self.engine.manifold.concepts.get(edge.target)
                    if tc is None:
                        continue
                    d = dist_fn(edge.target)
                    frontier[edge.target] = (d, src, edge.paradigm)

        for step_num in range(1, max_steps + 1):
            if not frontier:
                break

            # En az mesafeli adayı seç (greedy)
            best = min(frontier.items(), key=lambda x: x[1][0])
            best_name, (best_dist, from_name, paradigm) = best

            # Bu adım ilerleme sağlıyor mu?
            current_min = self._goal_distance(known_concepts, dist_fn)
            if best_dist >= current_min and step_num > 1:
                break  # daha fazla ilerleyemiyoruz

            # Eylem tipini belirle
            action = "learn" if paradigm in _SEMANTIC else "think"
            if paradigm in {"IS_A", "USES"}:
                action = "relate"

            steps.append(PlanStep(
                step_num=step_num,
                concept=best_name,
                paradigm=paradigm,
                from_concept=from_name,
                goal_distance=best_dist,
                action=action,
            ))

            # Bu kavramı bilinenlere ekle, frontier'dan çıkar
            known_set.add(best_name)
            known_concepts = list(known_set)
            del frontier[best_name]

            # Yeni kavramın komşularını frontier'a ekle
            for edge in tau.edges.get(best_name, []):
                if edge.target not in known_set and edge.target not in frontier:
                    tc = self.engine.manifold.concepts.get(edge.target)
                    if tc is None:
                        continue
                    d = dist_fn(edge.target)
                    frontier[edge.target] = (d, best_name, edge.paradigm)

            # Frontier'ı beam_width ile sınırla (bellekte)
            if len(frontier) > beam_width * 8:
                sorted_f = sorted(frontier.items(), key=lambda x: x[1][0])
                frontier = dict(sorted_f[:beam_width * 4])

        final_dist = steps[-1].goal_distance if steps else initial_dist

        return Plan(
            goal_name=goal.name,
            steps=steps,
            initial_distance=initial_dist,
            final_distance=final_dist,
        )

    def _goal_distance(self, known: list[str], dist_fn) -> float:
        """known kavramların hedefe min mesafesi — TEK tutarlı dist_fn ile (anlam ya da moment)."""
        if not known:
            return float("inf")
        dists = []
        for name in known[:10]:
            if name in self.engine.manifold.concepts:
                dists.append(dist_fn(name))
        return min(dists) if dists else float("inf")

    def _infer_known(self) -> list[str]:
        """Session'dan veya son turn'lerden mevcut kavramları çıkar."""
        session = getattr(self.engine, "session", None)
        if session and session.turns:
            known = []
            for turn in session.turns[-3:]:
                known.extend(turn.certified_concepts)
            if known:
                return list(dict.fromkeys(known))[:20]
        # Fallback: session yoksa manifoldun ilk kavramları
        return list(self.engine.manifold.concepts.keys())[:10]

    def execute_plan(self, plan: Plan, goal: "Goal") -> list[str]:
        """Planı Actor aracılığıyla uygula. Döner: eylem sonuçları."""
        from tantrium.research.actor import Actor, Action
        actor = Actor(self.engine)
        results = []
        for action_type, payload in plan.action_sequence():
            action = Action(action_type=action_type, payload=payload, goal_name=goal.name)
            r = actor.execute(action, goal=goal)
            results.append(r.summary)
        return results
