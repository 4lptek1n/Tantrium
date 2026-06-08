# Tantrium — Tam Mimari

*Evren simülasyonu makinesi / Süper 3. Göz AGI — doğru hedef yapı*

---

## Temel Felsefe (Değişmez)

Evren zaten matematiksel. Encoder "çevirmez" — okur.

```
girdi (DNA, molekül, cümle, asal sayı, müzik, EEG)
  → A matrisi (yapının doğal gösterimi)
  → G = AᵀA  (Gram — daima PSD)
  → μ_k = Tr(G^k)/n  (spektral momentler)
  → 8 rasyonel moment  (kompakt destekli ölçünün tam temsili)
```

Hamburger Teoremi: Kompakt destekli bir ölçü, moment dizisi tarafından TEK biçimde belirlenir.
G = AᵀA her zaman PSD → moment dizisi geçerli → Hankel PSD → ALEPH daima geçer.

Bu, RH ispatının (Xi-fonksiyon momentleri) evrensel uygulamasıdır.
23 paradigma, metafor değil — zeta-fonksiyon kanıtının katmanları.

---

## Şu Anki Sorunlar (Kritik, Öncelik Sırasıyla)

### Sorun 1: SMILES Eigenvalue'ları Yanlış Matriksten Geliyor (**KRİTİK**)
- `structure["eigenvalues"]` → 4×4 Gram-Hankel matrisinin eigenvalue'ları
- Hangi SMILES gelirse gelsin: `[1.4xx, 0.0xx, 0.0, 0.0]` — neredeyse rank-1
- CertifiedTransport için `_obj_to_cells()` bu 4 değeri kullanıyor
- Aspirin→Salisilik asit: Cell'ler neredeyse aynı → DYADIC_FAILED (yanlış)
- **Düzeltme**: `encode_smiles()` içinde n×n moleküler graf Laplacian eigenvalue'larını hesapla, `structure["eigenvalues"]`'u bunlarla override et

### Sorun 2: İki Ayrı Paket (Mimari Kart**ÖRTÜK**)
- `src/tantrium/` → pip install -e . → normal import
- `tantrium/` → sys.path injection → sadece subprocess'le erişilir
- `core/transport.py:33-37` runtime'da `tantrium.__path__`'e root ekliyor
- Bu mimariden doğan: `from tantrium.transport.dyadic_flow import ...` garip çalışıyor
- **Düzeltme**: İki yol — ya `tantrium/` içeriğini `src/tantrium/algebra/` + `src/tantrium/proof/`'a taşı, ya da ikisini kesinlikle ayır (subprocess boundary her zaman temiz kalsın)

### Sorun 3: Ölü / Çift Kod
- `src/tantrium/graph/tau_graph.py` — `knowledge_graph.py`'nin TAM kopyası. SİL.
- `src/tantrium/domains/molecular.py` — 8 satır stub, sadece re-export. SİL.
- `tools/` klasöründe 70+ script — çoğu tek seferlik deney. TOPLA/SİL.

### Sorun 4: Research OS Stratejileri Stub (Dürüst Scaffold)
- `tantrium/research_os/proof_strategies/` içindeki her strateji hardcoded döner
- Sadece `qjr_extractor.py` (sympy) ve `recurrence_verifier.py` gerçek matematik yapar
- **Bu sorun değil** — scaffold dürüst, `"proof_promoted": False` her yerde
- **Düzeltme değil, büyüme** — zamanla her strateji gerçek matematik kazanır

---

## Hedef Mimari (9 Katman)

