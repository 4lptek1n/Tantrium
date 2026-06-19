"""Eylem Döngüsü — Actor (sınırlı / sandbox eylemler).

Hedef → certified TAU walk → action plan → execute → certify → manifold güncelle.

Güvenlik sınırı — yalnızca manifold-güvenli eylemler:
  LearnAction    auto_learn(text)              — kavram + ilişki öğren
  RelateAction   add_relations_from_text()     — semantik ilişki çıkar
  SaveAction     auto_persist()                — checkpoint manifold/TAU
  ThinkAction    engine.think(question)        — derin düşün, session'a ekle
  ProgressAction goal.update_progress()        — hedef ilerlemesini güncelle

YASAK: dosya yazma, shell komutu, eval/exec, subprocess, ağ erişimi.
Her eylem Aleph filtreden geçer; başarısız eylemler manifold'a dokunmaz.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine
    from tantrium.research.goal import Goal, GoalManifold


ActionType = Literal["learn", "relate", "save", "think", "progress"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class Action:
    action_type: ActionType
    payload: str       # learn/relate/think için metin; save/progress için boş
    goal_name: str = ""
    certified: bool = False
    timestamp: str = field(default_factory=_now)


@dataclass
class ActionResult:
    action: Action
    success: bool
    summary: str
    concepts_learned: list[str] = field(default_factory=list)
    relations_added: int = 0
    error: str = ""


# ─── Actor ────────────────────────────────────────────────────────────────────

class Actor:
    """Sınırlı eylem döngüsü.

    plan()         → hedefe yönelik Action listesi üret
    execute()      → tek eylemi güvenli şekilde uygula
    pursue_goal()  → tam döngü: TAU walk → plan → execute → progress
    """

    # Payload içinde bu kalıplar varsa eylem reddedilir
    _UNSAFE = frozenset([
        "import os", "import sys", "subprocess", "eval(", "exec(",
        "__import__", "open(", ".write(", "os.remove", "os.unlink",
        "shutil", "rm -", "/bin/", "/usr/", "sudo ", "bash ", "shell(",
    ])

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ─── Plan ─────────────────────────────────────────────────────────────────

    def plan(
        self,
        goal: "Goal",
        candidates: list[tuple[str, float, str]],
    ) -> list[Action]:
        """Aday kavramlardan eylem planı üret.

        Sıra: learn (pekiştir) → relate (ilişki çıkar) → think (derin düşün)
              → progress (ilerleme güncelle) → save (checkpoint).
        """
        actions: list[Action] = []

        # 1. Hedefe yakın kavramları öğren/pekiştir
        for concept_name, _dist, paradigm in candidates[:3]:
            text = f"{concept_name} {paradigm.lower().replace('_', ' ')} {goal.name}"
            actions.append(Action("learn", text, goal_name=goal.name))

        # 2. Hedefin kendisini öğren
        actions.append(Action("learn", goal.name, goal_name=goal.name))

        # 3. İlişki çıkar
        if candidates:
            names = [c[0] for c in candidates[:3]]
            rel_text = f"{goal.name} uses {' and '.join(names)}"
            actions.append(Action("relate", rel_text, goal_name=goal.name))

        # 4. Derin düşün
        actions.append(Action("think", goal.name, goal_name=goal.name))

        # 5. İlerleme güncelle
        actions.append(Action("progress", "", goal_name=goal.name))

        # 6. Checkpoint
        actions.append(Action("save", "", goal_name=goal.name))

        return actions

    # ─── Execute ──────────────────────────────────────────────────────────────

    def execute(self, action: Action, goal: "Goal | None" = None) -> ActionResult:
        """Tek eylemi güvenli şekilde uygula."""
        if not self._is_safe(action):
            return ActionResult(
                action=action,
                success=False,
                summary="REDDEDİLDİ — güvensiz payload",
                error="UNSAFE_PAYLOAD",
            )
        try:
            if action.action_type == "learn":
                return self._learn(action)
            elif action.action_type == "relate":
                return self._relate(action)
            elif action.action_type == "save":
                return self._save(action)
            elif action.action_type == "think":
                return self._think(action)
            elif action.action_type == "progress":
                return self._progress(action, goal)
            else:
                return ActionResult(
                    action=action,
                    success=False,
                    summary=f"Bilinmeyen tür: {action.action_type}",
                    error="UNKNOWN_ACTION_TYPE",
                )
        except Exception as exc:
            return ActionResult(
                action=action,
                success=False,
                summary=f"Hata: {exc}",
                error=str(exc),
            )

    def _is_safe(self, action: Action) -> bool:
        low = action.payload.lower()
        return not any(unsafe in low for unsafe in self._UNSAFE)

    def _learn(self, action: Action) -> ActionResult:
        # Dil katmanı (metinden öğrenme) kaldırıldı — ASİ yapısal/sayısal kaynaklardan büyür.
        return ActionResult(
            action=action,
            success=False,
            summary="metinden öğrenme kaldırıldı (dil katmanı yok)",
            concepts_learned=[],
            relations_added=0,
        )

    def _relate(self, action: Action) -> ActionResult:
        from tantrium.graph.relations import add_relations_from_text
        n = add_relations_from_text(self.engine, action.payload)
        action.certified = True
        return ActionResult(
            action=action,
            success=True,
            summary=f"+{n} semantik ilişki",
            relations_added=n,
        )

    def _save(self, action: Action) -> ActionResult:
        n_concepts, n_edges = self.engine.auto_persist()
        action.certified = True
        return ActionResult(
            action=action,
            success=True,
            summary=f"Kaydedildi: {n_concepts} kavram | {n_edges} edge",
        )

    def _think(self, action: Action) -> ActionResult:
        result = self.engine.think(action.payload, depth=2)
        action.certified = result.fixed_point_found
        summary = (
            f"Düşünüldü: {result.total_certified} sertifika, {result.total_gaps} gap"
            + (" | TAV ✓" if result.fixed_point_found else "")
        )
        # Derin düşünce kavramlarını session'a ekle
        session = getattr(self.engine, "session", None)
        if session is not None:
            from tantrium.graph.memory import Turn
            thought_concepts = [
                c
                for lv in result.levels
                for c in lv.concepts
                if c in self.engine.manifold.concepts
            ]
            if thought_concepts:
                session.add_turn(Turn(
                    user_input=f"[think:{action.payload[:40]}]",
                    certified_concepts=thought_concepts,
                    new_concepts=[],
                ))
        return ActionResult(action=action, success=True, summary=summary)

    def _progress(self, action: Action, goal: "Goal | None") -> ActionResult:
        if goal is None:
            return ActionResult(
                action=action, success=False,
                summary="Hedef sağlanmadı", error="NO_GOAL",
            )
        session = getattr(self.engine, "session", None)
        recent: list[str] = []
        if session and session.turns:
            for turn in session.turns[-3:]:
                recent.extend(turn.certified_concepts)
        # Fallback: manifest'ten rastgele küçük set
        if not recent:
            recent = list(self.engine.manifold.concepts.keys())[:30]
        new_p = goal.update_progress(recent, self.engine)
        action.certified = True
        return ActionResult(
            action=action, success=True,
            summary=f"İlerleme güncellendi: {new_p:.0%}",
        )

    # ─── Full loop ────────────────────────────────────────────────────────────

    def pursue_goal(
        self,
        goal: "Goal",
        goal_manifold: "GoalManifold",
    ) -> list[ActionResult]:
        """Hedefe yönelik tam döngü: TAU walk → plan → execute → progress.

        Döner: execute edilen eylemlerin sonuçları.
        """
        candidates = goal_manifold.pursue(goal, self.engine)
        actions = self.plan(goal, candidates)

        results: list[ActionResult] = []
        for action in actions:
            r = self.execute(action, goal=goal)
            results.append(r)
            if r.concepts_learned:
                goal.action_trace.extend(r.concepts_learned[:3])
                self.engine.note_new_concepts(r.concepts_learned, r.relations_added)

        goal_manifold.save()
        return results
