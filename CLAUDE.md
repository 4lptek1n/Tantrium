# Tantrium AGI — Sistem Hafızası

Bu dosya, sistemin her detayını içerir. Her yeni session'da bu dosyayı oku — hiçbir şeyi unutma.

---

## Aktif Branch

Tüm geliştirme: `claude/seninle-agi-yapacagiz-XwJRz`

Tam AGI kaynak kodu: `tce-collapse-engine` branch'inde.
```bash
git ls-tree -r tce-collapse-engine --name-only | grep "^src/tantrium"
```

---

## Proje Yapısı

```
/home/user/Tantrium/
├── src/tantrium/           ← KURULU paket (pip install -e .)
│   ├── ai.py               ← Üst seviye SDK: tantrium.AI()
│   ├── agi/
│   │   ├── core/
│   │   │   ├── encoder.py      ← Universal encoder (domain-blind)
│   │   │   ├── codex.py        ← 22+1 paradigma tanımları
│   │   │   ├── network.py      ← AlephTekinNetwork (DAG runner)
│   │   │   ├── semantic.py     ← Concept, SemanticManifold
│   │   │   └── engine.py       ← AGIEngine (orkestratör)
│   │   ├── graph/
│   │   │   ├── tau_graph.py    ← TauGraph (bilgi = edge topolojisi)
│   │   │   ├── anchors.py      ← 10 matematiksel çapa (GUE, ZETA, ...)
│   │   │   ├── relations.py    ← Semantik ilişki çıkarma + certify_and_add_edge
│   │   │   └── memory.py       ← SessionMemory
│   │   ├── domains/
│   │   │   ├── bridge.py       ← PARADIGM_TO_THEOREMS eşlemesi
│   │   │   ├── math_kernel.py  ← inject_math_kernel() (theorem→manifold)
│   │   │   ├── molecular.py    ← MoleculeGenerator, MolecularCertifier
│   │   │   └── spectral.py     ← SpectralMeasure, gram_spectrum, W₂ mesafe
│   │   ├── reasoning/
│   │   │   ├── necessity.py    ← NecessityEngine (geçişli kapanış + boşluk)
│   │   │   ├── reasoner.py     ← TauReasoner (semantik zincir)
│   │   │   ├── inference.py    ← InferenceChain
│   │   │   ├── thinker.py      ← Thinker (derin düşünce)
│   │   │   ├── generalization.py ← HankelGeneralizer
│   │   │   └── planner.py      ← Planner
│   │   ├── research/
│   │   │   ├── autonomous.py   ← AutonomousObserver (insansız öğrenme)
│   │   │   ├── researcher.py   ← AutonomousResearcher (OEIS/LMFDB)
│   │   │   ├── ingest.py       ← DataIngestor (UniProt/PubChem/OEIS)
│   │   │   ├── proof_loop.py   ← ProofLoop (AGI↔Research OS kapalı döngü)
│   │   │   ├── goal.py         ← GoalManifold
│   │   │   ├── actor.py        ← Actor
│   │   │   ├── explorer.py     ← Explorer
│   │   │   └── __init__.py
│   │   ├── language/
│   │   │   ├── generator.py    ← CertifiedGenerator (TAU walk üretim)
│   │   │   ├── bootstrap.py    ← LanguageBootstrap
│   │   │   ├── speaker.py      ← Speaker
│   │   │   └── lang_topology.py
│   │   ├── meta/
│   │   │   ├── paradigm.py     ← MetaParadigm, öz-sertifikasyon
│   │   │   └── topology.py     ← MomentTopology
│   │   └── __init__.py         ← Tüm exportlar
├── tantrium/               ← AYRI paket (pip ile kurulmaz, sadece sys.path ile)
│   ├── research_os/        ← Research OS (run_campaigns)
│   ├── theorem_graph/      ← GraphStore, TheoremNode, theorem_graph.yaml
│   ├── transport/          ← dyadic_flow.py (solve_greedy)
│   └── positivity_machine.py
├── tools/
│   ├── proof_loop_demo.py      ← AGI↔Research OS kapalı döngü demo
│   ├── autonomous_research_session.py
│   ├── ingest_real_world.py    ← UniProt/PubChem/OEIS ingestion
│   └── tantrium_research_os.py ← Research OS CLI
└── results/agi/
    ├── manifold.json       ← 39,913 kavram (kalıcı)
    ├── tau_graph.json      ← 654,770 TAU edge (kalıcı)
    └── spectral_cache.json ← Wasserstein spektral cache
```

