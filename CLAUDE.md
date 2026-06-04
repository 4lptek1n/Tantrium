# Tantrium AGI — Sistem Hafızası

Bu dosya, sistemin her detayını içerir. Her yeni session'da bu dosyayı oku — hiçbir şeyi unutma.

---

## Aktif Branch

Tüm geliştirme: `claude/seninle-agi-yapacagiz-XwJRz`

Matematiksel temel (RH ispat araçları): `tce-collapse-engine` branch'inde.

---

## ÖNEMLI: Mimari Geçmişi

`src/tantrium/agi/` katmanı TAMAMEN SİLİNDİ. Artık TEK bir düz ağaç var.
Eski `tantrum.agi.*` import yolları YOK. Doğrusu: `from tantrium import ...`

---

## Proje Yapısı (GÜNCEL — DÜZ AĞAÇ)

```
/home/user/Tantrium/
├── src/tantrium/               ← KURULU paket (pip install -e .)
│   ├── __init__.py             ← Tüm ana exportlar
│   ├── ai.py                   ← Üst seviye SDK: tantrium.AI()
│   ├── core/
│   │   ├── encoder.py          ← Universal encoder (domain-blind)
│   │   ├── codex.py            ← 22+1 paradigma tanımları
│   │   ├── network.py          ← CertificationPipeline (DAG runner)
│   │   ├── semantic.py         ← Concept, SemanticManifold
│   │   ├── engine.py           ← CertificationEngine (orkestratör)
│   │   └── transport.py        ← CertifiedTransport (3 katman: dyadic+Sturm+Zeta)
│   ├── algebra/
│   │   ├── sturm.py            ← normalized_sturm_chain, normalized_sturm_pivots
│   │   ├── positivity.py       ← has_positive_coefficients, ramp_top_coefficient
│   │   └── sheffer.py          ← Lah sayıları, Sheffer polinomları
│   ├── graph/
│   │   ├── knowledge_graph.py  ← KnowledgeGraph (TAU), KnowledgeNode, KnowledgeEdge
│   │   ├── anchors.py          ← 10 matematiksel çapa (GUE, ZETA, ...)
│   │   ├── relations.py        ← Semantik ilişki çıkarma + certify_and_add_edge
│   │   └── memory.py           ← SessionMemory
│   ├── domains/
│   │   ├── bridge.py           ← PARADIGM_TO_THEOREMS eşlemesi, SemanticBridge
│   │   ├── math_kernel.py      ← inject_math_kernel() (theorem→manifold)
│   │   ├── certifier.py        ← MolecularCertifier (CertifiedTransport kullanır)
│   │   ├── generator.py        ← MoleculeGenerator
│   │   └── spectral.py         ← SpectralMeasure, gram_spectrum, W₂ mesafe
│   ├── reasoning/
│   │   ├── necessity.py        ← NecessityEngine (geçişli kapanış + boşluk)
│   │   ├── reasoner.py         ← GraphReasoner (semantik zincir)
│   │   ├── inference.py        ← InferenceChain
│   │   ├── thinker.py          ← Thinker
│   │   ├── generalization.py   ← HankelGeneralizer
│   │   └── planner.py          ← Planner
│   ├── research/
│   │   ├── proof_loop.py       ← ProofLoop (AGI↔Research OS kapalı döngü)
│   │   ├── autonomous.py       ← AutonomousObserver (insansız öğrenme)
│   │   ├── researcher.py       ← AutonomousResearcher (OEIS/LMFDB)
│   │   ├── ingest.py           ← DataIngestor (UniProt/PubChem/OEIS)
│   │   ├── goal.py             ← GoalManifold
│   │   ├── actor.py            ← Actor
│   │   └── explorer.py         ← Explorer
│   └── language/
│       ├── generator.py        ← CertifiedGenerator (TAU walk üretim)
│       ├── bootstrap.py        ← LanguageBootstrap
│       ├── speaker.py          ← Speaker
│       └── lang_topology.py
├── tantrium/                   ← AYRI paket (pip ile kurulmaz, sys.path ile)
│   ├── research_os/            ← Research OS (run_campaigns)
│   ├── theorem_graph/          ← GraphStore, TheoremNode, theorem_graph.yaml
│   ├── transport/              ← dyadic_flow.py (solve_greedy)
│   └── positivity_machine.py
├── tools/
│   ├── proof_loop_demo.py      ← AGI↔Research OS kapalı döngü demo
│   ├── autonomous_research_session.py
│   ├── ingest_real_world.py    ← UniProt/PubChem/OEIS ingestion
│   └── tantrium_research_os.py ← Research OS CLI
└── results/agi/
    ├── manifold.json           ← 39,918 kavram (kalıcı)
    ├── tau_graph.json          ← 654,834 TAU edge (kalıcı)
    └── spectral_cache.json     ← Wasserstein spektral cache
```

