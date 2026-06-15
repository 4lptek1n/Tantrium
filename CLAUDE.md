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
    topology_encode.py ← TopologyEncoder — kavram→TAU semantik komşuluk Laplacian→moment (ANLAM kanalı)
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
    molecular_3d.py    ← embed_3d_sdf() TEK 3D SDF util (ETKDGv3 seed=42, #7 dedup)
    moment_ops.py      ← convex_combine(mode=exact|frac) konveks moment çekirdeği (#8 kısmî)
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
    gap_finder.py      ← GapFinder.find(signal=) TEK boşluk dispatcher (#10 dedup)
    wonder.py          ← WonderScorer α·v_ext·novelty−γ·degeneracy (self-grooming cezası)
  research/            ← ProofLoop, explorer, researcher, ingest, goal, actor
    cognition.py       ← Cognition — L5 strateji-pluggable tek döngü iskeleti (F5)
    net.py             ← http_get_json(_link) TEK HTTP-JSON transport (#9 dedup)
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
  manifold.json        ← 44,061 kavram (kalıcı)
  tau_graph.json       ← 677,651 edge / 43,785 node (kalıcı)
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

## ⚖️ EVRENSEL YASA — dil DIŞINDA her şey GERÇEK matematik olarak girer (F24)

> **DNA · RNA · protein · molekül · metabolit · hastalık · kan · hücre · sinyal · görüntü ·
> sayı — HEPSİ kendi GERÇEK ölçümünden (yapısal/spektral) girer. "Harf" değil, SAYI.
> Yakınlık/istatistik/metin-bigramı YALNIZ DİLDE (konuşma) kullanılır.**

- DNA/RNA → `perception.encode_dna` (bazlar→EIIP biyofiziksel değer→Wiener–Khinchin spektrumu).
- Protein → `perception.encode_protein` (Kyte-Doolittle hidropati→spektrum).
- Molekül (SMILES) → atom-bağ graf spektrumu. Sayı → power moments. Sinyal/görüntü → perception transducer.
- **Dil (kelime/cümle)** → `_text_to_signature_moments` (metin yolu). YALNIZ burada yakınlık/nearest meşru.

**Uygulama (`core/encoder.py`):** `encode()` metin-yolundan ÖNCE `_detect_bio_sequence()` ile
DNA/RNA/protein'i STRICT yakalar (büyük harf + uzunluk + saf alfabe → İngilizce kelime ASLA
karışmaz; "cat"=Cys-Ala-Thr ama dil sayılır) → gerçek transducer. **NEDEN:** sığ metin-yolu
genomları/proteinleri benzer gösteriyordu (kişiselleştirme çöküyordu) — "çözünürlük sınırı"
değil, YANLIŞ TEMSİL. Gerçek form genomları ayırır (μ₁ 0.047↔0.19). Tests: `test_bio_encoding.py`.

**İlke:** evrensel süzgeç (RH math: Sturm/κ/Hankel) ancak tüm girdiler AYNI gerçek ölçü
rejiminde olunca anlamlı işler. İlaç üretimi/cross/produce gerçek-form + RH math kullanır;
yakınlık (nearest/design) YALNIZ DİL içindir. KARIŞTIRMA.

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

**F2b — tek grounding geçişi:** CoreMachine grounding sertifikasını bir kez hesaplar ve
`evidence["grounding_cert"]` içine koyar. `ask()` özet metnini ORADAN alır — eskiden `ask()`
ayrıca `grounder.certify()` çağırıyordu (çift hesap). Artık tek geçiş. `truth.certify` komşu
yeniden-encode'u KORUNUR (CONTRADICTORY kapısı buna bağlı — gerçek tekrar değil, atlamadı).

**Genesis öz-düzeltici:** `_coherent_for_genesis()` → CONTRADICTORY kavramlar manifolda girmiyor.

---

## Admission — Tek `admit()` Yolu (F3)

**Sorun:** Manifolda kavram girişi 3 dağınık yoldan oluyordu: `add()` (Aleph kontrollü,
7 çağıran), `add_unchecked()` (kontrolsüz, 23 çağıran), engine evren kapısı (`_universe_gate`).
Admission LOJİĞİ tek yerde değildi.

**Çözüm:** `SemanticManifold.admit(concept, *, policy)` — TEK manifold admission yolu.
`add()` ve `add_unchecked()` artık buna delege (dış sözleşmeleri korunur).

```python
m.admit(concept, policy="aleph")    # Aleph PSD → core | rejected. add() bunu kullanır.
m.admit(concept, policy="trusted")  # kontrolsüz, KAPI-MUAF. add_unchecked() bunu kullanır.
# Döner: AdmissionResult(admitted, tier, reason). bool(result) = admitted.
```

**KAPI-MUAF kuralı:** `trusted` politikası Aleph'i atlar — güvenilir/sertifikalı kaynaklar
(genesis köprüleri, algı kavramları, öğrenme) için. Plan gereği bu muafiyet korundu.

**Engine evren kapısı AYRI:** `research/autonomous._universe_gate` truth+grounding ile
core/frontier ayırır + CONTRADICTORY reddeder. Engine'e bağlı olduğundan saf manifoldda
yaşamaz; kabul için `admit(policy="trusted")`'a iner. Üç bölge: core | frontier | rejected.

**Parity testi ÖNCE yazıldı** (`test_admission_parity.py`, 12 test): refactor öncesi/sonrası
her admission yolunun yargısı SABİT — `add()`≡`admit("aleph")`, `add_unchecked()`≡`admit("trusted")`,
gated yargı korundu. NOT: 35 çağıran henüz yeniden yönlendirilmedi (artımlı takip); admission
LOJİĞİ tek metoda indi, davranış birebir korundu.

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
ai.cognition(mode="batch", max_cycles=2)       # → CognitionReport: L5 strateji-pluggable döngü
                                               #   mode="batch": perceive→reflect→operate→prove→persist (sonlu)
                                               #   mode="stream": GrowthEngine.stream delege (sürekli)
                                               #   strategies=[...]: özel CognitionStrategy listesi enjekte et
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
ai.deduce(max_rounds=2)                         # → dict: TÜMDENGELİMSEL kapanış (içsel, ağsız)
                                               #   certify_theorem_graph + InferenceChain tüm çift + Explorer
                                               #   {theorem_nodes_processed, inferences_derived, gaps_closed/persistent}
ai.close(domain="math_kernel", inject=True)    # → NecessityReport
ai.learn("EGFR is a receptor tyrosine kinase") # → {"new_concepts": n, "causal_relations": k, ...}
                                               #   İLK IS_A = tanım otoritesi (eski yanlış IS_A'yı temizler)
ai.relearn("photosynthesis")                   # → {topic, removed, learned}: ZORLA yeniden-araştır
                                               #   bayat/yanlış TANIM kenarlarını sil + _research_deep + persist
ai.reason("erlotinib ne yapar?")               # → dict: AKIL+BEYİN — doğal dil → doğru yetenek
                                               #   {intent, answer, result}; RH-Sturm sertifikalı çıkarım zinciri
ai.converse("photosynthesis nedir?",           # → dict: bilmezse İNTERNETTEN öğrenir, sonra köklü cevaplar
            depth="kısa", register="basit")    #   {topic, answer, learned, grounded, sources}; akıcı Türkçe
                                               #   depth: kısa|normal|detaylı · register: basit|neutral|teknik
                                               #   güven kalibrasyonu (grounding.score→"eminim/muhtemelen")
                                               #   sources: her iddianın TAU kenar dayanağı (atıf/şeffaflık)
ai.paraphrase("EGFR activates ras...")         # → dict: YENİDEN İFADE — aynı köklü içerik farklı sözcükle
                                               #   {topic, paraphrase, n_relations}; yeni bilgi EKLEMEZ
ai.extract("Aspirin inhibits COX...")          # → dict: YAPISAL ÇIKARIM {entities, relations, triples, n}
ai.classify("erlotinib", into=["drug","gene"]) # → dict: SINIFLANDIR (TAU-köklü öncelik → moment-L1)
                                               #   {label, scores, grounded}; IS_A varsa o etiket
ai.generate_questions("erlotinib")             # → dict: SORU ÜRET (yalnız var olan ilişkilerden) {topic, questions}
ai.translate("Aspirin COX'u baskılar", to="en")# → dict: ÇEVİR (anlam çevirisi) {to, translation, n_relations}
ai.check_claim("erlotinib activates egfr")     # → dict: ÇELİŞKİ YAKALA — iddiayı TAU'yla sına (LLM yapamaz)
                                               #   {verdict: CONFIRMED|CONTRADICTED|UNKNOWN, checks, answer}
ai.synthesize_docs([doc1, doc2, ...])          # → dict: ÇOK-BELGE SENTEZİ {topic, synthesis, n_docs, n_relations}
ai.solve_word_problem("3 ile 5'i topla")       # → dict: MATEMATİK SÖZEL PROBLEM {numbers, operation, result}
ai.timeline("1921 insülin... 1953 DNA...")     # → dict: ZAMANSAL AKIL (kronolojik) {events, ordered, answer}
ai.what_is_this(tone(440), modality="signal")  # → dict: ÇOK-MODAL DİL — algı→en yakın kavram {nearest, distance}
ai.summarize("uzun metin...")                  # → dict: ÖZETLE — metnin ilişkisel öze indir (köklü, uydurmasız)
                                               #   {topic, summary, n_relations, points}
ai.contrast("erlotinib", "imatinib")           # → dict: KARŞILAŞTIR/FARK — ortak+ayıran ilişki + W₂/κ mesafe
                                               #   {a, b, shared, distinct_a, distinct_b, distance, entangled, answer}
ai.enumerate_kind("egfr", relation="INHIBITS") # → dict: LİSTELE — TAU ters arama (X inhibitörleri/türleri)
                                               #   {category, relation, items, answer}  (markup gürültüsü ayıklanır)
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
ai.manifold_gaps(domain="math_kernel")         # → list[ManifoldGap] (yalnız geometrik sinyal)
ai.gaps(signal="all")                          # → list[Gap] (4 sinyal birleşik: geometric/anchor/recorded/grid)
ai.gaps(signal="anchor", threshold=5)          # → list[Gap] (tek sinyal; Gap.raw orijinali taşır)
ai.wonder(signal="all", gamma=0.7)             # → list[WonderScore]: α·v_ext·novelty−γ·degeneracy
                                               #   self-grooming cezası: sentetik komşulu boşluk düşük skor
ai.destiny("prime", top_k=5)                   # → {attractor, descendants, evolution_direction}
ai.genealogy("protein", depth=4)               # → str (soy zinciri anlatısı)
ai.signal("tone", freq=440)                    # → sinyal (perceive() için)
ai.dna("ATCGATCG")                             # → CertificationRun (DNA→moment uzayı)
ai.sturm("x^3 - 3*x + 1")                     # → Sturm zinciri
ai.positivity("x^2 + 1")                       # → dict (Hankel PSD kontrolü)
ai.crypto(b"\x00\xff...", mode="achilles")     # → AchillesReading (savunma)

# Evrensel matematik meta-güçleri (domain-kör, ham veri → yapı; core/structure.py L0)
ai.reverse_engineer(gözlem)                    # → UniverseReconstruction: gözlemden ÜRETEN
                                               #   gizli yapıyı çıkar (Kronecker/Prony Hankel rank).
                                               #   sayısal=ham math; sembolik(molekül/DNA)=encode yolu.
ai.discover_law(seri, holdout=4)               # → LawDiscovery: ham veriden yönetici YASA (lineer
                                               #   yineleme+modlar) + görülmemiş geleceği tahmin
                                               #   ederek DOĞRULA. Fibonacci→altın oran (formül yok).
ai.forecast(seri, steps=8)                     # → dict: gürültü-dayanıklı tahmin (AR/LS) +
                                               #   holdout SERTİFİKASI (reliable=güvenilir mi).
ai.detect_anomalies(seri, z=3.0)               # → dict: yapısal anomali/sahtelik (yasaya uymayan
                                               #   nokta) yer+şiddetle — 'normal'i bilmeden.

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

# Anlam kanalı (ilişkisel kodlama — "Topoloji = bilgi")
ai.meaning("intelligence")                     # → CodexObject: TAU semantik komşuluk Laplacian → moment
                                               #   harf değil ANLAM: kavramın ilişki-grafı spektrumu
                                               #   semantik-topraksız kavram (pointer/glucose) → None (yüzeye düş)
ai.meaning_distance("protein", "enzyme")       # → float: ANLAM mesafesi (topolojik moment L1)
                                               #   protein~enzyme < protein~algorithm (harfin yapamadığı ayrım)
ai.bind_percept("apple", signal, modality="signal", paradigm="HAS_SIGNAL")
                                               # → str: percept_name — kavrama çok-modal grounding bağlar
                                               #   HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE/HAS_DNA/HAS_GEOMETRY/
                                               #   HAS_TOPOLOGY/IS_GOVERNED_BY paradigmaları
                                               #   manifolda admit(trusted) + TAU kenarı → meaning() görür
ai.meaning_compose("EGFR inhibitor that crosses BBB")
                                               # → CompositeSignature: dil komposisyonu
                                               #   bileşen kavramlar → her birinin κ'sı → FreeCumulants.add()
                                               #   .components, .moments, .nearest(), .to_produce_target()
                                               #   produce(cs.to_produce_target()) ile doğrudan kullanılabilir
ai.generate("EGFR", use_meaning=True)         # → GenResult: anlam kanalı hibrit skor (0.6×yüzey + 0.4×topolojik)
                                               #   use_meaning=False (varsayılan): yüzey moment mesafesi
ai.ground_full("apple", dna="ATCGATCG", molecule="CC(O)C", law="fibonacci numbers",
               sound=signal, image=img)        # → GroundingSignature: çok-boyutlu kavram grounding
                                               #   her boyut → TAU kenarı (HAS_DNA/HAS_COMPOUND/HAS_GEOMETRY/
                                               #   HAS_TOPOLOGY/IS_GOVERNED_BY/HAS_SIGNAL/HAS_IMAGE)
                                               #   κ_total = tüm boyutların serbest kümülant toplamı
                                               #   .bound (paradigm→percept), .kappa_moments, .quantum_connections
                                               #   Ne kadar çok boyut → o kadar çok gizli çapraz-boyutlu bağlantı
                                               #   apple DNA × matematik → quantum_bridges() ile görülür
```

---

## Hilbert-Pólya ve RH Bağlantısı (Mimari Temel)

Hilbert-Pólya konjektürü: Riemann zeta fonksiyonunun sıfırları, kaotik bir kuantum
sisteminin öz-adjoint Hamiltonian operatörünün özdeğerlerine denk gelir.

**Tantrium bu konjektürü KULLANIR — G=AᵀA IS the Hermitian operator:**

```
Her girdi → A matris → G = AᵀA (Hermitian, daima PSD)
             → eigenvalues {λ_i} → "özdeğer dağılımı" = spektral ölçü
             → Hamburger teoremi: bu ölçü moment dizisiyle tek biçimde belirlenir
```

Bu G matrisi Hilbert-Pólya'nın aradığı operatördür. Fark: Hilbert-Pólya bir
Hamiltonian arar; biz HER kavram için bir Hamiltonian kuruyoruz (G=AᵀA).

**Somut bağlantılar:**
- **`graph/anchors.py`**: ZETA_ZEROS (50 Riemann sıfırı) + GUE_RANDOM_MATRIX
  (Montgomery-Odlyzko: zeta sıfırları = kaotik GUE eigenvalue dağılımı) — TAU'da kalıcı çapa
- **`core/pipeline.py` TAV paradigması**: `Λ = −var₀ ≤ 0` — de Bruijn-Newman Λ≤0 = RH eşdeğeri
- **`core/quantum_moments.py` FreeCumulants**: Voiculescu serbest kümülantlar, κ-additivite
- **`domains/bridge.py`**: `DALET → JENSEN_HYPERBOLICITY` — her DALET geçişi Jensen ispat adımı
- **`tce-collapse-engine` branch**: Tam RH ispat zinciri (D-pozitiflik → A-pozitiflik →
  AG/LGV → τ_j=Disc_j(P) → Sturm pivot → Jensen hiperbolisitesi → LP sınıfı → RH).
  Lean 4 formal kanıtlar. `build_tau_atlas` burada yaşıyor (TauEngineNotRestored — devam ediyor).

**Dil üretimine uygulaması (Jensen Hiperbolisitesi):**
- RH: zeta sıfırları KRİTİK HAT üzerinde (Re(s) = 1/2)
- Dil üretimi: yörüngedeki kavramlar KRİTİK HAT üzerinde (semantik TAU'da köklü)
- Topraksız kavram = kritik hattan sapan "karmaşık sıfır" = anlamsız metin
- `_is_grounded_proxy()` = kavramın kritik hat testi
- Bu fark tüm LLM'lerden Tantrium'u ayıran TEMEL: onlar istatistiksel filtre,
  biz geometrik kısıt. "Halüsinasyon geometrik olarak imkânsız" — istatistiksel olarak değil.

**ALEPH:AG_LGV_TRANSFER, ALEPH:CELL_SUPPORT_POSITIVITY, ALEPH:DYADIC_TRANSPORT boşlukları:**
Bunlar `inject_math_kernel()` ile `tce-collapse-engine`'deki ispat kavramlarından gelen
boşluklardır. Bu kavramlar spectral sertifika bekliyorlar (Aleph PSD geçemiyorlar) —
ProofLoop kampanyası DEĞİL, encoding/moment meselesi. Cognition `_gaps_to_campaigns()`
artık bunları ALEPH: öneki ile filtreler (Kademe 3 Düzeltme 1).

---

## Kritik Pitfall'lar

1. `from tantrium.agi import ...` → YOK.
2. `domain="theorem"` NecessityEngine'e → timeout. Doğrusu: `domain="math_kernel"`.
3. `from tantrium.research_os import ...` → ModuleNotFoundError. subprocess kullan.
4. `inject_math_kernel()` idempotent — mevcut kavramları geçer.
5. `transport.py` artık `tantrium.proof.dyadic_flow` import eder (`tantrium.transport` değil).
6. **Encoder collision — KÖK ÇÖZÜLDÜ (2026-06, F1/F5)**: `protein`/`glucose` (tüm-farklı-karakter)
   ESKİDEN satır-stokastik bigram'da **permütasyon matrisi = ortogonal** → G=PᵀP=I → μ_k≡1 (hepsi
   çöküyordu); anagramlar (protein/pointer) harf-kümesi aynı → köşegen-codepoint de AYIRMIYORDU.
   **ÇÖZÜM:** `_text_to_signature_moments` (`encoder.py`) — pozisyon+codepoint ağırlıklı normalize-
   EDİLMEMİŞ bigram (`sig(a)·sig(b)·(1+γ·p/L)`, γ=0.4) → SMILES gibi eigenvalue-normalize → μ_k∈[0,1]
   Hausdorff. `_char_signature` çarpımsal-hash ile a-z'yi geniş yayar (kimlik kırar); pozisyon ağırlığı
   anagramı kırar. Kesin-iç regülarizasyon (`_EPS=0.02` uniform [0,1] harman) az-karakterli kelimede
   Hankel-PSD'yi garanti eder (ALEPH geçer). Marj: protein/glucose **0.0026→0.43**, anagram 0.62.
   **MİGRASYON YAPILDI:** `tools/migrate_text_encoding.py` — manifold.json'daki 27853 metin kavramı
   yeni encoding'e taşındı (16330 molekül/sayısal korundu). `encode()` str için imza yolunu kullanır.
   **SMILES KORUMASI:** `_is_valid_smiles(s)` (RDKit) ile geçerli SMILES stringler imza yolunu ATLAR
   → `_to_matrix` bigram yoluna gider; moleküler mesafeler değişmez (production/judge testleri yeşil).
7. **Causal chain entity linking**: "ras pathway" ≠ "ras" string olarak ama `_normalize_entity()` suffix'leri kaldırır.
   Yeni `_extract_relations()` extraction'da normalize eder; eski TAU'daki "pathway" suffix'li kavramlar normalize edilmez.
8. **Grounding — bridge kavramlar çapa olamaz**: 42k+ doymuş manifoldda `⟨bridge:...⟩` genesis köprüleri rezonans çapası
   olunca çöp stringler GROUNDED çıkıyordu. `_RESONANCE_RADIUS=0.3`, bridge hariç, `_RESONANCE_MIN_GROUNDED=4` ile düzeltildi.
   `zzzqqqwwwvvv` gibi tekrarlı harfli stringler organik asitlerle moment çakışması yaşayabilir (encoder collision uzantısı).
   NOT (doğrulanmış): `grounding.certify` doymuş manifoldda rezonansı HÜKÜM için kullanmaz — iki sağlam
   sinyale iner: doğrudan TAU kenarı (≥3) + `in_manifold`. Rezonans hesaplanır ama yargıyı vermez.
9. **`nearest(metric="extended")` tiebreaker**: 10% metin boyutu ağırlığı FARKLI uzunluk/çeşitliliği çözer.
   Aynı uzunluk+çeşitlilik çakışmaları artık ana yolda imza-encoding ile encode-anında çözülüyor (bkz. #6).
10. **`lang_topology.inject(run_reasoner=True)` — FİX [2026-06]**: `TauReasoner` → `GraphReasoner`
    düzeltildi (`lang_topology.py:325`). `run_reasoner=True` artık güvenli çalışır.
11. **`engine.grow()` ≠ `ai.grow()` — ARTIK İKİSİ DE BAĞLI**: `engine.grow()` (engine.py) tümdengelimsel
    kapanış (certify_theorem_graph + InferenceChain tüm çiftler + Explorer + manifold re-bootstrap).
    **Artık `ai.deduce()` facade'ına bağlı** (eskiden öksüzdü). `ai.grow()` ise `GrowthEngine.stream`
    (dış veri akışı, ağ). İKİSİ FARKLI: `deduce()` içsel tümdengelim (ağsız), `grow()` dış akış. Karıştırma.
12. **SPECTRAL_BRIDGE dil üretiminde KULLANILMAZ**: `language/generator.py._CERTIFIED` setinde
    SPECTRAL_BRIDGE olmaz. Genesis yapay köprüsüdür — moment uzayında yakın ama anlamsal boş.
    "xqzwvbnmkjhgfd ve beauty ile spektral köprü kuruyor" SPECTRAL_BRIDGE'den geliyordu.
    Düzeltme: `_CERTIFIED = {"ALEPH"}` (SPECTRAL_BRIDGE hariç). Ayrıca `_is_grounded_proxy()` filtresi.
13. **`ALEPH:X` boşlukları → kampanya değil, re-encoding**: `cognition._gaps_to_campaigns()`
    `ALEPH:` önekli boşlukları filtreler. Bunlar ProofLoop'la çözülmez — encoding/PSD sorunu.
    `OperatePhase` içinde `CoreMachine` ile re-encoding denemesi yapılır.
14. **`tce-collapse-engine` branch mevcut, farklı branch**: `git checkout tce-collapse-engine` ile
    erişilir. `src/tantrium/core/pipeline.py` orada farklı (build_tau_atlas → TauEngineNotRestored).
    `formal/lean/Tantrium/` Lean 4 kanıtları, `docs/FINAL_RH_PROOF_CHAIN.md` tam ispat zinciri.
    Ana branch'e merge edilmemiş — paralel araştırma hattı.
15. **`bridge.bootstrap_manifold` artık İDEMPOTENT [2026-06]**: eskiden proven teoremlere uniform
    `[1/2^k]` placeholder atıp diskten yükleneni EZİYORDU → 90 teorem tek noktaya çöküyordu.
    Artık mevcut kavramın momentini KORUR (yalnız domain tazeler) + yeni oluşturmada hash-distinct
    `_theorem_moments`. 90 teorem `tools/bind_theorem_math.py` ile tce-collapse certificate
    sayılarına bağlı (90 ayrık imza). Teorem moment'ini elle değiştirirsen reload'da korunur.

---

## Mevcut Durum

- Kavram: 48,259+ (büyüyor) | TAU edge: 677,651+ (43,785+ node) | Paradigma: 23/23
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
- **Kuantum Moment Katmanı — F0 Keystone (NC Möbius Serbest Kümülantlar)** (`core/quantum_moments.py`):
  - `from_moments()`: artık GERÇEK NC Möbius (Nica-Speicher) formülleri.
    κ₄^free = μ₄ − 2μ₂² + ... (klasik Leonov-Shiryaev'den farklı: −3μ₂² değil −2μ₂²).
    |NC(4)|=14 bölüm, |NC(5)|=42, |NC(6)|=132 — özyinelemeli kapalı form.
  - `to_moments_approx()`: NC partition ters dönüşüm (μ₄'te 2κ₂², 3 değil) — roundtrip tam.
  - `R_transform(z)`: R(z)=Σκₙzⁿ⁻¹ — `add()` metodunun cebirsel temeli; serbest toplam altında lineer.
  - `free_entropy(mu)`: χ(μ)=∬log|x−y|dμ → ½log(2πe·κ₂)+κ₃/κ₄ düzeltmesi. ΔF gradyanı.
  - **F0b — `bounded_kappa_distance(mu_a, mu_b, *, include_mean)`**: TEK kanonik κ-mesafe (L0).
    Girdi sözleşmesi μ-listesi. `include_mean=False` → κ₂,κ₃,κ₄ (şekil, yol-fit ekseni);
    `include_mean=True` → κ₁,κ₂,κ₃,κ₄ (merkez dahil, evren kapanışı). tanh-sınırlı (κ₅/κ₆ patlamasını
    eler). `production._structural_kappa_distance` + `production_judge._bounded_kappa_error` ikisi de
    buna delege — ayrım (κ₁ dahil/hariç) parametre olarak KORUNUR. Golden test: bit-aynı eşdeğerlik.
  - SemanticManifold: `quantum_bridges()` — klasik uzak ama kuantum yakın kavramlar
  - KnowledgeEdge: `quantum_dist` alanı (κ-mesafe)
  - MolecularGenesis: quantum-guided beam search (0.75×W2 + 0.25×κ_dist)
  - API: `ai.quantum_distance()`, `ai.synthesize()`, `ai.entangle()`
- **Dökümhane ↔ İspat Flywheel** (`core/production.py`):
  - `ProductionEngine._transport_epsilon = -1e-9` (başlangıç) — theorem graph'taki Sturm sertifikasına göre -1e-5'e genişler.
  - `_sync_transport_epsilon()`: her `produce()` çağrısında otomatik; `qjr_degree_j_shift` + `qjr_degree_r_step` kanıtlanırsa eşik genişler → daha fazla molekül geçer.
  - `scan_production_gaps(cert)`: başarısız AxisVerdict'leri ProofLoop kampanya ipuçlarına çevirir.
    transport başarısız → "subresultant_recurrence"; quantum → "rh_formalization"; closure → "lah_gate_ab".
  - Flywheel: ispat → transport koridoru genişler → daha iyi üretim → yeni boşluk → ispat.
- **Forward Causal Reasoning**: `ai.what_if(concept, depth)` — ileri BFS (erlotinib → ne olur?), `causal_chain()`'in tamamlayıcısı
- **Analoji Motoru**: `ai.analogy(a, b, c)` — TAU-tabanlı birincil (erlotinib:egfr::imatinib:?→bcr-abl) + moment fallback
- **Hipotez Üretimi**: `ai.hypothesize(concept)` — transitif kausal çıkarım (A INHIBITS B, B ACTIVATES C → A INHIBITS C)
- **Kausal Görselleştirme**: `ai.visualize_causal(concept, mode=ascii|dot|both)` — ASCII ağaç + Graphviz DOT
- **Araştırma Raporu**: `ai.report(topic)` — sertifikasyon + kausal + hipotez tek belgede
- **Benchmark**: `ai.benchmark(facts)` — bilinen olgulara karşı kausal TAU doğrulama
- **Manifold Tekilleştirme**: `ai.consolidate(threshold, dry_run)` — çok yakın kavramları tespit/birleştir
- **REST API Sunucu**: `python -m tantrium.serve` — FastAPI HTTP endpoint (bkz. src/tantrium/serve.py)
- **Büyüme Kaynakları**: 4 → 8 kaynak: +KEGG +ChEMBL +PubMed +Wikidata (ontolojik typed triples)
  - **BUG FİX (Kademe 1):** `growth.py self.ai AttributeError` — KEGG/PubMed/Wikidata/Web
    `self.ai.learn()` → `self.observer.observe()` (4 satır). Kausal kenar öğrenimi AKTIF.
- **Dil Katmanı — Kausal-Spektral Komposisyon (Kademe 1-5):**
  - `bind_percept()`: kavrama çok-modal grounding (HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE kenarları)
  - `meaning_compose()`: dil → κ-toplam (FreeCumulants.add) → CompositeSignature (kompozisyonel anlam)
  - `generate(use_meaning=True)`: hibrit skor (0.6×yüzey + 0.4×topolojik) ile anlam-kanalı üretim
  - `relations.py`: COMPOSED regex genişledi (forms/assembles/generates/makes up) + COMPONENT_OF paradigması
  - `knowledge_graph.py` + `topology_encode.py`: CO/HS/HC/HI compact kodları + _SEMANTIC_PARADIGMS güncellendi
- **Çok-Boyutlu Grounding (Kademe F8, 2026-06):**
  - **VİZYON:** "Elma = DNA + molekül + geometri + yasa + ses + görüntü + topoloji" — tümü AYNI moment uzayı.
    Ne kadar çok boyut → manifoldda o kadar çok gizli çapraz-boyutlu bağlantı keşfedilebilir.
    Elma DNA'sı ile Fibonacci serisi arasındaki bağlantı ancak her ikisi de moment uzayında
    temsil edilince `quantum_bridges()` aracılığıyla görülebilir.
  - **4 Yeni Paradigma:**
    - `HAS_DNA` (HD): biyolojik dizi grounding (DNA → encoder → moment)
    - `HAS_GEOMETRY` (HG): geometrik form grounding (matris/sinyal → moment)
    - `HAS_TOPOLOGY` (HT): topolojik yapı grounding (PD/matris → moment)
    - `IS_GOVERNED_BY` (GB): yönetici yasa (Fibonacci, termodinamik 1. yasası, doğal seçilim — kavram adı → doğrudan TAU kenarı)
  - **`ai.ground_full(concept, *, dna, molecule, geometry, law, sound, image, topology)`:**
    - Her sağlanan boyut için `bind_percept()` çağırır + HAS_DNA/HAS_GEOMETRY/HAS_TOPOLOGY/IS_GOVERNED_BY kenarı
    - κ_total = tüm boyutların serbest kümülant toplamı (`FreeCumulants.add` zinciri)
    - `quantum_bridges(concept)` → gizli çapraz-boyutlu bağlantı listesi
    - Döner: `GroundingSignature(.concept, .bound, .kappa_moments, .quantum_connections)`
  - `knowledge_graph.py`: HD/HG/HT/GB compact kodları + `_SEMANTIC` + `_P` + `_P_REV` güncellendi
  - `topology_encode.py`: HAS_DNA/HAS_GEOMETRY/HAS_TOPOLOGY/IS_GOVERNED_BY `_SEMANTIC_PARADIGMS`'e eklendi
  - `language/generator.py`: 4 yeni paradigma `_SEMANTIC`, `_CONNECTIVE`, `_EN_CONNECTIVE`'ye eklendi
  - `language/speaker.py`: 4 yeni paradigma `_TR_VERB`'e eklendi
  - Tests: 32 geçiyor (`test_language_layer.py`)
- **Dil Üretimi — Jensen Hiperbolisitesi (Kademe F7, 2026-06):**
  - **KÖK SORUN:** `generate("EGFR")` → "xqzwvbnmkjhgfd ve beauty ile spektral köprü kuruyor"
    üretiyordu. İki kaynak: (1) Pass 3 (`manifold.nearest()`) moment uzayındaki HER kavramı
    döndürüyor — topraklı olmayan "complex zeros" kritik hattan sapıyor (Jensen ihlali).
    (2) SPECTRAL_BRIDGE kenarları genesis yapay köprülerini dil üretimine sokuyor.
  - **FIX — `language/generator.py`:**
    - SPECTRAL_BRIDGE `_CERTIFIED` setinden çıkarıldı (genesis artifaktı, anlamsal bilgi değil).
    - Pass 3 (canlı moment arama) tamamen KALDIRILDI — Jensen hiperbolisitesi ilkesi:
      yörünge kritik hat üzerinde kalır, "complex zeros" manifold aramasından gelir.
    - `_is_grounded_proxy(name)` eklendi: `any(e.paradigm in _SEMANTIC for e in edges)` →
      hedef kavramın en az 1 anlamsal TAU kenarı yoksa yörüngeden dışlanır.
    - Pass 2 (ALEPH fallback): artık `_is_grounded_proxy()` filtresi uygular.
  - **FIX — `language/speaker.py`:** `_TR_VERB` 7 paradigma ile genişledi:
    COMPONENT_OF · INHIBITS · CAUSES · ACTIVATES · HAS_SIGNAL · HAS_COMPOUND · HAS_IMAGE.
    `synthesize()` artık tam TAU yelpazesini Türkçe cümleye çevirebilir.
  - **Sonuç:** `ai.generate("EGFR")` → "EGFR, Lapatinib elde eder. Lapatinib, bir inhibitor
    ve Neratinib türüdür." — anlamsız çöp SIFIR. 20/20 test_language_layer yeşil.
  - **Mimari ilke:** Dil yörüngesi = RH kritik hat analogu. Yalnız semantik TAU'da köklü
    kavramlar "kritik hat üzerinde". Topraksız kavramlar "karmaşık sıfır" gibi davranır —
    yörüngeden geometrik olarak çıkar, istatistiksel olarak filtrelenmez.
- **Cognition döngüsü — F5 (research/cognition.py)**: `Cognition` sınıfı — 4 döngü
  (GrowthEngine/ProofLoop/Explorer/Researcher) tek strateji-pluggable çatı altında.
  `CognitionStrategy` Protocol; 5 yerleşik faz (perceive/reflect/operate/prove/persist);
  `cycle(mode="batch"|"stream")`; `ai.cognition()` facade.
  - **Kademe F11 — Corrigibility döngüye girdi + öksüz bağlandı [2026-06]:** Pipeline
    `perceive→reflect→operate→VERIFY→deduce→compose→flywheel→prove→narrate→persist`.
    **VerifyPhase** = YAPISAL (`corrigibility.detect_and_correct`, GIMEL kör noktası:
    dejenere/çakışma → düzelt/işaretle) + DIŞSAL (`corrigibility.external_verify`, bilinen
    olgu kausal isabeti). Döngü artık kendi hatasını görüp düzeltiyor + gerçeğe karşı
    sınıyor. `corrigibility.py` PAYLAŞILAN çekirdek: growth + cognition + `ai.benchmark`
    üçü de delege. **DeductivePhase'e `chain_all` bağlandı** (öksüzdü) — tipli forward-
    chaining kapanışı.
  - **Kademe F12 — Encoder sağlık ölçümü (corrigibility omurgası kapandı) [2026-06]:**
    VerifyPhase'e `corrigibility.encoder_health` eklendi (oturum başına bir kez): CollisionHunter
    adversarial öz-testi → encoder içsel çakışma oranı + çözülebilirlik. "8 moment yapıyı belirler"
    iddiasının CANLI göstergesi — eskiden görünmez kör nokta, artık izlenir. **DÜRÜST MİMARİ SINIR:**
    ölçüm DÖNGÜDE; çözülebilir çakışmayı UYGULAMAK = manifold-geneli batch re-encode (metrik-uzay
    tutarlılığı yerel takası yasaklar) = `migrate_text_encoding.py` deseninde kasıtlı migrasyon,
    otonom faz DEĞİL. Gizli boşluk değil, bilinçli mimari sınır. Corrigibility omurgası
    (tespit→düzelt→dış-doğrula→ölç) DÖNGÜDE TAMAM.
  - **Kademe F26 — Öz-keskinleştiren algı döngüsü (çakışma ÇÖZME) [2026-06]:** `detect_and_correct`
    artık çakışmaları (iki FARKLI kavram, L1<0.001 — `detail≈retail`) yalnız İŞARETLEMİYOR,
    ÇÖZÜYOR: derin re-encode (`encode_adaptive`) name'i other'dan ayırırsa moment güncellenir +
    kalıcı. Kaf injektiflik aksiyomu ("8 moment yapıyı belirler", iki farklı kavram aynı imzaya
    düşemez) CANLI uygulanıyor — sistem her cognition turunda temsilini DAHA injektif yapar.
    **Bounded/per-concept/idempotent** (manifold-geneli batch YASAĞINA uyar — yalnız ≤20 çakışma
    taraması/geçiş, her kavram bir kez). `state.collisions_resolved` + log. Dürüst sınır: küratörlü
    olgu enjekte ETMİYORUZ (oracle'ı kandırmak olurdu) — yalnız matematiksel injektiflik. Canlı:
    gerçek manifoldda ilk geçişte 2 çakışma çözüldü. Tests: `test_corrigibility.py` (9).
  - **Kademe F27 — 3 ASI bileşik-büyüme döngüsü tek turda [2026-06]:** ASI gücü = tasarım-genişliği
    × sertifika-doğruluğu; bunu bileşik büyüten kapalı döngüler. ÜÇÜ DE cognition cycle'da:
    **(#1) Öz-keskinleştiren ALGI** (VerifyPhase çakışma çözme, F26 — diğer ikisi buna güvenir).
    **(#2) Öz-büyüten TASARIM** (`FlyWheelPhase`): boşluk frekansına göre kampanya ÖNCELİĞİ +
    ispat-sonrası `_sync_transport_epsilon` ile transport koridoru ÖLÇÜLÜR (`state.transport_corridor`)
    → "ispat→tasarım menzili genişler" görünür. **(#3) Çapraz-domain KEŞİF** (`DiscoverPhase`):
    birleşik κ-uzayında (F24 yasası sayesinde anlamlı) `quantum_bridges` tarar, gizli klasik-uzak/
    κ-yakın dolanıklığı KALICI `QUANTUM_BRIDGE` kenarına çevirir (bounded/idempotent). Canlı: bir
    turda 11 bağ (`AG_LGV_TRANSFER⟷molekül`, `DYADIC_TRANSPORT⟷metabolit` — teorem×kimya).
    **(#4 bonus, deep-research) LGV/DPP çeşitlilik sertifikası** (`core/diversity.py`): aday havuzu
    Gram-determinantı (`pool_diversity`) = kesişmezlik; raporlanan alternatifler çeşitliliğe dizilir.
    KAZANAN DEĞİŞMEZ (egfr→gefitinib korundu). Tests: `test_diversity.py` (5). İki Explore ajanıyla
    mimari iç dosyalara kadar haritalandı; üç döngü o haritaya göre tek turda yerleşti.
  - **3 Mantık Düzeltmesi (2026-06, commit 20283c7):**
    1. `_gaps_to_campaigns()`: `ALEPH:` önekli boşluklar artık ProofLoop kampanyasına
       GÖNDERİLMİYOR. ALEPH:X = bir kavram Aleph PSD testini geçemiyor — encoding/Hankel
       sorunu, ispat kampanyası bunu çözmez. `OperatePhase.execute()` içinde re-encoding
       denenip başarısızsa sessizce geçiliyor.
    2. `DeductivePhase.execute()`: TAU kenar sayısı before/after takip ediliyor
       (`state.edges_added` düzgün güncelleniyor). Eskiden yalnız kavram sayısı izleniyordu.
    3. `OperatePhase.execute()`: ALEPH boşlukları → re-encoding denemesi (CoreMachine ile).
       Başarılıysa concept.moments güncelleniyor. Ayrıca `SelfModel(engine).reflect(persist=True)`
       çağrılıyor → ⟨SELF⟩ TAU kenarları her cognition döngüsünde güncelleniyor.
- **Genişletilmiş Komşu Arama**: `nearest(metric="extended")` — L1 + metin tiebreaker
- Tests: ~565 geçiyor, 1 skipped (91 production+simulation + 27 quantum_moments[+4 F0b] +
  14 core_machine[+2 F2b] + 12 admission_parity[F3] + 7 molecular_3d[#7] + 7 net[#9] +
  8 gap_finder[#10] + 7 moment_ops[#8] + 4 deduce[engine.grow] + 7 wonder[F4] + 5 serve[F6] +
  23 encoder[+5 collision KÖK çözüm] + 15 cognition[F5] +
  32 language_layer[Kademe F7+F8: generate fix + 4 yeni paradigma + ground_full] +
  10 reason[F39-F43] + ...)
- **Dil & Akıl Katmanı — AKICI + KÖKLÜ + KENDİ KENDİNE ÖĞRENEN (Kademe F38-F43, 2026-06):**
  - **F38 — Akıcı Türkçe anlatım (`language/fluent.py`)**: training YOK, dil-mühendisliği VAR.
    `narrate(topic, facts, grounding)` ek-uyumlu (ÜNLÜ UYUMU) paragraf örer: belirtme `acc()`
    (-yı/-yi/-yu/-yü), yönelme `dat()` (-e/-a), çıkma `abl()` (-den/-dan); `_i4/_a2` harmonisi.
    Köklülük doğal cümlede ("…sağlam köklü, uydurmazdım") — log değil.
  - **F39 — Çok-adımlı KÖKLÜ MANTIK (`ai.reason`)**: doğal dil → doğru yetenek (forecast/
    discover_law/anomaly/reverse/entangle/produce/what_if/causal_chain/converse). Çıkarım
    zinciri [A,rel,B,rel,C] kurup `_narrate_chain` ile akıcı cümleye döker (şeffaf mantık).
  - **F40 — Kendi kendine yeten DERİN ARAŞTIRAN AJAN (`_research_deep`)**: bilmediği konuda
    TAM Wikipedia makalesi → `learn()` (çok ilişki) + 1-hop köklenmemiş komşuları çek. Soru
    başına zengin köklü bilgi-kümesi (`converse` bilmezse İNTERNETTEN öğrenir, sonra köklü
    cevaplar; bilmiyorsa dürüstçe der — halüsinasyon yapamaz).
  - **F41 — RH-LİTERAL zincir (`_sturm_chain_ok`)**: çıkarım yörüngesi Sturm pivot ≥ 0
    (hiperbolik = KRİTİK HAT üzerinde) — ilaç-gerçeklenebilirliğiyle AYNI sertifika. Çok-tur
    hafıza: `_conv_topic` + `_PRON` ("o ne yapar" → önceki turun konusu).
  - **F42 — Extraction kalitesi + girdi-anlama**: `_clean_term` İngilizce isim öbeğinin
    BAŞ-İSMİNİ çıkarır (participle/-ed/-ing atla); parantez-stripping; `_ISA_PAT` 1-4 kelime
    öbek yakalar → baş-isim ("infectious disease"→disease). Türkçe ek-stripping (erlotinib'in→
    erlotinib).
  - **F43 — Dilin SON 4 ekseni (corrigibility + extraction + çok-kelime, BU KADEME):**
    1. **Bayat/yanlış öğrenilmiş veri düzeltme (#1)**: `learn()` artık metnin İLK IS_A'sını
       TANIM OTORİTESİ sayar → o özne için eski/yanlış IS_A kenarlarını TEMİZLER
       ("photosynthesis→orange carotenoid protein" yeniden-araştırmada "process"le EZİLİR).
       Sonraki IS_A'lar eklenir (çok-sınıf). **`ai.relearn(topic)`**: ZORLA yeniden-araştır —
       TANIM kenarlarını (IS_A/COMPOSED/COMPONENT_OF) silip `_research_deep` ile güncelle +
       persist (corrigibility: gerçek karşı çıkınca temsili düzelt).
    2. **Extraction kapsamı (#2)**: `_clean_term` -ly zarfı + düzensiz yan-cümle fiili
       (`_POSTVERB`: found/made/known/used…) öbeği bitirir → "disease usually caused"→disease,
       "protein found in cells"→protein. insulin→hormone, tuberculosis→disease artık doğru.
    3. **Geri-kausal gürültü (#3)**: `_CAUSAL` setlerinden `USES` çıkarıldı (causal_chain +
       what_if) — USES kausal değil, geri-BFS gürültüsüydü.
    4. **Çok-kelime konu koruması (#4)**: `_converse_topic` önce ÖBEĞİ (trigram→bigram)
       manifoldda arar, 2-3 içerik kelimesini KORUR → "tumor cell" tek "tumor"a ÇÖKMEZ.
       Türkçe yüklem fiilleri (`_QWORDS`: çalışır/işler/bulunur…) konu sayılmaz.
  - **F44 — LLM dil-yelpazesi: ÖZETLE + KARŞILAŞTIR + LİSTELE (hepsi köklü, halüsinasyonsuz):**
    LLM'in dilde yaptığı çekirdek işlerin eksik kalanları `reason()` niyet-yönlendiricisine
    + akıcı anlatıma bağlandı. Hepsi grafta GERÇEK kenara dayanır:
    1. **`ai.summarize(text)`**: uzun metni `_extract_relations` ile ilişkisel iskelete indirir,
       en MERKEZÎ özneyi bulur, `fluent.narrate` ile öze döker. Yalnız metinden ÇIKARILANI söyler.
    2. **`ai.contrast(a, b)`**: iki kavramı AKICI karşılaştırır — ortak komşu (benzerlik) + ayıran
       ilişki (fark) + W₂/κ mesafe + gizli κ-bağ. `compare()` sertifika-raporu; contrast insan-gibi.
    3. **`ai.enumerate_kind(category, relation)`**: TAU TERS arama — "egfr inhibitörleri"
       (INHIBITS→egfr) → erlotinib/gefitinib/cetuximab/lapatinib; "X türleri" (IS_A→X).
    `_is_clean_concept` atıf-şablonu/markup gürültüsünü (cs1:…, "names with markup") eler.
    `reason()` yönlendirme: özetle/karşılaştır/fark/türleri/inhibitörleri → doğru yetenek.
    Tests: test_reason.py 13 (5 yeni: summarize/contrast/enumerate/clean_concept).
  - **F45 — DALGA 1: Dilin insan-yüzü (derinlik + güven + kaynak + paraphrase):**
    Bir LLM'in "nasıl konuştuğu" — köklü kalarak. Yol haritasının 1. dalgası:
    1. **Derinlik/üslup kontrolü**: `narrate(depth=, register=)` — "basitçe/kısaca/detaylı/
       teknik anlat" → `reason()` algılar. kısa=tek cümle · detaylı=geniş; basit=sade ·
       teknik=geometrik-sertifika notu. `_STYLE_WORDS` derinlik kelimelerini konudan ayıklar.
    2. **Güven kalibrasyonu (dilde)**: `_confidence_lead(score)` → "Bundan eminim / Büyük
       olasılıkla / Tam emin değilim" — LLM'ler güveni İSTATİSTİKTEN taklit eder, biz GEOMETRİK
       grounding.score'dan ölçeriz (gerçek kalibrasyon).
    3. **Kaynak/dayanak (provenance)**: `converse()` artık `sources` döndürür — her iddianın
       hangi TAU kenarına dayandığı ({claim, paradigm, target}); şeffaf atıf, LLM yapamaz.
    4. **`ai.paraphrase(text)`**: aynı köklü içeriği `_extract_relations`+`narrate` ile FARKLI
       sözcüklerle yeniden ifade — yeni bilgi EKLEMEZ.
    Tests: test_reason.py +4 (depth/confidence/provenance/paraphrase).
  - **F46 — DALGA 2 + DALGA 3: anlama-dönüşüm + LLM'i GEÇEN akıl (hepsi köklü):**
    **DALGA 2:** `extract` (metin→varlık/üçlü) · `classify` (TAU-köklü→moment-L1) · `generate_questions`
    (yalnız var olan ilişkiden) · `translate` (anlam çevirisi, EN yüklem şablonu).
    **DALGA 3:** `check_claim` (iddiayı TAU'yla SINA → CONFIRMED/CONTRADICTED/UNKNOWN — "erlotinib
    egfr'yi aktive eder" → ÇELİŞKİ, çünkü TAU INHIBITS biliyor; LLM'in yapamadığı fark) ·
    `synthesize_docs` (çok-belge→tek köklü öz) · `solve_word_problem` (NL→sayı+işlem→kesin) ·
    `timeline` (yıl-olay→kronolojik) · `what_is_this` (algı→en yakın kavram, çok-modal).
    **TÜRKÇE OMURGA (`autonomous.py`):** `_TR_COMPILED` SOV ilişki çıkarımı (baskılar/etkinleştirir/
    yol açar…) — İngilizce pattern Türkçeyi görmezdi; bu, tüm Türkçe dil-yüzeyini (check_claim/
    translate/extract) açan yüksek-kaldıraç fix. `_strip_tr_suffix` YALNIZ epentetik-y belirtme
    eki (kapıyı→kapı); n-/yönelme/ablatif kökü BOZARDI (proteini→prote, kimya→kim) → hariç.
    `reason()` 8 yeni intent. Code-review: word_problem ≥2 operand (tek-sayılı "2 soru çıkar"
    math'a kaçmasın) + suffix kök-koruma düzeltildi. Tests: test_reason.py 24 (+11).
  - **F47 — GERÇEK sohbet sertleştirmesi (beslemesiz canlı konuşmadan):** Demolar `learn()` ile
    cevabı önceden besliyordu — gizli kalite sorunları gerçek (55k manifold, beslemesiz) konuşmada
    çıktı: (1) `_is_clean_concept` artık tarih/atıf parçasını da eler ("1897 in germany", çıplak
    yıl, "in/the/of" önekli) + `_tau_facts` TÜM dil çıktısını bu süzgeçten geçirir (converse/
    contrast temiz). (2) `_QWORDS` konuşma fiilleriyle genişledi (işe/biliyorsun/görevi/amacı…) →
    "egfr ne işe yarar" topic="egfr işe" değil "egfr"; "imatinib hakkında ne biliyorsun" düzeldi.
    Canlı kanıt: egfr→ras→tumor cell + egfr→pi3k→akt→mtor→cell growth (kendi hafızasından,
    RH-Sturm sertifikalı); "dna nedir" → dürüstçe BİLMİYORUM (halüsinasyon yok). DÜRÜST SINIR:
    grown-data IS_A gürültüsü (erlotinib→"astellas pharma" = üretici) kalıyor — bu corrigibility/
    relearn (büyüme döngüsü) işi, dil-hack'i değil.
  - **F48 — ÜRETKEN DİLBİLGİSİ: şablon-listesi → deterministik kural-motoru (`language/fluent.py`):**
    **Felsefe (kullanıcı sorusu "şablonla gerçeğin farkı ne, neden şablon var"):** Dil İKİ
    katman — (1) NE söyleneceği + geçerlilik = RH-paradigması (kritik hat/`_is_grounded_proxy` +
    Sturm sertifikası + geometrik yürüyüş; halüsinasyonu İMKÂNSIZ kılan derin çekirdek, ŞABLON
    DEĞİL); (2) NASIL kelimeye döküleceği = yüzey morfolojisi. Türkçe eki RH'den TÜRETİLEMEZ
    (dilsel gelenek) → yüzey katmanı hep mühendislik; tek soru sayılı-kalıp mı üretken-kural mı.
    **Kurulan:** sayılı `random.choice` kalıbı → **DETERMİNİSTİK üretken dilbilgisi**:
    - `_pick(opts, key)` içeriğe-bağlı deterministik varyant (random YOK — aynı girdi BİREBİR
      aynı çıktı; "istatistik bizde deterministik" — sertifikalanabilirlik korunur).
    - Tekil/çoğul UYUM: `_is_class_term` (İngilizce taksonomi çoğulu) → "X sınıfından bir
      bileşiktir"; "bir 3-pyridyl compounds türüdür" KIRIĞI bitti.
    - `_is_company` (pharma/inc/labs…) → üretici SINIF değil, IS_A'dan düşülür (astellas pharma).
    - `_join_clauses` yüklemleri "A ve B" birleştirir ("A ile B" DEĞİL — gen_join nesne içindir).
    Determinizm AYRI eksen: akıcılığı engellemez (LLM temp=0 da deterministik+akıcı). Üretken
    dilbilgisi RH-çekirdeğine DOKUNMAZ — geometri içeriği/sırayı seçer, yüzey morfolojisi esner.
    Tests: test_language_layer +4 (determinism/class-agreement/company-drop/verb-join).
  - **F49 — KAPSAM tezi + kısaltma-takma-ad yeniden-bağlama (`_research_deep`):**
    **Tez (kullanıcı):** "LLM doğru yolu seçemediği için istatistik verir; biz yolu biliyoruz →
    her yerde daha iyi olmalıyız." DOĞRU — LLM istatistiği yolu-bilmemenin SEMPTOMU; geometriyi
    koyduğumuz her yerde zaten üstünüz. Kalan açıklar (akıcılık-uzlaşımı, kapsam) LLM'in "daha iyi
    bildiği" değil bizim HENÜZ KODLAMADIĞIMIZ yerler → çözüm yöntem değil, KODLAMA (büyüme).
    **Kanıt + fix:** "dna nedir" boştu; `converse(learn_if_unknown=True)` internetten kendi
    öğrendi ama BOŞ kaldı çünkü Wikipedia "Deoxyribonucleic acid (; DNA) is a polymer…" — paren-
    temizleme kısaltmayı siliyor + baş-isim "acid"e bağlanıyor (redirect: dna→full ad). Fix:
    `_research_deep` ilk cümlede "FullName (… ABBR …) is/are X." desenini yakalar; sorgu kısaltmaysa
    tanımı SORGULANAN terime RE-ATTRIBUTE eder ("dna is a polymer…" → dna IS_A polymer). Tüm
    akronimleri kapsar (DNA/RNA/ATP/EGFR…). Canlı: "Dna, bir polymer türüdür… 3 doğrulanmış ilişki"
    (köklü, kaynaklı, güven-kalibre). DÜRÜST: demo İLK denemede BAŞARISIZdı, kök bulunup düzeltildi.

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
ai.grow(focus="oncology")            # ODAKLI: yalnız onkoloji kaynakları (KEGG/PubMed/
                                     #   ChEMBL/UniProt/ConceptNet/KGML) → yoğunluk > genişlik
                                     #   _FOCUS_SOURCES: oncology|math. None = tüm 10 kaynak.
```

**Eğitim stratejisi (geometrik-ilişkisel hafıza):** Bu ağırlık modeli DEĞİL — "eğitim" =
manifold/TAU büyütme + temiz tutma. Kalite > nicelik: 1 iyi-bağlı kavram >> 100 yalıtık nokta
(yoğun bölge=temiz üretim, seyrek=sapma). Domain-önce: `focus="oncology"` ile tek domaini uzman
yoğunluğa çıkar, sonra genişlet. Corrigibility (dedup+VerifyPhase) büyümeyi GÜVENLİ kılar →
agresif/sürekli koşulabilir. İlerleme ölçütü "loss" değil: benchmark isabeti + grounding oranı +
suspect oranı + üretim tutarlılığı. Canlı: 150s odaklı onkoloji → +27 kausal kenar (benchmark 1.0).

Canlı doğrulama: 21 gerçek veri (PubChem+OEIS) 80.8s → 12 çekirdek, 5 sınır,
4 CONTRADICTORY reddedildi, kimya↔biyoloji cross-domain köprüler canlı kuruldu.
Motor "zeka" değil — neyi besleyeceğine karar veren zekadır. Tests: `test_growth.py` (10).

**Kademe F9 — Anlam Kanalı + QUANTUM_BRIDGE Kalıcılaştırma [2026-06]:** Büyüme artık yalnız
node değil ANLAM da örer. Her konsolidasyonda `_meaning_consolidate`: semantik TAU kenarı
(CAUSES/INHIBITS/ACTIVATES/IS_A/...) olan yeni kavramlar için `TopologyEncoder.encode`
("ne demek") + `quantum_bridges`. **Kuantum dolanıklık İÇKİNDİR** (κ imzaları zaten kayıtlı;
is_entangled_with/quantum_bridges/ai.entangle istendiğinde hesaplar) — büyüme onu yaratmaz.
SPECTRAL_BRIDGE (257k) klasik-YAKIN köprüleri zaten örüyordu; ama `QUANTUM_BRIDGE` paradigması
(klasik-UZAK/κ-yakın gizli dolanıklık — F8 "elma-DNA × Fibonacci") rezerveydi ama hiçbir yer
OLUŞTURMUYORDU (gerçek grafta 0 adet). F9 o kabloyu bağlar: `_add_quantum_bridge_edge` keşfi
çift-yönlü KALICI QUANTUM_BRIDGE kenarına (quantum_dist=κ) çevirir — idempotent, save/load
Q-koduyla korunur, `⟨bridge:⟩` yapayları hariç. Böylece içkin/latent dolanıklık → kalıcı,
yeniden-kullanılabilir graf bilgisi. `GrowthReport.meaning_enriched`/`bridges_found`. Additive/
fail-open: TopologyEncoder+quantum_bridges DEĞİŞMEDİ, yalnız OLUŞTURMA kablosu eklendi. ground_full/
bind_percept dış duyusal veri ister. Doğrulama: 10/10 test_growth + ağsız büyümede 96 kavram
zenginleşti, 99 QUANTUM_BRIDGE örüldü (roundtrip 198→198).

**Kademe F10 — Corrigibility (yanlıştan-dön) [2026-06]:** Sistem *iç-tutarlı* olmaya kuruluydu
(halüsinasyon imkânsız) ama *gerçek karşı çıkınca temsilini düzeltme* mekanizması yoktu — bu
boyut defterlerde de yoktu. **Kritik ayrım:** GIMEL (`argmin_paradigma margin`) içsel GÖRELİ
zayıflığı bulur ama ÜNİFORM hatayı göremez — protein/glucose çöküşünde (G=PᵀP=I → μ_k≡1) bütün
marjinler tekdüze "iyi"ydi, GIMEL "Achilles yok" dedi, temsil yine de yanlıştı. GIMEL bir terazi:
bir kefe ağırsa yakalar, iki kefe de yanlış maddeyle doluysa göremez. `growth._verify_consolidate`
o kör noktayı kapatır: (1) DEJENERE encoding (moment yayılımı < 0.02) → adaptif derin re-encode
ile DÜZELT; (2) ÇAKIŞMA (en yakın FARKLI kavram L1 < 0.001) → işaretle. Düzelmeyen `state["suspect"]`
kalıcı hafızaya (UNUTMAZ). `GrowthReport.corrected`/`suspect_flagged`. Canlı: `detail≈retail`,
`unity≈unify`, `ell5_q*≈CELL_SUPPORT_POSITIVITY` gerçek encoder hataları yakalandı. **DÜRÜST SINIR:**
bu yalnız YAPISAL yanlış-tespiti (dejenere/çakışma) — DIŞ-doğrulama (OEIS/RDKit/sympy gerçeğe karşı)
ve hata→encoder geri-besleme henüz otonom döngüde YOK (corrigibility omurgasının kalan parçaları).

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