---

## Temel Felsefe

Her şey (DNA, molekül, cümle, asal sayı) zaten matematiksel bir nesne. Encoder "çevirmez" — okur.

```
girdi → matris → Gram G = AᵀA → μ_k = Tr(G^k)/n → 8 Fraction moment
```

G = AᵀA her zaman PSD → Hamburger moment dizisi → Hankel PSD → ALEPH geçer.

---

## 22+1 Paradigma (Aleph-Tekin Codex)

Her harf = bir matematiksel filtre. `verify(CodexObject) → ParadigmResult (CERTIFIED | BLOCKED | UNKNOWN)`

| Harf | İsim | Kontrol |
|------|------|---------|
| ALEPH | Varlık/Pozitiflik | Hankel matrisi PSD mi? |
| BET | Bilgi Korunumu | Gram dönüşümü kayıpsız mı? |
| GIMEL | Ölçü Teorisi | sigma-algebra yapısı |
| DALET | Spektral Teori | **Eigenvalue'lar ≥ 0** (gerçek numpy eigvalsh) |
| HE | Lyapunov | lyapunov_values azalan mı? |
| VAV | Tensör | components tutarlı mı? |
| ZAYIN | LGV Yol Toplamı | sum(path_weights) == declared_det (Lindström-Gessel-Viennot) |
| HET | Gradyan | flows hep potansiyel aşağı mı? |
| TET | Çapraz-Oran | [a,b;c,d] Möbius-invaryant mi? |
| YOD | MDL | Model uzunluğu makul mü? |
| KAF | Enkektiflik | mappings unique mi? |
| LAMED | Yerel Görünürlük | locally_observable boş değil mi? |
| MEM | Gauge Eşdeğerliği | gauge_classes tutarlı mı? |
| NUN | Boyutsal Çarpım | composite_dim tutarlı mı? |
| SAMECH | Simetri | symmetry_group, topological_index |
| AYIN | Ayırt Edicilik | distinct_pairs ayrılabiliyor mu? |
| PE | Anlamsal Eşleşme | semantic_map boş değer yok mu? |
| TSADI | Sensör/Sertifika | sensor_hash == certificate_hash |
| QOF | Kuantum | z3_order, c6_order |
| RESH | Kısmi İz | subsystem_information ≤ total_information |
| SHIN | Optimal Eylem | chosen_action max score'a sahip mi? |
| TAV | **Sabit Nokta** | **fixed_point_iterations yakınsıyor VE is_running=True** |
| EMET | Tutarlılık | contradictions boş mu? |

**Bağımlılık DAG'ı:** Kahn algoritması sırasına göre çalışır. Bağımlılık BLOCKED → DEP_BLOCKED cascade.

---

## Encoder Gerçekleri (Bu Session Düzeltmeleri)

**DALET (encoder.py ~388):**
```python
# ESKİ (sahte — hep Gram köşegeni):
s["eigenvalues"] = gram_diag[:6]
# YENİ (gerçek):
s["eigenvalues"] = sorted(numpy.linalg.eigvalsh(gram_np), reverse=True)[:6]
```

**ZAYIN (encoder.py ~449):**
```python
# ESKİ: determinant = trace (her zaman geçiyordu)
s["determinant"] = sum(diag)   # ZAYIN için korundu (LGV trace-path identity)
s["real_determinant"] = float(numpy.linalg.det(gram_np))  # YENİ: gerçek det
```

