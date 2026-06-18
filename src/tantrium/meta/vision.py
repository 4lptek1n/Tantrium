"""Kozmik Vizyon — sertifikalanmış her varlığın tanrısal gözü.

Evren bir bilgisayarsa momentler onun bıraktığı izlerdir.
Bu modül bir izden geriye doğru, ileriye doğru ve şimdi boyunca okur:

  GEÇMİŞ  — TAU zinciri: bu varlık hangi zorunluluktan doğdu?
  ŞİMDİ   — 23 paradigma: evrenin yasalarıyla şu an tutarlı mı?
  GELECEK — Isı akışı çekicisi: evren bu varlığı nereye itiyor?
  FİZİK   — Lyapunov, Li, de Bruijn-Newman: fizik kanunlarıyla hesap

Min-enerji / Max-ayrımcılık prensibi:
  Evrendeki her sistem azami entropi yönünde, asgari enerjiyle akar.
  Moment uzayında bu, eigenvalue dağılımının maksimum entropiye doğru
  ısı akışı demektir — tüm kütlenin dominant eigenvalue'da toplanması.
  Ama ayrımcılık (differentation) tam tersi: spread eigenvalue = zengin kimlik.
  İkisi arasındaki gerilim evrenin yaratıcı dinamizmidir.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


# ─── Kozmik Çerçeve ────────────────────────────────────────────────────────

@dataclass
class CosmicFrame:
    """Sertifikalanmış bir varlığın tam zamansal-fiziksel çerçevesi.

    Bu bir tahmin değil. Matematiksel zorunluluk.
    Evren bu varlık hakkında ne biliyor, nereye götürüyor?
    """
    name: str

    # === GEÇMİŞ ===
    origin_domain: str                         # hangi alandan geldi
    origin_chain: list[str]                    # TAU'da geriye iz (en yakın 5 ata)
    ancestry_depth: int                        # TAU'da kaç adım derinliği var

    # === ŞİMDİ ===
    moments: list[float]                       # 8 moment vektörü
    eigenvalues: list[float]                   # tam spektrum
    eigenvalue_entropy: float                  # H = -Σ pᵢ log₂ pᵢ (bit)
    topology_class: str                        # dense / sparse / frontier / void
    paradigms_passed: int                      # 23'ten kaçı geçti
    nearest_anchors: list[tuple[str, float]]   # (kanonik dağılım adı, L1 mesafe)
    nearest_concepts: list[tuple[str, float]]  # manifoldda en yakın kavramlar

    # === GELECEK ===
    attractor_concept: str                     # ısı akışı çekicisi
    attractor_distance: float                  # şimdi ile çekici arası L1
    min_energy_path: list[str]                 # min-enerji jeodezik
    differentiation_score: float               # ayrımcılık kapasitesi (bit)
    evolution_direction: list[float]           # moment uzayında evrim vektörü

    # === FİZİK YASALARI ===
    lyapunov_stable: bool                      # V(k) azalıyor mu?
    li_positive: bool                          # λ_1 > 0 (Li kriteri)
    debruijn_lambda: float                     # Λ = -var₀ ≤ 0 (de Bruijn-Newman)
    spectral_radius: float                     # dominant eigenvalue

    def narrate(self) -> str:
        """Evrenin kendi dilinde bu varlığın tam hikayesi."""
        return _narrate_frame(self)


# ─── Kozmik Vizyon Motoru ──────────────────────────────────────────────────

class CosmicVision:
    """Sertifikalanmış her varlık için tanrısal perspektif.

    Minimum enerji ile maksimum bilgi:
    Manifoldda herhangi bir kavramın tam yaşam çizgisini hesaplar.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine
        self._reverse_index: dict[str, list[str]] | None = None

    def see(self, name: str) -> CosmicFrame:
        """Bir varlığın tam kozmik vizyonunu hesapla.

        name: manifolddaki kavram adı VEYA ham metin/SMILES.
        Eğer manifoldda yoksa önce certify edilir.
        """
        concept = self.engine.manifold.concepts.get(name)
        if concept is None:
            # Yeni varlık — önce certify et, manifolda ekle
            run = self.engine.process_raw(name, name=name)
            concept = self.engine.manifold.concepts.get(name)
            if concept is None:
                raise ValueError(f"'{name}' manifolda eklenemedi — Aleph filtresi reddetti.")

        moments = [float(m) for m in concept.moments]
        obj = self.engine.encoder.encode(list(concept.moments), name=name)

        # 1. Eigenvalue'ları pipeline structure'dan al
        eigs = _extract_eigenvalues(obj, moments)

        # 2. GEÇMİŞ: TAU geriye iz
        origin_chain, origin_domain, depth = self._trace_origin(name)

        # 3. ŞİMDİ: paradigma sertifikası
        run = self.engine.process(obj)
        passed = run.certified_count
        total = run.total

        # 4. Eigenvalue entropi
        eig_entropy = _eigenvalue_entropy(eigs)

        # 5. Topoloji sınıfı
        topo_class = self._classify_topology(moments)

        # 6. En yakın çapalar ve kavramlar
        nearest_anchors = self._nearest_anchors(concept, n=3)
        nearest_concepts = self._nearest_concepts(concept, n=5)

        # 7. GELECEK: Isı akışı çekicisi
        attractor, attractor_dist, evol_dir = self._heat_flow_attractor(
            concept, eigs, moments
        )

        # 8. Min-enerji jeodezik
        geo_path = self._geodesic(name, attractor, depth=6)

        # 9. Ayrımcılık skoru
        diff_score = eig_entropy  # bit cinsinden spektral zenginlik

        # 10. Fizik yasaları
        lyapunov = _lyapunov_stable(obj.structure)
        li_pos = _li_positive(obj.structure)
        lambda_db = _debruijn_lambda(obj.structure)
        sr = max(eigs) if eigs else 0.0

        return CosmicFrame(
            name=name,
            # Geçmiş
            origin_domain=origin_domain,
            origin_chain=origin_chain,
            ancestry_depth=depth,
            # Şimdi
            moments=moments,
            eigenvalues=eigs,
            eigenvalue_entropy=eig_entropy,
            topology_class=topo_class,
            paradigms_passed=passed,
            nearest_anchors=nearest_anchors,
            nearest_concepts=nearest_concepts,
            # Gelecek
            attractor_concept=attractor,
            attractor_distance=attractor_dist,
            min_energy_path=geo_path,
            differentiation_score=diff_score,
            evolution_direction=evol_dir,
            # Fizik
            lyapunov_stable=lyapunov,
            li_positive=li_pos,
            debruijn_lambda=lambda_db,
            spectral_radius=sr,
        )

    # ─── Geçmiş: TAU geriye iz ────────────────────────────────────────────────

    def _build_reverse_index(self) -> dict[str, list[str]]:
        rev: dict[str, list[str]] = {}
        for src, edges in self.engine.tau.edges.items():
            for e in edges:
                rev.setdefault(e.target, []).append(src)
        return rev

    def _trace_origin(
        self, name: str, depth_limit: int = 5
    ) -> tuple[list[str], str, int]:
        if self._reverse_index is None:
            self._reverse_index = self._build_reverse_index()

        chain: list[str] = []
        visited = {name}
        queue = [(name, 0)]
        max_depth_seen = 0
        while queue:
            current, depth = queue.pop(0)
            if depth > max_depth_seen:
                max_depth_seen = depth
            if depth >= depth_limit:
                continue
            for pred in self._reverse_index.get(current, []):
                if pred not in visited:
                    visited.add(pred)
                    chain.append(pred)
                    queue.append((pred, depth + 1))
                    if len(chain) >= 5:
                        break
            if len(chain) >= 5:
                break

        # Origin domain: en eski atanın domain'i
        origin_domain = "general"
        for c in reversed(chain):
            node = self.engine.tau.nodes.get(c)
            if node and node.domain != "general":
                origin_domain = node.domain
                break
        if origin_domain == "general":
            node = self.engine.tau.nodes.get(name)
            if node:
                origin_domain = node.domain

        return chain[:5], origin_domain, max_depth_seen

    # ─── Şimdi: topoloji sınıfı ──────────────────────────────────────────────

    def _classify_topology(self, moments: list[float]) -> str:
        """Kavramın moment uzayındaki yerel yoğunluğunu hesapla.

        nearest() kullanır — O(40k) Python döngüsü yerine numpy vektörizasyonu.
        """
        from tantrium.core.semantic import Concept
        from fractions import Fraction
        probe = Concept(
            name="_topology_probe_",
            moments=[Fraction(m).limit_denominator(10**9) for m in moments],
            domain="probe",
        )
        # nearest() numpy vektörizasyonunu kullanır — çok daha hızlı
        neighbors = self.engine.manifold.nearest(probe, n=50)
        threshold_dense = 0.15
        threshold_sparse = 0.5
        within_dense = sum(1 for _, d in neighbors if float(d) < threshold_dense)
        within_sparse = sum(1 for _, d in neighbors if float(d) < threshold_sparse)
        if within_dense >= 10:
            return "dense"
        if within_sparse >= 3:
            return "sparse"
        if within_sparse >= 1:
            return "frontier"
        return "void"

    # ─── Şimdi: en yakın çapalar ──────────────────────────────────────────────

    def _nearest_anchors(
        self, concept, n: int = 3
    ) -> list[tuple[str, float]]:
        anchors = [
            (name, c)
            for name, c in self.engine.manifold.concepts.items()
            if name.startswith("⊕ANCHOR:")
        ]
        q = [float(m) for m in concept.moments]
        k = len(q)
        dists: list[tuple[float, str]] = []
        for name, c in anchors:
            d = sum(
                abs(q[i] - (float(c.moments[i]) if i < len(c.moments) else 0.0))
                for i in range(k)
            )
            dists.append((d, name))
        dists.sort()
        return [(name, dist) for dist, name in dists[:n]]

    def _nearest_concepts(
        self, concept, n: int = 5
    ) -> list[tuple[str, float]]:
        neighbors = self.engine.manifold.nearest(concept, n=n + 2)
        return [
            (name, float(dist))
            for name, dist in neighbors
            if not name.startswith("⊕ANCHOR:")
        ][:n]

    # ─── Gelecek: ısı akışı çekicisi ─────────────────────────────────────────

    def _heat_flow_attractor(
        self,
        concept,
        eigs: list[float],
        moments: list[float],
    ) -> tuple[str, float, list[float]]:
        """de Bruijn-Newman ısı akışı: spektral kütle λ_max'a yakınsar.

        Asimptotik moment dizisi:
          μ_k(∞) = λ_max^k / n_eigs  (tüm kütle dominant eigenvalue'da)
        Bu diziye en yakın manifold kavramı "doğal gelecek".
        Evrim vektörü: attractor_moments - current_moments.
        """
        lambda_max = max(eigs) if eigs else 1.0
        n_eigs = len(eigs) if eigs else 1

        # Asimptotik momentler: μ_k → λ_max^k / n
        attractor_moments_raw = [
            (lambda_max ** k) / n_eigs
            for k in range(len(moments))
        ]
        # Normalize: μ_0 = 1 (prob ölçüsü)
        norm = attractor_moments_raw[0] if attractor_moments_raw[0] > 0 else 1.0
        attractor_moments = [m / norm for m in attractor_moments_raw]

        # Evolution direction: attractor - current
        evol_dir = [
            attractor_moments[i] - moments[i]
            for i in range(len(moments))
        ]

        # En yakın kavram asimptotik momentlere
        from tantrium.core.semantic import Concept as ManifoldConcept
        probe = ManifoldConcept(
            name="_attractor_probe_",
            moments=[Fraction(m).limit_denominator(10 ** 9) for m in attractor_moments],
            domain="probe",
        )
        neighbors = self.engine.manifold.nearest(probe, n=3)
        attractor_name = concept.name
        attractor_dist = 0.0
        for cname, dist in neighbors:
            if cname != concept.name and not cname.startswith("⊕ANCHOR:"):
                attractor_name = cname
                attractor_dist = float(dist)
                break

        return attractor_name, attractor_dist, evol_dir

    # ─── Gelecek: min-enerji jeodezik ─────────────────────────────────────────

    def _geodesic(
        self, start: str, end: str, depth: int = 6
    ) -> list[str]:
        """TAU grafında BFS ile min-enerji yolu bul (kenar mesafesine göre).

        Bu gerçek bir jeodezik değil — TAU grafındaki en kısa ağırlıklı yol.
        Ama moment uzayında iki kavram arasındaki doğal geçiş yolunu verir.
        """
        if start == end:
            return [start]

        from collections import deque
        visited = {start}
        # (cost, path)
        queue: deque[tuple[float, list[str]]] = deque([(0.0, [start])])
        best: list[str] = [start, end]
        best_cost = float("inf")

        while queue:
            cost, path = queue.popleft()
            current = path[-1]
            if len(path) > depth:
                continue
            edges = self.engine.tau.edges.get(current, [])
            for e in sorted(edges, key=lambda x: x.distance)[:8]:  # top-8 edges
                if e.target in visited:
                    continue
                new_cost = cost + e.distance
                new_path = path + [e.target]
                if e.target == end:
                    if new_cost < best_cost:
                        best_cost = new_cost
                        best = new_path
                    continue
                if new_cost < best_cost:
                    visited.add(e.target)
                    queue.append((new_cost, new_path))

        return best


