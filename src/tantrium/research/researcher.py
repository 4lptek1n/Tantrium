"""Otonom Araştırma Motoru — AutonomousResearcher.

AGI kendi boşluklarını (MetaParadigm.blind_spots) tespit eder,
araştırma hedefleri oluşturur (GoalManifold), matematiksel veritabanlarından
veri çeker (OEIS API), AutonomousObserver aracılığıyla öğrenir.

Kapalı döngü:
  öz-değerlendirme → hedef → veri → öğren → ölç → kaydet → tekrar

OEIS (Online Encyclopedia of Integer Sequences) API:
  Ücretsiz, kısıtlama yok. Arama: oeis.org/search?q=keyword&fmt=json
  Her sorgu sonrası 0.6s bekleme (server-friendly).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

_RATE_LIMIT_S = 0.6  # OEIS rate-limit arası bekleme


# ─── Sonuç veri yapıları ──────────────────────────────────────────────────────

@dataclass
class ResearchCycle:
    """Tek bir araştırma döngüsünün özeti."""
    gaps_found: list[dict]
    goals_created: int
    sequences_fetched: int
    new_concepts: int
    bridges_found: list[tuple[str, str, str, float]]
    goal_progress: dict[str, tuple[float, float]]
    duration_s: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def summary(self) -> str:
        lines = [
            f"  ─── Döngü sonucu ───────────────────────────────────────",
            f"  Boşluk: {len(self.gaps_found)}  |  Hedef: {self.goals_created}  |  "
            f"Dizi: {self.sequences_fetched}  |  Yeni kavram: {self.new_concepts}  |  "
            f"Köprü: {len(self.bridges_found)}  ({self.duration_s:.1f}s)",
        ]
        for gname, (before, after) in self.goal_progress.items():
            delta = after - before
            if delta > 0:
                bar_b = "█" * int(before * 10) + "░" * (10 - int(before * 10))
                bar_a = "█" * int(after * 10) + "░" * (10 - int(after * 10))
                lines.append(f"  [{bar_b}]→[{bar_a}] {gname}")
        return "\n".join(lines)


@dataclass
class ResearchReport:
    """Bir araştırma oturumunun tam raporu."""
    cycles: list[ResearchCycle]
    total_new_concepts: int
    total_bridges: int
    remaining_gaps: list[dict]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def summary(self) -> str:
        lines = [
            "═══ OTONOM ARAŞTIRMA RAPORU ═══",
            f"Döngü sayısı:       {len(self.cycles)}",
            f"Yeni kavram:        {self.total_new_concepts}",
            f"Cross-domain köprü: {self.total_bridges}",
            f"Kalan boşluk:       {len(self.remaining_gaps)}",
        ]
        if self.remaining_gaps:
            lines.append("\n  Kalan boşluklar (öncelik sırası):")
            for gap in self.remaining_gaps[:5]:
                lines.append(f"    {gap['anchor']:<22}: {gap['count']} komşu")
        return "\n".join(lines)


# ─── Algoritmik dizi üretimi (ağ bağımsız, her seferinde benzersiz) ──────────

def _generate_sequences(anchor: str, batch: int = 0) -> list[tuple[str, list[float]]]:
    """Her anchor için algoritmik olarak üretilmiş diziler.
    batch parametresi her döngüde farklı segment alır → benzersiz isim.
    """
    import math

    tag = f"b{batch}"

    if anchor == "PRIME_GAPS":
        # Asal sayıları hesapla, gap'leri al
        limit = 500 + batch * 200
        sieve = [True] * (limit + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(limit**0.5) + 1):
            if sieve[i]:
                for j in range(i*i, limit + 1, i):
                    sieve[j] = False
        primes = [i for i in range(2, limit + 1) if sieve[i]]
        gaps = [float(primes[i+1] - primes[i]) for i in range(len(primes)-1)]
        offset = batch * 30
        chunk = gaps[offset:offset+32]
        return [(f"algo:prime_gaps_{tag}", chunk)] if len(chunk) >= 8 else []

    if anchor == "ZETA_ZEROS":
        # Riemann zeta sıfırlarının bilinen değerleri (50 tane)
        known = [
            14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
            37.586178, 40.918720, 43.327073, 48.005151, 49.773832,
            52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
            67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
            79.337376, 82.910381, 84.735493, 87.425275, 88.809111,
            92.491899, 94.651344, 95.870634, 98.831194, 101.317851,
            103.725538, 105.446623, 107.168611, 111.029536, 111.874659,
            114.320220, 116.226680, 118.790782, 121.370125, 122.946520,
            124.256819, 127.516683, 129.578704, 131.087688, 133.497737,
            134.756510, 138.116042, 139.736209, 141.123707, 143.111846,
        ]
        offset = (batch * 12) % (len(known) - 12)
        chunk = known[offset:offset+20]
        return [(f"algo:zeta_zeros_{tag}", chunk)]

    if anchor == "GUE_RANDOM_MATRIX":
        # GUE spacing distribution (Wigner surmise: p(s) = π/2 * s * exp(-π/4 * s²))
        import math
        spacings = []
        for k in range(32):
            # deterministic pseudo-sampling via inverse CDF approximation
            u = (k + 0.5 + batch * 0.1) / (32 + batch * 0.1)
            u = min(0.999, max(0.001, u))
            # approximate inverse of Wigner surmise CDF
            s = math.sqrt(-math.log(1 - u) * 4 / math.pi)
            spacings.append(round(s, 4))
        return [(f"algo:GUE_wigner_{tag}", spacings)]

    if anchor == "GEOMETRIC_GROWTH":
        seqs = []
        # Lucas numbers
        a, b = 2, 1
        lucas = []
        for _ in range(24):
            lucas.append(float(a))
            a, b = b, a + b
        seqs.append((f"algo:lucas_{tag}", lucas))
        # Tribonacci
        a, b, c = 0, 0, 1
        trib = []
        for _ in range(24):
            trib.append(float(a))
            a, b, c = b, c, a + b + c
        seqs.append((f"algo:tribonacci_{tag}", trib[1:]))
        return seqs

    if anchor == "GAUSSIAN_BELL":
        # Normal distribution PDF samples
        vals = []
        for k in range(32):
            x = -4.0 + k * 0.25 + batch * 0.1
            v = math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
            vals.append(round(v, 6))
        return [(f"algo:gaussian_pdf_{tag}", vals)]

    if anchor == "MODULAR_FORMS":
        # Ramanujan tau function τ(n) for small n
        tau = [0, -24, 252, -1472, 4830, -6048, -16744, 84480, -113643,
               -196884, 1, -24, 252, -1472, 4830, -6048, -16744, 84480,
               -113643, -196884, 166320, 21492, -25830, 65520, -242208]
        normalized = [float(abs(x)) / 200000 for x in tau[1:25]]
        return [(f"algo:ramanujan_tau_{tag}", normalized)]

    if anchor == "ELLIPTIC_CURVES":
        # Trace of Frobenius for elliptic curve y²=x³-x over F_p
        traces = []
        for p in [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43,
                  47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]:
            # simple heuristic: count points mod p
            count = sum(1 for x in range(p)
                        if pow(x*x*x - x, (p+1)//2, p) in (0, 1)) * 2 + 1
            traces.append(float(p + 1 - count))
        return [(f"algo:elliptic_trace_{tag}", traces)]

    if anchor == "EXPONENTIAL_DECAY":
        vals = [math.exp(-k * (0.1 + batch * 0.02)) for k in range(32)]
        return [(f"algo:exp_decay_{tag}", vals)]

    if anchor == "POISSON_PROCESS":
        # Poisson PMF with varying lambda
        lam = 2.5 + batch * 0.5
        vals = [math.exp(-lam) * (lam**k) / math.factorial(min(k, 20))
                for k in range(24)]
        return [(f"algo:poisson_pmf_{tag}", vals)]

    if anchor == "PERIODIC_LATTICE":
        # Cosine wave with varying frequency
        freq = 1.0 + batch * 0.25
        vals = [math.cos(2 * math.pi * freq * k / 32) for k in range(32)]
        return [(f"algo:cosine_{tag}", vals)]

    if anchor == "LINEAR_RAMP":
        start = batch * 10
        vals = [float(start + k) for k in range(32)]
        return [(f"algo:arithmetic_{tag}", vals)]

    if anchor == "UNIFORM_MEASURE":
        n = 32
        vals = [(k + batch * 0.01) / n for k in range(n)]
        return [(f"algo:uniform_{tag}", vals)]

    return []


# ─── Fallback dizileri (yedek) ────────────────────────────────────────────────

_FALLBACK: dict[str, list[tuple[str, list[float]]]] = {
    "GUE_RANDOM_MATRIX": [
        ("fallback:GUE_spacings_1",
         [0.27, 0.14, 0.38, 0.23, 0.51, 0.19, 0.33, 0.44,
          0.28, 0.36, 0.21, 0.42, 0.17, 0.55, 0.31, 0.25,
          0.46, 0.13, 0.39, 0.22, 0.52, 0.18, 0.34, 0.43]),
        ("fallback:GUE_spacings_2",
         [0.31, 0.22, 0.45, 0.18, 0.37, 0.52, 0.26, 0.41,
          0.35, 0.29, 0.47, 0.20, 0.38, 0.16, 0.43, 0.32,
          0.24, 0.49, 0.15, 0.40, 0.28, 0.53, 0.21, 0.36]),
    ],
    "POISSON_PROCESS": [
        ("fallback:poisson_intervals",
         [0.92, 1.43, 0.31, 2.07, 0.68, 1.82, 0.45, 1.23,
          0.77, 0.34, 1.95, 0.59, 1.11, 2.34, 0.43, 0.88,
          1.67, 0.22, 1.39, 0.74, 0.55, 2.18, 0.61, 1.05]),
    ],
    "PRIME_GAPS": [
        ("fallback:prime_gaps_first_40",
         [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2,
          6, 4, 6, 8, 4, 2, 4, 2, 4, 14, 4, 6, 2, 10, 2, 6, 6, 4, 6, 6]),
    ],
    "ZETA_ZEROS": [
        ("fallback:riemann_zeros_18",
         [14.135, 21.022, 25.011, 30.425, 32.935, 37.586,
          40.919, 43.327, 48.005, 49.774, 52.970, 56.446,
          59.347, 60.832, 65.113, 67.080, 69.546, 72.067]),
    ],
    "EXPONENTIAL_DECAY": [
        ("fallback:exp_decay",
         [1.000, 0.794, 0.631, 0.501, 0.398, 0.316, 0.251, 0.200,
          0.158, 0.126, 0.100, 0.079, 0.063, 0.050, 0.040, 0.032]),
    ],
    "GEOMETRIC_GROWTH": [
        ("fallback:fibonacci",
         [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]),
        ("fallback:powers_of_2",
         [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]),
    ],
    "GAUSSIAN_BELL": [
        ("fallback:gaussian_samples",
         [0.02, 0.05, 0.09, 0.15, 0.21, 0.26, 0.30, 0.32, 0.30, 0.26,
          0.21, 0.15, 0.09, 0.05, 0.02, 0.01, 0.24, 0.28, 0.18, 0.11]),
    ],
    "PERIODIC_LATTICE": [
        ("fallback:cosine_wave",
         [1.0, 0.866, 0.5, 0.0, -0.5, -0.866, -1.0, -0.866, -0.5, 0.0,
          0.5, 0.866, 1.0, 0.866, 0.5, 0.0, -0.5, -0.866, -1.0, -0.866]),
    ],
    "LINEAR_RAMP": [
        ("fallback:arithmetic_1_to_24",
         [float(i) for i in range(1, 25)]),
    ],
    "UNIFORM_MEASURE": [
        ("fallback:uniform_24",
         [i / 23.0 for i in range(24)]),
    ],
}


# ─── Otonom Araştırmacı ───────────────────────────────────────────────────────

class AutonomousResearcher:
    """AGI'nin kendi araştırma gündemini belirleyip uygulaması.

    MetaParadigm.blind_spots() → GoalManifold → AutonomousObserver
    üçlüsünü tek kapalı döngüde birleştirir.

    Örnek kullanım:
        researcher = AutonomousResearcher(engine)
        report = researcher.run(max_cycles=2)
        print(report.summary())
    """

    def __init__(
        self,
        engine: "CertificationEngine",
        max_sequences_per_gap: int = 8,
        bridge_threshold: float = 3e-2,
        oeis_timeout_s: float = 10.0,
    ) -> None:
        self.engine = engine
        self.max_seq = max_sequences_per_gap
        self.bridge_threshold = bridge_threshold
        self.oeis_timeout = oeis_timeout_s

        from tantrium.research.goal import GoalManifold
        self._goals = GoalManifold()

    # ─── Boşluk tespiti ────────────────────────────────────────────────────────

    def assess_gaps(self, threshold: int = 5) -> list[dict]:
        """Manifolddaki matematiksel boşlukları tespit et.

        Döner: [{"anchor": str, "count": int, "keywords": list[str]}, ...]
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self.engine).blind_spots(threshold=threshold)

    # ─── OEIS API ─────────────────────────────────────────────────────────────

    def fetch_oeis(
        self,
        keyword: str,
        max_results: int = 6,
    ) -> list[tuple[str, list[float]]]:
        """OEIS arama API'den anahtar kelimeye uyan dizileri çek.

        Başarısız veya ağ yoksa boş liste döner; caller fallback kullanır.
        """
        from tantrium.research.net import http_get_json
        encoded = urllib.parse.quote(keyword)
        url = f"https://oeis.org/search?q={encoded}&fmt=json&start=0"
        results: list[tuple[str, list[float]]] = []
        try:
            raw_data = http_get_json(url, timeout=self.oeis_timeout,
                                     user_agent="Tantrium-AGI/1.0")
            # OEIS /search returns list directly; some endpoints return dict with "results"
            if isinstance(raw_data, list):
                data_list = raw_data
            else:
                data_list = raw_data.get("results") or []
            for entry in data_list[:max_results]:
                num = entry.get("number")
                raw = entry.get("data", "")
                if num is None or not raw:
                    continue
                seq_id = f"oeis:A{int(num):06d}"
                try:
                    values = [
                        float(x.strip())
                        for x in str(raw).split(",")
                        if x.strip().lstrip("-").replace(".", "", 1).isdigit()
                    ]
                    if len(values) >= 6:
                        results.append((seq_id, values[:32]))
                except (ValueError, AttributeError):
                    continue
            time.sleep(_RATE_LIMIT_S)
        except Exception:
            pass
        return results

    # ─── LMFDB API ────────────────────────────────────────────────────────────

    def fetch_lmfdb_zeros(self, n: int = 20) -> list[tuple[str, list[float]]]:
        """LMFDB'den Riemann zeta sıfırlarını çek."""
        from tantrium.research.net import http_get_json
        url = f"https://www.lmfdb.org/api/Zeros/zeta/?N={n}&_format=json"
        try:
            data = http_get_json(url, timeout=self.oeis_timeout,
                                 user_agent="Tantrium-AGI/1.0")
            zeros = [float(item["zero"]) for item in (data or []) if "zero" in item]
            if len(zeros) >= 6:
                return [("LMFDB:riemann_zeros", zeros[:32])]
        except Exception:
            pass
        return []

    # ─── PubChem API ──────────────────────────────────────────────────────────

    def fetch_pubchem(self, query: str, max_results: int = 6) -> list[tuple[str, list[float]]]:
        """PubChem'den SMILES çek → Morgan fingerprint → moment dizisi."""
        from tantrium.core.encoder import encode_smiles
        from tantrium.research.net import http_get_json

        encoded = urllib.parse.quote(query)
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{encoded}/property/SMILES,MolecularFormula/JSON"
        )
        results: list[tuple[str, list[float]]] = []
        try:
            data = http_get_json(url, timeout=self.oeis_timeout,
                                 user_agent="Tantrium-AGI/1.0")
            compounds = (data.get("PropertyTable") or {}).get("Properties") or []
            for c in compounds[:max_results]:
                smiles = c.get("SMILES", "") or c.get("IsomericSMILES", "")
                cid = c.get("CID", "unknown")
                formula = c.get("MolecularFormula", "")
                if not smiles:
                    continue
                try:
                    obj = encode_smiles(smiles, name=f"PubChem:{cid}")
                    if obj.moments and len(obj.moments) >= 4:
                        results.append((f"PubChem:{cid}_{formula}", list(obj.moments)))
                except Exception:
                    continue
            time.sleep(_RATE_LIMIT_S)
        except Exception:
            pass
        return results

    # ─── PubChem toplu çekim ──────────────────────────────────────────────────

    _PUBCHEM_QUERIES: list[str] = [
        "erlotinib", "gefitinib", "imatinib", "sorafenib", "dasatinib",
        "sunitinib", "lapatinib", "vemurafenib", "crizotinib", "cetuximab",
        "tamoxifen", "doxorubicin", "paclitaxel", "vincristine", "methotrexate",
        "cisplatin", "carboplatin", "oxaliplatin", "fluorouracil", "gemcitabine",
        "caffeine", "aspirin", "glucose", "adenine", "guanine",
        "dopamine", "serotonin", "acetylcholine", "glutamate", "glycine",
    ]

    def fetch_pubchem_batch(self, batch: int = 0, size: int = 4) -> list[tuple[str, list[float]]]:
        """PubChem'den batch'e göre ilaç/metabolit SMILES çek."""
        queries = self._PUBCHEM_QUERIES
        start = (batch * size) % len(queries)
        selected = queries[start:start + size]
        results = []
        for q in selected:
            results.extend(self.fetch_pubchem(q, max_results=1))
        return results

    def _fetch_for_gap(self, gap: dict, batch: int = 0, network: bool = False) -> list[tuple[str, list[float]]]:
        """Bir boşluk için veri üret. network=False → saf algoritmik (hızlı)."""
        anchor = gap["anchor"]
        sequences: list[tuple[str, list[float]]] = []

        # Algoritmik diziler — ağ bağımsız, saf hesaplama
        sequences.extend(_generate_sequences(anchor, batch=batch))

        if network and len(sequences) < self.max_seq:
            keywords = gap.get("keywords", [])
            for kw in keywords[:2]:
                sequences.extend(self.fetch_oeis(kw, max_results=3))
                if len(sequences) >= self.max_seq:
                    break
            if anchor == "ZETA_ZEROS":
                sequences.extend(self.fetch_lmfdb_zeros(n=30))
            if len(sequences) < self.max_seq:
                sequences.extend(self.fetch_pubchem_batch(batch=batch, size=2))

        if not sequences:
            sequences.extend(_FALLBACK.get(anchor, []))

        return sequences[:self.max_seq]

    # ─── Tek araştırma döngüsü ────────────────────────────────────────────────

    def research_cycle(self, gap_threshold: int = 5, batch: int = 0, network: bool = False) -> ResearchCycle:
        """Tek araştırma döngüsü: değerlendirme → hedef → veri → öğren → raporla."""
        from tantrium.research.autonomous import AutonomousObserver
        from tantrium.research.goal import encode_goal

        t0 = time.monotonic()

        # 1. Boşlukları tespit et
        gaps = self.assess_gaps(threshold=gap_threshold)

        # 2. Her boşluk için araştırma hedefi oluştur (idempotent)
        goals_created = 0
        for gap in gaps[:5]:
            anchor = gap["anchor"]
            desc = f"araştır: {anchor.lower().replace('_', ' ')}"
            goal = encode_goal(self.engine, desc)
            if goal and self._goals.add(goal):
                goals_created += 1

        # 3. İlk 5 boşluk için veri çek (batch ile her döngüde farklı)
        all_sequences: list[tuple[str, list[float]]] = []
        for gap in gaps[:5]:
            seqs = self._fetch_for_gap(gap, batch=batch, network=network)
            all_sequences.extend(seqs)

        sequences_fetched = len(all_sequences)

        # 4. AutonomousObserver ile öğren (her dizi Aleph filtresinden geçer)
        observer = AutonomousObserver(
            self.engine,
            bridge_threshold=self.bridge_threshold,
            persist_every=9999,  # biz döngü sonunda persist edeceğiz
        )
        for seq_id, values in all_sequences:
            observer.observe(values, name=seq_id)

        new_concepts = sum(1 for o in observer.observations if o.is_new and o.certified)
        bridges = observer.bridges_found()

        # 5. Hedef ilerlemesini ölç
        concept_names = [o.name for o in observer.observations if o.certified]
        goal_progress: dict[str, tuple[float, float]] = {}
        for goal in self._goals.active_goals():
            before = goal.progress
            after = goal.update_progress(concept_names, self.engine)
            goal_progress[goal.name] = (before, after)

        # 6. Kalıcı kayıt (her 100 cycle'da bir — IO darboğazını önler)
        if batch % 100 == 0:
            self.engine.auto_persist()

        return ResearchCycle(
            gaps_found=gaps,
            goals_created=goals_created,
            sequences_fetched=sequences_fetched,
            new_concepts=new_concepts,
            bridges_found=bridges,
            goal_progress=goal_progress,
            duration_s=time.monotonic() - t0,
        )

    # ─── Çoklu döngü ─────────────────────────────────────────────────────────

    def run(
        self,
        max_cycles: int = 3,
        time_limit_s: float = 300.0,
        gap_threshold: int = 5,
        network: bool = False,
    ) -> ResearchReport:
        """max_cycles araştırma döngüsü çalıştır (veya time_limit dolana kadar).

        network=True → OEIS API kullan (gerçek matematiksel diziler).
        Her döngü: assess_gaps → fetch → observe → persist.
        Son: tam rapor.
        """
        t_start = time.monotonic()
        cycles: list[ResearchCycle] = []

        for i in range(max_cycles):
            if time.monotonic() - t_start >= time_limit_s:
                break
            cycle = self.research_cycle(gap_threshold=gap_threshold, batch=i, network=network)
            cycles.append(cycle)
            if not cycle.gaps_found:
                break

        remaining = self.assess_gaps(threshold=gap_threshold)
        return ResearchReport(
            cycles=cycles,
            total_new_concepts=sum(c.new_concepts for c in cycles),
            total_bridges=sum(len(c.bridges_found) for c in cycles),
            remaining_gaps=remaining,
        )
