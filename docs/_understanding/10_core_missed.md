# 10 — Çekirdekte Atlanan Dosyalar (Descriptive)

Daha önce okunmamış altı çekirdek dosyanın satır-düzeyi okumadan çıkarılmış SALT-TANIMSAL
defteri. Her dosya için: (1) tek-satır amaç, (2) çekirdek mantık/mekanizma, (3) anahtar
sınıf/fonksiyon. Yargı/kalite/boşluk değerlendirmesi YOK.

---

## src/tantrium/core/grounding.py

**(1) Amaç:** Sertifikasyonun 2. ekseni — bir token'ın YAPISAL geçerliliğin ötesinde
TOPRAKLANMIŞ (bilinen referanslara bağlı) olup olmadığını yargılar. 23 paradigma G=AᵀA PSD
olduğundan her şeyi "var" der; bu modül çöpü (sıfır kenarlı `xqzwvbnmkjhgfd`) bilinenden ayırır.

**(2) Mantık/mekanizma:** `GroundingCertifier` iki bağımsız sinyali hesaplar.
- **Doğrudan topraklama** (`_direct_grounding`): token TAU grafında köklü düğüm mü? Çıkan kenar
  (`tau.edges.get(token)` + lowercase) + gelen kenar (tüm edge listelerini tarayıp `e.target`
  eşleşmesi) toplanır; `in_manifold` = token VEYA lowercase'i `manifold.concepts`'te mi.
- **Rezonans topraklama** (`_resonance_grounding`): bilinmeyen token için moment imzasının köklü
  ve TUTARLI bir kümeye düşüp düşmediği. `manifold.nearest(concept, n=30)` komşuları; SADECE
  L1 ≤ `_RESONANCE_RADIUS=0.3` içindekiler sayılır (doymuş manifoldda her nokta bir komşuya
  yakındır — sıkı yarıçap gürültüyü eler); `⟨bridge:` köprüleri çapa olmaz (yapay ara nokta);
  her komşunun ≥3 kenarı varsa "köklü" sayılır, domain sayımı tutulur; baskın domain oranı =
  `coherence`.
- **Birleşik yargı** (`certify`): moment verilmezse encode edilir, `_grounding_probe::` adıyla
  geçici `Concept` kurulur. Yargı sıralı: `direct_edges ≥ 3` → **GROUNDED** (score 0.6 +
  edges/100); `direct_edges ≥ 1` → **WEAKLY_GROUNDED**; `in_manifold` + ≥1 köklü komşu →
  **WEAKLY_GROUNDED**; aksi → **UNGROUNDED** (score 0.0). Yorum notuna göre doymuş manifoldda
  rezonans hüküm için kullanılmaz; iki sağlam sinyale (doğrudan kenar + in_manifold) inilir.

**(3) Anahtar yapılar:**
- `GroundingCertificate` (dataclass): `token, verdict, direct_edges, in_manifold,
  grounded_neighbors, neighbor_coherence, dominant_domain, nearest_grounded, score`;
  `is_grounded` property + Türkçe `summary()`.
- `GroundingCertifier.certify(token, moments=None) -> GroundingCertificate` — ana giriş.
- Sabitler: `_GROUNDED_NEIGHBOR_MIN_EDGES=3`, `_RESONANCE_K=30`, `_RESONANCE_RADIUS=0.3`,
  `_COHERENCE_MIN_RATIO=0.5`, `_RESONANCE_MIN_GROUNDED=4`.

---

## src/tantrium/core/certificate.py

**(1) Amaç:** TEK geçerlilik para birimi — "aday doğru yolda mı (kritik hatta) ve ezber değil
genelleşiyor mu". Dağınık 5 kopyayı (positivity_ladder, Sturm-pivot, leave-one-out, holdout,
Sturm-zincir) tek arayüze indirir; meta-sentezin kabul kapısıdır.

**(2) Mantık/mekanizma:** İki eksen.
- `certify_transition(src, tgt, min_depth=3)`: moment geçişinin pozitiflik geçerliliğini
  `positivity_ladder.positivity_depth(src, tgt)`'e DELEGE eder (tek-gerçek math). Döner derinlik
  0–3 (Hankel → Newton → Sturm/Jensen); `on_path = depth >= min_depth`. Rung detayları
  `detail`'e konur.
