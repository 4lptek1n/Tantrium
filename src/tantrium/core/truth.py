"""Doğruluk Ekseni — sertifikasyonun ÜÇÜNCÜ ekseni.

İki eksen vardı:
  1. YAPISAL (23 paradigma): G=AᵀA daima PSD → "var mı?" → her şey var çıkar.
  2. TOPRAKLAMA (grounding): TAU'da köklü mü? → "anlamlı mı?" → bağlı mı?

Ama topraklama "bağlı mı?" der, "DOĞRU mu?" demez. İyi bağlanmış YANLIŞ bir
ifade GROUNDED çıkar. Üçüncü eksen bunu kapatır:

  3. DOĞRULUK (truth): kavram komşularıyla TUTARLI mı? Çevresiyle çelişiyor mu?

Matematiği — iki bağımsız sinyal:
  A. TRANSPORT TUTARLILIĞI: kavram en yakın komşularına CERTIFIED transport
     ile bağlanıyor mu? Tutarlı bölge → komşular arası taşıma sertifikalı.
     Çelişkili nokta → komşularına taşınamıyor (DYADIC_FAILED).
  B. EMET ÇAPRAZ-KONTROL: kavramın kendi pipeline'ında çelişki var mı?
     (EMET paradigması = cross-check, çelişki yok mu?)

Yargı:
  CONSISTENT    — komşularıyla tutarlı, çelişki yok (gerçeğe yakın)
  CONTESTED     — kısmen tutarlı, bazı komşularla çelişiyor (tartışmalı)
  CONTRADICTORY — komşularına taşınamıyor / EMET çelişki (yapısal yalan)

ÖNEMLİ: Bu doğruluğu KANITLAMAZ — tutarlılığı ölçer. Tutarlılık doğruluğun
gerekli (yeterli değil) koşuludur. Çelişkili = kesinlikle sorunlu;
tutarlı = sorun görünmüyor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


@dataclass
class TruthCertificate:
    """Bir kavramın doğruluk (tutarlılık) ekseni sertifikası."""
    name: str
    verdict: str                    # CONSISTENT | CONTESTED | CONTRADICTORY
    truth_score: float              # 0.0 (çelişkili) → 1.0 (tam tutarlı)

    neighbors_checked: int
    transport_certified: int        # kaç komşuya CERTIFIED transport
    transport_failed: int           # kaç komşuya transport başarısız
    emet_contradiction: bool        # kendi pipeline'ında EMET çelişkisi var mı

    consistent_neighbors: list[str] = field(default_factory=list)
    contested_neighbors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        glyph = {"CONSISTENT": "✓", "CONTESTED": "≈", "CONTRADICTORY": "✗"}.get(
            self.verdict, "?"
        )
        bar = int(self.truth_score * 20)
        bar_str = "█" * bar + "░" * (20 - bar)
        lines = [
            f"DOĞRULUK {glyph} «{self.name}»  [{bar_str}] {self.truth_score:.3f}",
            f"  yargı: {self.verdict}",
            f"  transport: {self.transport_certified}/{self.neighbors_checked} komşuya sertifikalı",
        ]
        if self.emet_contradiction:
            lines.append("  ⚠ EMET çelişkisi: kendi pipeline'ında iç çelişki")
        if self.consistent_neighbors:
            lines.append(f"  tutarlı: {', '.join(self.consistent_neighbors[:3])}")
        if self.contested_neighbors:
            lines.append(f"  tartışmalı: {', '.join(self.contested_neighbors[:3])}")
        return "\n".join(lines)


class TruthCertifier:
    """Kavramın komşularıyla tutarlılığını ölçen üçüncü eksen."""

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    def certify(
        self,
        name: str,
        n_neighbors: int = 6,
        moments: list | None = None,
    ) -> TruthCertificate:
        """Kavramın doğruluk eksenini hesapla.

        name manifoldda yoksa moments verilebilir (ya da encode edilir).
        """
        from tantrium.core.transport import CertifiedTransport
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode as enc

        # Kavramı al ya da encode et
        concept = self.engine.manifold.concepts.get(name)
        if concept is None:
            if moments is not None:
                from fractions import Fraction
                fracs = [Fraction(m).limit_denominator(10 ** 9) for m in moments]
                concept = Concept(name=name, moments=fracs, domain="probe", source="truth")
            else:
                obj = enc(name, name=name[:64])
                concept = Concept(name=name[:64], moments=list(obj.moments),
                                  domain="probe", source="truth")

        # EMET çapraz-kontrol: kendi pipeline'ında çelişki var mı?
        emet_contradiction = False
        try:
            obj = enc(list(concept.moments), name=name[:64])
            run = self.engine.process(obj)
            emet_node = None
            for pid in ("EMET", "emet"):
                emet_node = run.nodes.get(pid) if hasattr(run, "nodes") else None
                if emet_node is not None:
                    break
            if emet_node is not None and getattr(emet_node, "status", "") == "BLOCKED":
                emet_contradiction = True
        except Exception:
            pass

        # En yakın komşular (kendisi hariç)
        neighbors = self.engine.manifold.nearest(concept, n=n_neighbors + 1)
        neighbor_names = [nm for nm, _ in neighbors if nm != name][:n_neighbors]

        # Transport tutarlılığı: her komşuya CERTIFIED taşınabiliyor mu?
        ct = CertifiedTransport(self.engine)
        obj_self = enc(list(concept.moments), name=name[:64])

        certified = 0
        failed = 0
        consistent: list[str] = []
        contested: list[str] = []
        for nm in neighbor_names:
            nc = self.engine.manifold.concepts.get(nm)
            if nc is None:
                continue
            try:
                obj_n = enc(list(nc.moments), name=nm[:64])
                tc = ct.certify(obj_self, obj_n)
                if tc.certified:
                    certified += 1
                    consistent.append(nm)
                else:
                    failed += 1
                    contested.append(nm)
            except Exception:
                failed += 1

        checked = certified + failed

        # Doğruluk skoru: transport tutarlılık oranı, EMET çelişkisi cezalı
        if checked > 0:
            score = certified / checked
        else:
            score = 0.5  # komşu yok → belirsiz
        if emet_contradiction:
            score *= 0.5

        # Yargı
        if emet_contradiction or (checked > 0 and certified == 0):
            verdict = "CONTRADICTORY"
        elif score >= 0.6:
            verdict = "CONSISTENT"
        else:
            verdict = "CONTESTED"

        return TruthCertificate(
            name=name,
            verdict=verdict,
            truth_score=round(score, 4),
            neighbors_checked=checked,
            transport_certified=certified,
            transport_failed=failed,
            emet_contradiction=emet_contradiction,
            consistent_neighbors=consistent,
            contested_neighbors=contested,
        )