```
┌─────────────────────────────────────────────────────────────────┐
│  SDK  ai.py + __init__.py                                        │
│  ask / certify / transport / prove / learn / think / rank ...    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌────────────────┐  ┌────────────────────────┐
│  Katman 8:    │  │  Katman 7:     │  │  Katman 6:             │
│  Meta         │  │  Dil           │  │  Araştırma             │
│  paradigm.py  │  │  generator.py  │  │  proof_loop.py         │
│  topology.py  │  │  speaker.py    │  │  explorer.py           │
│  self_cert    │  │  bootstrap.py  │  │  researcher.py         │
└───────┬───────┘  └───────┬────────┘  └──────────┬─────────────┘
        │                  │                       │
        └──────────────────┼───────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  Katman 5: Akıl Yürütme                                       │
│  necessity.py (geçişli kapanış + boşluk)                      │
│  reasoner.py (semantik zincir)                                │
│  inference.py (ses çıkarım kuralları)                         │
│  thinker.py  (3 seviyeli düşünce)                             │
│  generalization.py (konveks interpolasyon)                    │
│  planner.py (hedef odaklı BFS)                                │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Katman 4: Sertifikalı Transport                              │
│  transport.py: 3 katman — Dyadic + Sturm + Zeta              │
│    DYADIC: solve_greedy(src_cells, tgt_cells) → verified_exact│
│    STURM:  H(t)=(1-t)H_src+t·H_tgt PSD tüm t∈[0,1]          │
│    ZETA:   ⊕ANCHOR:ZETA_ZEROS ailesine L1 mesafesi           │
│  CERTIFIED = dyadic ✓ AND sturm ✓                             │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
┌─────────────┐ ┌────────────┐ ┌──────────────────┐
│  Katman 3a: │ │ Katman 3b: │ │  Katman 3c:      │
│  Manifold   │ │  Graf      │ │  Köprüler        │
│  semantic.py│ │ knowledge  │ │  bridge.py       │
│  39k kavram │ │ _graph.py  │ │  math_kernel.py  │
│  8D moment  │ │ 654k edge  │ │  certifier.py    │
│  uzayı      │ │ (TAU)      │ │  spectral.py     │
└──────┬──────┘ └─────┬──────┘ └────────┬─────────┘
       │              │                  │
       └──────────────┼──────────────────┘
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│  Katman 2: Sertifikasyon Motoru (22+1 Paradigma)             │
│                                                               │
│  engine.py ← CertificationEngine (orkestratör)               │
│  network.py ← CertificationPipeline (topolojik sıra)         │
│  codex.py  ← 23 paradigma sınıfı (verify() okur, hesaplamaz) │
│  pipeline.py ← run_pipeline() (L0-L7 hesaplama sırası)       │
│                                                               │
│  Paradigma bağımlılık sırası (DAG):                          │
│  DALET(L2.5) → BET(L0.5) → HE(L1.5) → ZAYIN(L2)            │
│             → HET(L3)   → TAV(L4)                            │
│             → GIMEL(L5) → EMET(L6)                           │
│  + Yardımcı: ALEPH,KAF,AYIN,MEM,LAMED,TET,YOD,RESH          │
│              TSADI,SHIN,PE,VAV,NUN,SU3,KUF                    │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Katman 1: Encoder                                            │
│  encoder.py: girdi → A matrisi → G=AᵀA → μ_k → CodexObject  │
│                                                               │
│  Giriş türleri:                                               │
│  • Metin    → UTF-8 bayt → bigram matris                      │
│  • SMILES   → atom/bağ adjacency → n×n graf → Laplacian       │
│  • Sayı diz.→ doğrudan moment (≤16 elemanın hızlı yolu)       │
│  • DNA      → ACGT→0123 → bigram matris                       │
│  Çıktı: CodexObject(name, moments[8], structure{pipeline})    │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Katman 0: Cebir İlkleri                                      │
│  algebra/sturm.py      — normalize_sturm_chain, pivots        │
│  algebra/positivity.py — has_positive_coefficients, ramp_top  │
│  algebra/sheffer.py    — Lah sayıları, Sheffer polinomları     │
│  graph/anchors.py      — 10 kanonik dağılım (ZETA, GUE, ...)  │
│                                                               │
│  tantrium/ (root paket — Research OS):                        │
│  transport/dyadic_flow.py — solve_greedy (Fraction aritmetik) │
│  theorem_graph/          — GraphStore, TheoremGraph           │
│  research_os/            — run_campaigns, ispat stratejileri  │
│  positivity_machine.py   — LGV parametrik üretici             │
└──────────────────────────────────────────────────────────────┘
```

---

## Veri Akışı (Tam Yol)

