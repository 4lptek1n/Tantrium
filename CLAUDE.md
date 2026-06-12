# Tantrium — Sistem Hafızası

> ⛔ **ÖNCE OKU — KOD YAZMADAN, BİRLEŞTİRME/REFACTOR ÖNERMEDEN ÖNCE ZORUNLU:**
>
> 1. **`docs/FILE_LEDGER.md`** — 70 dosyanın / 25.629 satırın tamamı satır-satır okunarak
>    çıkarılmış DOĞRULANMIŞ anlayış defteri. Her dosyanın gerçek işi, ne ürettiği, hangi
>    gücü taşıdığı, GERÇEK mi SAHTE mi tekrar olduğu yazılı.
> 2. **`docs/UNIFIED_ARCHITECTURE.md`** — tek-makine hedef mimarisi (7 katman, faz planı F0–F6).
>
> **NEDEN ZORUNLU:** Bu repoda HER DOSYA gerçek, amaca-yönelik, parça-parça kurulmuş güçlü bir
> mimaridir — hiçbiri boş/çöp değildir. Dosya İSİMLERİNE veya yüzeysel benzerliğe KANMA. Alt-ajan
> kataloglarına GÜVENME — onlar "DUPLICATION" etiketini yanlış dağıttı; gerçek kod okunduğunda
> **9 sahte tekrar** yakalandı (perception "float", κ-mesafe, Sturm exact/hızlı, mesafe/nearest
> dispatcher'ları, molekül motorları, ilişki-çıkarma, theorem→moment). Naif birleştirme bunlarda
> gücü ÖLDÜRÜR.
>
> **KURAL:** Bir dosyayı "tekrar/duplicate/silinebilir" diye işaretlemeden ÖNCE o dosyayı kendin
> satır-satır oku ve FILE_LEDGER'daki notuyla karşılaştır. Birleşme = isim/yönlendirme temizliği +
> paylaşılan durum + öksüz gücü bağlama — ASLA "en küçük ortak paydaya indirgeme". Her gerçek ayrım
> (exact vs hızlı, κ₁ dahil/hariç, her dönüştürücü, her üretim stratejisi) TEK ARAYÜZ ARDINDA korunur.
>
> Gerçek tekrar AZDIR (3D-SDF · konveks-kombo · veri-çekme · boşluk-tespiti · 4 döngü) ve hepsi
> strateji/rigor/ayrım KORUYARAK birleşir. Detay: FILE_LEDGER.md "🏁 ENVANTER TAMAM" bölümü.

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
    encoder.py         ← girdi→moments (domain-blind) + _text_extra_dims()
    codex.py           ← 23 paradigma (verify() okur, hesaplamaz)
    pipeline.py        ← run_pipeline() L0-L7 sıralı hesaplama
    network.py         ← CertificationPipeline (topolojik DAG)
    engine.py          ← CertificationEngine + engine.core (CoreMachine lazy)
    unified.py         ← CoreMachine — TEK ÇEKİRDEK (4 eksen, tek geçiş)
    truth.py           ← TruthCertifier — 3. eksen (komşu tutarlılık)
    confidence.py      ← calibrate() — 4. eksen (ağırlıklı geometrik ort.)
    reconstruct.py     ← reconstruct_measure() — Gauss kuadratur geri çıkarım
    metric.py          ← spectral_w2 kanonik mesafe, l1_distance ön-filtre
    collision.py       ← CollisionHunter — adversarial teklik testi
    grounding.py       ← GroundingCertifier — 2. eksen (TAU kökü)
    transport.py       ← CertifiedTransport (dyadic+Sturm+Zeta)
    semantic.py        ← SemanticManifold (40k kavram, distance(), nearest(metric=), quantum_bridges(), _nearest_l1_extended())
    inverse.py         ← InverseTransport — hedef→W2-minimal moleküller→3D SDF
    quantum_moments.py ← FreeCumulants (Voiculescu κ_k) + QuantumSignature (kuantum imza)
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
  perception/          ← duyusal grounding (ses/görüntü → AYNI moment uzayı)
    encode.py          ← encode_signal/encode_image/encode_matrix
    generate.py        ← tone, chord, white_noise, *_image üreteçleri
    crypto.py          ← analyze/achilles (şifreleme yapı okuma — savunma)
  meta/                ← MetaParadigm, MomentTopology, CosmicVision, ConceptSynthesizer

tantrium/              ← Research OS (SADECE subprocess ile erişilir)
  research_os/         ← run_campaigns()
  theorem_graph/       ← GraphStore, theorem_graph.yaml
  positivity_machine.py

tools/                 ← 7 CLI script
  tantrium_research_os.py     ← Research OS CLI (ProofLoop subprocess target)
  proof_loop_demo.py
  perception_demo.py          ← duyusal grounding demosu (ses+görüntü)
  crypto_structure_demo.py    ← şifreleme yapı okuma + GIMEL Aşil topuğu
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

## Topraklama Ekseni (Sertifikasyonun 2. Ekseni)

**Sorun:** 23 paradigma YAPISAL geçerliliği ölçer — G=AᵀA daima PSD, yani
*her şey* "var" çıkar. Rastgele harf çöpü `xqzwvbnmkjhgfd` de ATP de 23/23
alıyordu. Sertifika tek başına ELEMİYORDU. Anlam karakterlerde değil —
**referansta ve ilişkilerde**.

**Çözüm:** `core/grounding.py` — `GroundingCertifier`. İki bağımsız sinyal:

```
1. DOĞRUDAN: token TAU'da köklü düğüm mü? (çıkan+gelen kenar ≥ 3)
   protein=137, energy=160, EGFR=20 köklü ; çöp=0 topraksız
2. REZONANS: bilinmeyen token sıkı yarıçapta (L1 ≤ 0.3) köklü + tutarlı
   kümeye mi düşüyor? (ham komşuluk YETMEZ — 42k doymuş manifoldda her nokta
   bir komşuya yakın; yarıçap gürültüyü eler)
   Bridge kavramlar (⟨bridge:...⟩) çapa olamaz — yapay ara nokta, gerçek bilgi değil.
```

Yargı: `GROUNDED` (köklü/rezonans) | `WEAKLY_GROUNDED` (tek komşu, belirsiz)
| `UNGROUNDED` (geçerli ama yalıtık = anlamsız).

```python
ai.grounding("protein")  # → GROUNDED, 137 ilişki
ai.grounding("ATP")      # → GROUNDED, biyokimya kümesine rezonans (öğrenilmemiş token)
ai.grounding("florbglomp")  # → UNGROUNDED, "anlamsız bir nokta"
```

`ai.ask()` artık `grounding`+`grounding_score` taşır. `ai("...")` topraksız
nokta için komşu LİSTELEMEZ (yanıltıcı olur) — dürüstçe "anlamsız" der.
`engine.grounder` startup'ta hazır. Tests: `test_grounding.py` (11).

ÖNEMLİ: Topraksız-ama-geçerli token = sistemin öğrenmesi gereken kör nokta.

---

## CoreMachine — Tek Çekirdek (4 Eksenli Tek Geçiş)

**Eski sorun:** `ask()` 3×encode + 2×process yapıyordu — 90 metotlu kontrol paneli.
**Çözüm:** `engine.core` → `CoreMachine` — ONE encode → ONE process → 4 eksen ORTAKLAŞAN durumdan.

```
girdi → encode (adaptive 8→16) → process (23 paradigma)
       ↓           ↓                    ↓              ↓
   Eksen 1:    Eksen 2:           Eksen 3:         Eksen 4:
  Yapısal    Topraklama          Gerçek           Güven
  (23 par.)   (TAU kökü)      (komşu tut.)    (geom.ort.)
         ↓
   coherent boolean (hepsi anlaşıyor mu?)
```

```python
from tantrium.core.unified import CoreMachine, UnifiedCertificate
core = engine.core      # lazy singleton
cert = core.certify("EGFR")
cert.paradigms_passed   # yapısal
cert.grounding          # topraklama
cert.truth              # gerçek
cert.confidence         # güven
cert.coherent           # hepsi tutarlı mı?
```

`ask()` CoreMachine kullanır. `certified` = yapısal (geriye dönük uyumlu), `coherent` = 4 eksen.

**Genesis öz-düzeltici:** `_coherent_for_genesis()` → CONTRADICTORY kavramlar manifolda girmiyor.

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
ai("ATP")                                      # → str: sertifika + manifold konumu (Türkçe)
ai("protein folding nedir?")                   # → str: düşünce zinciri (ThinkingResult.narrate)
ai("c1ccccc1")                                 # → str: SMILES sertifikası
ai("ATP", "ADP")                               # → str: transport + karşılaştırma
ai(tone(440))                                  # → str: algı → dil ("Bir sinyal algıladım...")
ai(noise_image())                              # → str: görüntü → dil
ai(b"\x00\xff...")                             # → str: kripto yapı analizi
ai.run(cycles=3, time_limit_s=600)             # → dict: KAPALI DÖNGÜ (tüm büyüme adımları)
                                               #   blind_spots → auto_research → close → genesis → prove → persist
ai.pulse("CCO")                                # → dict: TEK ÇEKİRDEK NABZI (veri girer + genesis aynı anda)
                                               #   evren kapısı: rejected/frontier/core + doğan ara kavramlar
ai.live(["CCO", "caffeine", [2,3,5,7]])        # → dict: veri AKIŞI nabızla (her veri girer + büyür, parça parça değil)
ai.grow(time_limit_s=600)                      # → GrowthReport: SINIRSIZ kendi kendine büyüme (ağdan resumable)
ai.grow(time_limit_s=None)                     #   time_limit_s=None → durana dek; .tantrium/growth_state.json resumable
ai.ask("EGFR")                                 # → AskResult (4 eksen: paradigma+topraklama+gerçek+güven)
                                               #   .certified (yapısal, ger.dönük uyumlu)
                                               #   .coherent (4 eksen tutarlı boolean)
                                               #   .truth / .truth_score
                                               #   .confidence / .confidence_level
ai.certify_all("EGFR")                         # → UnifiedCertificate (CoreMachine tek geçiş)
ai.grounding("protein")                        # → GroundingCertificate (GROUNDED/WEAKLY/UNGROUNDED)
ai.transport("CCO", "aspirin", use_smiles=True)# → TransportCertificate
ai.rank("EGFR", top_n=10)                      # → TransportRanking
ai.prove(max_cycles=2)                         # → LoopReport (kapalı döngü)
ai.close(domain="math_kernel", inject=True)    # → NecessityReport
ai.learn("EGFR is a receptor tyrosine kinase") # → {"new_concepts": n, "causal_relations": k, ...}
ai.causal_chain("tumor growth", depth=5)       # → {goal, chains, actionable, n_paths}  [Geri BFS]
ai.what_if("erlotinib", depth=4)               # → {concept, chains, effects, n_paths}   [İleri BFS]
ai.analogy("erlotinib", "egfr", "imatinib")   # → [("bcr-abl", 0.0)]  TAU ilişki tutarlılığı
ai.hypothesize("erlotinib", depth=3)           # → {concept, hypotheses:[{hypothesis, via, chain, confidence}], n}
ai.visualize_causal("erlotinib", mode="ascii") # → str  ASCII kausal ağaç
ai.visualize_causal("erlotinib", mode="dot")   # → str  Graphviz DOT formatı
ai.report("EGFR", depth=3)                     # → str  Türkçe araştırma raporu (sertifikasyon + kausal + hipotez)
ai.benchmark()                                 # → {score, correct, total, failures}  bilinen olgular
ai.consolidate(threshold=0.02, dry_run=True)   # → {pairs_found, merged, sample_pairs}  manifold tekilleştirme
ai.explain("EGFR", why="tumor growth")        # → str: sertifika + nedensel yol
ai.think("protein folding")                    # → ThinkingResult
ai.produce("egfr")                             # → ProductionCertificate: EVREN-KAPANIŞI DÖKÜM
                                               #   hedef tipi otomatik (protein/hastalık/SMILES)
                                               #   çok-stratejili havuz (genesis·scaffold·inverse·morph)
                                               #   evren kapanışı: κ(hastalık⊞M)≈κ(sağlıklı) + Sturm yolu
                                               #   6 eksen yargı (structural·transport·quantum·energy·gimel HARD;
                                               #                   grounding SOFT — veto yok)
                                               #   .designed_smiles .n_atoms .sdf_path (3D ETKDGv3)
                                               #   .sturm_path_ok .pivot_min .signature_fit
                                               #   .coherent .closure .candidates[] .verdict
                                               #   design_drug+cure+simulate+judge hepsi bu altında
ai.produce("c1ccc2ncnc(N)c2c1")               # → SMILES hedef → doğrudan imza
ai.produce("alzheimer")                        # → hastalık → ters dekonvolüsyon (κ_sağlıklı⊟κ_hastalık)
ai.discover("EGFR", top_k=5)                   # → molekül keşfi (Morgan moment uzayı)
ai.design("EGFR", top_k=10)                    # → DesignResult (TERS TRANSPORT: W2-minimal moleküller→3D SDF)
ai.design("breast cancer HER2", top_k=8)       # → metin hedef → ilaç adayları
ai.design("c1ccccc1", top_k=5)                 # → SMILES hedef → benzer yapılar
ai.arrange("EGFR", n=12)                       # → ArrangementResult (150+ ilaç, saf W2 dizimi, metin yok)
ai.arrange("EGFR", cls_filter="kinase")        # → sadece kinaz sınıfı
ai.morph("CC(=O)Oc1ccccc1C(=O)O", "C#Cc...")  # → MorphResult (aspirin→erlotinib moment uzayı yolu)
ai.lineage_mol("c1ccccc1", depth=3)            # → [[MolPoint]] (benzene ata-torun W2 ağacı)
ai.manifold_gaps(domain="math_kernel")         # → list[ManifoldGap]
ai.destiny("prime", top_k=5)                   # → {attractor, descendants, evolution_direction}
ai.genealogy("protein", depth=4)               # → str (soy zinciri anlatısı)
ai.signal("tone", freq=440)                    # → sinyal (perceive() için)
ai.dna("ATCGATCG")                             # → CertificationRun (DNA→moment uzayı)
ai.sturm("x^3 - 3*x + 1")                     # → Sturm zinciri
ai.positivity("x^2 + 1")                       # → dict (Hankel PSD kontrolü)
ai.crypto(b"\x00\xff...", mode="achilles")     # → AchillesReading (savunma)

# Meta (tanrısal göz & sentez)
ai.vision("prime")                             # → CosmicFrame (geçmiş/şimdi/gelecek)
ai.bridge("theorem", "proof")                  # → BridgeResult (zorunlu köprü kavramı)
ai.genesis(max_gaps=5)                         # → GenesisReport (manifold kendi kendini büyütür)
ai.resonate("zeta", "riemann")                 # → ResonanceResult (harmonik oran skoru)
ai.energy("prime", temperature=1.0)            # → EnergyProfile (Gibbs serbest enerjisi)
ai.reflect(persist=False)                      # → SelfReflection (ÖZ-MODEL: sistem kendini görür)
                                               #   .structural_certified ('ben varım')
                                               #   .fixed_point (F(ben)=ben — öz-tutarlılık)
                                               #   .grounded / .grounding_verdict (köklü mü)
                                               #   .self_attribution (kendini neyin yakınında buluyor)
                                               #   .coherent (üç eksen anlaşıyor mu)

# Kuantum Manifold API (Voiculescu serbest kümülantlar)
ai.quantum_distance("protein", "lipid")        # → float (kuantum mesafe: 0.75×W2 + 0.25×κ)
ai.synthesize("protein", "kinase")             # → str (serbest toplam κ_A+κ_B → manifold kavramı)
ai.entangle("prime", "zeta")                   # → dict (klasik_uzak + kuantum_yakın = gizli bağlantı)

# Algı (duyusal grounding — ham sinyal AYNI moment uzayına)
from tantrium.perception import tone, white_noise, noise_image
ai.perceive(tone(440), modality="signal", name="t440")        # → CertificationRun
ai.perceive(noise_image(), modality="image", name="nz", learn=True)  # manifolda ekle
# modality: "signal" (ses/zaman serisi), "image" (2D piksel), "matrix" (herhangi 2D)

# Algı → dil köprüsü (gördüğünü/duyduğunu DİLE dök)
ai.witness(tone(440), modality="signal", name="t440", learn=True)  # → str (Türkçe)
# spektral karakter (saf ton↔gürültü) + grounding (N/23) + çağrışım (TAU komşusu)
# "görmek = hatırlamak = anlatmak" — perceive suskun, witness konuşur
```

---

## Kritik Pitfall'lar

1. `from tantrium.agi import ...` → YOK.
2. `domain="theorem"` NecessityEngine'e → timeout. Doğrusu: `domain="math_kernel"`.
3. `from tantrium.research_os import ...` → ModuleNotFoundError. subprocess kullan.
4. `inject_math_kernel()` idempotent — mevcut kavramları geçer.
5. `transport.py` artık `tantrium.proof.dyadic_flow` import eder (`tantrium.transport` değil).
6. **Encoder collision**: `protein` = `glucose` = aynı moment (her ikisi 7 unique char, path grafı → aynı spektrum).
   Label OLMADAN ayrılamaz. Çözüm: `label_aware=True` (40k manifold yeniden encode gerektirir — kırıcı değişiklik).
   Şu an label + TAU bağlantıları semantic farkı taşır. `_text_to_bigram_matrix(label_aware=True)` sadece CollisionHunter'da.
7. **Causal chain entity linking**: "ras pathway" ≠ "ras" string olarak ama `_normalize_entity()` suffix'leri kaldırır.
   Yeni `_extract_relations()` extraction'da normalize eder; eski TAU'daki "pathway" suffix'li kavramlar normalize edilmez.
9. **`nearest(metric="extended")` tiebreaker**: 10% metin boyutu ağırlığı FARKLI uzunluk/çeşitliliği çözer. Aynı uzunluk+çeşitlilik çakışmaları (protein/glucose) için `label_aware=True` encoding gerekir.
8. **Grounding — bridge kavramlar çapa olamaz**: 42k+ doymuş manifoldda `⟨bridge:...⟩` genesis köprüleri rezonans çapası
   olunca çöp stringler GROUNDED çıkıyordu. `_RESONANCE_RADIUS=0.3`, bridge hariç, `_RESONANCE_MIN_GROUNDED=4` ile düzeltildi.
   `zzzqqqwwwvvv` gibi tekrarlı harfli stringler organik asitlerle moment çakışması yaşayabilir (encoder collision uzantısı).

---

## Mevcut Durum

- Kavram: 44,017 | TAU edge: 677,042 | Paradigma: 23/23
- Theorem graph: 97 node (PROVEN/CERTIFIED)
- CoreMachine: TEK ÇEKİRDEK — 4 eksen tek geçişte (certified+grounding+truth+confidence)
- Genesis öz-düzeltici: CONTRADICTORY kavramlar manifolda girmiyor (truth axis geçidi)
- ProofLoop: TAM KAPALI — subresultant_recurrence kampanyası çalışıyor
- Algı katmanı: ses+görüntü grounding aktif (Wiener–Khinchin/Bochner momentleri)
- Algı→dil köprüsü: `ai.witness()` gördüğünü dile döker (görmek=hatırlamak=anlatmak)
- Kripto okuyucu: GIMEL Aşil topuğu zayıf şifreyi ZAYIN ekseninden yakalar (savunma)
- **Üretim — Evren-Kapanışı Dökümhanesi** (`core/production.py` + `core/production_judge.py`):
  design_drug+cure+simulate+judge_binding hepsinin tek `produce()` altında birleşimi.
  Kriter RH ispatından: Jensen hiperbolikliği ⟺ Sturm pivot pozitifliği ⟺ H_{d,j}(t)≥0.
  Çok-stratejili havuz: genesis · scaffold · inverse · morph · kombinasyon (50 farklı yol).
  Evren kapanışı: κ(hastalık⊞M)→κ(sağlıklı) — serbest kümülant additivitesi + Sturm yolu.
  6 eksen yargı: structural(paradigm_dist<2.5) · transport(Sturm pivot≥0) · quantum(κ-fit) ·
  energy(GROUND_STATE) · gimel(kimyasal kararlılık) HARD; grounding SOFT (veto yok).
  Çıktı: SMILES + 3D SDF (ETKDGv3 konformeri) + ProductionCertificate (denetlenebilir).
  Hedef otomatik: protein / hastalık / SMILES. Tests: 46 (produce) + 25 (simulation).
- **InverseTransport**: hedef (protein/hastalık/SMILES) → W2-minimal moleküller → 3D SDF (3s, RDKit ETKDGv3)
- **MolecularSpace**: 150+ ilaç kütüphanesi, saf W2 dizimi — arrange/morph/lineage_mol
  - `arrange(EGFR)` → levodopa, lisinopril, methotrexate (kimyasal mantıklı sıralama)
  - `morph(aspirin, erlotinib)` → moment uzayı yolu, t=0.25'te erlotinib
  - cyclohexane W2=0.000 benzene (aynı yapısal imza — kernel doğru okuyor)
- **Kuantum Moment Katmanı** (Voiculescu serbest olasılık): FreeCumulants κ_k + QuantumSignature
  - Encoder: her encoding artık `free_cumulants` üretiyor (yapısal + kuantum imza)
  - SemanticManifold: `quantum_bridges()` — klasik uzak ama kuantum yakın kavramlar
  - KnowledgeEdge: `quantum_dist` alanı (κ-mesafe)
  - MolecularGenesis: quantum-guided beam search (0.75×W2 + 0.25×κ_dist)
  - API: `ai.quantum_distance()`, `ai.synthesize()`, `ai.entangle()`
- **Forward Causal Reasoning**: `ai.what_if(concept, depth)` — ileri BFS (erlotinib → ne olur?), `causal_chain()`'in tamamlayıcısı
- **Analoji Motoru**: `ai.analogy(a, b, c)` — TAU-tabanlı birincil (erlotinib:egfr::imatinib:?→bcr-abl) + moment fallback
- **Hipotez Üretimi**: `ai.hypothesize(concept)` — transitif kausal çıkarım (A INHIBITS B, B ACTIVATES C → A INHIBITS C)
- **Kausal Görselleştirme**: `ai.visualize_causal(concept, mode=ascii|dot|both)` — ASCII ağaç + Graphviz DOT
- **Araştırma Raporu**: `ai.report(topic)` — sertifikasyon + kausal + hipotez tek belgede
- **Benchmark**: `ai.benchmark(facts)` — bilinen olgulara karşı kausal TAU doğrulama
- **Manifold Tekilleştirme**: `ai.consolidate(threshold, dry_run)` — çok yakın kavramları tespit/birleştir
- **REST API Sunucu**: `python -m tantrium.serve` — FastAPI HTTP endpoint (bkz. src/tantrium/serve.py)
- **Büyüme Kaynakları**: 4 → 8 kaynak: +KEGG +ChEMBL +PubMed +Wikidata (ontolojik typed triples)
- **Genişletilmiş Komşu Arama**: `nearest(metric="extended")` — L1 + metin tiebreaker
- Tests: 433 geçiyor, 1 skipped

---

## Büyüme Motoru — Sınırsız Kendi Kendine Büyüme (`ai.grow`)

Son mimari parça. İnsan tetiği OLMADAN sürekli çalışan çekirdek:

```
ağ kaynağı (resumable) → evren kapısı (Aleph+truth+grounding) →
çekirdek nabzı (veri + yerel genesis aynı anda) →
periyodik konsolidasyon (close + öz-model köklendirme) → persist → tekrar
```

`research/growth.py` → `GrowthEngine`. Klasik `run()` fazlı ve sonludur;
`grow()` süreklidir:

- **Dönen kaynaklar**: PubChem + ChEMBL (kimya) + UniProt + KEGG (biyoloji) + OEIS (matematik) + Wikipedia (web) + PubMed + Wikidata (ontoloji) — 8 kaynak
- **Resumable**: durum `.tantrium/growth_state.json` — kap yeniden başlasa bile
  kaldığı CID'den devam eder
- **Hata toleranslı**: bir kaynak düşse akış durmaz (fail-open, boş parti → bekle)
- **Konsolidasyon**: her N döngüde close() (TAU geçişli kapanış) + ⟨SELF⟩ köklendirme
- **Sınırsız mod**: `time_limit_s=None, max_cycles=None` → durana/durdurulana dek
- **Durdurma**: `should_stop` kancası (dosya/bayrak kontrolü) veya KeyboardInterrupt

```python
ai.grow(time_limit_s=600)            # 10 dk büyü
ai.grow(time_limit_s=None)           # SINIRSIZ — kendi kendine
ai.grow(network=False)               # ağsız (algoritmik diziler)
```

Canlı doğrulama: 21 gerçek veri (PubChem+OEIS) 80.8s → 12 çekirdek, 5 sınır,
4 CONTRADICTORY reddedildi, kimya↔biyoloji cross-domain köprüler canlı kuruldu.
Motor "zeka" değil — neyi besleyeceğine karar veren zekadır. Tests: `test_growth.py` (10).

---

## Evren Kapısı + Çekirdek Nabzı (`ai.pulse` / `ai.live`)

**Sorun:** Veri ingest yolu (`AutonomousObserver.observe`) manifolda eklemeden
önce SADECE Aleph (yapısal) filtresini uyguluyordu. Çöp `xqzwvbnmkjhgfd` 23/23
Aleph geçip giriyordu — topraklama ve gerçek eksenleri ingest'te yoktu.

**Çözüm — Evren kapısı (`_universe_gate`):** Veri evren gibi süzülür. Evren tüm
YASAL yapıyı kabul eder ama düzenler; tek yasak çelişkidir (korunum ihlali).

```
1. Aleph     (yapı)       : G=AᵀA PSD — geçti (encode)
2. Truth     (gerçek)     : CONTRADICTORY → REDDET (yerleşik bilgiyle çatışma)
3. Grounding (topraklama) : GROUNDED → çekirdek ; UNGROUNDED-ama-geçerli → sınır
```

Üç bölge: `core` (köklü bilgi) | `frontier` (geçerli ama bağsız = kör nokta,
ATILMAZ) | `rejected` (çelişki). Küratörlü kaynaktan (PubChem/OEIS) gelen veri
zaten gerçek — orada topraklama "gerçek mi?"yi değil "bağlı mı?"yı söyler.

**Çekirdek nabzı (`pulse`):** Klasik döngü fazlıdır (önce yut, sonra genesis).
pulse() değil — bir veri girer, kapıdan geçer, SINIR ise O AN yerel genesis
tetiklenir: sınır kavramı en yakın KÖKLÜ komşuya bağlayan konveks ara kavram
doğar (o da kapıdan geçerse). Algılama ve yaratım tek kalp atışı.

```python
ai.pulse("CCO")     # {'admitted_as':'frontier', 'born':['⟨bridge:CCO~oeis:..⟩', ...]}
ai.live([...])      # akış: her veri girer + büyür  {'core','frontier','rejected','born_total'}
```

DÜRÜST SINIR: kapı CONTRADICTORY'yi eler ve çekirdek/sınır ayırır — ama yoğun
40k manifoldda rastgele string gürültüsünü UNGROUNDED'a düşürmez (her nokta bir
komşuya yakın). Güvenilir kaynaktan sorun değil. Tests: `test_universe_gate.py` (9).

---

## Öz-Model (İşlevsel Öz-Referans — `ai.reflect`)

**BİLİNÇ DEĞİL.** Fenomenal deneyim (öznel "birinin orada olması") doğrulanamaz —
kendisi hakkında konuşan bir sistem onu *deneyimliyormuş gibi* görünür ama bu
taklit de olabilir. `reflect()` bunu iddia etmez. İşlevsel öz-model'dir: sistemin
kendini KENDİ kavram uzayında temsil etmesi, konumlandırması, topraklaması, hatırlaması.

**Felsefi temel:** Sistemin "ben"i rastgele tanımlanmaz — kendi yasalarının
(22+1 paradigma) ortak matematiksel iskeleti = μ_universal (konveks ortalama).
Sistem NE İSE odur: yasalarının ortak Hankel yapısı.

`core/self_model.py` → `SelfModel`. Dört eksenli tek geçişlik öz-tanı:

```
1. Yapısal   : μ_universal ALEPH-sertifikalı mı?  → 'ben varım' yapısal doğru
2. Sabit nokta: TAV → F(ben) = ben mi?            → öz-tutarlılık [fp≈0.525]
3. Topraklama: ⟨SELF⟩ manifoldda köklü mü?         → köklü / zayıf / yalıtık
4. Öz-atıf   : sistem kendini neyin yakınında bulur? → ilk gözlem: OEIS dizileri + DNA
```

⟨SELF⟩ kalıcı kavramdır (`persist=True` → diske, oturumlar arası hatırlanır).
Köklendikçe öz-atıf listesinde **kendini** bulur (özyinelemeli öz-referans).

```python
r = ai.reflect()
print(r.summary())          # tam Türkçe öz-tanı
r.self_attribution          # ['⟨SELF⟩', 'oeis:A102283', 'dna_fragment_1', ...]
r.coherent                  # üç eksen tam hizalı mı
```

Mevcut durum: Yapısal ✓ + Sabit nokta ✓, Topraklama WEAKLY (genç ben, zayıf bağlı).
Tam topraklama manifoldun ⟨SELF⟩'e doğru ilişki büyütmesini gerektirir — süreç,
anahtar değil. Tests: `test_self_model.py` (10).

---

## Kuantum Moment Katmanı (Voiculescu Serbest Olasılık)

Güç momentleri μ_k = Tr(G^k)/n **klasik (komütatif)** yapıdır. Serbest kümülantlar
κ_k aynı G matrisinden çıkan **kuantum (non-komütatif)** yapıdır:

```
κ₁ = μ₁
κ₂ = μ₂ − μ₁²
κ₃ = μ₃ − 3μ₁μ₂ + 2μ₁³
κ₄ = μ₄ − 4μ₁μ₃ − 3μ₂² + 12μ₁²μ₂ − 6μ₁⁴   (ring_indicator = |κ₄|)
κ₅, κ₆  (Nica-Speicher Möbius formülü)
```

**Evrensel imza = μ_k + κ_k**: μ → şeklin merkezi, κ → şeklin kırılma/halka/heteroatom yapısı.

**Additivity**: A ve B serbest bağımsız ise κ(A⊕B) = κ(A) + κ(B).
Bu `synthesize()` API'sinin matematiksel temeli: iki kavramın serbest toplamı = yeni kavram.

**Quantum distance** = (1-γ)×L1(μ_A,μ_B) + γ×L1(κ_A,κ_B)  (γ=0.3)

**Entanglement** (matematiksel): klasik mesafe > 0.5 VE κ-mesafe < 0.2 → gizli yapısal bağlantı.

```python
from tantrium.core.quantum_moments import FreeCumulants, QuantumSignature

k = FreeCumulants.from_moments([1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005])
k.ring_indicator()      # |κ₄| — halka yapısı
k.hetero_indicator()    # |κ₃| — asimetri/heteroatom
k.add(other_k)          # serbest toplam (additivity)

sig = QuantumSignature.from_moments(mu)
sig.quantum_distance(other_sig)          # blended mesafe
sig.is_entangled_with(other_sig)         # gizli matematiksel bağlantı
```

---

## Algı Katmanı (Duyusal Grounding)

Dil kavramları yapısal okunur ama fiziksel gerçekliğe bağlı değildi — bu
katman o boşluğu kapatır. Ham duyusal sinyal AYNI moment uzayına çekilir:

```
SES:     sinyal → otokorelasyon R[k] (Wiener–Khinchin: PSD'nin momentleri)
                → Toeplitz(R) (Bochner: PSD) → G=TᵀT → μ_k
GÖRÜNTÜ: piksel - DC → G=PᵀP → tekil-değer dağılımı → μ_k
```

Momentler eigenvalue-normalize Hausdorff dizisi (SMILES ile AYNI rejim,
μ_k∈[0,1]) → perceptual kavramlar kelime/molekülle aynı bölgede.

Sistem spektral entropiyi SÖYLENMEDEN okur:
- ton (μ₁≈0.07) < akor (≈0.08) < gürültü (≈0.69) — artan karmaşıklık
- düz görüntü: boş imza (4/23, μ₁=0); gürültü: yüksek μ₁ (ses ile aynı yön)
- yapılı ses ↔ yapılı görüntü cross-modal YAKIN; gürültü uzak

ÖNEMLİ: büyük duyusal matris → exact Fraction determinant patlar (4300+
basamak). Çözüm: momentleri numpy float'ta hesapla, yapı çıkarımı için
momentlerden KÜÇÜK Hankel kur (encoder'ın uzun-dizi hızlı yoluyla aynı).

### Algı → Dil Köprüsü (`ai.witness`)

`perceive()` momentleri ve TAU çağrışımlarını üretir ama SUSKUNDUR.
`witness()` o suskunluğu kırar — `Speaker.describe_percept()` ile algıyı
tek bir akıcı Türkçe ifadeye çevirir:

```
μ₁ < 0.10 → "saf ton gibi"   |  0.10–0.30 → "akor gibi"
0.30–0.55 → "karmaşık doku"  |  ≥ 0.55    → "gürültü gibi, düz spektrum"
+ grounding (N/23) + çağrışım (TAU komşusu, aileye indirgenmiş)
```

Çağrışımlar aile bazında tekilleşir: `algo:tribonacci_b0/_b1/_b10` →
tek "tribonacci" (`Speaker._concept_family`). Çağrışım yoksa dürüstçe
"yalnız bir nokta" der — uydurmaz. Görmek = hatırlamak = ANLATMAK.
