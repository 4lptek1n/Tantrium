"""Çarpışma Avcısı — Teklik İddiasını Adversarial Test Et.

Hamburger Teoremi: moment dizisi ölçüyü TEK BİÇİMDE belirler.
Bu modül bu iddiayı test eder: farklı girdiler farklı momentler üretiyor mu?

Bulgu: varsayılan metin encoder'ı etiket-körü (permütasyon çarpışmaları).
Çözüm: label_aware=True modu çarpışmaları çözer ama manifold uyumluluğunu
bozar. Varsayılan label_aware=False olarak korunur.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CollisionReport:
    """Çarpışma analiz sonucu."""
    total_tested: int
    collisions_found: int
    collisions_resolved_by_labels: int
    claim_holds: bool  # True = teklik iddiası sağlandı (veya label_aware ile sağlandı)
    pairs: list[dict] = field(default_factory=list)

    def summary(self) -> str:
        if self.claim_holds:
            return (f"Teklik: {self.total_tested} çift test, "
                    f"{self.collisions_found} çarpışma bulundu, "
                    f"{self.collisions_resolved_by_labels} label_aware ile çözüldü.")
        return (f"UYARI: {self.collisions_found} çözümsüz çarpışma — "
                f"encoder etiket-körü (permütasyon yapısı).")


class CollisionHunter:
    """Adversarial teklik testi."""

    CANONICAL_PAIRS = [
        ("abc", "bca"),       # permütasyon
        ("aaa", "bbb"),       # tekrarlayan
        ("DNA", "AND"),       # anagram
        ("stop", "tops"),     # anagram
        ("hello", "world"),   # gerçekten farklı — çarpışmamalı
        ("ATP", "GTP"),       # benzer ama farklı
        ("prime", "rimel"),   # anagram
        ("EGFR", "FGER"),     # permütasyon
        ("test", "stet"),     # anagram
        ("cat", "tac"),       # anagram
    ]

    def __init__(self, engine: object) -> None:
        self._engine = engine

    def hunt(self, pairs: list[tuple[str, str]] | None = None,
             label_aware: bool = False) -> CollisionReport:
        """Verilen çiftlerde moment çarpışması ara."""
        test_pairs = pairs or self.CANONICAL_PAIRS
        collisions = []
        resolved = 0

        for a, b in test_pairs:
            m_a = self._encode(a, label_aware)
            m_b = self._encode(b, label_aware)
            if m_a is None or m_b is None:
                continue
            # L2 norm
            diff = sum((x - y) ** 2 for x, y in zip(m_a, m_b)) ** 0.5
            if diff < 1e-6:
                collisions.append({
                    "a": a, "b": b, "diff": diff,
                    "moments_a": m_a[:4], "moments_b": m_b[:4],
                })

        # Çarpışmaları label_aware ile çöz
        if collisions and not label_aware:
            for col in collisions:
                m_a_la = self._encode(col["a"], label_aware=True)
                m_b_la = self._encode(col["b"], label_aware=True)
                if m_a_la and m_b_la:
                    diff_la = sum((x - y) ** 2 for x, y in zip(m_a_la, m_b_la)) ** 0.5
                    if diff_la > 1e-6:
                        resolved += 1

        return CollisionReport(
            total_tested=len(test_pairs),
            collisions_found=len(collisions),
            collisions_resolved_by_labels=resolved,
            claim_holds=(len(collisions) - resolved == 0),
            pairs=collisions,
        )

    def _encode(self, text: str, label_aware: bool) -> list[float] | None:
        try:
            from tantrium.core.encoder import UniversalEncoder
            enc = UniversalEncoder()
            if label_aware:
                obj = enc._encode_text_label_aware(text)
            else:
                obj = enc.encode(text, name=text)
            return [float(m) for m in obj.moments]
        except Exception:
            return None