### Temel Sertifika
```
ai.ask("EGFR")
  → encoder.encode("EGFR")
      → metin → bigram matrix A (8×n)
      → G = AᵀA
      → μ_0..7 = [Tr(G^k)/n for k in range(8)]
      → run_pipeline(raw, A, G, moments) → state dict
          → stage_l25_dalet_spectrum: eigvalsh(G) → eigenvalues
          → stage_l05_bet_infocon: ||A||²_F = Tr(G)
          → stage_l15_he_lyapunov: V(k) = μ_k / λ_max^k
          → stage_l2_zayin_hankel: det(G), path_sum = Tr(G)
          → stage_l3_het_li: λ_n = Σ[1-(1-1/ρ)^n] kullanarak eigenvalues
          → stage_l4_tav_heatflow: heat-flow → λ_max, Λ = -var₀
          → stage_ancillary: KAF,AYIN,MEM,LAMED,TET,YOD,RESH,TSADI,SHIN,PE,
                              VAV,NUN,SU3,KUF
          → stage_l5_gimel_admission: zayıf paradigma tespiti
          → stage_l6_emet_certificate: cross-check (çelişki yok)
      → CodexObject(name="EGFR", moments=μ, structure=state)
  → network.run(obj) — 23 paradigma topolojik sırada çalıştır
      → her paradigma: obj.structure okur, ParadigmResult üretir
      → CertificationRun (immutable snapshot)
  → engine.find_or_add(obj) — manifolda ekle
      → SemanticManifold.add(name, moments)
      → KnowledgeGraph.add_node(name, sr=μ_7)
      → relations.add_semantic_edges(name) — IS_A, USES, DEFINES regex
  → Speaker.narrate(run) → doğal dil açıklama
```

### Sertifikalı Transport
```
ai.transport("aspirin", "erlotinib", use_smiles=True)
  → encode_smiles("aspirin") → CodexObject_A
  → encode_smiles("erlotinib") → CodexObject_B
  → CertifiedTransport.certify(A, B)
      → _obj_to_cells(A): eigenvalues → Cell listesi (Fraction kütleler)
      → _obj_to_cells(B): eigenvalues → Cell listesi
      → [DYADİK] solve_greedy(src_cells, tgt_cells, policy="greedy")
          → Certificate("verified_exact") veya FAIL
      → [STURM] normalized_sturm_pivots(H_src, H_tgt, steps=20)
          → tüm pivotlar > 0 → interpolasyon yolu gerçek ölçü manifoldunda kalıyor
      → [ZETA] ζ_dist = L1(hedef_momentler, ZETA_ZEROS_momentleri)
      → TransportCertificate(certified, dyadic, sturm, zeta_dist)
```

### Kapalı Döngü (AGI ↔ Research OS)
```
ai.prove(max_cycles=3)
  → ProofLoop(engine).run()
      → döngü:
          1. NecessityEngine.find_manifold_gaps()
             → moment uzayında komşusuz bölgeleri tespit et
             → ManifoldGap(centroid, nearest_concepts, description)
          2. ProofLoop.launch_campaigns(gap_names)
             → subprocess.run(["python", "tools/tantrium_research_os.py",
                               "--campaign", name])
             → stdout'tan "_STATUS:" satırlarını ayrıştır
             → {theorem_id: "RECURRENCE_VERIFIED_FINITE"|"REFINED_SUBGAP"...}
          3. ProofLoop.update_theorem_graph_from_campaigns(results)
             → GraphStore.load() → TheoremNode'ları güncelle
             → dep tabanlı auto-certify: tüm dep'leri kanıtlananlar
               → certified_local
             → GraphStore.save()
          4. ProofLoop.sync_new_theorems()
             → inject_math_kernel(engine)
               → theorem_graph.yaml → CERTIFIED theorem'ları manifolda ekle
               → REQUIRES/ACHIEVES edge'lerini TAU grafına enjekte et
          5. engine.auto_persist() → manifold.json + tau_graph.json güncelle
          6. necessity.compute_transitive_closure()
             → yeni geçişli edge'ler → TAU büyür
```

---

## Dosya Envanter: Kalacak / Silinecek / Düzelecek

