"""İlişkisel kodlayıcı — kavramın TAU topolojisini moment imzasına çevirir.

Mimarinin kurucu tezi (`graph/knowledge_graph.py`): "Bilgi node'da değil EDGE'de.
Topoloji = bilgi." Bir kelimenin anlamı harflerinde değil, TAU'daki ilişki
komşuluğundadır. Bu transducer o komşuluğu okur — molekülün bağ-grafı için
yapılanın AYNISI: graf → A → G=AᵀA → eigenvalue-normalize → μ_k ∈ [0,1].

Yüzey kodlaması (encoder._text_to_signature_moments) "nasıl yazılıyor"u okur;
bu kodlama "ne demek"i okur. İki kanal: yüzey + anlam.

DÜRÜST SINIR (gerçek grafla doğrulanmış): anlam, ilişki-çıkarımının kalitesi
kadar keskin. Yoğun-temiz komşulukta güçlü (intelligence~reasoning), seyrek/
jenerik-hub kavramlarda zayıf. IDF (ters-derece) ağırlık jenerik hub'ları
(consciousness/knowledge gibi herkesin bağlandığı) bastırır ama gürültüyü
tamamen elemez. Darboğaz matematik DEĞİL, graf yoğunluğu — büyüdükçe keskinleşir.
"""
from __future__ import annotations

import math
from fractions import Fraction

import numpy as np

from tantrium.core.codex import CertifiableObject as CodexObject
from tantrium.core.encoder import (
    _DEFAULT_ENCODER,
    _gram,
    _sequence_to_hankel_matrix,
)

# Anlam taşıyan tipli kenarlar — geometrik (ALEPH/SPECTRAL_BRIDGE) HARİÇ.
# Geometrik kenarlar moment-yakınlığından doğar (doygun manifoldda gürültü);
# tipli kenarlar gerçek ilişkidir (relations.extract_relations + ingest üçlüleri).
_SEMANTIC_PARADIGMS = frozenset({
    "IS_A", "USES", "REQUIRES", "ACHIEVES", "COMPOSED",
    "DEFINES", "INHIBITS", "CAUSES", "ACTIVATES", "TARGETS", "BINDS",
    # Kesin biyokimyasal yüklemler (gramatik zenginleştirme — çöküş yok)
    "REGULATES", "PHOSPHORYLATES", "EXPRESSES", "ENCODES",
    # Multi-modal ve kausal zincir paradigmaları (atom→DNA→elma)
    "COMPONENT_OF", "HAS_SIGNAL", "HAS_COMPOUND", "HAS_IMAGE",
    # Çok-boyutlu grounding: DNA + geometri + topoloji + yasa (elma = tüm boyutlar)
    "HAS_DNA", "HAS_GEOMETRY", "HAS_TOPOLOGY", "IS_GOVERNED_BY",
})

_MAX_NEIGHBORS = 24       # alt-graf kenarı ≤ 25 → eigvalsh O(n³) hızlı
_MIN_NEIGHBORS = 2        # bunun altında topraksız — None (caller yüzeye düşer)