- `certify_generalization(builder, instances, verify, min_instances=3)`: leave-one-out holdout.
  Her örnek sırayla dışarıda bırakılır; `builder(train)` kalanlardan aday kurar, `verify(cand,
  [held])` dışarıdakini sağlıyor mu denetler; HEPSİ geçerse `True`. `n < min_instances` →
  `False` (güvenilir test edilemez = iddia etme).

**(3) Anahtar yapılar:**
- `CertResult` (dataclass): `on_path, depth, generalizes, detail`; `__bool__` = `on_path`.
- `certify_transition(...) -> CertResult`, `certify_generalization(...) -> bool`.
- Sabit: `_FULL_DEPTH = 3`.

---

## src/tantrium/core/meaning_cache.py

**(1) Amaç:** Kalıcı "zengin-düğüm" katmanı — köklü kavramların `meaning_pipeline.measure`
ile üretilen ölçüm imzasını (topoloji + Li-cascade + akış/flow) oturumlar arası biriktirir.
Concept'in kanonik 8-momentini bozmadan, AYRI bir JSON dosyasında zenginliği taşır.

**(2) Mantık/mekanizma:** `MeaningStore` bir `dict[name -> compact-sig]` saklar.
- `_compact(sig)`: `MeaningSignature`'ı JSON-dostu kayda indirir (topo momentleri 6 hane, li/flow
  4 hane yuvarlanır, komşular ilk 8'e kırpılır, `spectrum_n`/`n_neighbors` tutulur).
- CRUD: `has/get/put/__len__`; `put` yalnız `sig.grounded` ise saklar.
- Kalıcılık: `load(path)` / `save(path)` → `results/agi/meaning_cache.json` (`{"signatures": {...}}`);
  yükleme hatası fail-open boş store döner.