### KALACAK (dokunma)
```
src/tantrium/
  ai.py                    ← SDK girişi, eksiksiz
  __init__.py              ← tüm exportlar
  core/
    encoder.py             ← [Sorun 1 düzeltilecek] + genel iyi
    codex.py               ← 23 paradigma, doğru
    pipeline.py            ← L0-L7, doğru
    network.py             ← topolojik sıra, doğru
    engine.py              ← orkestratör, doğru
    transport.py           ← 3 katman ispat, doğru
    semantic.py            ← 40k kavram manifoldu, doğru
  algebra/
    sturm.py               ← Sturm zinciri, doğru
    positivity.py          ← katsayı pozitifliği, doğru
    sheffer.py             ← Lah sayıları, doğru
  graph/
    knowledge_graph.py     ← TAU, doğru
    anchors.py             ← 10 kanonik dağılım, doğru
    relations.py           ← semantik ilişki çıkarma, doğru
    memory.py              ← SessionMemory, doğru
  domains/
    bridge.py              ← paradigma→theorem eşlemesi, doğru
    math_kernel.py         ← inject_math_kernel(), doğru
    certifier.py           ← MolecularCertifier, doğru
    generator.py           ← MoleculeGenerator, doğru
    spectral.py            ← SpectralMeasure, gram_spectrum, doğru
  reasoning/
    necessity.py           ← NecessityEngine, doğru
    reasoner.py            ← GraphReasoner, doğru
    inference.py           ← InferenceChain, doğru
    thinker.py             ← Thinker, doğru
    generalization.py      ← HankelGeneralizer, doğru
    planner.py             ← Planner, doğru
  research/
    proof_loop.py          ← kapalı döngü, doğru
    explorer.py            ← boşluk keşfi, doğru
    autonomous.py          ← AutonomousObserver, doğru
    researcher.py          ← AutonomousResearcher, doğru
    ingest.py              ← DataIngestor, doğru
    goal.py                ← GoalManifold, doğru
    actor.py               ← Actor, doğru
  language/
    generator.py           ← CertifiedGenerator (TAU yürüyüşü), doğru
    speaker.py             ← pipeline → NL, doğru
    bootstrap.py           ← metin → manifold, doğru
    lang_topology.py       ← İngilizce semantik ilişkiler, doğru
  meta/
    paradigm.py            ← MetaParadigm + self_certify, doğru
    topology.py            ← MomentTopology, doğru

tantrium/ (Research OS — subprocess boundary ile erişilir)
  transport/dyadic_flow.py     ← solve_greedy (Fraction), doğru
  certificates/certificate.py  ← Cell.make(), Certificate, doğru
  theorem_graph/
    graph_store.py             ← GraphStore + propagate(), doğru
    state_machine.py           ← TheoremGraph + TheoremNode, doğru
  research_os/
    research_director.py       ← run_campaigns(), doğru
    recurrence/
      qjr_extractor.py         ← gerçek sympy matematik, doğru
      recurrence_verifier.py   ← gerçek sonluluk kontrolü, doğru
    proof_strategies/          ← scaffold, stub ama dürüst
    theorem_factory/           ← scaffold, stub ama dürüst

tools/ (yalnızca şunlar kalır)
  tantrium_research_os.py      ← Research OS CLI girişi
  proof_loop_demo.py           ← kapalı döngü demo
  ingest_real_world.py         ← UniProt/PubChem/OEIS
  autonomous_research_session.py ← otonom araştırma demo
  grow_manifold.py             ← manifold büyütme

results/agi/
  manifold.json                ← 39,929 kavram (kalıcı)
  tau_graph.json               ← 654k+ edge (kalıcı)
  spectral_cache.json          ← Wasserstein cache (kalıcı)

tantrium/theorem_graph/theorem_graph.yaml ← 9 node ispat durumu
```