class TopologyEncoder:
    """Kavram → TAU komşuluk-Laplacian spektrumu → moment imzası.

    `engine.tau` (KnowledgeGraph) üzerinde çalışır. Semantik in-derece bir kez
    hesaplanır (IDF için) ve cache'lenir.
    """

    def __init__(self, engine) -> None:
        self.engine = engine
        self._indeg: dict[str, int] | None = None

    def _semantic_indegree(self) -> dict[str, int]:
        """Her hedefe kaç kavramın tipli kenarla işaret ettiği = jeneriklik.

        Yüksek in-derece = jenerik hub (consciousness ~2148) = düşük ayırt-edicilik.
        IDF ağırlığı bunu bastırır.
        """
        if self._indeg is None:
            indeg: dict[str, int] = {}
            for elist in self.engine.tau.edges.values():
                for e in elist:
                    if e.paradigm in _SEMANTIC_PARADIGMS:
                        indeg[e.target] = indeg.get(e.target, 0) + 1
            self._indeg = indeg
        return self._indeg

    def _idf(self, target: str) -> float:
        d = self._semantic_indegree().get(target, 1)
        return 1.0 / math.log(d + 1.5)

    def neighborhood(self, name: str, max_neighbors: int = _MAX_NEIGHBORS
                     ) -> list[tuple[str, float]]:
        """En ayırt-edici (en yüksek IDF) tipli komşular — top-K."""
        weighted: dict[str, float] = {}
        for e in self.engine.tau.edges.get(name, []):
            if e.paradigm in _SEMANTIC_PARADIGMS and e.target != name:
                w = self._idf(e.target)
                if w > weighted.get(e.target, 0.0):
                    weighted[e.target] = w
        return sorted(weighted.items(), key=lambda kv: -kv[1])[:max_neighbors]

    def _subgraph_matrix(self, name: str, top: list[tuple[str, float]]) -> np.ndarray:
        """İndüklenmiş alt-graf adjacency: merkez + komşular + komşu-içi kenarlar.

        Satır/sütun 0 = merkez kavram. A[0][i] = merkez↔komşu IDF ağırlığı.
        A[i][j] = komşu i↔j tipli kenarı varsa IDF ağırlığı (küme-şekli sinyali).
        Spektrum hem komşuluğun ayırt-edicilik profilini hem iç küme yapısını taşır.
        """
        neigh = [t for t, _ in top]
        idx = {t: i + 1 for i, t in enumerate(neigh)}
        nset = set(neigh)
        n = len(neigh) + 1
        A = np.zeros((n, n), dtype=np.float64)
        for t, w in top:
            A[0][idx[t]] = w
            A[idx[t]][0] = w
        # Komşu-içi bağlantılar (kümenin şekli)
        for t in neigh:
            for e in self.engine.tau.edges.get(t, []):
                if (e.paradigm in _SEMANTIC_PARADIGMS
                        and e.target in nset and e.target != t):
                    w = self._idf(e.target)
                    i, j = idx[t], idx[e.target]
                    if w > A[i][j]:
                        A[i][j] = w
                        A[j][i] = w
        return A

    def encode(self, name: str, *, max_neighbors: int = _MAX_NEIGHBORS
               ) -> CodexObject | None:
        """Kavram → ilişkisel CodexObject. Yetersiz komşulukta None.

        Momentler [0,1] Hausdorff (SMILES/algı/yüzey ile aynı rejim) → manifold
        karşılaştırılabilir. structure["modality"]="relational".
        """
        top = self.neighborhood(name, max_neighbors)
        if len(top) < _MIN_NEIGHBORS:
            return None
        A = self._subgraph_matrix(name, top)
        moments, structure = _moments_and_structure(A, f"⟨topo:{name}⟩", name)
        structure["modality"] = "relational"
        structure["n_neighbors"] = len(top)
        structure["neighbors"] = [t for t, _ in top]
        structure["encoder"] = "topological_spectral"
        return CodexObject(name=name, moments=moments, structure=structure)


# ─── Transducer çekirdeği (perception/encode.py deseniyle birebir) ────────────

def _hausdorff_moments(A: np.ndarray, num_moments: int):
    """G=AᵀA eigenvalue'larını [0,1]'e normalize → μ_k = ort(λ^k).

    SMILES/algı ile AYNI rejim: μ₀=1, μ_k ∈ [0,1]. _EPS uniform harman →
    seyrek alt-grafta bile Hankel-PSD (ALEPH geçer), float→Fraction yuvarlamasına dayanır.
    """
    G = A.T @ A
    eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
    max_eig = float(eigs.max()) or 1.0
    norm = sorted((eigs / max_eig).tolist())
    nv = len(norm)
    _EPS = 0.02
    moments = [Fraction(1)]
    for k in range(1, num_moments):
        emp = sum(d ** k for d in norm) / nv
        uni = 1.0 / (k + 1)
        mk = (1.0 - _EPS) * emp + _EPS * uni
        moments.append(Fraction(float(mk)).limit_denominator(10 ** 9))
    return moments, sorted(norm, reverse=True)


def _moments_and_structure(A_np: np.ndarray, raw_input, name: str):
    """İlişkisel matris A → (moments, structure). Yapı için momentlerden küçük
    Hankel (exact Fraction determinant patlamasını atla — algı deseniyle aynı)."""
    moments, norm_eigs = _hausdorff_moments(A_np, _DEFAULT_ENCODER.num_moments)
    A_small = _sequence_to_hankel_matrix(moments)
    G_small = _gram(A_small)
    structure = _DEFAULT_ENCODER._extract_structure(raw_input, A_small, G_small, moments)
    structure["eigenvalues"] = norm_eigs
    structure["eigenvalue_source"] = "topological_gram"
    structure.update({
        "matrix_size": int(A_np.shape[0]),
        "num_moments": _DEFAULT_ENCODER.num_moments,
    })
    return moments, structure