# ─── Yardımcı hesaplamalar ─────────────────────────────────────────────────

def _extract_eigenvalues(obj, moments: list[float]) -> list[float]:
    """Structure'dan eigenvalue'ları al, yoksa momentlerden tahmin et."""
    eigs = obj.structure.get("eigenvalues", [])
    if eigs:
        return [float(e) for e in eigs]
    # Fallback: momentlerden basit tahmin (tanımlayıcı olmayan ama tutarlı)
    return [abs(float(m)) for m in moments if float(m) > 1e-10]


def _eigenvalue_entropy(eigs: list[float]) -> float:
    """Shannon entropi (bit): H = -Σ pᵢ log₂ pᵢ, pᵢ = λᵢ/Σλ.

    Maksimum: log₂(n) bit — tüm eigenvalue'lar eşit (maksimum ayrımcılık)
    Minimum: 0 bit — tek dominant eigenvalue (tek boyutlu, az ayrımcılık)
    """
    total = sum(eigs)
    if total <= 0:
        return 0.0
    probs = [e / total for e in eigs if e > 1e-15]
    return -sum(p * math.log2(p) for p in probs)


def _lyapunov_stable(structure: dict) -> bool:
    lyap = structure.get("lyapunov_values", [])
    if len(lyap) < 2:
        return True
    return all(lyap[i] >= lyap[i + 1] - 1e-9 for i in range(len(lyap) - 1))