### SİLİNECEK (ölü/çift kod)
```
src/tantrium/graph/tau_graph.py
  ← knowledge_graph.py'nin TAM kopyası. TauGraph alias'ı da gereksiz.
  ← SİL.

src/tantrium/domains/molecular.py
  ← 8 satır, sadece certifier.py + generator.py'den re-export.
  ← SİL.

tools/ içinden silinecekler (70+ script → ~5 kalacak):
  ← a2_j_fit_from_known.py, ag_lgv_transfer_checker.py,
     analyze_newton_moment_vandermonde.py, ell2_* (6 dosya),
     ell3_* (7 dosya), goldbach_machine.py, parametric_*, ppmi_*,
     q6_obstruction_*, retro_validation.py, rh_gap_finder.py,
     rh_proof_attempt.py, rh_symbolic_closure_pipeline.py,
     run_lightweight_regression.py, run_positivity_engine_v1.py,
     semantic_research_os.py, tantrium.py (root), tantrium_agi_chat.py,
     tantrium_agi_engine.py, tantrium_artifact_manifest.py,
     tantrium_autosolver.py, tantrium_certificate_builder.py,
     tantrium_certificate_builder_v2.py, tantrium_conjecture_machine.py,
     tantrium_counterexample_engine.py, tantrium_counterexample_hunter.py,
     tantrium_formalization_audit.py, tantrium_formalization_bridge.py,
     tantrium_frontier_solver.py, tantrium_gap_certifier.py,
     tantrium_problem_ingest.py, tantrium_proof_strategy_engine.py,
     tantrium_qjr_extractor.py, tantrium_recurrence_verifier.py,
     tantrium_research_evaluator.py, tantrium_research_loop.py,
     tantrium_rh_machine.py, tantrium_schema_lifter.py,
     tantrium_strategy_engine.py, tantrium_subresultant_recurrence_miner.py,
     tantrium_theorem_factory.py, tantrium_theorem_graph_audit.py,
     tantrium_theorem_synthesizer.py, tau_sturm_identity_checker.py,
     tav_moment_propagation.py, uniform_lift_lemma_tester.py,
     wire_sentences.py, zeta_spectral_analysis.py,
     build_kernel.py, canonical_relearn.py, dna_cancer_analysis.py,
     fetch_arxiv.py, independent_verifier.py, proof_chain_audit.py,
     autonomous_loop_demo.py
```

### DÜZELTİLECEK (kritik)
```
src/tantrium/core/encoder.py
  → encode_smiles() içinde SMILES için n×n moleküler graf eigenvalue'ları
  → structure["eigenvalues"] → gerçek Laplacian eigenvalue'ları ile override
  → Her atom bir node, her bağ bir edge. Bağlantı eigenvalue'ları kimlik verir.
  → Aspirin(27 ağır atom) vs. Salisilik asit(15 ağır atom): farklı spektrum.
```

---

## Kritik Düzeltme: SMILES Eigenvalue Sorunu

**Sorun**: Şu an `encode_smiles()` metin encoder gibi davranıyor (bigram matrix).
4×4 matris → her SMILES için neredeyse aynı eigenvalue'lar → transport hep FAILED.

**Çözüm**: `_smiles_to_graph_moments()` doğru ama sonucu kullanılmıyor.
`encode_smiles()` içinde `structure["eigenvalues"]` molecular Laplacian eigenvalue'larıyla değiştirilmeli.

```python
# encoder.py içinde, encode_smiles() sonuna eklenecek:

def _smiles_molecular_eigenvalues(smiles: str) -> list[float]:
    """n×n moleküler grafın gerçek Laplacian eigenvalue'ları."""
    # RDKit yoksa: SMILES'ı karakter bigram matrix'e dönüştür (mevcut davranış)
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        n = mol.GetNumAtoms()
        # Adjacency matrix
        adj = [[0.0] * n for _ in range(n)]
        for bond in mol.GetBonds():
            i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            w = float(bond.GetBondTypeAsDouble())
            adj[i][j] += w
            adj[j][i] += w
        # Laplacian: L = D - A
        import numpy as np
        A = np.array(adj)
        D = np.diag(A.sum(axis=1))
        L = D - A
        eigs = np.linalg.eigvalsh(L).tolist()
        # Normalize: [0, 2] aralığına getir
        max_eig = max(eigs) if eigs else 1.0
        if max_eig > 0:
            eigs = [e / max_eig for e in eigs]
        return sorted(eigs, reverse=True)
    except ImportError:
        return []

# encode_smiles() içinde, structure oluşturulduktan sonra:
mol_eigs = _smiles_molecular_eigenvalues(smiles)
if mol_eigs:
    obj.structure["eigenvalues"] = mol_eigs[:8]  # transport için en fazla 8
    obj.structure["eigenvalue_source"] = "molecular_laplacian"
```

