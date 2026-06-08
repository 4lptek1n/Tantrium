"""TAU Ağı — Tantrium L2: Tau/Hankel Kernel.

SemanticManifold'un yerini alır. Fark:
  - Manifold: 6748 kavram × 8 moment vektör = 1425 KB (flat, bağımsız)
  - KnowledgeGraph:  6748 node × 1 float (sr) + sparse edges = ~200 KB (ağ topolojisi)

Her kavram bağımsız bir vektör değil — TAU ağında bir node.
Bilgi node'da değil, EDGE'de. Edge var → Hankel PSD → certified bağlantı.

DNA analojisi:
  - DNA atomları değil bağları saklar
  - KnowledgeGraph momentleri değil topolojiyi saklar
  - Encoder + kelime → moment (deterministik, her zaman yeniden üretilir)

Kuantum dolanıklık:
  - Bir node değişince bağlı tüm node'lar etkilenir
  - Edge'ler TAV fixed-point'i — sistem kapandığında ağ tutarlı
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.semantic import Concept, SemanticManifold


# ─── Node & Edge ──────────────────────────────────────────────────────────────

@dataclass
class KnowledgeNode:
    name: str
    domain: str = "general"
    source: str = "undefined"
    sr: float = 0.0   # spectral radius = μ_7 (dominant eigenvalue, 96% variance)


@dataclass
class KnowledgeEdge:
    source: str
    target: str
    distance: float
    paradigm: str = "ALEPH"  # certifying paradigm


# ─── TAU Graph ────────────────────────────────────────────────────────────────

class KnowledgeGraph:
    """Tau / Hankel Kernel ağı.

    Tantrium diyagramındaki L2 katmanının tam implementasyonu.
    Node = kavram kimliği + spektral yarıçap.
    Edge = PSD-certified Hankel bağlantısı.
    Topoloji = bilginin kendisi.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: dict[str, list[KnowledgeEdge]] = {}  # adjacency list
        self._sr_sorted: list[tuple[float, str]] = []  # hızlı nearest için (sr, name)
        self._dirty: bool = False

    # ─── Node operasyonları ───────────────────────────────────────────────────

    def add_node(self, concept: "Concept") -> None:
        """Kavramı node olarak ekle. Sadece isim + spektral yarıçap saklanır."""
        sr = float(concept.moments[-1]) if concept.moments else 0.0
        self.nodes[concept.name] = KnowledgeNode(
            name=concept.name,
            domain=concept.domain,
            source=concept.source,
            sr=sr,
        )
        self._dirty = True

    def _rebuild_sr_index(self) -> None:
        self._sr_sorted = sorted((n.sr, name) for name, n in self.nodes.items())
        self._dirty = False

    # ─── Edge operasyonları ───────────────────────────────────────────────────

    def certify_edge(
        self,
        a: "Concept",
        b: "Concept",
    ) -> KnowledgeEdge | None:
        """İki node arasındaki Hankel kernel'i sertifikala.

        Her iki kavram zaten ALEPH'ten geçti (manifold'dan geliyorlar).
        Joint PSD → dyadic transport var → edge certified.
        """
        from tantrium.core.semantic import moment_distance
        d = float(moment_distance(a, b))
        return KnowledgeEdge(
            source=a.name,
            target=b.name,
            distance=d,
            paradigm="ALEPH",
        )

    def add_edges_for(
        self,
        concept: "Concept",
        manifold: "SemanticManifold",
        k: int = 5,
    ) -> int:
        """Bir node için K yakın certified edge — sr-index ile O(√n)."""
        if self._dirty:
            self._rebuild_sr_index()
        q = [float(m) for m in concept.moments]
        klen = len(q)
        sr_q = q[-1] if q else 0.0
        candidates = self._sr_candidates(sr_q, window=min(200, len(self.nodes)))
        dists: list[tuple[float, str]] = []
        for cand_name in candidates:
            if cand_name == concept.name:
                continue
            cand = manifold.concepts.get(cand_name)
            if cand is None:
                continue
            d = sum(
                abs(q[i] - (float(cand.moments[i]) if i < len(cand.moments) else 0.0))
                for i in range(klen)
            )
            dists.append((d, cand_name))
        dists.sort()
        edges: list[KnowledgeEdge] = [
            KnowledgeEdge(source=concept.name, target=name, distance=d, paradigm="ALEPH")
            for d, name in dists[:k]
        ]
        self.edges[concept.name] = edges
        return len(edges)

    # ─── Nearest — 2 aşamalı hızlı arama ─────────────────────────────────────

    def nearest(
        self,
        name: str,
        k: int = 5,
        concept: "Concept | None" = None,
        manifold: "SemanticManifold | None" = None,
    ) -> list[tuple[str, float]]:
        """K en yakın certified komşuyu döndür.

        Bilinen node → pre-computed edge'lere bak (O(1)).
        Yeni kavram → spektral yarıçap filtresi → exact distance (O(√n)).
        """
        # Bilinen node: pre-computed
        if name in self.edges and self.edges[name]:
            edges = sorted(self.edges[name], key=lambda e: e.distance)
            return [(e.target, e.distance) for e in edges[:k]]

        # Yeni kavram: sr-tabanlı hızlı arama
        if concept is None or manifold is None:
            return []

        if self._dirty:
            self._rebuild_sr_index()

        sr_q = float(concept.moments[-1]) if concept.moments else 0.0

        # 1. Aşama: sr farkı en küçük olan adaylar (binary search ile)
        candidates = self._sr_candidates(sr_q, window=min(200, len(self.nodes)))

        # 2. Aşama: adaylar içinde exact distance
        from tantrium.core.semantic import moment_distance
        q_m = concept.moments
        k_len = len(q_m)

        dists: list[tuple[float, str]] = []
        for cand_name in candidates:
            if cand_name == name:
                continue
            cand = manifold.concepts.get(cand_name)
            if cand is None:
                continue
            d = sum(
                abs(float(q_m[i]) - (float(cand.moments[i]) if i < len(cand.moments) else 0.0))
                for i in range(k_len)
            )
            dists.append((d, cand_name))

        dists.sort()
        return [(n, d) for d, n in dists[:k]]

    def _sr_candidates(self, sr: float, window: int) -> list[str]:
        """Spektral yarıçapı en yakın `window` node'u döndür (binary search)."""
        if not self._sr_sorted:
            return list(self.nodes.keys())[:window]

        lo, hi = 0, len(self._sr_sorted)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._sr_sorted[mid][0] < sr:
                lo = mid + 1
            else:
                hi = mid

        half = window // 2
        start = max(0, lo - half)
        end = min(len(self._sr_sorted), start + window)
        start = max(0, end - window)  # push start left if end was clipped
        return [name for _, name in self._sr_sorted[start:end]]

    # ─── Build from SemanticManifold ──────────────────────────────────────────

    @classmethod
    def build(
        cls,
        manifold: "SemanticManifold",
        k: int = 5,
        verbose: bool = True,
    ) -> "KnowledgeGraph":
        """Manifold'dan TAU ağı inşa et.

        Her node için K certified edge bulur.
        Bir kez çalıştır, kaydet — sonraki başlangıçlarda diskten yükle.
        """
        g = cls()

        # Tüm node'ları ekle
        for name, concept in manifold.concepts.items():
            g.add_node(concept)
        g._rebuild_sr_index()

        if verbose:
            print(f"  TAU: {len(g.nodes)} node eklendi. Edge'ler hesaplanıyor (k={k})...")

        total_edges = 0
        for i, (name, concept) in enumerate(manifold.concepts.items()):
            n_edges = g.add_edges_for(concept, manifold, k=k)
            total_edges += n_edges
            if verbose and (i + 1) % 1000 == 0:
                print(f"  {i+1}/{len(manifold.concepts)} node işlendi...")

        if verbose:
            print(f"  TAU: {total_edges} certified edge oluşturuldu.")

        return g

    # ─── Persistence ──────────────────────────────────────────────────────────

    def save(self, path: str) -> tuple[int, int]:
        """TAU ağını integer-ID formatında kaydet.

        String isimler yerine sayısal indeks — edge'ler [tgt_id, dist] çifti.
        Format:
          "n": [[name, domain_char, sr], ...]   ← node listesi (indeks = ID)
          "e": [[tgt_id, dist], ...]             ← her node'un edge listesi
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        names = list(self.nodes.keys())
        id_map = {name: i for i, name in enumerate(names)}

        # Domain tek harf: g=general, l=language, t=theorem, d=derived, q=query
        def _d(domain: str) -> str:
            return domain[0] if domain else "g"

        node_list = [
            [name, _d(self.nodes[name].domain), round(self.nodes[name].sr, 8)]
            for name in names
        ]

        # ALEPH: moment-distance certified (L2 Hankel kernel) — k=10, distance sorted
        # Semantic: pattern-extracted logical relationships (IS_A, USES, ACHIEVES, etc.)
        # L0 statistical (sentence co-occurrence, PPMI) is excluded.
        _SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED",
                     "SPECTRAL_BRIDGE"}
        # Paradigm → single-char code for compact storage
        _P = {"ALEPH": "A", "IS_A": "I", "USES": "U", "DEFINES": "D",
              "ACHIEVES": "V", "REQUIRES": "R", "COMPOSED": "C",
              "SPECTRAL_BRIDGE": "S"}
        edge_list: list[list] = []
        total_edges = 0
        for name in names:
            all_edges = self.edges.get(name, [])
            # ALEPH edges: geometric certified, keep k=10 closest
            aleph = [e for e in all_edges if e.paradigm == "ALEPH"]
            aleph.sort(key=lambda e: e.distance)
            aleph = aleph[:10]
            # Semantic edges: logically certified relationships
            semantic = [e for e in all_edges if e.paradigm in _SEMANTIC]
            combined = aleph + semantic
            edge_list.append(
                [[id_map[e.target], round(e.distance, 6), _P.get(e.paradigm, "A")]
                 for e in combined if e.target in id_map]
            )
            total_edges += len(combined)

        data = {"n": node_list, "e": edge_list}
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False, separators=(',', ':')),
            encoding="utf-8",
        )
        return len(names), total_edges

    @classmethod
    def load(cls, path: str) -> "KnowledgeGraph":
        """TAU ağını integer-ID formatından yükle. Eski string formatı da desteklenir."""
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        g = cls()

        # Yeni format: "n" ve "e" listeleri
        if "n" in data:
            domain_map = {"g": "general", "l": "language", "t": "theorem",
                          "d": "derived", "q": "query"}
            names: list[str] = []
            for row in data["n"]:
                name, d_char, sr = row[0], row[1], row[2]
                domain = domain_map.get(d_char, "general")
                g.nodes[name] = KnowledgeNode(name=name, domain=domain, source="saved", sr=sr)
                names.append(name)
            _P_REV = {"A": "ALEPH", "I": "IS_A", "U": "USES", "D": "DEFINES",
                      "V": "ACHIEVES", "R": "REQUIRES", "C": "COMPOSED",
                      "S": "SPECTRAL_BRIDGE"}
            for i, edge_rows in enumerate(data["e"]):
                src = names[i]
                g.edges[src] = [
                    KnowledgeEdge(
                        source=src,
                        target=names[row[0]],
                        distance=row[1],
                        paradigm=_P_REV.get(row[2] if len(row) > 2 else "A", "ALEPH"),
                    )
                    for row in edge_rows
                    if row[0] < len(names)
                ]
        # Eski format: "nodes" ve "edges" dict'leri
        elif "nodes" in data:
            for name, v in data["nodes"].items():
                g.nodes[name] = KnowledgeNode(
                    name=name,
                    domain=v.get("d", "general"),
                    source=v.get("s", "saved"),
                    sr=v.get("r", 0.0),
                )
            for name, edge_list in data.get("edges", {}).items():
                g.edges[name] = [
                    KnowledgeEdge(source=name, target=e["t"], distance=e["d"])
                    for e in edge_list
                ]

        g._rebuild_sr_index()
        return g

    # ─── Status ───────────────────────────────────────────────────────────────

    def summary(self) -> str:
        total_edges = sum(len(e) for e in self.edges.values())
        avg_deg = total_edges / max(len(self.nodes), 1)
        return (
            f"TAU GRAPH  |  {len(self.nodes)} node  |  "
            f"{total_edges} certified edge  |  "
            f"avg degree {avg_deg:.1f}  |  "
            f"topoloji = bilgi"
        )