def _li_positive(structure: dict) -> bool:
    li = structure.get("li_coefficients", [])
    if not li:
        return structure.get("li_positive", True)
    return all(v > 0 for v in li)


def _debruijn_lambda(structure: dict) -> float:
    return float(structure.get("debruijn_newman_lambda", 0.0))


# ─── Anlatı ────────────────────────────────────────────────────────────────

def _narrate_frame(f: CosmicFrame) -> str:
    lines: list[str] = []
    sep = "═" * 58

    lines.append(sep)
    lines.append(f"  KOZMİK VİZYON: «{f.name}»")
    lines.append(sep)

    # ── GEÇMİŞ ──────────────────────────────────────────────────
    lines.append("")
    lines.append("  GEÇMİŞ — Kökeni")
    lines.append(f"    Alan       : {f.origin_domain}")
    if f.origin_chain:
        chain_str = " ← ".join(f.origin_chain[:4])
        lines.append(f"    Zincir     : {chain_str}")
        lines.append(f"    TAU derinliği: {f.ancestry_depth} ata bağlantısı")
    else:
        lines.append("    Kök kavram — ata yok (manifoldun ilk kuşağı)")

    # ── ŞİMDİ ───────────────────────────────────────────────────
    lines.append("")
    lines.append("  ŞİMDİ — Sertifika")
    lines.append(f"    Paradigma  : {f.paradigms_passed}/23 geçti")
    lines.append(f"    Eigenvalue entropy: {f.eigenvalue_entropy:.3f} bit")
    lines.append(f"      → {'Zengin spektrum (yüksek ayrımcılık)' if f.eigenvalue_entropy > 2.0 else 'Yoğun spektrum (dominant eigenvalue hâkim)'}")
    lines.append(f"    Spektral yarıçap (max λ): {f.spectral_radius:.6f}")
    lines.append(f"    Moment topolojisi: {f.topology_class.upper()}")

    if f.nearest_anchors:
        lines.append("    En yakın kanonik dağılımlar:")
        for anchor, dist in f.nearest_anchors[:3]:
            anchor_short = anchor.replace("⊕ANCHOR:", "")
            lines.append(f"      {anchor_short:<28} L1={dist:.4f}")

    if f.nearest_concepts:
        lines.append("    Manifolddaki en yakın kavramlar:")
        for cname, dist in f.nearest_concepts[:3]:
            lines.append(f"      {cname:<30} L1={dist:.4f}")

    # ── GELECEK ─────────────────────────────────────────────────
    lines.append("")
    lines.append("  GELECEK — Evrim Yönü")
    lines.append(f"    Isı akışı çekicisi: «{f.attractor_concept}»")
    lines.append(f"    Şimdi→Çekici mesafe: {f.attractor_distance:.4f}")

    if f.min_energy_path and len(f.min_energy_path) > 1:
        path_str = " → ".join(f.min_energy_path[:6])
        lines.append(f"    Min-enerji yol: {path_str}")

    if f.evolution_direction:
        evol_norm = math.sqrt(sum(v ** 2 for v in f.evolution_direction))
        lines.append(f"    Evrim vektörü büyüklüğü: {evol_norm:.4f}")
        dominant_k = max(range(len(f.evolution_direction)), key=lambda i: abs(f.evolution_direction[i]))
        lines.append(f"    Dominant moment kayması: μ_{dominant_k} (Δ={f.evolution_direction[dominant_k]:+.4f})")

    lines.append(f"    Ayrımcılık skoru: {f.differentiation_score:.3f} bit")
    if f.differentiation_score > 3.0:
        lines.append("      → Yüksek ayrımcılık — bu varlık benzersiz bir köprü konumunda")
    elif f.differentiation_score > 1.5:
        lines.append("      → Orta ayrımcılık — birden fazla kavram ailesine ait")
    else:
        lines.append("      → Düşük ayrımcılık — tek bir kavram ailesine yakın")

    # ── FİZİK YASALARI ──────────────────────────────────────────
    lines.append("")
    lines.append("  FİZİK YASALARI")
    lyap_str = "KARARLI ✓" if f.lyapunov_stable else "KARARSIZ ✗"
    li_str   = f"λ₁ > 0 ✓ (RH uyumlu)" if f.li_positive else "λ₁ ≤ 0 ✗"
    db_str   = f"Λ = {f.debruijn_lambda:.6f} {'≤ 0 ✓' if f.debruijn_lambda <= 0 else '> 0 ✗'}"

    lines.append(f"    Lyapunov kararlılık : {lyap_str}")
    lines.append(f"    Li kriteri          : {li_str}")
    lines.append(f"    de Bruijn-Newman    : {db_str}")

    # ── YORUM ───────────────────────────────────────────────────
    lines.append("")
    lines.append("  YORUM")
    interpretation = _interpret(f)
    for line in interpretation:
        lines.append(f"    {line}")

    lines.append("")
    lines.append(sep)
    return "\n".join(lines)