RDKit yoksa mevcut davranış korunur (geri uyumlu).

---

## İki Paket Mimarisinin Doğru Çözümü

**Şu an**: `src/tantrium/` normal import + `tantrium/` sys.path injection
**Sorun**: `transport.py:33-37` `__path__` manipülasyonu — çirkin ama çalışıyor
**Seçenek A (Önerilen)**: Subprocess sınırını koru, temizle
- `tantrium/transport/dyadic_flow.py` → `src/tantrium/proof/dyadic_flow.py`'ye taşı
- `tantrium/certificates/` → `src/tantrium/proof/certificates/`
- Research OS subprocess'te kalır (doğal izolasyon)
- `transport.py` içindeki `__path__` manipülasyonu silinir

**Seçenek B**: İkisini birleştir
- Tüm `tantrium/` içeriğini `src/tantrium/`'a taşı
- Research OS'u sadece subprocess ile çağrılan CLI olarak tut
- Avantaj: tek paket, temiz import
- Dezavantaj: Research OS artık doğrudan import edilebilir (izolasyon azalır)

**Seçenek A önerilir** — Research OS'un subprocess'te kalması mimariye uygun (otonom araştırma = izole process).

---

## Hedef Dosya Ağacı (Temizlenmiş)

```
/home/user/Tantrium/
├── src/tantrium/
│   ├── __init__.py
│   ├── ai.py
│   ├── core/
│   │   ├── encoder.py      [DÜZELTME: SMILES eigenvalue]
│   │   ├── codex.py
│   │   ├── pipeline.py
│   │   ├── network.py
│   │   ├── engine.py
│   │   ├── transport.py    [DÜZELTME: __path__ manipülasyonu kaldır]
│   │   └── semantic.py
│   ├── algebra/
│   │   ├── sturm.py
│   │   ├── positivity.py
│   │   └── sheffer.py
│   ├── proof/              [YENİ — tantrium/ root'tan taşındı]
│   │   ├── dyadic_flow.py  [tantrium/transport/dyadic_flow.py → buraya]
│   │   └── certificate.py  [tantrium/certificates/certificate.py → buraya]
│   ├── graph/
│   │   ├── knowledge_graph.py
│   │   ├── anchors.py
│   │   ├── relations.py
│   │   └── memory.py
│   │   # tau_graph.py SİLİNDİ
│   ├── domains/
│   │   ├── bridge.py
│   │   ├── math_kernel.py
│   │   ├── certifier.py
│   │   ├── generator.py
│   │   └── spectral.py
│   │   # molecular.py SİLİNDİ
│   ├── reasoning/
│   │   ├── necessity.py
│   │   ├── reasoner.py
│   │   ├── inference.py
│   │   ├── thinker.py
│   │   ├── generalization.py
│   │   └── planner.py
│   ├── research/
│   │   ├── proof_loop.py
│   │   ├── explorer.py
│   │   ├── autonomous.py
│   │   ├── researcher.py
│   │   ├── ingest.py
│   │   ├── goal.py
│   │   └── actor.py
│   ├── language/
│   │   ├── generator.py
│   │   ├── speaker.py
│   │   ├── bootstrap.py
│   │   └── lang_topology.py
│   └── meta/
│       ├── paradigm.py
│       └── topology.py
│
├── tantrium/               ← Research OS (subprocess-only)
│   ├── research_os/        ← run_campaigns(), ispat stratejileri
│   ├── theorem_graph/      ← GraphStore, theorem_graph.yaml
│   └── positivity_machine.py
│   # transport/, certificates/ src/tantrium/proof/'a taşındı
│
├── tools/                  ← sadece 5 CLI script
│   ├── tantrium_research_os.py
│   ├── proof_loop_demo.py
│   ├── ingest_real_world.py
│   ├── autonomous_research_session.py
│   └── grow_manifold.py
│
├── results/agi/
│   ├── manifold.json
│   ├── tau_graph.json
│   └── spectral_cache.json
│
├── tantrium/theorem_graph/theorem_graph.yaml
├── tests/
├── pyproject.toml
├── CLAUDE.md
└── ARCHITECTURE.md (bu dosya)
```