---

## Temel Felsefe

Her şey (DNA, molekül, cümle, asal sayı) zaten matematiksel bir nesne. Encoder "çevirmez" — okur.

```
girdi → matris → Gram G = AᵀA → μ_k = Tr(G^k)/n → 8 Fraction moment
```

G = AᵀA her zaman PSD → Hamburger moment dizisi → Hankel PSD → ALEPH geçer.

---

## 22+1 Paradigma Gerçek Durumu

**NOT**: Encoder geçerli Gram moment dizisi üretir. Geçerli inputlar için ÇOĞU paradigma zaten geçer (bu tasarım gereği). Asıl filtre CertifiedTransport'ta.

| Paradigma | Gerçek mi? | Notlar |
|-----------|-----------|--------|
| ALEPH | ✓ Gerçek | Hankel PSD, Sylvester kriteri |
| DALET | ✓ Gerçek | numpy.eigvalsh(Gram) — gerçek eigenvalue |
| HE | ✓ Gerçek | V(k)=μ_k/ρ^k, ρ=max eigenvalue — DOĞAL azalan |
| TET | ✓ Gerçek | Möbius cross-ratio = (a-c)(b-d)/((a-d)(b-c)) |
| KAF | ✓ Gerçek | SHA256(position+content) — enjektif |
| HET | ✓ Gerçek | V(m_k)=1/(k+1) her zaman azalıyor |
| SHIN | ✓ Gerçek | argmax moment skoru |
| TAV | ✓ Gerçek (trivial) | Picard x→0.01x+0.99*m1 → m1'e yakınsıyor, is_running=True |
| ZAYIN | ✓ Geçerli | Tr(G) = Σ self-loop paths — LGV trace identity |
| RESH | ✓ Gerçek | Üst yarı eigenvalue = subsystem — real partial trace |
| TSADI | Trivial | hash=hash her zaman doğru |
| BET | Trivial | information_loss=0 hardcoded |
| SU3 | Trivial | center_order=3 hardcoded |
| KUF | Trivial | topological_index=18 hardcoded |
| MEM | Trivial | gauge_classes tutarlı tasarımla |
| YOD | Trivial | alternative_models=[] → her zaman minimal |
| GIMEL | Trivial | open_obstructions=[] → her zaman closed |
| VAV/NUN | Trivial | composite_dim=n*m her zaman |
| LAMED | Trivial | locally_observable=physical_differences |
| PE | Trivial | semantic_map dolu her zaman |
| AYIN | Trivial | position_index her zaman ayırt eder |
| EMET | Trivial | contradictions=[] hardcoded |

**Gerçek discrimination CertifiedTransport'ta:**
- benzene DYADIC_FAILED (simetrik ring → farklı spektral kütle dağılımı)
- aspirin CERTIFIED, caffeine CERTIFIED
- Zeta mesafesi: aspirin ζ-dist=2.09, benzene ζ-dist=2.00

---

## Encoder Gerçekleri (Güncel)

**DALET**: `numpy.linalg.eigvalsh(Gram)` — gerçek eigenvalue'lar ✓

**HE (Lyapunov)**: `V(k) = μ_k / (max_eigenvalue^k)` — gerçek Lyapunov fonksiyonu, klip YOK ✓

**ZAYIN**: `path_weights = diag(G)`, `declared_det = trace(G) = sum(diag)` — LGV trace identity ✓
Ayrıca `real_determinant = det(G)` kaydedilir (discrimination için)

**TAV**: Picard `x_{n+1} = 0.01*x + 0.99*m1` → m1'e yakınsar. is_running=True ✓

**RESH**: `subsystem_info = sum(top_half_eigenvalues)`, `total_info = sum(all_eigenvalues)` — gerçek ✓

---

## AGI Motor: CertifiedTransport (`core/transport.py`)

Bu sistem NEAREST-NEIGHBOR ARAMIYOR — SERTIFIKALAMA YAPIYOR.

