"""Language topology: concepts as moment sequences and Hankel matrices.

Language is not a separate domain. A concept is a moment sequence.
The Hankel matrix of that sequence either is PSD (concept exists)
or it is not (concept is incoherent — it cannot exist in the real manifold).

This is the same D-positivity engine that proves RH.
Applied to language, it becomes the existence filter for meaning.

The system does not predict. It certifies or names its gap.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from fractions import Fraction

from tantrium.core.codex import (
    CertifiableObject as CodexObject,
)
from tantrium.core.codex import (
    ParadigmResult,
)
from tantrium.core.codex import (
    PositivityParadigm as AlephParadigm,
)

# ─── Admission verdict (F3: tek admit() yolu) ──────────────────────────────


@dataclass
class AdmissionResult:
    """admit() yargısı — TEK manifold admission yolunun çıktısı.

    admitted : kavram manifolda girdi mi
    tier     : "core" (Aleph sertifikalı) | "trusted" (kapı-muaf) | "rejected"
    reason   : insan-okunur gerekçe (Aleph gap adı / kaynak güveni)
    """

    admitted: bool
    tier: str
    reason: str
    concept_name: str = ""

    def __bool__(self) -> bool:
        return self.admitted


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
    def from_counts(
        cls, name: str, counts: Sequence[int | float], domain: str = "general"
    ) -> Concept:
        """Build a concept from raw co-occurrence or measurement counts.
        Normalizes to a probability-like moment sequence summing to 1.
        """
        total = sum(counts)
        if total == 0:
            raise ValueError(f"Concept '{name}': zero total — cannot form a moment sequence.")
        moments = [Fraction(c, total) for c in counts]
        return cls(name=name, moments=moments, domain=domain, source="counts")

    @classmethod
    def from_rational(
        cls, name: str, moments: Sequence[Fraction], domain: str = "general"
    ) -> Concept:
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
            },
        )

    def verify_existence(self) -> ParadigmResult:
        """Aleph test: does this concept exist in the real manifold?
        PSD Hankel ⟺ the concept is realizable as a genuine measure.
        A concept that fails this test is not real — it has no referent.
        """
        return AlephParadigm("ALEPH", "Positivity", "D ≥ 0, p_i ≥ 0, A ⪰ 0", []).verify(
            self.to_codex_object()
        )

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
    return sum(abs(x - y) for x, y in zip(a_m, b_m, strict=False))


def are_gauge_equivalent(a: Concept, b: Concept, tol: Fraction = Fraction(1, 1000)) -> bool:
    """Mem test: are two concepts indistinguishable?
    Two concepts are gauge-equivalent if their moment sequences are
    within tolerance — they are the same thing seen from different angles.
    (Synonyms in language. Gauge transformations in physics.)
    """
    return moment_distance(a, b) <= tol


def semantic_fixed_point(
    concept: Concept,
    interpretation_fn: Callable[[Concept], Concept],  # noqa: F821
    max_iter: int = 50,
    tol: Fraction = Fraction(1, 10**9),
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

    def admit(self, concept: Concept, *, policy: str = "aleph") -> AdmissionResult:
        """TEK admission yolu — tüm manifold girişleri buraya iner (F3).

        policy="aleph"   : Aleph PSD kontrolü (verify_existence). Geçerse core,
                           geçmezse rejected. add() bu politikayı kullanır.
        policy="trusted" : kontrolsüz kabul (güvenilir/sertifikalı kaynak).
                           KAPI-MUAF (plan gereği). add_unchecked() bunu kullanır.

        Engine-seviyesi evren kapısı (truth+grounding ile core/frontier ayrımı,
        CONTRADICTORY reddi) `research/autonomous._universe_gate`'tedir — engine'e
        bağlı olduğundan saf manifoldda yaşamaz; o da kabul için buraya
        (policy="trusted") iner. Burada engine bağımlılığı YOK.

        Döner: AdmissionResult(admitted, tier, reason).
        """
        if policy == "trusted":
            self.concepts[concept.name] = concept
            return AdmissionResult(True, "trusted", "trusted source — gate-exempt", concept.name)
        if policy == "aleph":
            result = concept.verify_existence()
            if result.is_certified():
                self.concepts[concept.name] = concept
                return AdmissionResult(True, "core", "Aleph PSD certified", concept.name)
            return AdmissionResult(False, "rejected", str(result.gap_name), concept.name)
        raise ValueError(f"Unknown admission policy: {policy!r} (expected 'aleph' or 'trusted')")

    def add(self, concept: Concept) -> SemanticManifold:
        result = self.admit(concept, policy="aleph")
        if not result.admitted:
            raise ValueError(
                f"Concept '{concept.name}' rejected by Aleph filter: {result.reason}. "
                f"It does not exist in the real manifold."
            )
        return self

    def add_unchecked(self, concept: Concept) -> SemanticManifold:
        """Add without Aleph check — use only for trusted certified inputs.

        admit(policy="trusted")'a delege — kapı-muaf tek yol.
        """
        self.admit(concept, policy="trusted")
        return self

    def distance(self, name_a: str, name_b: str, metric: str = "spectral_w2") -> float | None:
        """İki kavram arasındaki KANONİK mesafe (varsayılan: spektral W2).

        Tek tutarlı mesafe — manifold/transport/spectral üçlü tutarsızlığını kapatır.
        İki kavram da manifoldda olmalı; biri yoksa None.
        """
        from tantrium.core.metric import distance as _metric_distance

        ca = self.concepts.get(name_a)
        cb = self.concepts.get(name_b)
        if ca is None or cb is None:
            return None
        return _metric_distance(ca.moments, cb.moments, metric=metric)

    def nearest(
        self, concept: Concept, n: int = 5, metric: str = "l1"
    ) -> list[tuple[str, Fraction]]:
        """Find the n nearest concepts by moment distance (gradient flow direction).

        metric="l1" (varsayılan): hızlı L1 ön-eleme — büyük manifoldda hız için.
        metric="spectral_w2": kanonik spektral Wasserstein (anlamsal hüküm için).
          L1 ile geniş aday kümesi seçilir, sonra kanonik W2 ile yeniden sıralanır.
        metric="quantum": Voiculescu serbest kümülant mesafesi (0.7×W2 + 0.3×κ).
          Klasik şekil + kuantum (halka/heteroatom) yapısı birlikte.

        Float path: 6748 kavram için Fraction L1 yerine float L1 — ~50x hızlı.
        Sonuçlar Fraction'a çevrilir (API uyumluluğu için).
        """
        if metric == "quantum":
            mu = [float(m) for m in concept.moments]
            hits = self._nearest_quantum_vec(mu, top_k=n + 1)
            out = []
            for nm, d in hits:
                if nm == concept.name:
                    continue
                out.append((nm, Fraction(d).limit_denominator(10**6)))
            return out[:n]
        if metric == "extended":
            return self._nearest_l1_extended(concept, n)
        if metric == "spectral_w2":
            # L1 ile geniş aday kümesi (3n), sonra kanonik W2 ile yeniden sırala
            from tantrium.core.metric import canonical_distance

            wide = self._nearest_l1(concept, n=max(n * 3, n + 5))
            reranked = []
            for nm, _ in wide:
                c = self.concepts.get(nm)
                if c is None:
                    continue
                d = canonical_distance(concept.moments, c.moments)
                reranked.append((d, nm))
            reranked.sort()
            return [(nm, Fraction(d).limit_denominator(10**6)) for d, nm in reranked[:n]]
        return self._nearest_l1(concept, n)

    _L1_W = 8  # karşılaştırma genişliği (standart moment sayısı)

    def _nearest_l1(self, concept: Concept, n: int = 5) -> list[tuple[str, Fraction]]:
        """Hızlı L1 en-yakın-komşu (iç ön-eleme yolu) — numpy vektörize, ARTIMLI cache.

        HIZ: numpy moment-matris cache. KRİTİK: büyümede her pulse kavram ekler →
        count-keyed FULL rebuild her çağrıda 46k×8 matrisi baştan kuruyordu (~350ms,
        pulse'ı boğuyordu). ÇÖZÜM: artımlı ekleme — yalnız YENİ kavramları vstack ile
        ekle (O(yeni), ~ms); her 64 eklemede bir full-resync (silme/yerinde-değişim drift'i).
        l1 "ön-eleme, hüküm değil" — küçük staleness kabul edilebilir.
        """
        import numpy as np

        W = self._L1_W
        n_now = len(self.concepts)
        cached = getattr(self, "_l1_count", -1)
        appends = getattr(self, "_l1_appends", 0)

        def _row(c):
            mu = [float(x) for x in c.moments[:W]]
            return mu + [0.0] * (W - len(mu)) if len(mu) < W else mu[:W]

        if cached < 0 or n_now < cached or not hasattr(self, "_l1_M") or appends > 64:
            # FULL rebuild (ilk / küçülme / periyodik resync)
            names = list(self.concepts.keys())
            rows = [_row(self.concepts[nm]) for nm in names]
            self._l1_names = names
            self._l1_M = np.asarray(rows, dtype=float) if rows else np.zeros((0, W))
            self._l1_count = n_now
            self._l1_appends = 0
        elif n_now > cached:
            # ARTIMLI: yalnız yeni kavramları ekle (insertion-order: yeniler sonda)
            new_names = list(self.concepts.keys())[cached:]
            new_rows = [_row(self.concepts[nm]) for nm in new_names]
            if new_rows:
                self._l1_M = np.vstack([self._l1_M, np.asarray(new_rows, dtype=float)])
                self._l1_names = self._l1_names + new_names
            self._l1_count = n_now
            self._l1_appends = appends + 1

        if self._l1_M.shape[0] == 0:
            return []
        qmu = [float(m) for m in concept.moments[:W]]
        if len(qmu) < W:
            qmu = qmu + [0.0] * (W - len(qmu))
        qv = np.asarray(qmu, dtype=float)
        d = np.abs(self._l1_M - qv).sum(axis=1)
        nn = min(n + 1, d.shape[0])
        idx = np.argpartition(d, nn - 1)[:nn]
        idx = idx[np.argsort(d[idx])]
        out: list[tuple[str, Fraction]] = []
        for i in idx:
            name = self._l1_names[int(i)]
            if name == concept.name:
                continue
            out.append((name, Fraction(float(d[int(i)])).limit_denominator(10**6)))
            if len(out) >= n:
                break
        return out

    def _nearest_l1_extended(
        self, concept: Concept, n: int = 5, text_weight: float = 0.10
    ) -> list[tuple[str, Fraction]]:
        """L1 moment mesafesi + metin boyutu tiebreaker (uzunluk + çeşitlilik).

        text_weight=0.10 (10%): temel moment geometrisi korunur, metin özelliği
        hafifçe blendlenir. Farklı uzunluk veya karakter çeşitliliğindeki
        çakışmaları çözmeye yardımcı olur; aynı uzunluk+çeşitlilik çakışmaları
        (protein/glucose) için label_aware encoding gerekir.
        """
        from tantrium.core.encoder import _text_extra_dims

        q = [float(m) for m in concept.moments]
        q_text = _text_extra_dims(concept.name)
        k = len(q)
        best: list[tuple[float, str]] = []

        for name, c in self.concepts.items():
            if name == concept.name:
                continue
            cm = c.moments
            d_moment = sum(abs(q[i] - (float(cm[i]) if i < len(cm) else 0.0)) for i in range(k))
            c_text = _text_extra_dims(name)
            d_text = abs(q_text[0] - c_text[0]) + abs(q_text[1] - c_text[1])
            d = (1.0 - text_weight) * d_moment + text_weight * d_text
            if len(best) < n:
                best.append((d, name))
                if len(best) == n:
                    best.sort(reverse=True)
            elif d < best[0][0]:
                best[0] = (d, name)
                best.sort(reverse=True)

        best.sort()
        return [(name, Fraction(d).limit_denominator(10**6)) for d, name in best]

    def nearest_spectral(
        self,
        concept: Concept,
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
        from tantrium.domains.spectral import moments_to_spectral, spectral_distance

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
                arr[i, : len(ev)] = ev
            self._spec_mat = arr
            self._spec_labels = list(cache_keys)
            self._spec_index = {nm: i for i, nm in enumerate(cache_keys)}
            mat = arr
        elif len(cache_keys) > len(labels):
            # Büyüme: yeni eklenen kavramları sona ekle (O(yeni) — O(N) değil)
            L = self._spec_L
            new_keys = cache_keys[len(labels) :]
            new_rows = np.zeros((len(new_keys), L), dtype=np.float64)
            for j, nm in enumerate(new_keys):
                ev = sorted(cache[nm].eigenvalues, reverse=True)[:L]
                new_rows[j, : len(ev)] = ev
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
        q[: len(qv)] = qv

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
        from tantrium.domains.spectral import moments_to_spectral

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

        from tantrium.domains.spectral import SpectralMeasure

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
        for name, eigs in zip(data["labels"], data["e"], strict=False):
            if name in self.concepts:
                self._spec_cache[name] = SpectralMeasure.from_list(eigs, name=name)
        return len(self._spec_cache)

    def clear_spectral_cache(self) -> None:
        """Spektral ölçü cache'ini temizle (manifold güncellemesinden sonra)."""
        self._spec_cache = {}
        self._spec_mat = None
        self._spec_labels = None

    # ─── Kuantum moment metotları ─────────────────────────────────────────────

    def _get_quantum_sig(self, name: str) -> object | None:
        """Kavramın QuantumSignature'ını al (tembel hesaplama + cache)."""
        c = self.concepts.get(name)
        if c is None:
            return None
        from tantrium.core.quantum_moments import QuantumSignature

        cache = getattr(self, "_cumulant_cache", None)
        if cache is None:
            self._cumulant_cache: dict[str, list[float]] = {}
            cache = self._cumulant_cache
        kappa = cache.get(name)
        if kappa is not None:
            from tantrium.core.quantum_moments import FreeCumulants

            return QuantumSignature(
                moments=[float(m) for m in c.moments],
                cumulants=FreeCumulants(kappa),
            )
        sig = QuantumSignature.from_moments([float(m) for m in c.moments])
        cache[name] = sig.cumulants.k
        return sig

    def _nearest_quantum_vec(
        self,
        mu: list[float],
        top_k: int = 10,
        gamma: float = 0.3,
    ) -> list[tuple[str, float]]:
        """Kuantum mesafeyle en yakın kavramlar: (1-γ)×W2_proxy + γ×κ_mesafe."""
        from tantrium.core.quantum_moments import QuantumSignature

        query = QuantumSignature.from_moments(mu)
        results: list[tuple[str, float]] = []
        for name in self.concepts:
            sig = self._get_quantum_sig(name)
            if sig is None:
                continue
            results.append((name, query.quantum_distance(sig, gamma=gamma)))
        results.sort(key=lambda x: x[1])
        return results[:top_k]

    def quantum_bridges(self, name: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Klasik uzak ama kuantum yakın kavramlar — gizli matematiksel bağlantılar."""
        sig_q = self._get_quantum_sig(name)
        if sig_q is None:
            return []
        bridges: list[tuple[str, float]] = []
        for cname in self.concepts:
            if cname == name:
                continue
            sig_c = self._get_quantum_sig(cname)
            if sig_c is None:
                continue
            if sig_q.is_entangled_with(sig_c):  # type: ignore[union-attr]
                bridges.append((cname, sig_q.quantum_distance(sig_c)))  # type: ignore[union-attr]
        return sorted(bridges, key=lambda x: x[1])[:top_k]

    def gauge_class(self, concept: Concept, tol: Fraction = Fraction(1, 1000)) -> list[str]:
        """Find all concepts gauge-equivalent to the given one (Mem).
        These are synonyms — different names, same referent.
        """
        return [name for name, c in self.concepts.items() if are_gauge_equivalent(concept, c, tol)]

    def is_injective(self) -> bool:
        """Kaf test: are all concepts distinct?
        A manifold where two concepts are indistinguishable collapses —
        the representation has a collision.
        """
        names = list(self.concepts.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if are_gauge_equivalent(
                    self.concepts[names[i]], self.concepts[names[j]], tol=Fraction(0)
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

        _DC = {
            "physics": "p",
            "math": "a",
            "cs_ai": "c",
            "biology": "b",
            "theorem": "t",
            "language": "l",
            "general": "g",
            "philosophy": "f",
        }

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
    def load(cls, path: str) -> SemanticManifold:
        """JSON'dan manifold yükle. v3 (parallel arrays) ve eski formatları destekler."""
        import json
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        m = cls()

        _DC_REV = {
            "p": "physics",
            "a": "math",
            "c": "cs_ai",
            "b": "biology",
            "t": "theorem",
            "l": "language",
            "g": "general",
            "f": "philosophy",
        }

        if data.get("v") == 3:
            # v3: parallel arrays
            labels = data["labels"]
            domains = data.get("d", ["g"] * len(labels))
            moments_list = data["m"]
            for name, d_char, raw in zip(labels, domains, moments_list, strict=False):
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
            lines.append(
                f"  [{r.status}] {name} ({len(concept.moments)} moments, domain={concept.domain})"
            )
        if len(self.concepts) > 10:
            lines.append(f"  ... and {len(self.concepts) - 10} more")
        return "\n".join(lines)