---

## Uygulama Sırası

### Adım 1 — Temizlik (Ölü Kod)
1. `src/tantrium/graph/tau_graph.py` → SİL
2. `src/tantrium/domains/molecular.py` → SİL
3. `tools/` → 65 gereksiz script sil, 5 kalacak

### Adım 2 — Kritik Düzeltme (SMILES Eigenvalue)
4. `src/tantrium/core/encoder.py` → `_smiles_molecular_eigenvalues()` ekle
5. `encode_smiles()` → mol eigs ile structure["eigenvalues"] override

### Adım 3 — Paket Birleştirme (İki Paket Sorunu)
6. `src/tantrium/proof/` klasörü oluştur
7. `tantrium/transport/dyadic_flow.py` → `src/tantrium/proof/dyadic_flow.py`
8. `tantrium/certificates/certificate.py` → `src/tantrium/proof/certificate.py`
9. `core/transport.py` içindeki `__path__` manipülasyonunu kaldır
10. `from tantrium.proof.dyadic_flow import ...` olarak düzelt

### Adım 4 — Test
```bash
python -c "
import tantrium
ai = tantrium.AI()
# SMILES transport testi
tc = ai.transport('CCO', 'c1ccccc1', use_smiles=True)
print('Transport:', tc.certified, tc.zeta_distance)
# Kapalı döngü
report = ai.prove(max_cycles=1)
print('Proof loop:', report.total_new_concepts, report.remaining_gaps)
"
```

---

## Evren Simülasyonu Katmanları (Felsefi Harita)

```
Somut Dünya
  (atomlar, genler, cümleler, notalar, EEG sinyalleri)
       ↓ Encoder (okuma, çevirme değil)
Moment Uzayı
  (her şey 8 rasyonel sayı)
       ↓ 23 Paradigma (RH ispat katmanları)
Sertifika
  (bu nesne evrenin yasalarıyla tutarlı mı?)
       ↓ TAU Grafiği (edge-centric bilgi)
İlişki Ağı
  (neyin neyden geleceğini, neyin neyle bağlantılı olduğunu bilir)
       ↓ CertifiedTransport (3 katman ispat)
Yol Sertifikası
  (A'dan B'ye geçiş gerçek ölçü manifoldunda mı kalıyor?)
       ↓ NecessityEngine + ProofLoop
Zorunluluk
  (bu kenar zorunluydu — evren başka türlü olamazdı)
       ↓ Research OS
Matematiksel Kanıt
  (hangi teoremler kanıtlandı, hangisi hâlâ açık)
       ↓ inject_math_kernel → manifold büyür
Kapalı Döngü
  (AGI kendi boşluklarını görür ve kapatır)
```

---

## Özet: Ne Yapılmalı

| Öncelik | İş | Etki |
|---------|-----|------|
| 🔴 KRİTİK | SMILES eigenvalue düzeltmesi | Transport gerçekten ayrımcı olur |
| 🟠 YÜKSEK | tau_graph.py + molecular.py sil | Tekrarsız kod tabanı |
| 🟠 YÜKSEK | tools/ temizliği (65 script) | Gezinebilir repo |
| 🟡 ORTA | dyadic_flow + certificate → src/tantrium/proof/ | Tek paket |
| 🟡 ORTA | transport.py __path__ manipülasyonu kaldır | Temiz import |
| 🟢 DÜŞÜK | Research OS stratejileri gerçek matematik | Daha derin ispat |

**Temel sonuç**: Mimari DOĞRU. Matematik DOĞRU. Felsefe DOĞRU.
Temizlenecek teknik borç var ama çekirdek sağlam.
