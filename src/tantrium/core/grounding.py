"""Topraklama Sertifikası — sertifikasyonun ikinci ekseni.

23 paradigma bir nesnenin YAPISAL geçerliliğini ölçer: G=AᵀA daima PSD,
yani her şey "var" çıkar. Bu tasarım gereğidir (Hamburger) ama tek başına
ELEMEZ — rastgele harf çöpü de ATP de 23/23 alır.

Eksik olan: TOPRAKLAMA. Bir token anlamlıdır ÇÜNKÜ bilinen referanslara
bağlıdır. "protein" 71 TAU kenarına sahip; "xqzwvbnmkjhgfd" sıfır. Anlam
karakterlerde değil — ilişkilerde ve referanstadır.

Bu modül iki bağımsız sinyali birleştirir:

  1. DOĞRUDAN topraklama — token TAU grafında köklü bir düğüm mü?
     (çıkan + gelen kenar sayısı; öğrenilmiş gerçek ilişkiler)

  2. REZONANS topraklama — bilinmeyen bir token için: moment imzası
     KÖKLÜ kavramlardan oluşan TUTARLI bir kümeye mi düşüyor?
     Ham mesafe yetmez (40k yoğun manifoldda her nokta bir komşuya yakın);
     komşuluğun (a) kendi topraklanmışlığı, (b) domain tutarlılığı ölçülür.

Sonuç dürüst bir yargıdır:
  GROUNDED         — köklü düğüm veya tutarlı köklü kümeye rezonans
  WEAKLY_GROUNDED  — köklü kavramlara yakın ama tutarsız komşuluk
  UNGROUNDED       — yapısal olarak geçerli (PSD) ama yalıtık/anlamsız

Sistem artık her şeye 23/23 damgası vurmaz; bildiğini gürültüden ayırır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine
    from tantrium.core.semantic import Concept


# Bir komşunun "köklü" sayılması için gereken minimum TAU kenar sayısı
_GROUNDED_NEIGHBOR_MIN_EDGES = 3
# Rezonans için taranacak aday komşu sayısı
_RESONANCE_K = 30
# Rezonans yarıçapı (L1): bunun ötesindeki komşular "rezonans" sayılmaz.
# Doymuş manifoldda ham komşuluk ayırmaz; sıkı yarıçap gürültüyü eler.
_RESONANCE_RADIUS = 0.5
# Tutarlı küme için baskın domain'in köklü komşular içindeki minimum oranı
_COHERENCE_MIN_RATIO = 0.5
# Rezonansla GROUNDED demek için gereken minimum sıkı-köklü komşu sayısı
_RESONANCE_MIN_GROUNDED = 2


@dataclass
class GroundingCertificate:
    """Bir nesnenin topraklama yargısı — yapısal sertifikadan ayrı eksen."""
    token: str
    verdict: str                       # GROUNDED | WEAKLY_GROUNDED | UNGROUNDED
    direct_edges: int                  # token'ın doğrudan TAU kenar sayısı
    in_manifold: bool                  # token doğrudan manifoldda mı
    grounded_neighbors: int            # köklü komşu sayısı (rezonans)
    neighbor_coherence: float          # baskın domain'in komşu oranı [0,1]
    dominant_domain: str               # komşuluğun baskın domain'i
    nearest_grounded: list[str] = field(default_factory=list)  # köklü komşular
    score: float = 0.0                 # birleşik topraklama skoru [0,1]

    @property
    def is_grounded(self) -> bool:
        return self.verdict == "GROUNDED"

    def summary(self) -> str:
        if self.verdict == "GROUNDED":
            if self.direct_edges > 0:
                return (f"Topraklı — {self.token} TAU grafında köklü bir düğüm "
                        f"({self.direct_edges} ilişki).")
            joined = ", ".join(self.nearest_grounded[:3])
            return (f"Topraklı — {self.token} bilinen bir token değil ama "
                    f"'{self.dominant_domain}' bölgesindeki köklü kavramlara "
                    f"rezonans veriyor ({joined}).")
        if self.verdict == "WEAKLY_GROUNDED":
            tek = self.nearest_grounded[0] if self.nearest_grounded else "tek bir kavram"
            return (f"Zayıf topraklı — {self.token} yalnızca '{tek}' kavramına yakın, "
                    f"tutarlı bir kümeye oturmuyor. Yapısal olarak geçerli, anlamı belirsiz.")
        return (f"Topraksız — {self.token} yapısal olarak geçerli bir moment "
                f"dizisi ama bildiğim hiçbir şeye bağlı değil. Anlamsız bir nokta.")


class GroundingCertifier:
    """Topraklama eksenini hesaplar: token bilinen referanslara bağlı mı?"""

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ── Doğrudan topraklama: TAU düğüm + kenar ───────────────────────────────

    def _direct_grounding(self, token: str) -> tuple[bool, int]:
        """Token doğrudan TAU'da köklü mü? (manifoldda_mı, toplam_kenar)."""
        tau = self.engine.tau
        edges_out = len(tau.edges.get(token, []))
        edges_in = 0
        for _src, edge_list in tau.edges.items():
            for e in edge_list:
                if e.target == token:
                    edges_in += 1
        in_manifold = token in self.engine.manifold.concepts
        return in_manifold, edges_out + edges_in

    # ── Rezonans topraklama: komşuluğun topraklanmışlığı + tutarlılığı ────────

    def _resonance_grounding(
        self, concept: "Concept",
    ) -> tuple[int, float, str, list[str]]:
        """Bilinmeyen token için: köklü, tutarlı bir kümeye mi düşüyor?

        SADECE rezonans yarıçapı içindeki köklü komşular sayılır. Doymuş
        manifoldda her nokta bir komşuya yakındır; sıkı yarıçap olmadan
        rastgele çöp de "topraklı" çıkar. Yarıçap gürültüyü eler.

        Döner: (sıkı_köklü_komşu, domain_tutarlılığı, baskın_domain, köklü_komşular)
        """
        neighbors = self.engine.manifold.nearest(concept, n=_RESONANCE_K)
        if not neighbors:
            return 0, 0.0, "yok", []

        tau = self.engine.tau
        grounded: list[str] = []
        domain_counts: dict[str, int] = {}

        for name, dist in neighbors:
            if float(dist) > _RESONANCE_RADIUS:
                continue  # yarıçap dışı — rezonans değil
            # komşunun kendi topraklanmışlığı: kaç kenarı var?
            n_edges = len(tau.edges.get(name, []))
            if n_edges >= _GROUNDED_NEIGHBOR_MIN_EDGES:
                grounded.append(name)
                c = self.engine.manifold.concepts.get(name)
                dom = (c.domain if c else None) or "general"
                domain_counts[dom] = domain_counts.get(dom, 0) + 1

        if not grounded:
            return 0, 0.0, "yok", []

        dominant_domain = max(domain_counts, key=domain_counts.get)
        coherence = domain_counts[dominant_domain] / len(grounded)
        return len(grounded), coherence, dominant_domain, grounded

    # ── Birleşik yargı ────────────────────────────────────────────────────────

    def certify(self, token: str, moments: list | None = None) -> GroundingCertificate:
        """Bir token'ın topraklama sertifikasını üret.

        moments verilmezse token encode edilir. Yargı: doğrudan köklülük VEYA
        tutarlı köklü kümeye rezonans → GROUNDED.
        """
        from tantrium.core.semantic import Concept

        in_manifold, direct_edges = self._direct_grounding(token)

        # Moment imzasını al (verilmemişse encode et)
        if moments is None:
            obj = self.engine.encoder.encode(token, name=token)
            moments = list(obj.moments)

        probe = Concept(name=f"_grounding_probe::{token}", moments=moments, domain="_probe")
        g_neighbors, coherence, dom, grounded_names = self._resonance_grounding(probe)

        # ── Yargı mantığı ──
        # 1. Doğrudan köklü düğüm → kesin GROUNDED (sistem bu token'ı öğrenmiş)
        if direct_edges >= _GROUNDED_NEIGHBOR_MIN_EDGES:
            verdict = "GROUNDED"
            score = min(1.0, 0.6 + direct_edges / 100.0)
        # 2. Bilinmeyen token: sıkı yarıçapta köklü + tutarlı kümeye rezonans
        elif g_neighbors >= _RESONANCE_MIN_GROUNDED and coherence >= _COHERENCE_MIN_RATIO:
            verdict = "GROUNDED"
            score = 0.4 + 0.4 * coherence
        # 3. Tek bir köklü komşuya yakın — zayıf, anlamı belirsiz
        elif g_neighbors >= 1:
            verdict = "WEAKLY_GROUNDED"
            score = 0.2 + 0.2 * coherence
        # 4. Yalıtık — yapısal geçerli ama hiçbir köklü kavrama yakın değil
        else:
            verdict = "UNGROUNDED"
            score = 0.0

        return GroundingCertificate(
            token=token,
            verdict=verdict,
            direct_edges=direct_edges,
            in_manifold=in_manifold,
            grounded_neighbors=g_neighbors,
            neighbor_coherence=coherence,
            dominant_domain=dom,
            nearest_grounded=grounded_names[:5],
            score=round(score, 3),
        )
