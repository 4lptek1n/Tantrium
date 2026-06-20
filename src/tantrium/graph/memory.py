"""Çalışma Belleği ve Oturum Sürekliliği — SessionMemory.

Multi-turn akıl yürütme için. Her konuşma turn'ünü kaydeder, son
turn'lerin kavramlarını recency-decay ile "aktif" tutar.

Bu, manifold (uzun-dönem bellek) ile anlık konuşma (çalışma belleği)
arasındaki köprüdür. Manifold her şeyi tutar; SessionMemory ise
"şu an neyden bahsediyoruz" sorusunu cevaplar.

Süreklilik: SessionMemory.latest() en son oturumu sürdürür — sistem
bir önceki konuşmanın kaldığı yerden devam eder.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_DECAY = 0.7  # her turn'de eski kavramların ağırlığı bu katsayıyla azalır
_SESSION_DIR = "results/agi/sessions"


@dataclass
class Turn:
    """Tek bir konuşma turn'ü."""

    user_input: str
    certified_concepts: list[str] = field(default_factory=list)  # bilinen + yeni
    new_concepts: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=_now)


@dataclass
class SessionMemory:
    """Bir konuşma oturumunun çalışma belleği.

    active_concepts: kavram → recency ağırlığı [0,1]. Her turn'de mevcut
    ağırlıklar _DECAY ile çarpılır, yeni kavramlar 1.0 ile eklenir.
    Böylece yeni bahsedilenler ağır, eskiyenler hafif olur.
    """

    session_id: str
    turns: list[Turn] = field(default_factory=list)
    active_concepts: dict[str, float] = field(default_factory=dict)
    created: str = field(default_factory=_now)

    # ─── Turn ekleme ──────────────────────────────────────────────────────────

    def add_turn(self, turn: Turn) -> None:
        """Turn'ü ekle, aktif kavramları decay + güncelle."""
        self.turns.append(turn)
        # Mevcut ağırlıkları decay et
        for name in list(self.active_concepts.keys()):
            self.active_concepts[name] *= _DECAY
            if self.active_concepts[name] < 0.05:
                del self.active_concepts[name]
        # Bu turn'ün kavramlarını tam ağırlıkla ekle
        for name in turn.certified_concepts:
            self.active_concepts[name] = 1.0

    def context_concepts(self, top_n: int = 8) -> list[tuple[str, float]]:
        """En yüksek ağırlıklı N aktif kavram (sonraki encode'a karışacak)."""
        return sorted(self.active_concepts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def clear_working(self) -> None:
        """Çalışma belleğini temizle (/forget). Turn geçmişi korunur."""
        self.active_concepts.clear()

    # ─── Kalıcılık ────────────────────────────────────────────────────────────

    def save(self, path: str | None = None) -> str:
        """Oturumu JSON'a kaydet. Yol verilmezse session_id'den türetir."""
        p = Path(path) if path else Path(_SESSION_DIR) / f"{self.session_id}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "session_id": self.session_id,
            "created": self.created,
            "active_concepts": self.active_concepts,
            "turns": [asdict(t) for t in self.turns],
        }
        p.write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return str(p)

    @classmethod
    def load(cls, path: str) -> SessionMemory:
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        s = cls(
            session_id=data["session_id"],
            created=data.get("created", _now()),
            active_concepts=dict(data.get("active_concepts", {})),
        )
        s.turns = [Turn(**t) for t in data.get("turns", [])]
        return s

    @classmethod
    def latest(cls, directory: str = _SESSION_DIR) -> SessionMemory | None:
        """En son değiştirilmiş oturumu sürdür. Yoksa None."""
        d = Path(directory)
        if not d.exists():
            return None
        files = sorted(d.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            return None
        try:
            return cls.load(str(files[0]))
        except (json.JSONDecodeError, KeyError):
            return None

    @classmethod
    def new(cls) -> SessionMemory:
        """Yeni oturum — timestamp tabanlı kimlik."""
        sid = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return cls(session_id=sid)

    def summary(self) -> str:
        active = self.context_concepts(top_n=6)
        active_str = ", ".join(f"{n}({w:.2f})" for n, w in active) if active else "—"
        return f"Oturum: {self.session_id}  |  {len(self.turns)} turn  |  aktif: {active_str}"