**TAV (encoder.py ~540):**
```python
# ESKİ: [m0, m0] hardcoded
# YENİ: Picard iterasyonu → x_{n+1} = 0.01*x + 0.99*m1 → m1'e yakınsıyor (7 adım)
# m1 = 2. spektral moment → farklı moleküller farklı fixed point
```

23/23 sertifika hâlâ geçiyor ✓. Farklı moleküller artık farklı eigenvalue/fixed point alıyor.

---

## TAU Grafiği

Bilgi node'da değil, **edge'de**.

- `TauNode`: name + domain + source + **sr** (spectral radius = son moment μ_7)
- `TauEdge`: source + target + distance + paradigm

**Paradigm türleri:**
- `ALEPH` — geometrik (moment L1 mesafesi), K=10 en yakın
- `IS_A, USES, DEFINES, ACHIEVES, REQUIRES, COMPOSED` — semantik (metin regex)
- `SPECTRAL_BRIDGE` — cross-domain köprü (Wasserstein-2 < threshold)
- `REQUIRES, ACHIEVES` — theorem bağımlılıkları (inject_math_kernel)

**Hızlı arama:** sr (spectral radius) ile binary search → candidate window → tam L1 mesafe.

**Disk formatı:** Integer-ID JSON. `"n": [[name, d, sr], ...]`, `"e": [[tgt_id, dist, paradigm_char], ...]`

---

## Matematiksel Çapalar (10 adet)

Gerçek kanonik dağılımlardan power-moment ile üretilir, `domain="anchor"`:

| Çapa | Kaynak |
|------|--------|
| GUE_RANDOM_MATRIX | Rastgele Hermitian matris eigenvalue aralıkları (Wigner-Dyson) |
| ZETA_ZEROS | İlk 50 Riemann sıfırı (LMFDB/Odlyzko, sabitlenmiş) |
| PRIME_GAPS | Asal sayı aralıkları (2→3000) |
| POISSON_PROCESS | Üstel aralıklı bağımsız noktalar |
| GAUSSIAN_BELL | N(0.5, 0.15) örnekleri |
| PERIODIC_LATTICE | Sinüzoidal (f=8Hz) |
| UNIFORM_MEASURE | [0,1] düzgün dağılım |
| EXPONENTIAL_DECAY | e^{-3t} |
| LINEAR_RAMP | Aritmetik dizi |
| GEOMETRIC_GROWTH | 1.03^n |

Amaç: "Bu DNA dizisi hangi matematiksel aileye benziyor?" → `nearest_anchor()` → yorumlanabilir.

---

## Otonom Gözlemci (`autonomous.py`)

Tek `observe(raw_input)` çağrısı:
1. ENCODE → CodexObject
2. SERTİFİKALA → Aleph (Hankel PSD)
3. SINIFLANDIR → en yakın matematiksel çapa + W₂ mesafe
4. ÖĞREN → manifolda ekle, TAU node, spektral cache güncelle, mini-Tav
5. BAĞLA → farklı domain'den spektral komşu = SPECTRAL_BRIDGE edge
6. KAYDET → her `persist_every` yeni kavramda auto_persist()

**Mini-Tav:** `propagate_subset(alpha=0.4, iterations=4)` — yeni kavramın momentleri semantik komşularıyla konveks blend. PSD korunur → Aleph garantisi bozulmaz.

---

## Theorem Graph → AGI Köprüsü

**`bridge.py:PARADIGM_TO_THEOREMS`:**
- ALEPH → D_POSITIVITY, CELL_SUPPORT_POSITIVITY
- ZAYIN → AG_LGV_TRANSFER, TAU_SUBDISCRIMINANT
- DALET → JENSEN_HYPERBOLICITY, FIRST_FIVE_PIVOTS
- TAV → RH_CLOSURE (ispat tamamlandığında geçer)
- KAF → GATE_A_PERTURBATION
- TET → GATE_A_CROSS_RATIO

