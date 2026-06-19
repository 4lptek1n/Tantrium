# 08 — `src/tantrium/research/` (Otonom Araştırma / Büyüme Katmanı)

> Saf-betimsel kayıt. Bu klasör sistemin "insansız" döngüsüdür: veri çek →
> sertifikala → öğren → boşluk kapat → kanıtla → kendini düzelt → kaydet.
> Her dosya satır-satır okunarak çıkarıldı. PER-FILE: (1) amaç (2) çekirdek
> mantık (3) anahtar sınıf/fonksiyon.

İçerikteki dosyalar:
`__init__.py` (boş) · `net.py` · `text_source.py` · `hf_source.py` · `ingest.py` ·
`autonomous.py` · `growth.py` · `cognition.py` · `proof_loop.py` · `explorer.py` ·
`researcher.py` · `goal.py` · `actor.py` · `corrigibility.py`.

---

## `__init__.py`
**(1) Amaç:** Paket işaretçisi. **(2) Mantık:** Tamamen boş (0 satır içerik) —
hiçbir re-export yok; her şey `from tantrium.research.<modül> import ...` ile düz
erişilir. **(3) Sembol:** yok.

---

## `net.py` — Paylaşılan HTTP-JSON transport (#9 dedup)
**(1) Amaç:** ingest/growth/researcher üçünün tekrar ettiği `urllib.request` GET→JSON
desenini TEK yere indiren ortak transport katmanı. Parse mantığı modül-başına FARKLI
kalır (gerçek ayrım korunur); yalnız HTTP taşıma birleşti.

**(2) Mantık:** İki ince fonksiyon. İstisnalar YUTULMAZ — her caller fallback'i
kendi yönetir. `errors` ile UTF-8 decode modu seçilir (`strict` = ingest/researcher,
`replace` = growth toleranslı). `http_get_json_link` Link header'ından
`rel="next"` cursor URL'sini regex (`<...>; rel="next"`) ile çeker — URL içindeki
virgüllere (`fields=a,b,c`) dayanıklı (UniProt cursor sayfalama).

**(3) Semboller:**
- `DEFAULT_UA` — sabit User-Agent string.
- `http_get_json(url, *, timeout, user_agent, errors)` — URL'den JSON GET, hata fırlatır.
- `http_get_json_link(url, ...) -> (body, next_url|None)` — JSON + Link-next cursor.

---

## `text_source.py` — Fitsiz metin-büyüme kaynağı (Wikipedia → absorb)
**(1) Amaç:** Büyümenin "edinme" yarısı, fit'siz: internetten ham metin çekip
`ai.absorb` ile gizli-yapı keşfi → evren-kapısı → kNN COOCCURS kenarı borusundan
geçirir. Gradyan/eğitim yok; sertifika kapısı korunur (çöp/çelişki reddedilir).

