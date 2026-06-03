"""Language topology: concepts as moment sequences and Hankel matrices.

Language is not a separate domain. A concept is a moment sequence.
The Hankel matrix of that sequence either is PSD (concept exists)
or it is not (concept is incoherent — it cannot exist in the real manifold).

This is the same D-positivity engine that proves RH.
Applied to language, it becomes the existence filter for meaning.

The system does not predict. It certifies or names its gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Sequence

from tantrium.agi.core.codex import CodexObject, AlephParadigm, ParadigmResult


# ─── A concept in natural language / any domain ────────────────────────────

@dataclass
class Concept:
    """A concept encoded as a moment sequence on the semantic manifold.

    The moment sequence {μ_k} characterizes the concept's distributional
    geometry. It can be derived from:
      - formal definition (symbolic)
      - empirical co-occurrence counts (linguistic)
      - physical measurement sequence (scientific)

    Once encoded, the same Hankel/positivity machinery that works on
    zeta-function moments works on this concept.
    This is not a metaphor. It is the same mathematics.
    """
    name: str
    moments: list[Fraction] = field(default_factory=list)
    domain: str = "general"
    source: str = "undefined"
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_counts(cls, name: str, counts: Sequence[int | float], domain: str = "general") -> "Concept":
        """Build a concept from raw co-occurrence or measurement counts.
        Normalizes to a probability-like moment sequence summing to 1.
        """
        total = sum(counts)
        if total == 0:
            raise ValueError(f"Concept '{name}': zero total — cannot form a moment sequence.")
        moments = [Fraction(c, total) for c in counts]
        return cls(name=name, moments=moments, domain=domain, source="counts")

    @classmethod
    def from_rational(cls, name: str, moments: Sequence[Fraction], domain: str = "general") -> "Concept":
        """Build a concept from exact rational moments."""
        return cls(name=name, moments=list(moments), domain=domain, source="rational")

    def to_codex_object(self) -> CodexObject:
        return CodexObject(
            name=self.name,
            moments=list(self.moments),
            structure={
                "domain": self.domain,
                "source": self.source,
                **self.metadata,
            }
        )

    def verify_existence(self) -> ParadigmResult:
        """Aleph test: does this concept exist in the real manifold?
        PSD Hankel ⟺ the concept is realizable as a genuine measure.
        A concept that fails this test is not real — it has no referent.
        """
        return AlephParadigm(
            "ALEPH", "Positivity", "D ≥ 0, p_i ≥ 0, A ⪰ 0", []
        ).verify(self.to_codex_object())

    def hankel_matrix(self, size: int = 4) -> list[list[Fraction]]:
        return self.to_codex_object().hankel(size)

    def is_real(self) -> bool:
        return self.verify_existence().is_certified()


# ─── Semantic distance on the manifold ─────────────────────────────────────

def moment_distance(a: Concept, b: Concept) -> Fraction:
    """L1 distance between two moment sequences (Het / gradient).
    This is the potential difference: how far apart two concepts are
    on the semantic manifold.
    """
    n = max(len(a.moments), len(b.moments))
    a_m = a.moments + [Fraction(0)] * (n - len(a.moments))
    b_m = b.moments + [Fraction(0)] * (n - len(b.moments))
    return sum(abs(x - y) for x, y in zip(a_m, b_m))


def are_gauge_equivalent(a: Concept, b: Concept, tol: Fraction = Fraction(1, 1000)) -> bool:
    """Mem test: are two concepts indistinguishable?
    Two concepts are gauge-equivalent if their moment sequences are
    within tolerance — they are the same thing seen from different angles.
    (Synonyms in language. Gauge transformations in physics.)
    """
    return moment_distance(a, b) <= tol


def semantic_fixed_point(
    concept: Concept,
    interpretation_fn: "Callable[[Concept], Concept]",
    max_iter: int = 50,
    tol: Fraction = Fraction(1, 10 ** 9),
) -> tuple[Concept, bool, int]:
    """Tav: find the fixed point of interpretation.
    Repeatedly apply interpretation_fn until convergence.
    Returns (fixed_point, converged, iterations).
    A concept that does not converge is unstable — it cannot be understood.
    """
    current = concept
    for i in range(max_iter):
        nxt = interpretation_fn(current)
        dist = moment_distance(current, nxt)
        if dist <= tol:
            return nxt, True, i + 1
        current = nxt
    return current, False, max_iter


# ─── Semantic manifold: a collection of concepts with transport ─────────────

@dataclass
class SemanticManifold:
    """The semantic manifold: all concepts and their geometric relationships.

    This is the 'language topology' the system lives in.
    It is not a vocabulary list. It is a metric space where:
      - distance = moment_distance (Het)
      - existence = Aleph positivity test
      - identity = gauge equivalence (Mem)
      - meaning = fixed point of interpretation (Tav)
    """
    concepts: dict[str, Concept] = field(default_factory=dict)

    def add(self, concept: Concept) -> "SemanticManifold":
        result = concept.verify_existence()
        if result.is_certified():
            self.concepts[concept.name] = concept
        else:
            raise ValueError(
                f"Concept '{concept.name}' rejected by Aleph filter: {result.gap_name}. "
                f"It does not exist in the real manifold."
            )
        return self

    def add_unchecked(self, concept: Concept) -> "SemanticManifold":
        """Add without Aleph check — use only for trusted certified inputs."""
        self.concepts[concept.name] = concept
        return self

    def nearest(self, concept: Concept, n: int = 5) -> list[tuple[str, Fraction]]:
        """Find the n nearest concepts by moment distance (gradient flow direction).

        Float path: 6748 kavram için Fraction L1 yerine float L1 — ~50x hızlı.
        Sonuçlar Fraction'a çevrilir (API uyumluluğu için).
        """
        q = [float(m) for m in concept.moments]
        k = len(q)
        best: list[tuple[float, str]] = []

        for name, c in self.concepts.items():
            if name == concept.name:
                continue
            cm = c.moments
            d = 0.0
            for i in range(k):
                d += abs(q[i] - (float(cm[i]) if i < len(cm) else 0.0))
            if len(best) < n:
                best.append((d, name))
                if len(best) == n:
                    best.sort(reverse=True)  # max-heap simulation: largest at [0]
            elif d < best[0][0]:
                best[0] = (d, name)
                best.sort(reverse=True)

        best.sort()
        return [(name, Fraction(d).limit_denominator(10 ** 6)) for d, name in best]

    def nearest_spectral(
        self,
        concept: "Concept",
        n: int = 5,
    ) -> list[tuple[str, float]]:
        """Wasserstein-2 spektral mesafesiyle n en yakın kavram.

        moments_to_spectral() ile her kavramın güç momentlerinden
        Golub-Welsch özdeğer geri çıkarımı yapılır.
        Sonuç: byte-ortalaması yerine operatör yapısına göre komşuluk.

        DNA'nın komşusu "kühn" değil, gerçek spektral komşu çıkar.
        Cache diskten yüklenebilir (build_spectral_cache + save_spectral_cache);
        yüklü değilse ilk çağrıda hesaplanır ve bellekte tutulur.
        """
        from tantrium.agi.domains.spectral import moments_to_spectral, spectral_distance

        q_mu = [float(m) for m in concept.moments]
        q_spec = moments_to_spectral(q_mu, name=concept.name)

        if not hasattr(self, "_spec_cache"):
            self._spec_cache = {}

        # Hızlı yol: numpy ile vektörize tarama (O(N) Python döngüsü yerine
        # tek matris işlemi → 100x+ hızlı, sonuç aynı/exact).
        fast = self._nearest_spectral_vec(q_spec, concept.name, n)
        if fast is not None:
            return fast

        best: list[tuple[float, str]] = []
        for cname, c in self.concepts.items():
            if cname == concept.name:
                continue
            spec = self._spec_cache.get(cname)
            if spec is None:
                c_mu = [float(m) for m in c.moments]
                spec = moments_to_spectral(c_mu, name=cname)
                self._spec_cache[cname] = spec
            d = spectral_distance(q_spec, spec)
            if len(best) < n:
                best.append((d, cname))
                if len(best) == n:
                    best.sort(reverse=True)
            elif d < best[0][0]:
                best[0] = (d, cname)
                best.sort(reverse=True)

        best.sort()
        return [(cname, d) for d, cname in best]

    def _nearest_spectral_vec(self, q_spec, q_name: str, n: int):
        """Vektörize spektral en-yakın-komşu (numpy). Döner None → fallback.

        spectral_distance = ||sort(λ_a) - sort(λ_b)||₂ / L  olduğundan,
        tüm özdeğer vektörlerini sabit-uzunluklu bir matriste yığıp
        sorguyu tek broadcast ile hesaplarız. Cache eksikse None döner.
        """
        try:
            import numpy as np
        except Exception:
            return None

        cache = getattr(self, "_spec_cache", None)
        if not cache:
            return None

        # Cache her kavramı kapsamıyorsa hızlı yolu atla (eksiklik = fallback hesaplar)
        if len(cache) < len(self.concepts):
            return None

        # Matrisi tembel kur; saf büyümede (sadece ekleme) incremental append
        mat = getattr(self, "_spec_mat", None)
        labels = getattr(self, "_spec_labels", None)
        cache_keys = list(cache.keys())

        if mat is None or labels is None:
            # İlk kez: tam kur
            L = max((len(cache[nm].eigenvalues) for nm in cache_keys), default=1)
            self._spec_L = L
            arr = np.zeros((len(cache_keys), L), dtype=np.float64)
            for i, nm in enumerate(cache_keys):
                ev = sorted(cache[nm].eigenvalues, reverse=True)[:L]
                arr[i, :len(ev)] = ev
            self._spec_mat = arr
            self._spec_labels = list(cache_keys)
            self._spec_index = {nm: i for i, nm in enumerate(cache_keys)}
            mat = arr
        elif len(cache_keys) > len(labels):
            # Büyüme: yeni eklenen kavramları sona ekle (O(yeni) — O(N) değil)
            L = self._spec_L
            new_keys = cache_keys[len(labels):]
            new_rows = np.zeros((len(new_keys), L), dtype=np.float64)
            for j, nm in enumerate(new_keys):
                ev = sorted(cache[nm].eigenvalues, reverse=True)[:L]
                new_rows[j, :len(ev)] = ev
            self._spec_mat = np.vstack([mat, new_rows])
            base = len(self._spec_labels)
            self._spec_labels.extend(new_keys)
            for j, nm in enumerate(new_keys):
                self._spec_index[nm] = base + j
            mat = self._spec_mat
        elif len(cache_keys) < len(labels):
            # Küçülme (silme) → güvenli tarafta kal, tam yeniden kur
            self._spec_mat = None
            self._spec_labels = None
            return self._nearest_spectral_vec(q_spec, q_name, n)

        L = self._spec_L
        qv = sorted(q_spec.eigenvalues, reverse=True)[:L]
        q = np.zeros(L, dtype=np.float64)
        q[:len(qv)] = qv

        # Wasserstein-2 benzeri: L2 / L  (tüm satırlar tek seferde)
        dists = np.sqrt(((mat - q) ** 2).sum(axis=1)) / max(L, 1)

        # kendini ele (varsa)
        self_idx = self._spec_index.get(q_name, -1)
        k = min(n + 1, len(dists))
        # en küçük k indeks (sıralamasız) → sonra sırala
        part = np.argpartition(dists, k - 1)[:k]
        part = part[np.argsort(dists[part])]

        out: list[tuple[str, float]] = []
        for idx in part:
            if idx == self_idx:
                continue
            out.append((self._spec_labels[idx], float(dists[idx])))
            if len(out) >= n:
                break
        return out

    def build_spectral_cache(self, verbose: bool = False) -> int:
        """Tüm kavramlar için spektral ölçüleri önceden hesapla.

        Bir kez çalışır (27k × Jacobi ≈ 5s), sonuç save_spectral_cache()
        ile diske yazılabilir. Döner: cache'lenen kavram sayısı.
        """
        from tantrium.agi.domains.spectral import moments_to_spectral

        self._spec_cache = {}
        total = len(self.concepts)
        for i, (cname, c) in enumerate(self.concepts.items()):
            c_mu = [float(m) for m in c.moments]
            self._spec_cache[cname] = moments_to_spectral(c_mu, name=cname)
            if verbose and i % 5000 == 0:
                print(f"    spektral cache: {i}/{total}")
        return len(self._spec_cache)

    def save_spectral_cache(self, path: str) -> int:
        """Spektral ölçü cache'ini diske yaz (kompakt özdeğer dizileri).

        Format: {"v": 1, "labels": [...], "e": [[λ₁,λ₂,λ₃,λ₄], ...]}
        Döner: kaydedilen ölçü sayısı.
        """
        import json
        from pathlib import Path

        if not getattr(self, "_spec_cache", None):
            self.build_spectral_cache()

        labels = list(self._spec_cache.keys())
        data = {
            "v": 1,
            "labels": labels,
            "e": [self._spec_cache[name].to_list() for name in labels],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return len(labels)

    def load_spectral_cache(self, path: str) -> int:
        """Spektral ölçü cache'ini diskten yükle. Döner: yüklenen ölçü sayısı.

        Manifold ile uyuşmayan (silinmiş) etiketler atlanır; eksik olanlar
        ilk nearest_spectral çağrısında tembel hesaplanır.
        """
        import json
        from pathlib import Path
        from tantrium.agi.domains.spectral import SpectralMeasure

        p = Path(path)
        if not p.exists():
            return 0
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return 0
        if data.get("v") != 1:
            return 0

        self._spec_cache = {}
        for name, eigs in zip(data["labels"], data["e"]):
            if name in self.concepts:
                self._spec_cache[name] = SpectralMeasure.from_list(eigs, name=name)
        return len(self._spec_cache)

    def clear_spectral_cache(self) -> None:
        """Spektral ölçü cache'ini temizle (manifold güncellemesinden sonra)."""
        self._spec_cache = {}

    def gauge_class(self, concept: Concept, tol: Fraction = Fraction(1, 1000)) -> list[str]:
        """Find all concepts gauge-equivalent to the given one (Mem).
        These are synonyms — different names, same referent.
        """
        return [
            name for name, c in self.concepts.items()
            if are_gauge_equivalent(concept, c, tol)
        ]

    def is_injective(self) -> bool:
        """Kaf test: are all concepts distinct?
        A manifold where two concepts are indistinguishable collapses —
        the representation has a collision.
        """
        names = list(self.concepts.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if are_gauge_equivalent(
                    self.concepts[names[i]], self.concepts[names[j]],
                    tol=Fraction(0)
                ):
                    return False
        return True

    def save(self, path: str) -> int:
        """Manifold'u compact parallel-array formatında kaydet.

        Format v3:
          "labels": [name, ...]          ← insan etiketi (metadata)
          "d": [domain_char, ...]        ← tek harf domain
          "m": [[f0,f1,...,f7], ...]     ← kavramın kendisi (8 float)
        İsim dict key değil — index = concept ID.
        """
        import json
        from pathlib import Path

        _DC = {"physics": "p", "math": "a", "cs_ai": "c", "biology": "b",
               "theorem": "t", "language": "l", "general": "g", "philosophy": "f"}

        names = list(self.concepts.keys())
        data = {
            "v": 3,
            "labels": names,
            "d": [_DC.get(self.concepts[n].domain, "g") for n in names],
            "m": [[float(x) for x in self.concepts[n].moments] for n in names],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return len(names)

    @classmethod
    def load(cls, path: str) -> "SemanticManifold":
        """JSON'dan manifold yükle. v3 (parallel arrays) ve eski formatları destekler."""
        import json
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        m = cls()

        _DC_REV = {"p": "physics", "a": "math", "c": "cs_ai", "b": "biology",
                   "t": "theorem", "l": "language", "g": "general", "f": "philosophy"}

        if data.get("v") == 3:
            # v3: parallel arrays
            labels = data["labels"]
            domains = data.get("d", ["g"] * len(labels))
            moments_list = data["m"]
            for name, d_char, raw in zip(labels, domains, moments_list):
                moments = [Fraction(*float(f).as_integer_ratio()) for f in raw]
                m.concepts[name] = Concept(
                    name=name,
                    moments=moments,
                    domain=_DC_REV.get(d_char, "general"),
                    source="saved",
                )
        else:
            # Eski format: {name: {moments, domain, source}}
            for name, v in data.items():
                if not isinstance(v, dict):
                    continue
                raw = v["moments"]
                if raw and isinstance(raw[0], list):
                    moments = [Fraction(num, den) for num, den in raw]
                else:
                    moments = [Fraction(*float(f).as_integer_ratio()) for f in raw]
                m.concepts[name] = Concept(
                    name=name,
                    moments=moments,
                    domain=v.get("domain", "general"),
                    source=v.get("source", "saved"),
                )
        return m

    def summary(self) -> str:
        lines = [
            f"SemanticManifold: {len(self.concepts)} concepts",
            f"  injective: {self.is_injective()}",
        ]
        for name, concept in list(self.concepts.items())[:10]:
            r = concept.verify_existence()
            lines.append(f"  [{r.status}] {name} ({len(concept.moments)} moments, domain={concept.domain})")
        if len(self.concepts) > 10:
            lines.append(f"  ... and {len(self.concepts) - 10} more")
        return "\n".join(lines)