```
Kaynak moment → Hankel → eigenvalue → Cell nesneleri (dyadic kütleler)
Hedef moment  → Hankel → eigenvalue → Cell nesneleri

1. DYADIC: solve_greedy(src_cells, tgt_cells, policy) → "verified_exact" veya fail
2. STURM: H(t)=(1-t)H_src + t*H_tgt her t için PSD mi? (normalized_sturm_pivots)
3. ZETA: hedef momentlerinin ⊕ANCHOR:ZETA_ZEROS ailesine L1 mesafesi

CERTIFIED = dyadic ✓ AND sturm ✓
BLOCKED = DYADIC_FAILED veya STURM_FAILED
```

**API:**
```python
from tantrium import CertifiedTransport, TransportCertificate, TransportRanking

# Doğrudan
ct = CertifiedTransport(engine)
tc = ct.certify(source_moments, target_moments)
# tc.certified, tc.dyadic_verified, tc.sturm_verified, tc.zeta_distance

# AI SDK üzerinden
ai = tantrium.AI()
tc = ai.transport("CCO", "aspirin", use_smiles=True)  # SMILES moleküler
tc = ai.transport("EGFR", "erlotinib")                # metin semantik
ranking = ai.rank("EGFR", top_n=10)                  # sıralama
```

---

## TAU Grafiği (KnowledgeGraph)

Bilgi node'da değil, **edge'de**.

- `KnowledgeNode`: name + domain + source + **sr** (spectral radius = son moment μ_7)
- `KnowledgeEdge`: source + target + distance + paradigm

**Paradigm türleri:**
- `ALEPH` — geometrik (moment L1 mesafesi), K=10 en yakın
- `IS_A, USES, DEFINES, ACHIEVES, REQUIRES, COMPOSED` — semantik (metin regex)
- `SPECTRAL_BRIDGE` — cross-domain köprü (Wasserstein-2 < threshold)
- `REQUIRES, ACHIEVES` — theorem bağımlılıkları (inject_math_kernel)

---

## Matematiksel Çapalar (10 adet)

Gerçek kanonik dağılımlardan power-moment ile üretilir, `domain="anchor"`:

| Çapa | Kaynak |
|------|--------|
| ⊕ANCHOR:ZETA_ZEROS | İlk 50 Riemann sıfırı (sabitlenmiş) |
| ⊕ANCHOR:GUE_RANDOM_MATRIX | Wigner-Dyson GUE aralıkları |
| ⊕ANCHOR:PRIME_GAPS | Asal sayı aralıkları (2→3000) |
| ⊕ANCHOR:POISSON_PROCESS | Üstel aralıklı bağımsız noktalar |
| ⊕ANCHOR:GAUSSIAN_BELL | N(0.5, 0.15) örnekleri |
| ⊕ANCHOR:PERIODIC_LATTICE | Sinüzoidal (f=8Hz) |
| ⊕ANCHOR:UNIFORM_MEASURE | [0,1] düzgün dağılım |
| ⊕ANCHOR:EXPONENTIAL_DECAY | e^{-3t} |
| ⊕ANCHOR:LINEAR_RAMP | Aritmetik dizi |
| ⊕ANCHOR:GEOMETRIC_GROWTH | 1.03^n |

---

## Kapalı Döngü — ProofLoop (`research/proof_loop.py`)

```
NecessityEngine.find_manifold_gaps()
    → 5 boşluk bulundu (GATE_A_PERTURBATION cluster)
    → kampanya eşlemesi: GAP_TO_CAMPAIGN dict
ProofLoop.launch_campaign(name)
    → subprocess: python tools/tantrium_research_os.py --campaign <name>
ProofLoop.sync_new_theorems()
    → inject_math_kernel(engine) yeniden çalışır (idempotent)
engine.auto_persist()
```

**API:**
```python
import tantrium
ai = tantrium.AI()
report = ai.prove(max_cycles=3)  # kapalı döngü
print(report.total_new_concepts)
print(report.remaining_gaps)
```

---

## Research OS (`tantrium/research_os/`)

**ÖNEMLI:** `tantrium/` kökündeki paket `src/tantrium/` ile FARKLI.
- `src/tantrium/` → pip install, normal import
- `tantrium/research_os/` → sadece subprocess ile erişilir

Research OS subprocess çağrısı:
```bash
python tools/tantrium_research_os.py --campaign lah_gate_ab
```

**Geçerli kampanya isimleri:**
`subresultant_recurrence, lah, lah_gate_ab, coefficient_frontier, goldbach_minor_arc, rh_formalization, all`

---

## NecessityEngine (`reasoning/necessity.py`)