**(2) Mantık:** Wikipedia w/api.php endpoint'i. Tek-makale (`fetch_wikipedia`,
redirect izlenir, ≥200 char), rastgele başlık (`fetch_random_titles`), ve TOPLU
çekim (`fetch_random_articles`: `generator=random` + `prop=extracts` + `exintro` →
N round-trip'i 1 HTTP çağrısına indirir, lead = ansiklopedik tanım). `absorb_topics`
her konuyu çekip `ai.absorb(persist=False)` ile işler, sonda tek persist. **Tek-yazar
kuralı:** `persist=True` yalnız canlı runner DURMUŞKEN (aynı dosyaya iki yazar = bozulma).

**(3) Semboller:**
- `fetch_wikipedia(title)` · `fetch_random_titles(n)` · `fetch_random_articles(n, *, min_chars)`.
- `absorb_topics(ai, topics, *, persist, fetch, **absorb_kw)` — birikimli rapor döner
  (`topics/fetched/concepts_admitted/rejected/edges_added/per_topic`). `fetch` enjekte-edilebilir (test mock).

---

## `hf_source.py` — HuggingFace veri borusu (anahtarsız)
**(1) Amaç:** Public HF dataset'lerini API anahtarı GEREKMEDEN çekip sistemin mevcut
ingestion'ına (observe → encode + kenar + evren-kapısı) akıtır. Yeni makine değil —
`net.http_get_json` + `AutonomousObserver`'a delege.

**(2) Mantık:** `datasets-server.huggingface.co/rows` HTTP API. Satırdan en iyi metin
alanını (`_TEXT_FIELDS` tercih sırası → en uzun string fallback) seçer. `stream_hf_text`
bounded streaming (offset ilerletir, limit dolunca durur). `feed` her satırı
`AutonomousObserver.observe`'a verir, core/frontier/rejected bölgelerini sayar; opsiyonel
`enrich=True` ile köklü kavramı `ai.enrich` çok-boyutlu çapalar. `persist=False` →
canlı manifoldu kirletmez (kanıt/deneme).

**(3) Semboller:**
- `fetch_hf_rows(dataset, *, config, split, offset, length)`.
- `_best_text(row, text_fields)` · `stream_hf_text(...) -> Iterator[str]`.
- `feed(ai, dataset, *, ..., enrich, persist) -> dict` (`{dataset, fed, admitted_core, admitted_frontier, rejected, sample}`).
- `_ROWS_URL`, `_TEXT_FIELDS`.

---

## `ingest.py` — Gerçek veri ingestion (`DataIngestor`)
**(1) Amaç:** Sentetik değil GERÇEK bilimsel veritabanlarından (UniProt protein dizileri,
PubChem SMILES, OEIS tamsayı dizileri) akan veriyle manifoldu büyütür. Her kayıt
`AutonomousObserver`'dan geçer. Resumable (`.tantrium/ingest_state.json`).

**(2) Mantık:** HTTP `net`'e delege (`_http_json`/`_http_json_with_link`). Durum diske:
`uniprot_cursor` (Link-next sayfalama), `pubchem_cid` (CID ilerler), `ingested` (kaynak→
görülmüş key listesi, son 5000). `_observe_all` ortak boru: her item `observer.observe`,
domain düzeltmesi ("observed"→gerçek domain), certified/new/bridges sayımı, persist+state-save.
`fetch_uniprot` (reviewed/Swiss-Prot, dizi≥20 → biology), `fetch_pubchem`
(`encode_smiles` → moment, chemistry), `fetch_oeis` (≥6 değer → math). `run()` tek oturum,
`scale()` çoklu tur (resumable durum → her tur farklı kayıt, time_limit'te durur).

**(3) Semboller:**
- `DataIngestor(engine, *, bridge_threshold, persist_every, verbose)`.
- `_load_state/_save_state/_seen/_mark` (resumable durum).
- `_observe_all(items, source) -> IngestBatch`.
- `fetch_uniprot / fetch_pubchem / fetch_oeis`.
- `run(uniprot, pubchem, oeis_keywords) -> IngestReport` · `scale(rounds, ...)`.
- dataclass `IngestBatch`, `IngestReport`.

---

## `autonomous.py` — Otonom gözlemci + ilişki çıkarımı (`AutonomousObserver`)
**(1) Amaç:** Tav döngüsünü gerçekten kapatan çekirdek: insan/LLM döngüde olmadan
GÖZLEMLE → SERTİFİKALA → SINIFLANDIR → ÖĞREN → BAĞLA → KAYDET. Ayrıca tüm metin→ilişki
çıkarım mantığının (regex + opt-in spaCy + Türkçe) TEK-GERÇEK yeridir.

**(2) Mantık — iki büyük blok:**

*Metin → ilişki çıkarımı (modül-seviye fonksiyonlar):*
- `_CAUSAL_VERB_MAP`/`_COMPILED_VERBS` — İngilizce fiil regex'leri → paradigma (INHIBITS/
  CAUSES/ACTIVATES + kesin biyokimyasal yüklemler TARGETS/BINDS/REGULATES/PHOSPHORYLATES/
  ENCODES… "anlam kenarda yaşar", binds≠causes ayrımı korunur). `_PASSIVE_PAT`/`_PASSIVE_MAP`
  pasif sesi ("Y is activated by X" → X ACTIVATES Y) özne/nesne ters çevirir.
- spaCy gramer parser (opt-in, `_PARSER_ENABLED` varsayılan KAPALI; `enable_parser()` açar;
  growth hız için kapalı, converse/research kalite için açar). `_get_nlp` (lazy md→sm→False),
  `_relations_from_doc` (nsubj/nsubjpass + dobj/attr + agent → üçlü; kopula "is a" → IS_A;
  "part of"→COMPONENT_OF, "kind of"→IS_A hedef; `_doc_subjects` koordinasyon/kontrol özne taşır;
  `_LEMMA_REL` + AÇIK SÖZLÜK: bilinmeyen içerik fiili kendi TİP'ini doğurur, `_OPEN_VERB_STOP` eler).
- Türkçe SOV pass (`_TR_VERB_MAP`/`_TR_COMPILED`, apostrof-eki yutulur, `_strip_tr_suffix`
  YALNIZ epentetik-y belirtme ekini atar — kök bozulmaz).
- Temizlik: `_clean_term` (isim öbeğinin BAŞ-İSMİ, participle/-ly/postverb atlama),
  `_normalize_entity` (gürültü suffix: "ras pathway"→"ras"), `_is_nonclass_obj`
  (üretici/şirket/meta-isim IS_A nesnesi olamaz). `_ISA_PAT` tanım kalıbı.
- `_regex_relations` (tüm regex pass'leri) → `_extract_relations` (regex + opt-in spaCy + dedup)
  → tekil-metin; `extract_relations_batch` (regex belge-başı + spaCy `nlp.pipe` TOPLU = 3-8× hız,
  birebir aynı sonuç).

*Gözlem döngüsü (`AutonomousObserver`):*
`observe()` 7 adım: (1) encode; (2) TAM 23 paradigma sayımı (`_full_paradigm_count`, Aleph
ön-koşul + yapısal eşik passed≥total−3); (2b) EVREN KAPISI (`_universe_gate`: Truth ekseni
CONTRADICTORY→**rejected**; Grounding ekseni GROUNDED→**core** / geçerli-ama-yalıtık→**frontier**;
fail-open core); (3) en yakın çapa; (4) manifolda add_unchecked + tau node + spec cache + mini_tav;
(5) cross-domain köprü (`_discover_bridges`: farklı-domain/anchor komşu < bridge_threshold →
çift-yönlü SPECTRAL_BRIDGE kenarı); (6) metin ise `_inject_relations` (üçlüler → kavram+kenar,
max 20); (7) eşikte persist. `pulse()` = çekirdek nabzı (gözlem + SINIR ise O AN `_local_genesis`:
sınırı en yakın KÖKLÜ komşuyla konveks ara `⟨bridge:...⟩` kavramı doğurur). `run()` akış işler.

**(3) Semboller:**
- dataclass `Observation` (certified/is_new/admitted_as/grounding_verdict/truth_verdict/
  paradigms_passed/bridges/...; `.summary()`).
- `AutonomousObserver(engine, *, bridge_threshold, persist_every)`:
  `observe / pulse / run / _universe_gate / _full_paradigm_count / _discover_bridges /
  _inject_relations / _add_bridge_edge / _local_genesis / report / bridges_found`.
- modül fonksiyonları: `_extract_relations`, `extract_relations_batch`, `_regex_relations`,
  `_spacy_extract`, `_relations_from_doc`, `enable_parser`, `_clean_term`, `_normalize_entity`.

---

## `growth.py` — Sınırsız kendi-kendine büyüme (`GrowthEngine`)
**(1) Amaç:** Son mimari parça — insan tetiği OLMADAN sürekli çalışan akış:
ağ kaynağı (resumable) → evren kapısı → çekirdek nabzı → periyodik konsolidasyon → tekrar.
`ai.grow` bunu çağırır.

**(2) Mantık:**

*Kaynaklar (10, paralel, hata-toleranslı, resumable durum `.tantrium/growth_state.json`):*
`_fetch_pubchem` (CID ilerler, SMILES) · `_fetch_oeis` (anahtar-kelime rotasyonu, tamsayı dizisi) ·
`_fetch_uniprot` (gen/protein adı + FUNCTION metni→observe) · `_fetch_web` (`_refresh_gap_cache`
ile boşluk-güdümlü Wikipedia + RANDOM makaleler; paralel; kategori→IS_A kenarı; extract→observe) ·
`_fetch_kegg` (yolak gen isimleri) · `_fetch_chembl` (biyoaktif SMILES) · `_fetch_pubmed`
(`_pubmed_clean` başlık/gövde ayrımı, yazar/metadata eler, gövde→observe) · `_fetch_wikidata`
(SPARQL ilaç→tedavi→hastalık typed-triple) · `_fetch_conceptnet` (`_CN_REL_MAP` 600k+ kurallı
triple → doğrudan TAU) · `_fetch_kegg_kgml` (KGML XML relation type → INHIBITS/ACTIVATES doğrudan).
`_FOCUS_SOURCES` ile odaklı büyüme (oncology/math/language → kaynak alt-kümesi). `_next_batch`
10 kaynağı `ThreadPoolExecutor`'la paralel toplar (ağsızsa algoritmik diziler). `_ensure_in_manifold`/
`_inject_direct_edge` küratörlü kaynak için NLP'siz doğrudan kenar.

*Ana döngü (`stream`):* zaman/döngü/`should_stop` durma koşulları; her döngü gap-cache yeniler,
batch çeker, her item `observer.pulse(grow=)`'a verir (core/frontier/rejected sayımı), persist_every'de
persist+state-save; `consolidate_every`'de `_consolidate`.

*Konsolidasyon (`_consolidate` 6 alt-faz):*
- `NecessityEngine.run(math_kernel)` zorunlu kenar + `SelfModel.locate` öz-kök.
- `_meaning_consolidate` — semantik-köklü yeni kavramlar için `TopologyEncoder.encode` (anlam imzası)
  + `quantum_bridges` tarayıp gizli klasik-uzak/κ-yakın dolanıklığı KALICI `QUANTUM_BRIDGE` kenarına
  (`_add_quantum_bridge_edge`, idempotent). `_enrich_multidim` kimyasal-aday kavrama GERÇEK molekülünü
  (`ai.enrich` → HAS_COMPOUND) bağlar (F8 çok-boyutlu).
- `_verify_consolidate` — corrigibility: `corrigibility.detect_and_correct` (dejenere/çakışma
  tespit+düzelt), düzelmeyen `state["suspect"]` (son 500, kalıcı).
- `_dedup_family_windows` — kanonik üreteçlerin (lucas/tribonacci/ramanujan) AYNI momente inen
  `algo:<aile>_b<N>` pencere-kopyalarını tek temsilciye indirir, kenarları yönlendirir (artımlı, bounded).
- `_science_consolidate` — `causal_rules.derive_transitive_hypotheses` ile transitif hipotez (A→B→C
  ⟹ A-C), YENİ olanları RH-Sturm sertifikalar, `state["hypotheses"]`'e (son 500). `_SCI_GENERIC`
  jenerik terimleri eler.

**(3) Semboller:**
- `GrowthEngine(engine, observer=None)`: `stream / _next_batch / _consolidate` + 10 `_fetch_*` +
  `_refresh_gap_cache / _ensure_in_manifold / _inject_direct_edge / _meaning_consolidate /
  _enrich_multidim / _verify_consolidate / _dedup_family_windows / _science_consolidate /
  _add_quantum_bridge_edge / _load_state / _save_state`.
- dataclass `GrowthReport` (cycles/processed/core/frontier/rejected/born/meaning_enriched/
  bridges_found/hypotheses_generated/corrected/collisions_resolved/suspect_flagged/windows_deduped; `.summary()`).
- modül: `_http_json`, `_http_json_link`, `_pubmed_clean`, `_FOCUS_SOURCES`, `_OEIS_KEYWORDS`.

---

## `cognition.py` — L5 strateji-pluggable döngü (`Cognition`)
**(1) Amaç:** GrowthEngine + ProofLoop + Explorer + AutonomousResearcher'ı TEK Cognition
iskeleti altında birleştirir. İki mod: `batch` (sonlu fazlı, `ai.run` stili) / `stream`
(sürekli resumable, GrowthEngine'e delege). Her faz değiştirilebilir `CognitionStrategy`.

**(2) Mantık:** `CognitionState` paylaşılan durum tüm fazlar arası taşınır (sayaçlar,
`open_gap_names`, `frontier_concepts`, `compose_targets`, `cycle_history`, `should_stop`...).
`_DEFAULT_BATCH_PHASES` sıralı faz listesi; `Cognition.cycle` → `_batch` (her tur döngü-bazlı
sayaç sıfırlama, taşınanları koru, her stratejiyi `execute(engine, state)`) ya da `_stream`
(%75 GrowthEngine + %15 Compose/FlyWheel + Deduce + Narrate + Persist).

*Fazlar (sırasıyla):*
- **SchedulePhase** — meta-kontrol: önceki turun ölçümlerinden (benchmark/pharma_recall/gaps)
  ZAYIF eksen → `state.focus`; transport_corridor → üretim beam-bütçesi (`prod_budget` 4→8).
- **PerceivePhase** — manifold boyutu ölç; önceki tur boşluklarını GrowthEngine `_gap_cache`'e iletir.
- **ReflectPhase** — `GapFinder.find(all)` + `WonderScorer` önceliklendirme; `_weakly_grounded_frontier`
  kör-nokta kavramları (1-3 bağ); `SelfModel.reflect` zayıf eksenden öncelik-sıralaması.
- **OperatePhase** — Genesis (`ConceptSynthesizer.genesis`) + ALEPH:X re-encode + `SelfModel.reflect(persist)`
  + `AutonomousResearcher.run` + `Explorer.run_loop`.
- **VerifyPhase** — corrigibility: `detect_and_correct` (YAPISAL dejenere/çakışma, çözer);
  `external_verify` (DIŞSAL bilinen-olgu isabeti); oturum-bir-kez `encoder_health` + `computational_verify`
  (hesap-oracle); INHIBITS↔ACTIVATES çelişki tarama; `_autonomy`-kapılı oto-`relearn` + `empirical_verify` (RH-Sturm).
- **CuriosityPhase** — merak-güdümlü oto-araştırma: en değerli frontier kavram için `generate_questions` +
  `_research_deep` (internet), `_curiosity_done` rotasyon (`_autonomy`-kapılı).
- **DeductivePhase** — `engine.grow()` (= `ai.deduce`: certify_theorem_graph + InferenceChain tüm çiftler +
  Explorer + re-bootstrap) + `GraphReasoner.chain_all` tipli forward-chaining (öksüz güç bağlandı).
- **ScienceStep** — döngüde transitif hipotez (`derive_transitive_hypotheses`) + RH-Sturm; `_autonomy`'de
  en üst hipotezi `produce` ile test (HİPOTEZ→TASARIM→DOĞRULA).
- **RootingPhase** — zayıf-köklü kavramı SERTİFİKALI transitif bağ ile LANDMARK'a kablolar ("şehri sokak
  sokak öğren"); ağırlık değil graph-degree; yalnız Sturm-sertifikalı + obj landmark (≥3 sem. kenar).
- **MetaSynthesisPhase** — sistem kendi KURALINI icat eder (`meta_synthesize` GraphAdapter leave-one-out;
  converse/implication/analogy aileleri materyalize; özyineleme + teleoloji-tohumu; `_autonomy`-kapılı).
- **CodeGrowthPhase** — `ai.grow_code(rounds=1, research=False)` otonom kod-kapsamı (`_autonomy`-kapılı).
- **ComposePhase** — boşluk → `TopologyEncoder.encode` (anlam) → centroid `manifold.nearest` → `compose_targets`.
- **FlyWheelPhase** — `ProductionEngine.produce` (koridor-beam) → `scan_production_gaps` → kampanya votes →
  `launch_campaign`; üretilen SMILES'ı evren-kapısından geri-yut (`artifacts_reingested`); `_sync_transport_epsilon`
  ile koridoru ölç (`transport_corridor`).
- **DiscoverPhase** — birleşik κ-uzayında `quantum_bridges` tarayıp gizli çapraz-domain bağı KALICI
  QUANTUM_BRIDGE'e (`_add_bridge`, idempotent).
- **MeaningCachePhase** — köklü kavramların ÖLÇÜLEN imzasını (topoloji+cascade+flow) `meaning_cache.json`'a biriktir.
- **GoalPhase** — ASI Pilar B: insan hedefi yoksa `_auto_goal` (en değerli boşluktan, Aleph-sertifikalı);
  `Actor.pursue_goal`; `_goal_grounding_progress` (içerik kelimelerinin GERÇEK köklülük oranı, doyma+self-grooming
  bağışık); ulaşınca/durakladıkça auto-rotasyon ya da (insan hedefi) `should_stop`.
- **ProvePhase** — `open_gap_names` → `_gaps_to_campaigns` (ALEPH:X filtreli) → hedefli `launch_campaign`; boşluk
  yoksa kör `ProofLoop.run`.
- **NarratePhase** — döngünün öğrendiğini Türkçe'ye döker + stagnasyon tespiti (3 tur 0-kavram → should_stop).
- **PersistPhase** — `engine.auto_persist`.

`_gaps_to_campaigns` gap-adı → kampanya (`_GAP_PREFIX_TO_CAMPAIGN` + `_GAP_KEYWORD_TO_CAMPAIGN`, ALEPH:X eler,
frekans=öncelik).

**(3) Semboller:** dataclass `CognitionState`, `CognitionReport`; Protocol `CognitionStrategy`;
faz sınıfları (yukarıdaki 19); `Cognition(engine, strategies=None)`: `add_strategy / cycle / _batch / _stream`;
helper `_weakly_grounded_frontier`, `_goal_grounding_progress`, `_gaps_to_campaigns`; `_DEFAULT_BATCH_PHASES`.

---

## `proof_loop.py` — AGI ↔ Research OS kapalı döngü (`ProofLoop`)
**(1) Amaç:** NecessityEngine'in bulduğu manifold boşluklarını Research OS ispat
kampanyaları ile (subprocess) kapatır; yeni kanıtlanan teoremler manifolda enjekte edilir;
döngü tekrarlar.

**(2) Mantık:** Boşluk tespiti iki yoldan: `scan_gaps` (NecessityEngine geometry, domain
"theorem"→"math_kernel") + `scan_theorem_graph` (`theorem_graph.yaml` açık node'ları, `_OPEN_STATUSES`).
Kampanya seçimi: `_gap_to_campaigns` (boşluk açıklama→anahtar kelime→kampanya, fallback lah_gate_ab).
`launch_campaign` = `subprocess.run(tantrium_research_os.py --campaign X, timeout=120)`, STATUS satırını
parse eder; `inject=True` ise theorem_graph güncelle + sync + `inject_math_kernel`. `update_theorem_graph_from_campaigns`:
(1) sertifikalı kampanya → node status (`_CAMPAIGN_CERTIFIES`, `_PROOF_LOOP_CERTIFIABLE`); (2) bağımlılık-kapanışı
(tüm dep'leri sertifikalı node'lar `certified_local`, "dependency_closure" — DÜRÜSTÇE kanıt değil işaretlenir).
`sync_new_theorems` (`inject_math_kernel` + manuel tarama fallback) · `ingest_campaign_candidates`
(results/research_os/candidates/*.json → manifold). `run_cycle` = scan→campaigns→update→sync→ingest→persist;
`run(max_cycles, time_limit_s)` çoklu döngü, ilerleme yoksa erken durur.

**(3) Semboller:** dataclass `LoopCycle`, `LoopReport`; `ProofLoop(engine, theorem_graph_path=None)`:
`scan_gaps / scan_theorem_graph / launch_campaign / update_theorem_graph_from_campaigns / sync_new_theorems /
ingest_campaign_candidates / run_cycle / run`; eşleme tabloları `_GAP_TO_CAMPAIGN / _KEYWORD_TO_CAMPAIGN /
_CAMPAIGN_CERTIFIES / _OPEN_NODE_TO_CAMPAIGN / _OPEN_STATUSES / _PROOF_LOOP_CERTIFIABLE / _INJECTED_STATUSES`.

---

## `explorer.py` — Bilgi-sınırı keşif döngüsü (`Explorer`)
**(1) Amaç:** Bilgi sınırını (gerçekten BLOKLANMIŞ paradigmalar) bilgi-deposundan okur,
o paradigmayı sınayan minimal probe nesnesi üretir, motora geçirir, sonucu CLOSED/REFINED/
PERSISTENT sınıflar, hepsini depoya (append-only) yazar. Tahmin etmez — matematiği izler.

**(2) Mantık:** `scan_frontier` knowledge.jsonl'i okur, `knowledge_frontier` (bloklu paradigma)
frekans+`_PARADIGM_PRIORITY` ile sıralı `ExplorationObjective`'ler üretir (oturumda çözülenler atlanır).
`_make_probe` her paradigmaya minimal CodexObject (moments=(1/2)^k + paradigma-özel `extras` yapı).
`explore` probe'u `engine.process`'e geçirir: paradigma node CERTIFIED → **CLOSED**; yeni farklı
frontier → **REFINED**; aynı kalır → **PERSISTENT**. `run_loop` her tur scan→explore (max_attempts);
PERSISTENT'ta son denemede `_try_research_os` (subprocess kampanya, `_GAP_TO_CAMPAIGN`); fixed-point
ya da tüm-kapalı'da durur. `_record_result` jsonl'e append.

**(3) Semboller:** dataclass `ExplorationObjective`, `ExplorationResult`; `Explorer(engine, max_attempts_per_gap)`:
`scan_frontier / explore / run_loop / _try_research_os / _record_result / report`; modül `_make_probe`,
`_GAP_TO_CAMPAIGN`, `_PARADIGM_PRIORITY`.

---

## `researcher.py` — Otonom araştırmacı (`AutonomousResearcher`)
**(1) Amaç:** AGI kendi boşluklarını (`MetaParadigm.blind_spots`) tespit eder, araştırma
hedefleri (`GoalManifold`) kurar, matematiksel veri (algoritmik diziler + OEIS/LMFDB/PubChem)
çeker, `AutonomousObserver` ile öğrenir. Kapalı döngü: öz-değerlendirme→hedef→veri→öğren→ölç→kaydet.

**(2) Mantık:** `assess_gaps` → blind_spots (anchor+count+keywords). `_generate_sequences` her
matematiksel çapa (PRIME_GAPS/ZETA_ZEROS/GUE/GEOMETRIC_GROWTH/GAUSSIAN/MODULAR_FORMS/ELLIPTIC/
EXPONENTIAL/POISSON/PERIODIC/LINEAR/UNIFORM) için ağ-bağımsız algoritmik dizi üretir (`batch` ile
çeşitlilik). Ağ kaynakları: `fetch_oeis` (net'e delege), `fetch_lmfdb_zeros`, `fetch_pubchem` +
`fetch_pubchem_batch` (`_PUBCHEM_QUERIES` ilaç/metabolit listesi). `_fetch_for_gap` algoritmik →
(network) OEIS/LMFDB/PubChem → fallback (`_FALLBACK` sabit yedek). `research_cycle`: gaps → hedef
(`encode_goal`, idempotent) → her boşluk için veri → `AutonomousObserver.observe` → new_concepts/
bridges → hedef ilerlemesi (`goal.update_progress`) → periyodik persist. `run` çoklu döngü.

**(3) Semboller:** dataclass `ResearchCycle`, `ResearchReport`; `AutonomousResearcher(engine, *,
max_sequences_per_gap, bridge_threshold, oeis_timeout_s)`: `assess_gaps / fetch_oeis / fetch_lmfdb_zeros /
fetch_pubchem / fetch_pubchem_batch / _fetch_for_gap / research_cycle / run`; modül `_generate_sequences`,
`_FALLBACK`.

---

## `goal.py` — Hedef temsili (`Goal`, `GoalManifold`)
**(1) Amaç:** Her hedef manifoldda Aleph-sertifikalı bir kavram (canonical byte encoding).
`GoalManifold.pursue()` hedefe en yakın TAU yolu = sonraki eylem adayları (Actor için).

**(2) Mantık:** `Goal` (name/moments/priority/progress/action_trace); `to_concept` →
`goal:<name>` Concept; `update_progress` bilinen kavramların hedefe `moment_distance`'ından
proximity (scale=35). `GoalManifold` CRUD + `pursue`: ANLAM-PUSULASI (`meaning_pipeline.goal_distance_function`
hedef köklü kavrama indirgenebiliyorsa anlam-mesafesi, değilse momente düşer fail-open); `_seed_candidates`
(çapa köklüyse çapanın GRAF komşuları via `resolve_goal_anchors`/`nearest_meaning`, değilse harf-nearest);
seed + semantic TAU komşuları (typed-edge bonus ×0.5) → sıralı adaylar. `save`/`load` (`results/agi/goals/goals.json`).
`encode_goal` description→encode→ALEPH certify→`Goal` ya da None.

**(3) Semboller:** dataclass `Goal` (`to_concept / distance_to / update_progress`); dataclass
`GoalManifold` (`add / get / active_goals / pursue / _seed_candidates / save / load / summary`);
fonksiyon `encode_goal(engine, description)`; `_SEMANTIC_PARADIGMS` (knowledge_graph'tan).

---

## `actor.py` — Eylem döngüsü (`Actor`, sandbox)
**(1) Amaç:** Hedef → certified TAU walk → eylem planı → güvenli execute → certify →
manifold güncelle. YALNIZ manifold-güvenli eylemler (learn/relate/save/think/progress);
dosya/shell/eval/subprocess/ağ YASAK.

**(2) Mantık:** `plan` hedef adaylarından sıralı `Action` listesi (learn×3 + hedef-learn +
relate + think + progress + save). `execute` güvenlik filtresi (`_UNSAFE` payload pattern'leri →
RED) sonra tür-dispatch: `_learn` (`LanguageBootstrap(domain="goal_learning").auto_learn`),
`_relate` (`add_relations_from_text`), `_save` (`auto_persist`), `_think` (`engine.think` +
session'a thought-concepts), `_progress` (`goal.update_progress` son turlardan). `pursue_goal`
tam döngü: `goal_manifold.pursue` → `plan` → her `execute` → `note_new_concepts` → `goal_manifold.save`.

**(3) Semboller:** dataclass `Action`, `ActionResult`; `Actor(engine)`: `plan / execute / _is_safe /
_learn / _relate / _save / _think / _progress / pursue_goal`; `_UNSAFE`; tip `ActionType`.

---

## `corrigibility.py` — Temsil-hatası tespit + düzeltme + doğrulama (PAYLAŞILAN çekirdek)
**(1) Amaç:** GIMEL'in göremediği ÜNİFORM hatayı (protein/glucose μ_k≡1) kapatan kör-nokta
çekirdeği. growth `_verify_consolidate` ve cognition `VerifyPhase` AYNI fonksiyonları çağırır
(tek tanım). Ayrıca dış/hesap/ampirik doğrulama oracle'larının TEK-GERÇEK yeri (`ai.benchmark`
buna delege).

**(2) Mantık:**
- `detect_and_correct` — (1) DEJENERE encoding (moment yayılımı < `_DEGEN_SPREAD` 0.02) →
  `encode_adaptive` ile DÜZELT, düzelmezse suspect; (2) ÇAKIŞMA (en yakın FARKLI kavram L1 <
  `_COLLISION_EPS` 0.001) → derin re-encode ile ayrıştırmayı dene (ÇÖZ — Kaf injektiflik
  aksiyomu), olmazsa suspect. Bounded (`_VERIFY_MAX`/`_VERIFY_COLLISION_MAX`), `:`-önekli (oeis/algo/theorem) atla.
- `external_verify` — küratörlü `_DEFAULT_FACTS` (erlotinib INHIBITS egfr…) kausal TAU'da var mı →
  ampirik isabet skoru + failures (DIŞSAL doğruluk).
- `computational_verify` — HESAP-ORACLE: (1) `_STURM_CASES` her polinom için Sturm pivot pozitifliği
  (`normalized_sturm_pivots`) ⟺ numpy companion-matris köklerinin hepsi-reel (bağımsız gerçek); (2)
  Hankel moment-dizisi PSD (gerçek atomik ölçü → DAİMA PSD, geçersiz dizi → red, `is_moment_sequence`).
- `empirical_verify` — AMPİRİK ORACLE: leave-one-out farmakoloji geri-kazanım; her ligand kendi
  hedefinin DİĞER ligand profiline + rakip hedeflere `metric="kappa"` (κ-yakınlık) ya da `"sturm"`
  (RH evren-kapanışı pivot) ile sıralanır; gerçek hedef tepe-1/akraba-isabet (lab YOK).
- `encoder_health` — `CollisionHunter` adversarial öz-test: 8-moment çakışma oranı + derinlik/label/içkin ayrımı.

**(3) Semboller:** `detect_and_correct(engine, seen, *, max_per_pass, collision_max, correct)`;
`external_verify(engine, facts=None)`; `computational_verify(engine=None, *, tol)`;
`empirical_verify(engine, *, targets, metric)`; `encoder_health(engine, *, n_samples)`; eşikler
`_DEGEN_SPREAD/_COLLISION_EPS/_VERIFY_MAX/_VERIFY_COLLISION_MAX`; veriler `_DEFAULT_FACTS/_CAUSAL/
_STURM_CASES/_PANEL_TARGETS`.

---

wrote docs/_understanding/08_research.md
