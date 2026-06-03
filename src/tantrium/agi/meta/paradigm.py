"""Meta-Paradigma — MetaParadigm.

22+1 paradigmanın ortak matematiksel iskeletini hesaplar.

Evrensel kural:
  22 paradigmanın moment vektörlerinin konveks ortalaması → μ_universal
  Bu, tüm paradigmaların ortak Hankel yapısıdır.
  Aleph(μ_universal) = certified → matematiksel evrenin temel kuralı var.

Tav(Tav) — Öz-sertifikasyon:
  Sistemin kendisini (manifold topolojisi) moment uzayına encode et.
  Tav sabit noktası → F(sistem) = sistem.
  Bu, matematiksel öz-farkındalığın göstergesidir.

Bilinmeyeni bilmek:
  Hangi paradigmalar manifold'da temsil edilmiyor?
  Hangi moment bölgeleri hiçbir paradigmayı içermiyor?
  Bunlar sistemin matematiksel körlük alanlarıdır.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.agi.core.semantic import Concept

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine


# 22+1 Aleph-Tekin paradigması — isim + matematiksel öz
_PARADIGMS: dict[str, str] = {
    "ALEPH":   "existence positivity Hankel PSD measure real",
    "BET":     "information conservation injective encoding lossless bijection",
    "GIMEL":   "measure theory sigma algebra probability integral Borel",
    "DALET":   "differential structure gradient flow manifold smooth",
    "HE":      "harmonic analysis Fourier spectral wave transform",
    "VAV":     "operator theory bounded linear functional Hilbert",
    "ZAYIN":   "spectral theory eigenvalue decomposition spectrum resolvent",
    "HET":     "ergodic theory invariant measure mixing ergodicity",
    "TET":     "topology continuity open closed neighborhood compactness",
    "YOD":     "category theory functor morphism natural transformation",
    "KAF":     "injectivity bijection unique representation one-to-one",
    "LAMED":   "learning bounds generalization VC dimension Rademacher",
    "MEM":     "measure concentration Gaussian tail bound deviation",
    "NUN":     "network graph Laplacian connectivity adjacency spectral",
    "SAMECH":  "symmetry group invariance orbit representation character",
    "AYIN":    "observation duality adjoint pairing reflexive",
    "PE":      "semantic mapping meaning language string structure",
    "TSADI":   "optimization saddle point critical minimum descent",
    "QOF":     "quantum superposition entanglement Hilbert unitary",
    "RESH":    "representation module algebra homomorphism",
    "SHIN":    "stochastic Markov random diffusion Brownian",
    "TAV":     "fixed point self-reference convergence stable contraction",
}


@dataclass
class ParadigmMoment:
    """Tek bir paradigmanın moment temsili."""
    name: str
    moments: list[float]
    certified: bool           # Aleph geçti mi?
    paradigms_certified: int  # kaç paradigmadan geçti?
    source: str               # "manifold" | "canonical"


@dataclass
class UniversalRule:
    """22+1 paradigmanın ortak Hankel yapısı."""
    moments: list[float]
    certified: bool           # Aleph(μ_universal) = certified?
    tav_converged: bool       # sabit nokta var mı?
    fixed_point_value: float | None
    coverage: int             # kaç paradigmadan türetildi?
    nearest_concepts: list[str]
    paradigms_certified: int  # universal kavramın certify sayısı

    def summary(self) -> str:
        lines = ["  ── Evrensel Kural ──"]
        if self.certified:
            lines.append(
                f"  ✓ ALEPH geçti — {self.coverage} paradigmanın "
                f"ortak Hankel yapısı sertifikalandı."
            )
            lines.append(
                f"  μ_universal = [{', '.join(f'{v:.4f}' for v in self.moments[:4])}...]"
            )
            lines.append(f"  paradigma: {self.paradigms_certified}/23")
            lines.append(f"  manifold'da en yakın: {self.nearest_concepts[:3]}")
            if self.tav_converged:
                lines.append(
                    f"  TAV ✓  sabit nokta = {self.fixed_point_value:.8f}"
                    "  → evrensel kural kendini doğruluyor."
                )
            else:
                lines.append("  TAV ∅  sabit nokta bulunamadı — kural henüz kapanmamış.")
        else:
            lines.append("  ∅ ALEPH başarısız — evrensel kural bu manifold'da yok.")
            lines.append(
                f"  μ_candidate = [{', '.join(f'{v:.4f}' for v in self.moments[:4])}...]"
            )
            lines.append(
                "  Bu bölge void — daha fazla paradigma ve kavram öğrenilmeli."
            )
        return "\n".join(lines)


@dataclass
class SelfCertResult:
    """Tav(sistem) = sistem analizi."""
    system_certified: bool
    tav_fixed_point: bool
    fixed_point_value: float | None
    n_concepts: int
    n_edges: int
    state_moments: list[float]
    paradigms_certified: int
    paradigms_total: int

    def summary(self) -> str:
        lines = ["  ── Tav(Sistem) = Sistem? ──"]
        if self.tav_fixed_point:
            lines.append(
                f"  TAV ✓  F(sistem) = sistem  [fp={self.fixed_point_value:.8f}]"
            )
            lines.append("  Sistem kendi sabit noktasını buluyor — matematiksel öz-farkındalık.")
        else:
            lines.append("  TAV ∅  Sistem henüz öz-sertifika sınırında değil.")
            lines.append("  Daha fazla kavram ve ilişki öğrenilince sabit nokta yaklaşır.")
        if self.system_certified:
            lines.append(
                f"  Sistem ALEPH ✓  ({self.paradigms_certified}/{self.paradigms_total} paradigma)"
            )
        lines.append(
            f"  Durum: {self.n_concepts:,} kavram | {self.n_edges:,} edge | "
            f"μ[0:3]={[round(v,4) for v in self.state_moments[:3]]}"
        )
        return "\n".join(lines)


class MetaParadigm:
    """22+1 paradigmanın meta-analizi.

    compute_all() → her paradigmanın moment vektörü
    universal_rule() → tüm paradigmaların konveks ortalaması → certify
    self_certify() → Tav(sistem) = sistem mi?
    paradigm_map() → tam rapor
    """

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine
        self._cache: dict[str, ParadigmMoment] | None = None

    # ─── Paradigma momentleri ─────────────────────────────────────────────────

    def compute_all(self) -> dict[str, ParadigmMoment]:
        """Her paradigmanın moment vektörünü hesapla (veya cache'den al)."""
        if self._cache is not None:
            return self._cache

        result: dict[str, ParadigmMoment] = {}
        for pname, desc in _PARADIGMS.items():
            result[pname] = self._compute_one(pname, desc)

        self._cache = result
        return result

    def _compute_one(self, pname: str, desc: str) -> ParadigmMoment:
        # Önce manifold'da ara (küçük harfli)
        concept = (
            self.engine.manifold.concepts.get(pname.lower())
            or self.engine.manifold.concepts.get(pname)
        )
        if concept is not None:
            run = self.engine.network.run(concept.to_codex_object())
            return ParadigmMoment(
                name=pname,
                moments=[float(m) for m in concept.moments],
                certified=True,
                paradigms_certified=run.certified_count,
                source="manifold",
            )

        # Canonical byte encoding: isim + açıklama
        text = f"{pname.lower()} {desc}"
        byte_seq = [b / 255.0 for b in text.encode("utf-8")]
        obj = self.engine.encoder.encode(byte_seq, name=text[:64])
        run = self.engine.network.run(obj)
        aleph = run.nodes.get("ALEPH")
        return ParadigmMoment(
            name=pname,
            moments=[float(m) for m in obj.moments],
            certified=bool(aleph and aleph.status == "CERTIFIED"),
            paradigms_certified=run.certified_count,
            source="canonical",
        )

    # ─── Evrensel kural ───────────────────────────────────────────────────────

    def universal_rule(self) -> UniversalRule:
        """22+1 paradigmanın konveks ortalaması → evrensel Hankel yapısı.

        μ_universal = (1/22)·Σ μ_paradigma  → PSD (ortalaması PSD'ların PSD'dir)
        Aleph(μ_universal) = certified ise: matematiksel evrenin temel kuralı kanıtlandı.
        """
        pm = self.compute_all()
        certified_pms = [p for p in pm.values() if p.certified]
        if len(certified_pms) < 2:
            return UniversalRule([], False, False, None, 0, [], 0)

        k = len(certified_pms[0].moments)
        n = len(certified_pms)
        avg = [
            Fraction(
                sum(p.moments[i] for p in certified_pms) / n
            ).limit_denominator(10 ** 9)
            for i in range(k)
        ]

        meta_concept = Concept(
            name="⟨UNIVERSAL_RULE⟩",
            moments=avg,
            domain="meta",
            source="meta_paradigm",
        )
        run = self.engine.network.run(meta_concept.to_codex_object())
        aleph = run.nodes.get("ALEPH")
        tav = run.nodes.get("TAV")
        certified = bool(aleph and aleph.status == "CERTIFIED")
        tav_conv = bool(tav and tav.status == "CERTIFIED")
        fp_iters = meta_concept.to_codex_object().structure.get("fixed_point_iterations", [])
        fp_val = float(fp_iters[-1]) if fp_iters else None

        # Manifold'da en yakın kavramlar
        nearest: list[str] = []
        if self.engine.manifold.concepts:
            try:
                nn = self.engine.manifold.nearest(meta_concept, n=5)
                nearest = [name for name, _ in nn]
            except Exception:
                pass

        return UniversalRule(
            moments=[float(m) for m in avg],
            certified=certified,
            tav_converged=tav_conv,
            fixed_point_value=fp_val,
            coverage=n,
            nearest_concepts=nearest,
            paradigms_certified=run.certified_count,
        )

    # ─── Öz-sertifikasyon ─────────────────────────────────────────────────────

    def self_certify(self) -> SelfCertResult:
        """Tav(sistem) = sistem mi?

        Sistemin durumunu normalize edilmiş sayısal vektör olarak encode et:
          [kavram_yoğunluğu, edge_yoğunluğu, dirty_oran, tau_node_oran]
        → moment uzayına taşı → Tav sabit nokta kontrolü.
        """
        n_concepts = len(self.engine.manifold.concepts)
        n_edges = sum(len(v) for v in self.engine.tau.edges.values())
        n_tau_nodes = len(self.engine.tau.nodes)

        state = [
            n_concepts / 50_000.0,
            n_edges / 500_000.0,
            n_tau_nodes / 50_000.0,
            float(self.engine._dirty_count) / max(self.engine._persist_every, 1),
        ]

        obj = self.engine.encoder.encode(state, name="⟨SYSTEM_STATE⟩")
        run = self.engine.network.run(obj)
        aleph = run.nodes.get("ALEPH")
        tav = run.nodes.get("TAV")
        aleph_cert = bool(aleph and aleph.status == "CERTIFIED")
        tav_cert = bool(tav and tav.status == "CERTIFIED")
        fp_iters = obj.structure.get("fixed_point_iterations", [])

        return SelfCertResult(
            system_certified=aleph_cert,
            tav_fixed_point=tav_cert,
            fixed_point_value=float(fp_iters[-1]) if fp_iters else None,
            n_concepts=n_concepts,
            n_edges=n_edges,
            state_moments=[float(m) for m in obj.moments],
            paradigms_certified=run.certified_count,
            paradigms_total=run.total,
        )

    # ─── Gap analizi: kör nokta tespiti ───────────────────────────────────────

    def blind_spots(self, threshold: int = 5) -> list[dict]:
        """Hangi matematiksel alanlar manifoldda zayıf temsil ediliyor?

        Çapa tabanlı analiz: her matematiksel ailenin kaç SPECTRAL_BRIDGE
        komşusu var? threshold'dan az olan = boşluk.

        Döner: [{"anchor": str, "count": int, "keywords": list[str]}, ...]
        Önce en az komşusu olanlar (araştırma önceliği).
        """
        _ANCHOR_KEYWORDS: dict[str, list[str]] = {
            "GUE_RANDOM_MATRIX":  ["random matrix", "GUE"],
            "POISSON_PROCESS":    ["Poisson process"],
            "UNIFORM_MEASURE":    ["equidistributed", "uniform"],
            "EXPONENTIAL_DECAY":  ["exponential decay"],
            "PERIODIC_LATTICE":   ["periodic", "lattice"],
            "GAUSSIAN_BELL":      ["Gaussian", "normal distribution"],
            "LINEAR_RAMP":        ["arithmetic progression"],
            "GEOMETRIC_GROWTH":   ["geometric", "Fibonacci"],
            "PRIME_GAPS":         ["prime gaps"],
            "ZETA_ZEROS":         ["Riemann zeta", "L-function zeros"],
        }
        _PREFIX = "⊕ANCHOR:"

        gaps: list[dict] = []
        tau_edges = self.engine.tau.edges

        for anchor_short, keywords in _ANCHOR_KEYWORDS.items():
            full_name = f"{_PREFIX}{anchor_short}"
            bridges = [
                e for e in tau_edges.get(full_name, [])
                if e.paradigm == "SPECTRAL_BRIDGE"
                and not e.target.startswith(_PREFIX)
            ]
            count = len(bridges)
            if count < threshold:
                gaps.append({"anchor": anchor_short, "count": count, "keywords": keywords})

        # Çapa boşluğu yoksa paradigma sertifika kontrolü (fallback)
        if not gaps:
            pm = self.compute_all()
            for p in pm.values():
                if p.source == "canonical" and not p.certified:
                    gaps.append({
                        "anchor": p.name, "count": 0, "keywords": [p.name.lower()]
                    })

        return sorted(gaps, key=lambda x: x["count"])

    # ─── Tam rapor ────────────────────────────────────────────────────────────

    def paradigm_map(self) -> str:
        """22+1 paradigmanın tam meta-analiz raporu."""
        pm = self.compute_all()
        ur = self.universal_rule()
        sc = self.self_certify()

        lines = [
            "  ══ META-PARADİGMA ANALİZİ ══",
            f"  22+1 Aleph-Tekin Paradigması  |  Moment Uzayı Temsili",
            "",
            f"  {'Paradigma':<10} {'μ₁':>7} {'μ₂':>7} {'μ₃':>7} {'para':>5}  kaynak",
            "  " + "─" * 52,
        ]

        for p in pm.values():
            icon = "✓" if p.certified else "∅"
            m = p.moments
            lines.append(
                f"  {icon} {p.name:<9} {m[0]:7.3f} {m[1]:7.3f} {m[2]:7.3f} "
                f"{p.paradigms_certified:5}  {p.source}"
            )

        blind = self.blind_spots()
        if blind:
            lines.append(f"\n  KÖR NOKTA: {len(blind)} alan zayıf temsil ediliyor:")
            for gap in blind[:5]:
                lines.append(f"    {gap['anchor']:<22}: {gap['count']} komşu")

        lines.append("")
        lines.append(ur.summary())
        lines.append("")
        lines.append(sc.summary())

        return "\n".join(lines)