```python
ne = NecessityEngine(engine)
report = ne.run(domain="math_kernel", inject=True, find_gaps=True)
# report.necessary_edges → [NecessaryEdge(source, target, chain, is_new)]
# report.manifold_gaps   → [ManifoldGap(centroid, nearest_concepts, description)]
# report.edges_injected  → 42 (bu oturumda)
```

**ÖNEMLİ:** `domain="math_kernel"` kullan, `"theorem"` değil.

---

## Mevcut Durum (Son Ölçüm)

- **Kavram:** 39,918
- **TAU edge:** 654,834
- **Paradigma:** 23/23 (tüm geçerli girdiler geçiyor)
- **Theorem graph:** 94 node, 6 open/conjectural
- **NecessityEngine:** 42 zorunlu kenar, 5 manifold boşluğu
- **Çapalar:** 10 matematiksel kanonik dağılım
- **CertifiedTransport:** Çalışıyor — benzene DYADIC_FAILED, aspirin/caffeine CERTIFIED
- **Tests:** 92 geçiyor

---

## API Özeti

```python
import tantrium

ai = tantrium.AI()

# Durum
print(ai.status())
# "Tantrium AI  |  39,918 kavram  |  654,834 TAU kenar  |  Aleph-Tekin 23 paradigma"

# Sertifika
r = ai.ask("EGFR nedir?")
print(r.certified, r.paradigms_passed)   # True, 23

# Molekül certify
r = ai.certify("Erlotinib", smiles="COCCOC1=CC2=...", target="EGFR")

# Molekül üret
r = ai.discover("EGFR", top_k=5)
print(r.best.smiles, r.best.dyadic_score)

# Certified dyadic transport (3 katman)
tc = ai.transport("CCO", "aspirin", use_smiles=True)  # SMILES
print(tc.summary())  # CERTIFIED | dyadic=✓ | sturm=✓ | ζ-dist=2.09

tc = ai.transport("EGFR inhibitor", "kinase blocker")  # metin
print(tc.summary())

# Transport ile sıralama
ranking = ai.rank("EGFR", top_n=10)
print(ranking.certified_only())  # sadece CERTIFIED adaylar
print(ranking.best())             # en iyi (en düşük ζ-mesafe)

# Zorunlu kenarlar türet
r = ai.close(domain="math_kernel", inject=True)
print(r.edges_injected, len(r.manifold_gaps))  # 42, 5

# Research OS kapalı döngü
r = ai.prove(max_cycles=2, time_limit_s=180)
print(r.total_new_concepts, r.remaining_gaps)

# Öğrenme
result = ai.learn("EGFR is a receptor tyrosine kinase.")
print(result)  # {"new_concepts": n, "already_known": n, "relations": n, "persisted": bool}
```

---

## Sık Yapılan Hatalar

1. **`from tantrium.agi import ...`** → YOKTUR, agi/ katmanı silindi. Doğrusu: `from tantrium import ...`

2. **`domain="theorem"` NecessityEngine'e geçirme** → tüm 39k kavram → timeout. Doğrusu: `domain="math_kernel"`.

3. **`from tantrium.research_os import ...`** → ModuleNotFoundError. Doğrusu: subprocess ile `tools/tantrium_research_os.py`.

4. **inject_math_kernel() idempotent** — zaten manifoldda olanlar atlanır, yeni proven'lar eklenir.

5. **CertifiedTransport namespace**: `tantrium.transport.dyadic_flow` root `tantrium/` paketindedir (pip ile kurulmaz). `core/transport.py` `tantrium.__path__` üzerinden erişir.

6. **SMILES vs metin transport**: `ai.transport(src, tgt, use_smiles=True)` ECFP4 fingerprint kullanır. `use_smiles=False` (default) metin bigram kullanır.

---

## Matematiksel Temel

Tüm sistem şu özdeşliğe dayanır:

**Hamburger Teoremi:** Sınırlı destekli kompakt ölçü, moment dizisi tarafından TEK biçimde belirlenir.

**CertifiedTransport ↔ RH bağlantısı:**
- Sturm chain pivotları > 0 ↔ H(t) tüm t için PSD
- H(t) PSD ↔ interpolasyon yolu "gerçek ölçü" manifoldunda kalıyor
- ζ-sıfırları moment ailesi = Hamburger optimal ölçü

**D-positivity (ramp_top_coefficient)**:
`2^T_j * Π_{m=1}^j (n+m)^m` — bu katsayı Sturm pivot büyüme oranını verir.
`algebra/positivity.py:ramp_top_coefficient(j, n)` ile hesaplanır.