- `_semantic_outdegree(engine)`: her kavramın semantik (tipli, `_SEMANTIC_PARADIGMS`'te) çıkan
  kenar sayısı = köklülük derecesi (>0 olanlar).
- `refresh_meaning_cache(engine, store, limit=30, max_neighbors=24)`: cache'te OLMAYAN en yüksek
  semantik-çıkan-dereceli adayları (`limit*3` tarar) `measure(...)` ile ölçer; `grounded`
  çıkanları `store.put` ile ekler; `limit`'e ulaşınca durur. Bounded/fail-open. Eklenen sayı döner.

**(3) Anahtar yapılar:**
- `MeaningStore` (`sigs: dict`; `has/get/put/load/save`).
- `_compact(sig) -> dict`, `_semantic_outdegree(engine) -> dict[str,int]`,
  `refresh_meaning_cache(engine, store, ...) -> int`.
- Sabit: `_CACHE_PATH = "results/agi/meaning_cache.json"`.

---

## src/tantrium/core/meta.py

**(1) Amaç:** TEK meta-sentez motoru — sistem kendi KURAL/STRATEJİsini (alan-bağımsız) icat eder.
Graf-kural icadı ile kod-şema icadı AYRI motorlar değil; tek `meta_synthesize(adapter)` + çoğul
adaptör; kabul kapısı tek (`certify_generalization`).

**(2) Mantık/mekanizma:**
- `meta_synthesize(adapter, engine, max_candidates=16, **kw)`: adaptörün `candidates(...)`'ını
  alır; her aday `certify_generalization(build, instances, verify)` geçidinden geçer; geçen
  adayın tüm-veriyle nihai artefaktı kurulup `commit(art)` ile kaydedilir → icat-adı listesi.
  Bounded, fail-open (her aday try/except).
- `MetaCandidate` (dataclass): `name, build(train)->artefakt|None, instances, verify(art,held)->bool,
  commit(art)->ad|None`. `MetaAdapter` Protocol: `domain` + `candidates(engine, **kw)`.
- **GraphAdapter** (`domain="graph"`): grafı gözleyip üç kural ailesini İCAT eder. `priority`
  tohumları (boşluk/frontier) ÖNCE taranır (teleoloji). Bir geçişte düğümleri (`max_seeds=300`)
  tarar:
  - **Aile 1 (transitif):** `a -relA-> b -relB-> c` zinciri varken `a -relC-> c` doğrudan kenar
    varsa, `(relA,relB) -> relC` gözlemi toplanır; ≥`min_obs=3` ve tabloda OLMAYAN çiftler aday
    (`register_transitive_rule`). Build = tüm gözlemde tek tutarlı relC.
  - **Aile 2 (converse):** `a -relX-> b` varken `b -relY-> a` ters kenar gözlemi → `relX⁻¹→relY`
    (`register_converse_rule`).
  - **Aile 3 (implication/içerme):** `relX` olan HER çiftte `relY` de varsa (karşı-örnek yok) →
    `relX⊑relY` (`register_implication_rule`). Çift kümeleri kesişimi ile bulunur.
  - `GENERIC_TERMS` ve `⟨` önekli düğümler atlanır; sabit `TRANSITIVE_CAUSAL`/`LEARNED_*`'te
    olanlar geçilir (elle bilgi korunur).
- **Uygulama fonksiyonları** (öğrenilen kuralları grafa materyalize eder, her uygulama AYRI
  `certify_transition(min_depth=2)` pozitiflik geçidi, bounded):
  - `apply_converse_rules`: `LEARNED_CONVERSE`'e göre eksik `b -relY-> a` kenarı ekler.
  - `apply_implication_rules`: `LEARNED_IMPLICATION`'a göre eksik `a -relY-> b` kenarı ekler.
  - `derive_analogy_edges` (4. aile, conjecture): ≥`min_shared=3` ORTAK tipli komşulu analog
    çiftler bulup X'in ilişkisini analog Y'ye transfer eder (pozitiflik geçerse) — KONSERVATİF.
- **CodeAdapter** (`domain="code"`): `code_meta._CANDIDATE_SCHEMAS` şema-ailelerini AYNI motora
  bağlar; build = şema-kurucu, verify = `_verify_source(held)`, commit = `register_schema`.

**(3) Anahtar yapılar:**
- `meta_synthesize(adapter, engine, ...) -> list[str]`.
- `MetaCandidate`, `MetaAdapter` (Protocol).
- `GraphAdapter` (`candidates` + `_make_candidate`/`_make_converse_candidate`/
  `_make_implication_candidate`).
- `apply_converse_rules`, `apply_implication_rules`, `derive_analogy_edges`.
- `CodeAdapter`.

---

## src/tantrium/core/primitive_invention.py

**(1) Amaç:** CAPSTONE — taban sentez ve tüm şemalar bir spec'i çözemediğinde yeni ATOMİK İLKEL
(taban operatörün kendisi) icat eder; en derin frontier.

**(2) Mantık/mekanizma:** İki kanal — TASTE (icat etmeye değer mi, deterministik Wonder yargısı)
+ TRUTH (geçerli mi, leave-one-out holdout).
- Tohumlanmış üretken aileler (parametreli): `_fit_modular` (`y = (x%m)+c`, m=2..12 dener, offset
  tutarlıysa) ve `_fit_power` (`y = x**k` veya `x**k - x`, k=3..6). Her biri uyan parametreyi
  train'den FİT eder, `InventedPrimitive` döner (`_primitive_pool` formatlı `prim_str` + predict
  lambda).
- `_wonder(prim, examples)`: TASTE — novelty (1.0) eksi dejenere cezası (sabit çıktı → +1.0;
  kimlik fonksiyonu → +1.0), `novelty - 0.5*degeneracy`.
- `invent_primitive(examples, register=True)`: ≥3 örnek ve tüm-int (bool hariç) tek-arg şart.
  Her aile için `certify_generalization` (TRUTH/holdout) geçerse `fam(examples)` ile ilkel kurulur,
  `_wonder` skoru atanır, en yüksek wonder seçilir (TASTE); seçilen `register_primitive` ile
  `_INVENTED_NUM`'a eklenir (gelecekte taban havuzu kullanır). Genelleşen yoksa `None` (dürüst
  başarısızlık).

**(3) Anahtar yapılar:**
- `InventedPrimitive` (dataclass): `name, prim_str, predict, family, wonder`.
- `invent_primitive(examples, register=True) -> InventedPrimitive | None` — ana giriş.
- `register_primitive(prim) -> bool`, `invented_primitives() -> list[str]`.
- `_fit_modular`, `_fit_power`, `_wonder`; modül-global `_INVENTED_NUM`, `_FAMILIES`.

---

## src/tantrium/serve.py

**(1) Amaç:** Tantrium'un FastAPI tabanlı REST/HTTP arayüzü (`python -m tantrium.serve`).