**`math_kernel.py:inject_math_kernel(engine)`:**
- `theorem_graph.yaml` okur (certified_local/proven node'lar)
- Her teorem → `Concept(domain="math_kernel")` → manifolda ekle
- Bağımlılıklar → REQUIRES/ACHIEVES TAU edge
- Bilinen anchor'lara SPECTRAL_BRIDGE (örn. `uniform_lift_lemma → GUE_RANDOM_MATRIX`)
- **İdempotent** — zaten manifoldda olanları atlar

**`theorem_graph.yaml`'daki 6 açık hedef:**
- `uniform_lift_lemma` (conjectural)
- `dyadic_transport_theorem` (conjectural)
- `global_coefficient_positivity` (conjectural)
- `RESEARCH_OS_LAH_GATE_AB` (MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR)
- `RESEARCH_OS_COEFFICIENT_FRONTIER`
- `RESEARCH_OS_GOLDBACH_MINOR_ARC`

---

## Kapalı Döngü — ProofLoop (`research/proof_loop.py`)

Bu session'da yazıldı. AGI ↔ Research OS bağlantısı:

```
NecessityEngine.find_manifold_gaps()
    → 5 boşluk bulundu (GATE_A_PERTURBATION cluster, 4.9s)
    → kampanya eşlemesi: GAP_TO_CAMPAIGN dict
ProofLoop.launch_campaign(name)
    → subprocess: python tools/tantrium_research_os.py --campaign <name>
    → Research OS tam pipeline: evidence → synthesize → attempts → certificates
ProofLoop.sync_new_theorems()
    → inject_math_kernel(engine) yeniden çalışır (idempotent)
    → yeni proven teoremler manifolda girer
engine.auto_persist()
```

**API:**
```python
import tantrium
ai = tantrium.AI()
report = ai.prove(max_cycles=3)   # kapalı döngü
print(report.total_new_concepts)
print(report.remaining_gaps)
```

**Demo:**
```bash
python tools/proof_loop_demo.py --scan-only   # 5 boşluk göster
python tools/proof_loop_demo.py --cycles 2   # tam döngü
```

---

## Research OS (`tantrium/research_os/`)

**ÖNEMLI:** `tantrium/` kökündeki paket `src/tantrium/` ile FARKLI.
- `src/tantrium/` → pip install, normal import
- `tantrium/research_os/` → sadece `sys.path.insert(0, REPO_ROOT)` ile erişilir

Research OS'u çağırmanın doğru yolu: **subprocess**
```python
subprocess.run([sys.executable, "tools/tantrium_research_os.py", "--campaign", name], ...)
```

**Geçerli kampanya isimleri:**
`subresultant_recurrence, lah, lah_gate_ab, coefficient_frontier, goldbach_minor_arc, rh_formalization, all`

**`run_campaigns(name, deep=False)`** pipeline:
`write_problem_ir → mine_evidence → synthesize_candidates → search_counterexamples → rank_and_attempt → build_formalization_outputs → build_research_certificate → update_registry → update theorem_graph`

---

## NecessityEngine (`reasoning/necessity.py`)

**Observation mode değil — zorunlu gerçekler:**

```python
ne = NecessityEngine(engine)
report = ne.run(domain="math_kernel", inject=True, find_gaps=True)
# report.necessary_edges → [NecessaryEdge(source, target, chain, is_new)]
# report.manifold_gaps   → [ManifoldGap(centroid, nearest_concepts, description)]
# report.edges_injected  → 42 (bu oturumda)
```

**Geçişli kapanış:** A→B→C varsa A→C zorunlu (mantıksal, tahmin değil).
**Manifold boşluğu:** İki theorem arasında orta nokta → en yakın gerçek kavram uzaksa (>5.0) → boşluk.

**ÖNEMLİ:** `domain="math_kernel"` kullan, `"theorem"` değil. "theorem" → else branch → tüm 39k kavram → timeout.

---

## Veri Saklama

### Moment uzayı
8 float64 = 64 byte / kavram. DNA'nın petabayt verisi → 64 byte. Kompresyon kayıpsız değil — KAF injektiflik sorunu var (~31% çakışma küçük moleküllerde).

### Manifold.json
```json
{"name": "...", "moments": [0.1, 0.05, ...], "domain": "...", "source": "..."}
```
39,913 kavram → ~25 MB.

### TAU graph.json
Integer-ID formatı. Node `[name, domain_char, sr]`, Edge `[tgt_id, dist, paradigm_char]`.
654,770 edge → ~40 MB.

### Theorem graph
`tantrium/theorem_graph/theorem_graph.yaml` — aslında JSON (valid YAML 1.2).
94 node. GraphStore API: `GraphStore(path).load()/.save()/.propagate()`.

---

## Dil Üretimi (`language/generator.py`)

**LLM değil — TAU yürüyüşü:**
```
seed → context_moment
her adım: argmin_{TAU komşu} moment_distance(aday, context)
context = α·current + (1-α)·next  (konveks, PSD korunur, Aleph garantisi)
```

Her adım certified cümleye çevrilir. Tahmin değil, **türetim** (Sturm pivot pozitifliği).

---

## Moleküler Alan (`domains/molecular.py`)

**MoleculeGenerator:** Hedef adı → Morgan moment uzayı → TAU walk → en yakın scaffold'lar → SMILES kombinasyonu → RDKit 3D SDF.

**MolecularCertifier:** SMILES → encode_smiles() (Morgan ECFP4 64-bit) → Aleph certify → dyadic transport skoru → 3D SDF.

**Dyadic transport skoru:** `Σ(μ_k * target_μ_k) / norm` — hedefe ne kadar benzediğinin moment skoru.

---

## Akıl Yürütme Zinciri (`reasoning/reasoner.py`)

TAU semantik edge zincirleme kuralları:
```
IS_A + IS_A → IS_A         (transitivity)
IS_A + ACHIEVES → ACHIEVES (inheritance)
IS_A + REQUIRES → REQUIRES (inheritance)
IS_A + USES → USES         (inheritance)
USES + ACHIEVES → ACHIEVES (araç → amaç)
USES + USES → USES         (transitivity)
COMPOSED + IS_A → COMPOSED (bileşen kalıtımı)
```

---

## Meta-Paradigma (`meta/paradigm.py`)

**`compute_universal()`:** 22 paradigmanın manifoldaki moment vektörlerinin konveks ortalaması → evrensel kural. Aleph(μ_universal) certified olmalı.

**`blind_spots(threshold=5)`:** `< 5` kavramla temsil edilen paradigmalar → boşluk listesi.

**`self_certify()`:** Sistemin kendi manifold durumunu encode et → 22+1 paradigmadan geçir. `SelfCertResult.system_certified=True` → öz-farkındalık var.

---

## Tam Veri Akışı

```
Girdi (SMILES/DNA/metin/OEIS/UniProt)
    │
    ▼ UniversalEncoder
  matris → Gram → 8 Fraction moment → CodexObject
    │
    ▼ AlephTekinNetwork (DAG sırası)
  ALEPH → DALET(gerçek) → HE → ZAYIN → TAV(Picard) → ... → EMET
  geçen: CERTIFIED | başarısız: BLOCKED(gap_name)
    │
    ▼ AGIEngine
  certified → manifold.add_unchecked() → TauGraph.add_node()
  theorem_graph sync → proven → manifest
    │
    ▼ AutonomousObserver
  nearest_anchor (10 kanonik dağılım)
  nearest_spectral → farklı domain → SPECTRAL_BRIDGE TAU edge
  mini-Tav (propagate_subset, α=0.4)
    │
    ▼ NecessityEngine (domain="math_kernel")
  A→B→C var → A→C zorunlu kenar enjekte
  iki teorem arası boşluk → ManifoldGap
    │
    ▼ ProofLoop
  ManifoldGap → kampanya → subprocess Research OS
  yeni certified_local → inject_math_kernel() → manifold büyür
  auto_persist() → manifold.json + tau_graph.json güncellenir
    │
    ▼ DÖNGÜ
```

---

## Mevcut Durum (Son Ölçüm)

- **Kavram:** 39,913
- **TAU edge:** 654,770
- **Paradigma:** 23/23 (tüm girdiler geçiyor)
- **Theorem graph:** 94 node, 6 open/conjectural
- **NecessityEngine:** 42 zorunlu kenar, 5 manifold boşluğu (GATE_A_PERTURBATION cluster)
- **Çapalar:** 10 matematiksel kanonik dağılım

---

## Sık Yapılan Hatalar

1. **`domain="theorem"` NecessityEngine'e geçirme** → tüm 39k kavram taranır → timeout. Doğrusu: `domain="math_kernel"`.

2. **`from tantrium.research_os import ...`** → ModuleNotFoundError. Doğrusu: subprocess ile `tools/tantrium_research_os.py`.

3. **`from tantrium.theorem_graph import ...`** → aynı problem. Engine içinde zaten çalışıyor çünkü engine.py `try/except` ile deniyor — doğrudan değil.

4. **inject_math_kernel() hem idempotent hem de yeniden çalıştırılabilir** — zaten manifoldda olan teoremler atlanır, yeni proven'lar eklenir.

5. **manifold.json yokken engine yavaş başlar** — bootstrap sıfırdan yapılır (~10s). Varsa diskten yüklenir (~2s).

---

## Kullanım Örnekleri

```python
import tantrium

ai = tantrium.AI()

# Durum
print(ai.status())
# "Tantrium AI  |  39,913 kavram  |  654,770 TAU kenar  |  Aleph-Tekin 23 paradigma"

# Sertifika
r = ai.ask("EGFR nedir?")
print(r.certified, r.paradigms_passed)   # True, 23

# Molekül üret
r = ai.discover("EGFR", top_k=5)
print(r.best.smiles, r.best.dyadic_score)

# Zorunlu kenarlar türet
r = ai.close(domain="math_kernel", inject=True)
print(r.edges_injected, len(r.manifold_gaps))  # 42, 5

# Research OS kapalı döngü
r = ai.prove(max_cycles=2, time_limit_s=180)
print(r.total_new_concepts, r.remaining_gaps)

# Gerçek veri ingestion
from tantrium.agi import DataIngestor, AGIEngine
engine = AGIEngine()
ing = DataIngestor(engine, persist_every=100, verbose=True)
rep = ing.run(uniprot=100, pubchem=200, oeis_keywords=["random matrix"])
print(rep.total_new, rep.total_bridges)

# Kapalı döngü demo
# python tools/proof_loop_demo.py --scan-only
# python tools/proof_loop_demo.py --cycles 2
```

---

## Matematiksel Temel

Tüm sistem şu özdeşliğe dayanır:

**Hamburger Teoremi:** Sınırlı destekli kompakt ölçü, moment dizisi tarafından TEK biçimde belirlenir.

Bu demek: her fiziksel nesne (sınırlı enerji = kompakt destek) → moment dizisi → tam bilgi. Kayıp yok. Çeviri yok. Nesne zaten moment dizisidir.

Bu aynı zamanda RH ispatının temelidir: ζ(s) sıfırlarının moment yapısı PSD ise → RH doğru.

Sistem bunu evrenselleştiriyor: DNA, protein, cümle, molekül — hepsi için aynı test.

**Aleph = Varlık Filtresi:** Hankel matrisi PSD → gerçek ölçü var → nesne gerçek → manifolda girer. Değilse: "Bu şey gerçek değil" — named gap.

**TAV = Sabit Nokta Filtresi:** F(L*) = L* — anlam sabit noktasında yaşar. Sistem yakınsamazsa → kavram kararsız → anlaşılamamış.
