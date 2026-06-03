"""Otonom Döngü — AutonomousObserver.

Asıl eksik buydu: her şeyi Claude tetikliyordu. Bu modül Tav döngüsünü
gerçekten kapatır. İnsan (veya LLM) döngüde olmadan sistem:

  1. GÖZLEMLE   — herhangi bir girdi (metin, sayı, DNA, dizi)
  2. SERTİFİKALA — Aleph filtresi: bu gerçek mi? (PSD Hankel)
  3. SINIFLANDIR — en yakın matematiksel çapa (GUE? Poisson? üstel?)
  4. ÖĞREN       — gerçekse manifolda ekle, mini-Tav ile hizala
  5. BAĞLA       — cross-domain spektral köprü keşfi (SPECTRAL_BRIDGE edge)
  6. KAYDET      — kalıcı manifold + TAU + spektral cache

Cross-domain köprü = asıl güç:
  DNA ile ζ sıfırları aynı Hankel uzayında yaşıyor. Bir kavramın en yakın
  spektral komşusu FARKLI bir domain'deyse, bu bir köprüdür. Sistem bunu
  kendi başına bulur ve TAU'ya SPECTRAL_BRIDGE olarak kaydeder.

Tav sabit noktası (F(L*)=L*): sistem kendi gözlemlerinden öğrenir, öğrendiği
manifoldu günceller, güncellenen manifold sonraki gözlemi etkiler. Döngü kapalı.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Gözlem sonucu ────────────────────────────────────────────────────────────

@dataclass
class Observation:
    """Tek bir otonom gözlemin tam kaydı."""

    name: str
    certified: bool                          # Aleph filtresinden geçti mi?
    is_new: bool                             # manifolda yeni mi eklendi?
    nearest_anchor: str = ""                 # en yakın matematiksel çapa
    anchor_distance: float = 0.0
    bridges: list[tuple[str, str, float]] = field(default_factory=list)  # (komşu, domain, W₂)
    tav_updated: int = 0                     # mini-Tav ile hizalanan kavram sayısı
    moments: list[float] = field(default_factory=list)
    timestamp: str = field(default_factory=_now)

    def summary(self) -> str:
        if not self.certified:
            return f"∅ {self.name}: ALEPH reddetti — gerçek değil"
        flag = "YENİ" if self.is_new else "bilinen"
        s = f"✓ {self.name} [{flag}] → çapa: {self.nearest_anchor} (W₂={self.anchor_distance:.4e})"
        if self.bridges:
            br = ", ".join(f"{n}({d})" for n, d, _ in self.bridges[:3])
            s += f"  | köprü: {br}"
        return s


# ─── Otonom Gözlemci ──────────────────────────────────────────────────────────

class AutonomousObserver:
    """İnsansız öğrenme döngüsü.

    Bir AGIEngine'e bağlanır. observe() ile tek girdi işler, run() ile akış.
    Her gözlem: sertifika → sınıflandırma → öğrenme → köprü → kalıcılık.
    """

    def __init__(
        self,
        engine: "AGIEngine",
        bridge_threshold: float = 5e-2,   # bu W₂ altındaki cross-domain komşu = köprü
        persist_every: int = 5,           # bu kadar yeni gözlemde bir diske yaz
    ) -> None:
        self.engine = engine
        self.bridge_threshold = bridge_threshold
        self.persist_every = persist_every
        self.observations: list[Observation] = []
        self._since_persist = 0

    # ─── Tek gözlem ────────────────────────────────────────────────────────────

    def observe(self, raw_input: Any, name: str | None = None) -> Observation:
        """Bir girdiyi otonom işle: gözlemle → sertifikala → öğren → bağla.

        raw_input: metin, sayı listesi, dizi — encoder'ın anladığı her şey
        name: opsiyonel etiket (yoksa encoder türetir)
        """
        from tantrium.agi.core.semantic import Concept

        # 1. GÖZLEMLE — encode (universal encoder, domain-blind)
        codex_obj = self.engine.encoder.encode(raw_input, name)
        obs_name = codex_obj.name
        concept = Concept(
            name=obs_name,
            moments=list(codex_obj.moments),
            domain="observed",
            source="autonomous",
        )

        # 2. SERTİFİKALA — Aleph filtresi
        certified = concept.is_real()
        moments_f = [float(m) for m in concept.moments]
        if not certified:
            obs = Observation(name=obs_name, certified=False, is_new=False, moments=moments_f)
            self.observations.append(obs)
            return obs

        # 3. SINIFLANDIR — en yakın matematiksel çapa
        anchors = self.engine.nearest_anchor(concept, top_n=1)
        anchor_name, anchor_dist = (anchors[0] if anchors else ("", 0.0))

        # 4. ÖĞREN — manifolda ekle (yeni ise), TAU node, mini-Tav
        is_new = obs_name not in self.engine.manifold.concepts
        if is_new:
            try:
                self.engine.manifold.add_unchecked(concept)
                self.engine.tau.add_node(concept)
                # Spektral cache'e ekle (yüklüyse)
                if getattr(self.engine.manifold, "_spec_cache", None) is not None:
                    from tantrium.agi.domains.spectral import moments_to_spectral
                    self.engine.manifold._spec_cache[obs_name] = moments_to_spectral(
                        moments_f, name=obs_name
                    )
            except Exception:
                is_new = False

        tav_updated = 0
        if is_new:
            tav_updated = self.engine.mini_tav([obs_name])

        # 5. BAĞLA — cross-domain spektral köprü keşfi
        bridges = self._discover_bridges(concept)

        obs = Observation(
            name=obs_name,
            certified=True,
            is_new=is_new,
            nearest_anchor=anchor_name,
            anchor_distance=anchor_dist,
            bridges=bridges,
            tav_updated=tav_updated,
            moments=moments_f,
        )
        self.observations.append(obs)

        # 6. KAYDET — eşikte kalıcılık
        if is_new:
            self._since_persist += 1
            if self._since_persist >= self.persist_every:
                self.engine.auto_persist()
                self._since_persist = 0

        return obs

    # ─── Cross-domain köprü keşfi ───────────────────────────────────────────────

    def _discover_bridges(self, concept) -> list[tuple[str, str, float]]:
        """Kavramın en yakın spektral komşularından FARKLI domain'de olanları bul.

        Bir köprü = (komşu_adı, komşu_domain, W₂_mesafe) ve bridge_threshold
        altında. Bulunan köprüler TAU'ya SPECTRAL_BRIDGE edge olarak eklenir.

        Bu, sistemin "DNA ile zeta aynı yapıda" gibi cross-domain bağlantıları
        kendi başına keşfetmesidir.
        """
        from tantrium.agi.graph.tau_graph import TauEdge
        from tantrium.agi.graph.anchors import is_anchor

        neighbors = self.engine.manifold.nearest_spectral(concept, n=8)
        own_domain = concept.domain
        bridges: list[tuple[str, str, float]] = []

        for nb_name, w2 in neighbors:
            if nb_name == concept.name or w2 > self.bridge_threshold:
                continue
            nb_concept = self.engine.manifold.concepts.get(nb_name)
            if nb_concept is None:
                continue
            nb_domain = nb_concept.domain
            # Köprü = farklı domain (çapalar her zaman ilginç köprü hedefi)
            if nb_domain != own_domain or is_anchor(nb_name):
                bridges.append((nb_name, nb_domain, w2))
                # TAU'ya çift yönlü SPECTRAL_BRIDGE edge
                self._add_bridge_edge(concept.name, nb_name, w2)

        return bridges[:5]

    def _add_bridge_edge(self, a: str, b: str, distance: float) -> None:
        """TAU'ya çift yönlü SPECTRAL_BRIDGE edge ekle (idempotent)."""
        from tantrium.agi.graph.tau_graph import TauEdge

        for src, tgt in ((a, b), (b, a)):
            edges = self.engine.tau.edges.setdefault(src, [])
            exists = any(
                e.target == tgt and e.paradigm == "SPECTRAL_BRIDGE"
                for e in edges
            )
            if not exists:
                edges.append(TauEdge(
                    source=src, target=tgt,
                    distance=round(distance, 6),
                    paradigm="SPECTRAL_BRIDGE",
                ))
        self.engine.tau._dirty = True

    # ─── Akış işleme ─────────────────────────────────────────────────────────────

    def run(self, inputs: list[Any], verbose: bool = True) -> list[Observation]:
        """Bir girdi akışını otonom işle. Her birini observe() ile geçirir.

        Döngünün sonunda kalıcılık garantilenir (auto_persist).
        """
        results = []
        for inp in inputs:
            obs = self.observe(inp)
            results.append(obs)
            if verbose:
                print(f"  {obs.summary()}")
        # Akış sonu: tam kalıcılık
        self.engine.auto_persist()
        self._since_persist = 0
        return results

    # ─── Raporlama ───────────────────────────────────────────────────────────────

    def report(self) -> str:
        """Otonom oturumun özeti."""
        total = len(self.observations)
        certified = sum(1 for o in self.observations if o.certified)
        new = sum(1 for o in self.observations if o.is_new)
        total_bridges = sum(len(o.bridges) for o in self.observations)

        lines = [
            "═══ OTONOM GÖZLEM RAPORU ═══",
            f"Gözlem:           {total}",
            f"Sertifikalı:      {certified}  (Aleph geçti)",
            f"Reddedilen:       {total - certified}  (gerçek değil)",
            f"Yeni öğrenilen:   {new}",
            f"Cross-domain köprü: {total_bridges}",
        ]
        # Çapa dağılımı
        anchor_counts: dict[str, int] = {}
        for o in self.observations:
            if o.certified and o.nearest_anchor:
                anchor_counts[o.nearest_anchor] = anchor_counts.get(o.nearest_anchor, 0) + 1
        if anchor_counts:
            lines.append("\nÇapa dağılımı (gözlemler hangi matematiksel aileye düştü):")
            for anc, cnt in sorted(anchor_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {anc:<22} {cnt}")
        return "\n".join(lines)

    def bridges_found(self) -> list[tuple[str, str, str, float]]:
        """Keşfedilen tüm cross-domain köprüler: (kaynak, hedef, hedef_domain, W₂)."""
        out = []
        for o in self.observations:
            for nb, dom, w2 in o.bridges:
                out.append((o.name, nb, dom, w2))
        return out