**(2) Mantık/mekanizma:** FastAPI opsiyonel — import başarısızsa `_FASTAPI_OK=False`, `app=None`
(import-safe). Tek lazy singleton `_ai` (`_get_ai()` ilk çağrıda `tantrium.AI()` kurar). Her
endpoint için Pydantic `BaseModel` request şeması; handler `_get_ai()` üzerinden ilgili `ai.*`
metodunu çağırıp JSON/PlainText döndürür. `__main__` argparse ile uvicorn'u başlatır (`--host`
0.0.0.0, `--port` 8000, `--reload`); FastAPI yoksa kurulum mesajıyla çıkar.

**(3) Endpoint'ler / request modelleri:**
- `GET /health` → `{status, fastapi}`; `GET /status` → `ai.status()`.
- `POST /ask` (`TokenReq`) → 4-eksen alanları (certified, paradigms, grounding, truth, confidence).
- `POST /learn` (`LearnReq{text}`) → `ai.learn`.
- `POST /grounding` (`TokenReq`) → verdict/score/edges/summary.
- `POST /causal_chain` (`CausalReq{goal,depth}`), `POST /what_if` (`WhatIfReq{concept,depth}`).
- `POST /analogy` (`AnalogyReq{a,b,c,top_k}`), `POST /hypothesize` (`HypothesizeReq{concept,depth}`).
- `POST /visualize` (`VisualizeReq`, PlainText), `POST /report` (`ReportReq`, PlainText).
- `POST /benchmark` (`BenchmarkReq{facts?}`).
- `POST /quantum_distance`, `POST /synthesize`, `POST /entangle` (query params `a`,`b`).
- `POST /bind_percept` (`BindPerceptReq{concept,signal,modality,paradigm,name}`; numpy dizisine
  çevirir).
- `POST /meaning_compose` (`MeaningComposeReq{text}`) → CompositeSignature alanları (None-safe).
- `POST /generate` (`GenerateReq{seed,steps,goal,lang,use_meaning}`).
- Modeller: `LearnReq, TokenReq, CausalReq, WhatIfReq, AnalogyReq, HypothesizeReq, VisualizeReq,
  ReportReq, BenchmarkReq, BindPerceptReq, MeaningComposeReq, GenerateReq`; modül-global `app`, `_ai`.

---

## src/tantrium/__init__.py (export notu)

Paket düz-import yüzeyi (`from tantrium import ...`). `AI` ve sonuç tipleri (`AskResult,
MolResult, GenResult, ReasonResult, DiscoverResult, DesignResult`) + tüm çekirdek motor/sınıflar
re-export edilir: `CertificationEngine`, `CoreMachine`/`UnifiedCertificate`, reconstruct,
`TruthCertifier`, `Confidence/calibrate`, metric (`canonical_distance`/`l1_distance`),
`CollisionHunter`, encoder, `SemanticManifold`/`Concept`/`AdmissionResult`, transport, proof
ilkleri (`Cell`/`Certificate`/`solve_greedy`), graph (`KnowledgeGraph`/`SessionMemory`), research
(`ProofLoop`/`GrowthEngine`/`Goal`/`Actor`/`Ingest`/`Researcher`), reasoning (`GapFinder`/
`WonderScorer`/`GraphReasoner`/`Planner`/`NecessityReport`), language (`CertifiedGenerator`/
`Speaker`), spectral, meta (`SelfModel`/`ConceptSynthesizer`/`CosmicVision`), perception
(`encode_signal/image/matrix`), inverse/molecular_space/molecular_genesis, quantum_moments
(`FreeCumulants`/`QuantumSignature`/`bounded_kappa_distance`/`free_entropy`). `__all__` aynı
yüzeyi açıkça listeler. NOT: bu üst-paket `__init__` grounding/certificate/meaning_cache/meta/
primitive_invention'ı re-export ETMEZ — bunlar `tantrium.core.<modül>` ile erişilir.

## src/tantrium/core/__init__.py (export notu)

Çekirdek alt-paket yüzeyi: `codex` (`PARADIGMS, PARADIGM_BY_ID, CertifiableObject,
ParadigmResult`), `semantic` (`Concept, SemanticManifold`), `encoder` (`UniversalEncoder, encode,
encode_smiles`), `network` (`CertificationPipeline, CertificationRun`), `engine`
(`CertificationEngine`) re-export eder; `__all__` aynısını listeler. Bu dosyalar (grounding,
certificate, meaning_cache, meta, primitive_invention) `core/__init__`'te re-export EDİLMEZ;
doğrudan `tantrium.core.grounding` vb. tam yol ile import edilir.

---

wrote docs/_understanding/10_core_missed.md