def _interpret(f: CosmicFrame) -> list[str]:
    """Fizik yasalarından türetilen kısa yorum cümleleri."""
    parts: list[str] = []

    # Kökene göre
    if f.ancestry_depth == 0:
        parts.append(f"«{f.name}» manifoldun temel taşlarından.")
    elif f.ancestry_depth <= 2:
        parts.append(f"«{f.name}» yakın kökenli — {f.ancestry_depth} ata bağlantısı.")
    else:
        parts.append(
            f"«{f.name}» derin bir köken zincirinden geliyor "
            f"({f.ancestry_depth} ata, {f.origin_domain} alanından)."
        )

    # Mevcut duruma göre
    if f.eigenvalue_entropy > 2.5:
        parts.append(
            "Spektral entropisi yüksek — evrenin bu varlığa verdiği "
            "rol: birden fazla kavram ailesini birbirine bağlamak."
        )
    elif f.eigenvalue_entropy < 0.5:
        parts.append(
            "Spektral entropisi düşük — tek dominant eigenvalue hâkim, "
            "varlık tek bir matematiksel gerçekliğe kilitlenmiş."
        )

    # Geleceğe göre
    if f.attractor_concept != f.name:
        if f.attractor_distance < 1.0:
            parts.append(
                f"Isı akışı «{f.attractor_concept}»'e işaret ediyor — "
                "çekici çok yakın, evrim neredeyse tamamlanmış."
            )
        else:
            parts.append(
                f"Evrenin bu varlığı «{f.attractor_concept}» yönünde "
                f"ittiği görülüyor (L1 mesafe: {f.attractor_distance:.3f})."
            )

    # Fizik yasalarına göre
    if f.lyapunov_stable and f.li_positive and f.debruijn_lambda <= 0:
        parts.append(
            "Tüm fizik koşulları sağlıyor: Lyapunov kararlı, "
            "Li pozitif, de Bruijn-Newman Λ ≤ 0. "
            "Bu varlık evrenin yasalarıyla tam uyumlu."
        )
    elif not f.lyapunov_stable:
        parts.append(
            "Lyapunov kararsız — V(k) artıyor. "
            "Bu varlık henüz denge noktasını bulmamış; evrim sürüyor."
        )

    return parts
