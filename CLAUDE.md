# Tantrium — Sistem Hafızası

## Aktif Branch
`claude/seninle-agi-yapacagiz-XwJRz` — tüm geliştirme buraya.

## Temel Kural
`from tantrium.agi import ...` → YOK. Her şey düz: `from tantrium import ...`

---

## Proje Yapısı

```
src/tantrium/          ← pip install -e . ile kurulu paket
  ai.py                ← tantrium.AI() — SDK girişi
  core/
    encoder.py         ← girdi→moments (domain-blind)
    codex.py           ← 23 paradigma (verify() okur, hesaplamaz)
    pipeline.py        ← run_pipeline() L0-L7 sıralı hesaplama
    network.py         ← CertificationPipeline (topolojik DAG)
    engine.py          ← CertificationEngine (orkestratör)
    transport.py       ← CertifiedTransport (dyadic+Sturm+Zeta)
    semantic.py        ← SemanticManifold (40k kavram, L1 mesafe)
  proof/               ← dyadic ispat ilkleri (pip'ten erişilir)
    dyadic_flow.py     ← solve_greedy (Fraction aritmetik)
    certificate.py     ← Cell, Certificate, TransportEdge
  algebra/             ← Sturm, positivity, Sheffer
  graph/
    knowledge_graph.py ← KnowledgeGraph / TAU (654k+ edge)
    anchors.py         ← 10 kanonik dağılım (ZETA, GUE, ...)
    relations.py       ← semantik ilişki çıkarma
    memory.py          ← SessionMemory
  domains/
    bridge.py          ← paradigma→theorem eşlemesi
    math_kernel.py     ← inject_math_kernel() (theorem→manifold)
    certifier.py       ← MolecularCertifier
    generator.py       ← MoleculeGenerator
    spectral.py        ← SpectralMeasure, gram_spectrum
  reasoning/           ← NecessityEngine, reasoner, inference, thinker...
  research/            ← ProofLoop, explorer, researcher, ingest, goal, actor
  language/            ← CertifiedGenerator, Speaker, LanguageBootstrap
  meta/                ← MetaParadigm, MomentTopology

tantrium/              ← Research OS (SADECE subprocess ile erişilir)
  research_os/         ← run_campaigns()
  theorem_graph/       ← GraphStore, theorem_graph.yaml
  positivity_machine.py

tools/                 ← 5 CLI script
  tantrium_research_os.py     ← Research OS CLI (ProofLoop subprocess target)
  proof_loop_demo.py
  ingest_real_world.py
  autonomous_research_session.py
  grow_manifold.py

results/agi/
  manifold.json        ← 39,929 kavram (kalıcı)
  tau_graph.json       ← 654,962+ edge (kalıcı)
  spectral_cache.json
```

---

## Felsefe

```
girdi → A matris → G=AᵀA (daima PSD) → μ_k=Tr(G^k)/n → 8 moment
```
Hamburger Teoremi: kompakt destekli ölçü moment dizisiyle tek biçimde belirlenir.
Encoder "çevirmez" — okur. DNA, molekül, cümle, asal sayı — hepsi aynı formül.

---

## 23 Paradigma (L0-L7 Pipeline Sırası)

| Aşama | Paradigma | Hesaplama |
|-------|-----------|-----------|
| L2.5 | DALET | eigvalsh(Gram) → gerçek eigenvalue'lar |
| L0.5 | BET | ‖A‖²_F = Tr(G) (Frobenius) |
| L1.5 | HE | V(k) = μ_k / λ_max^k |
| L2   | ZAYIN | path_sum = Tr(G), det(G) ayrıca |
| L3   | HET | Li: λ_n = Σ[1−(1−1/ρ)^n] > 0 |
| L4   | TAV | de Bruijn-Newman: Λ = −var₀ ≤ 0 |
| L5   | GIMEL | Achilles: zayıf paradigma yok |
| L6   | EMET | cross-check, çelişki yok |
| Yrd. | ALEPH,KAF,AYIN,MEM,LAMED,TET,YOD,RESH,TSADI,SHIN,PE,VAV,NUN,SU3,KUF | |

Gerçek ayrımcılık CertifiedTransport'ta: benzene DYADIC_FAILED, aspirin CERTIFIED.

---

## CertifiedTransport

```
Kaynak eigenvalues → Cell nesneleri (Fraction kütleler)
Hedef eigenvalues  → Cell nesneleri

1. DYADIC: solve_greedy → "verified_exact" veya FAIL
2. STURM:  H(t)=(1-t)H_src+t·H_tgt tüm t∈[0,1] için PSD
3. ZETA:   L1(hedef, ⊕ANCHOR:ZETA_ZEROS)

CERTIFIED = dyadic ✓ AND sturm ✓
```

**ÖNEMLİ:** SMILES için `structure["eigenvalues"]` = n×n moleküler Laplacian eigenvalue'ları.
Metin için = 4×4 Gram-Hankel eigenvalue'ları.

---

## ProofLoop (AGI ↔ Research OS)

```python
ai.prove(max_cycles=3)
  → NecessityEngine.find_manifold_gaps()       # boşluk tespiti
  → subprocess: tantrium_research_os.py --campaign <name>  # ispat
  → update_theorem_graph_from_campaigns()       # theorem_graph.yaml güncelle
  → inject_math_kernel(engine)                  # manifolda ekle
  → engine.auto_persist()                       # kaydet
```

Research OS subprocess:
```bash
python tools/tantrium_research_os.py --campaign subresultant_recurrence
# Geçerli kampanyalar: subresultant_recurrence, lah_gate_ab,
#   coefficient_frontier, goldbach_minor_arc, rh_formalization, all
```

NecessityEngine: `domain="math_kernel"` kullan (domain="theorem" → timeout).

---

## API

```python
import tantrium
ai = tantrium.AI()

ai.status()                                    # kavram/edge/paradigma sayısı
ai.ask("EGFR")                                 # → CertificationRun (23 paradigma)
ai.transport("CCO", "aspirin", use_smiles=True)# → TransportCertificate
ai.rank("EGFR", top_n=10)                      # → TransportRanking
ai.prove(max_cycles=2)                         # → LoopReport (kapalı döngü)
ai.close(domain="math_kernel", inject=True)    # → NecessityReport
ai.learn("EGFR is a receptor tyrosine kinase") # → {"new_concepts": n, ...}
ai.think("protein folding")                    # → ThinkingResult
ai.discover("EGFR", top_k=5)                   # → molekül keşfi
```

---

## Kritik Pitfall'lar

1. `from tantrium.agi import ...` → YOK.
2. `domain="theorem"` NecessityEngine'e → timeout. Doğrusu: `domain="math_kernel"`.
3. `from tantrium.research_os import ...` → ModuleNotFoundError. subprocess kullan.
4. `inject_math_kernel()` idempotent — mevcut kavramları geçer.
5. `transport.py` artık `tantrium.proof.dyadic_flow` import eder (`tantrium.transport` değil).

---

## Mevcut Durum

- Kavram: 39,929 | TAU edge: 654,962+ | Paradigma: 23/23
- Theorem graph: 9 node, 9/9 CERTIFIED
- ProofLoop: TAM KAPALI — subresultant_recurrence kampanyası çalışıyor
- Tests: 92 geçiyor
