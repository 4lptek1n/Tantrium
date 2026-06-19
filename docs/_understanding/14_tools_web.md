# 14 — `tools/*.py` + `web/` — CLI Koşucuları, Demolar, Web API

Bu defter `tools/` altındaki 23 script ile `web/api.py` + `web/run.py` dosyalarını DOSYA-DOSYA
betimler. Her madde: (1) tek-satır amaç, (2) çalıştırıldığında NE yapar (koşucu/demo/CLI akışı —
neyi yutar/eğitir/gösterir), (3) anahtar giriş noktaları. Saf betimleyici; yargı/eksik/hata yok.

Genel desen: çoğu koşucu `import tantrium; ai = tantrium.AI()` ile başlar, `ai._engine` (veya
`ai.engine`) üzerinden manifold/tau'ya erişir, periyodik olarak `eng.auto_persist()` ile diske
yazar. "SONSUZ" koşucular `.tantrium/STOP_*` dosyasını izleyerek düzgün durur ve
`.tantrium/<ad>_status.json` ile canlı ilerleme yazar. Demolar tek seferlik çalışıp konsola
formatlı çıktı basar.

---

## Sürekli/Sonsuz Büyüme Koşucuları (`.tantrium/STOP_*` ile durur, resumable)

### `tools/absorb_forever.py`
1. **Amaç:** Internetten sürekli oku → fitsiz `ai.absorb` ile manifolda kalıcı emdir (eğitimsiz).
2. **Ne yapar:** `STATE.mkdir` sonrası sonsuz döngü; her turda `fetch_random_titles(BATCH=6)` ile
   rastgele Wikipedia başlıkları çeker, her başlık için `fetch_wikipedia(title)` ham metin alıp
   `ai.absorb(text, persist=False)` borusundan geçirir (SVD keşif → evren-kapısı → kNN kenar →
   graf-ölçülen anlam re-encode). Throttle `THROTTLE_S=1.2s` (Wikipedia 429 koruması). Batch
   sonunda `eng.auto_persist()` + `absorb_status.json` yazar (articles, fetch_failed,
   concepts_total, cum_admitted, cum_edges, uptime, last_titles). `STOP_ABSORB` ile durur.
   Halüsinasyon gardiyanı girişte değil ÇIKIŞTA (kritik-hat). TEK-YAZAR uyarısı.
3. **Giriş:** `main()`; `nohup python -u tools/absorb_forever.py`; durdurma `touch .tantrium/STOP_ABSORB`.

### `tools/autonomous_forever.py`
1. **Amaç:** İnsan eli olmadan sonsuz dönen 9-halka native cognition koşucusu (zeka gelişimi).
2. **Ne yapar:** Sonsuz tur döngüsü. FAZ 1 (her tur): `ai.grow(focus=None, time_limit_s=grow_budget,
   network=True)` ile 8/10 kaynaktan geniş veri akışı; eklenen kavram sayısını ölçer. FAZ 2 (her
   `COGNITION_EVERY=5` turda): `ai.cognition(mode="batch", network=False)` ile ağsız akıl/self/
   hipotez/dedup. Toplamları biriktirir (concepts/edges/hypotheses/curiosity/relearn/bridges/
   reingest/proofs/contradictions). Her tur `e.auto_persist()` + `autonomy_status.json`; yeni
   sertifikalı hipotezleri `autonomy_hypotheses.jsonl`'e ekler. `_git`/`_commit_growth` git
   commit/push yardımcıları (`COMMIT_EVERY=0` → kapalı). `STOP_AUTONOMY` ile durur.
3. **Giriş:** `main()`, `_git`, `_commit_growth`; `nohup python -u tools/autonomous_forever.py`.

### `tools/grow_multidim.py`
1. **Amaç:** Çok-boyutlu fitsiz büyüme — dil + molekül + sayı + protein hepsi aynı moment uzayı,
   F24 yasasıyla her boyut kendi GERÇEK ölçümünden girer.
2. **Ne yapar:** `AutonomousObserver` + `GrowthEngine` kurar (state `multidim_state.json`'dan
   resume). Başta `ai.set_goal(...)` ile 3 ASI hedefi (GoalPhase NO-OP olmasın). Sonsuz döngüde her
   tur: (1) `ge._fetch_pubchem(10)` SMILES → `obs.observe` (tam evren-kapısı), (2) `ge._fetch_oeis(4)`
   sayı dizisi → observe + `ai.discover_law` ile yönetici yasayı keşfedip `ai.ground_full(law=...)`
   (IS_GOVERNED_BY), (3) `ge._fetch_uniprot(6)` protein → observe, (4) `fetch_random_titles(4)` +
   `fetch_wikipedia` → `ai.absorb` (hızlı dil). Her `COGNITION_EVERY=4` turda `ai.cognition
   (network=True)` ASI bilişi (köprü/hipotez/öz-düzeltme/ispat). Her tur persist + `multidim_status
   .json` (dims sayaçları + asi sayaçları). `STOP_MULTIDIM` ile durur.
3. **Giriş:** `main()`, iç `_obs(x)`; `python tools/grow_multidim.py`.

### `tools/batch_corpus.py`
1. **Amaç:** Çok belgeyi TOPLU, FİTSİZ, HIZLI ör (Fix #3 ölçek) — corpus batch işleme darboğazını kapat.
2. **Ne yapar:** Sonsuz döngü; her turda `fetch_random_articles(20)` tek HTTP çağrısıyla ~20
   makalenin düz metnini çeker, `ai.absorb_corpus(texts, persist=...)` ile tüm cümleleri TEK
   nlp.pipe akışında işler (tipli kenarlar, evren-kapısı korunur). Sayaç biriktirir (docs,
   sentences, relations, edges_added, concepts_admitted) + `batch_status.json` (docs_per_s dahil).
   `STOP_BATCH` ile durur, son `auto_persist`.
3. **Giriş:** `main()`; `nohup python -u tools/batch_corpus.py`.

---

## HuggingFace STREAM Eğitim Koşucuları (gradyansız, fitsiz; `.tantrium/STOP_*`)

### `tools/train_hf_corpus.py`
1. **Amaç:** fineweb-edu STREAM → vektörize global ortak-geçiş → torch truncated-SVD = fitsiz
   "eğitilmiş" gömme (GloVe deseni, kapalı-form).
2. **Ne yapar:** `FastCooccurrence` (checkpoint `fast_cooc.npz`'den resume) kurar, `load_dataset
   ("HuggingFaceFW/fineweb-edu","sample-10BT", streaming=True)` akıtır. Cümleleri (`SENT` regex,
   ≥4 kelime) tampona toplar, `CHUNK=4000`'de `g.update(buf)`. Her `STATUS_EVERY=4000` belgede
   ilerleme satırı + `train_status.json`. Her `REFRESH_EVERY=25000` belgede `_refresh` (=
   `g.embed(dim=128, min_count=10)` → `embeddings.npy` + `embed_vocab.json` kaydet + PROBES
   kelimeleri için en-yakın komşu bas) + `_save_ckpt`. `STOP_TRAIN` ile durur. `embed_nearest/relate`
   bu gömmeyi canlı okur.
3. **Giriş:** `main()`, `_save_ckpt`, `_load_ckpt`, `_refresh`.

### `tools/train_lm.py`
1. **Amaç:** fineweb-edu STREAM → `FitlessLM` (yönlü ortak-geçiş→SVD log-bilineer) eğit, fitsiz
   serbest yüzey ÜRETİM modeli (akıcılık) — gradyansız.
2. **Ne yapar:** `FitlessLM(max_vocab=30000, window=5)` kurar, fineweb-edu akıtır, cümleleri (≥4
   kelime) tamponlayıp 4000'de `lm.update`. Her 5M token'da log satırı. Her `CHECKPOINT_EVERY=30M`
   token'da `_checkpoint` (= `lm.fit(dim=160, min_count=8)` → `.tantrium/fitless_lm` save + PROBES
   prompt'larıyla örnek üretim bas). `TARGET_TOKENS` (env `LM_TOKENS`, varsayılan 150M) dolunca
   biter. `STOP_LM` ile durur. `ai.generate_text` bunu okur.
3. **Giriş:** `main()`, `_checkpoint`.

### `tools/train_ngram.py`
1. **Amaç:** fineweb-edu STREAM → `NGramLM` (stupid-backoff) eğit — yerel akıcılık (sadece sayım).
2. **Ne yapar:** `NGramLM(order=4)` (env override), fineweb-edu akıtır, 4-40 kelimelik cümleleri
   tamponlayıp `lm.update`. Her `PRUNE_EVERY=20M` token'da `lm.prune(min_count=2)` + `lm.save
   (.tantrium/fitless_lm)` + PROBES üretim örnekleri. `TARGET` (env `NGRAM_TOKENS`=60M) dolunca
   biter; sonda prune+save+örnekler. `STOP_NGRAM` ile durur. `ai.generate_text(engine='ngram')` okur.
3. **Giriş:** `main()`.

---

## Manifold Tek-Atış Büyütme / Araştırma CLI'leri

### `tools/grow_manifold.py`
1. **Amaç:** Dev edebî/bilimsel corpus dosyalarını co-occurrence Gram ile öğretip ALEPH-sertifikalı
   manifolda ekle, TAU'yu yeniden inşa et.
2. **Ne yapar:** `CertificationEngine` yükler, sabit `CORPORA` listesindeki `/tmp/*.txt` dosyalarını
   (Shakespeare, Tolstoy, Darwin, ... domain etiketli) `LanguageBootstrap(window=5, min_freq=3)`
   ile `from_file` çağrısıyla öğretir (her kavram Hankel PSD → ALEPH). Sonra `save_manifold`,
   `KnowledgeGraph.build(k=10)` ile TAU'yu yeniden kurup kaydeder, `engine.grow(max_rounds=3)` ile
   inference zincirlerini genişletir, final raporu (kavram/edge/süre/depolama) basar.
3. **Giriş:** `main()`, `fmt`.

### `tools/ingest_real_world.py`
1. **Amaç:** Gerçek bilimsel veritabanlarından (UniProt/PubChem/OEIS) manifold büyüt, resumable.
2. **Ne yapar:** argparse (`--rounds`, `--uniprot`, `--pubchem`, `--time-limit`, `--oeis`).
   `CertificationEngine` + `DataIngestor(persist_every=100)`. `rounds` kez `ing.run(uniprot=,
   pubchem=, oeis_keywords=)` çağırır (zaman limiti aşılırsa kırılır); her kayıt Aleph'ten geçer,
   cross-domain köprü keşfedilir. Sonda domain dağılımını (`Counter` ile uniprot:/pubchem:/oeis:/
   theorem: önekleri) ve kavram/edge/köprü artışını basar.
3. **Giriş:** `main()`.

### `tools/autonomous_research_session.py`
1. **Amaç:** AGI kendi gündemini belirleyen tek-oturum otonom araştırma (insan döngüde değil).
2. **Ne yapar:** `CertificationEngine` yükler + başlangıç istatistiği (kavram/teorem/OEIS/çapa/edge).
   `AutonomousResearcher(max_sequences_per_gap=8, bridge_threshold=3e-2)`. `researcher.assess_gaps
   (threshold=5)` ile boşlukları (MetaParadigm.blind_spots) öncelik sırasıyla listeler.
   `researcher.run(max_cycles=2, time_limit_s=180, network=True)` → OEIS'ten gerçek diziler indirir,
   AutonomousObserver ile öğrenir, cross-domain SPECTRAL_BRIDGE köprüleri kurar. Döngü raporlarını,
   gerçek OEIS↔teorem/çapa köprülerini (W₂ sıralı), kümülatif köprüleri ve manifold artışını basar;
   sonda `engine.auto_persist()`.
3. **Giriş:** `main()`.

### `tools/proof_loop_demo.py`
1. **Amaç:** AGI ↔ Research OS kapalı döngü demosu (boşluk → ispat kampanyası → yeni teorem).
2. **Ne yapar:** argparse (`--cycles=2`, `--time-limit=180`, `--scan-only`). `CertificationEngine` +
   `ProofLoop`. `loop.scan_gaps(domain="theorem")` ile boşlukları tarayıp ilk 5'ini (domain/
   description/komşular) basar. `--scan-only` değilse `loop.run(max_cycles, time_limit_s)` çalıştırır;
   her tur için boşluk/kampanya-durumu/kavram-delta/edge-delta raporlar, sonda toplam yeni kavram/
   edge ve kalan boşlukları basar.
3. **Giriş:** `main()`, `fmt_delta`.

### `tools/tantrium_research_os.py`
1. **Amaç:** Research OS ispat kampanyalarını çalıştıran CLI (ProofLoop subprocess hedefi).
2. **Ne yapar:** `sys.path`'i kök-tantrium görünür olacak şekilde düzenler (`src/tantrium`
   paketinin `__path__`'ine kök `tantrium/` dizinini ekler → `research_os/` görünür). argparse
   `--campaign` (subresultant_recurrence | lah | lah_gate_ab | coefficient_frontier |
   goldbach_minor_arc | rh_formalization | all), `--deep`, `--iterations`. `run_campaigns(campaign,
   deep)`'i iterasyon kez çağırır, her kampanya özetinin public_name/status/refined_subgap'ini ve
   `RESULT: RESEARCH_OS_COMPLETED` satırını basar.
3. **Giriş:** `main()`; `python tools/tantrium_research_os.py --campaign <name>`.

---

## Manifold Bakım / Migrasyon Araçları (`--dry-run` / `--apply`)

### `tools/dedup_manifold.py`
1. **Amaç:** Büyüme-üreteci pencere-kopyalarını (`algo:<aile>_b<N>` tıpatıp aynı momente çökenler)
   tekilleştir.
2. **Ne yapar:** Her `:` önekli `_b\d+` adını aileye (`_FAMILY_RE`) ayırır; (aile, tam-moment)
   grubunda b-index'i en küçük olanı temsilci tutar, kalanları silmek için `remap` kurar. `--apply`
   ile: silinenlere işaret eden kenarları temsilciye yönlendirir, ölü düğümlerin kenarlarını
   temsilciye taşır (`KnowledgeEdgeRetarget`), düğümleri/nodes'u siler, kenarları tekilleştirir
   (self-loop + (target,paradigm) tekrar eler), `tau._dirty=True` + `auto_persist`. Öneksiz gerçek
   kelime/teoreme dokunmaz. Rapor (families_collapsed, copies_to_delete, before/after) basar.
3. **Giriş:** `dedup(apply)`, `_family`, `KnowledgeEdgeRetarget`; `python tools/dedup_manifold.py
   --apply`.

### `tools/migrate_text_encoding.py`
1. **Amaç:** Eski bigram-rejimli metin kavramlarını yeni imza-encoding'e taşı (F1/F5 collision kök çözümü).
2. **Ne yapar:** `results/agi/manifold.json` (v3) okur; her etiket için `_old_text_moments(name)`
   ile eski bigram encode'unu numpy float'ta yeniden hesaplar, stored momentlerle L1 < `_EPS=1e-3`
   ise = METİN kavramı → `_text_to_signature_moments(name, 8)` ile yeni momenti yazar; eşleşmezse
   (molekül/sayısal/algo) DOKUNMAZ. `--dry-run` raporlar (migrated/kept/skipped/failed), gerçek
   modda manifold.json'ı yazar + stale `spectral_cache.json`'ı siler (tembel yeniden kurulur).
3. **Giriş:** `main(dry_run)`, `_old_text_moments`.

### `tools/bind_theorem_math.py`
1. **Amaç:** 90 teoremin placeholder `[1,½,¼,...]` momentini gerçek tce-collapse matematiğiyle değiştir.
2. **Ne yapar:** Ön koşul: tce içeriği `/tmp/tce`'ye çıkarılmış. `theorem_graph.yaml` node'larını
   yükler. Placeholder'a (dyadic dizi) çöken `domain="theorem_graph"` kavramları hedefler; her biri
   için `_source_files` (artifacts/certificate_path + ell_q .md/.json + named .md) bulur,
   `_math_sequence` (ell/q sayıları + dosyalardaki tüm sayılar + ad-imzası tie-breaker) çıkarır,
   `UniversalEncoder(8).encode` ile o teoreme özgü moment hesaplar (placeholder'dan ayrışmazsa
   atlar). `--apply` ile concepts[name].moments'i Fraction olarak yazar + `auto_persist`. Çakışma
   kontrolü (distinct_signatures, collisions_remaining) ve rapor basar.
3. **Giriş:** `bind(apply)`, `_load_graph`, `_source_files`, `_extract_numbers`, `_math_sequence`.

---

## Hızlı Tek-Atış Yardımcı Koşucu

### `tools/absorb_grow.py`
1. **Amaç:** Verilen Wikipedia konularını fitsiz `ai.absorb` ile çekip öğren (büyümenin "edinme" yarısı).
2. **Ne yapar:** argv ayrıştırır (`--dry` = persist yok, kalan argümanlar konu listesi). `tantrium.AI()`
   sonra `absorb_topics(ai, topics, persist=not dry, neighbors_per=4, min_sim=0.45)` çağırır (keşfet
   → evren-kapısı → kNN COOCCURS kenarı). Konu başına raporu + toplam (admitted/rejected/edges)
   basar. TEK-YAZAR uyarısı (persist=True yalnız canlı runner durunca).
3. **Giriş:** `main(argv)`; `python tools/absorb_grow.py [--dry] <konu> ...`.

---

## Tanıtım / Demo Scriptleri (tek seferlik, konsol çıktısı)

### `tools/unified_demo.py`
1. **Amaç:** `ai(herhangi_şey)` tek giriş noktasının her girdi türünü anladığını göster.
2. **Ne yapar:** `tantrium.AI()` kurup sırayla `ai(...)` çağrılarını bloklar halinde basar: metin
   kavram (EGFR/ATP), metin soru (protein folding nedir?), SMILES (benzene/ethanol), iki-girdi
   transport (ATP/ADP, benzene/CCO), sinyal (`tone`/`chord`/`white_noise`), görüntü
   (`concentric_image`/`noise_image`), bytes (güçlü rastgele + elle kurulan ECB şifreli tekrarlı
   metin → kripto okuması). Hepsi kanıtlanmış Türkçe üretir.
3. **Giriş:** `main()`, `hr`, `block`.

### `tools/perception_demo.py`
1. **Amaç:** Algı katmanı — ham ses/görüntünün aynı moment uzayına çekildiğini ve dile döküldüğünü göster.
2. **Ne yapar:** 5 bölüm: [1] SES (`tone`/`chord`/`white_noise`) → `ai.perceive(modality="signal")`,
   μ₁ entropi çubuğu (ton düşük, gürültü yüksek); [2] GÖRÜNTÜ (solid/stripes/concentric/noise) →
   `perceive(modality="image")`; [3] GROUNDING — birkaç percept'i `learn=True` ile manifolda
   kalıcılaştırıp kavram artışını + TAU çağrışımlarını basar; [4] CROSS-MODAL — ses/görüntü gürültü
   ve ton/halka arası L1 mesafeleri; [5] ALGI→DİL — `ai.witness(...)` ile her percept'i Türkçe
   ifadeye çevirir (görmek=hatırlamak=anlatmak).
3. **Giriş:** `main()`, `bar`.

### `tools/crypto_structure_demo.py`
1. **Amaç:** Şifreli veriyi moment uzayında yapısal oku — zayıf şifrelemenin sızdırdığı yapıyı yakala (denetim).
2. **Ne yapar:** Tekrarlı düz metinden (`b"ATTACK AT DAWN. "*64`) 4 örnek üretir: düz, zayıf
   kısa-anahtar XOR, zayıf ECB (`ecb_encrypt` blok deterministik), güçlü CTR (`ctr_keystream` PRNG).
   Her örneğe `analyze(data, block_size=16)` uygulayıp `summary()` basar; sonra düz-metin hariç her
   örneğe `achilles(data)` (GIMEL Aşil topuğu = en zayıf/sızan eksen) basar. Anahtar kurtarmaz —
   zayıf şifre ZAYIN ekseninden yapı sızdırır, güçlü şifre gürültüden ayırt edilemez.
3. **Giriş:** `main()`, `xor_bytes`, `ctr_keystream`, `ecb_encrypt`.

### `tools/inverse_design_demo.py`
1. **Amaç:** Ters transport demosu — hedef (protein/hastalık/SMILES) → W2-minimal moleküller → 3D SDF.
2. **Ne yapar:** argv'den hedef + top_k alır, `tantrium.AI()` kurar, manifold durumunu basar,
   `ai.design(target, top_k, n_fragment_rounds=2)` çağırır (hedef kodla → manifold araması +
   fragment mutasyonu), DesignResult'ı + toplam süreyi basar; en iyi adayın SDF yolu varsa
   RDKit görüntüleme komutunu yazar.
3. **Giriş:** `main()`; `python tools/inverse_design_demo.py EGFR`.

### `tools/molecular_space_demo.py`
1. **Amaç:** Moleküler uzay demosu — saf spektral W2, metin araması yok.
2. **Ne yapar:** İlk argümanla komut seçer: `arrange` (`ai.arrange(target, n=12, cls_filter)`),
   `morph` (`ai.morph(smi_a, smi_b, steps=6)`), `lineage` (`ai.lineage_mol(smiles, depth=3)` → katman
   katman MolPoint ağacı W2/sınıf/SMILES ile), `kinase` (kinaz sınıfı filtreli arrange). Her komut
   ilgili `summary()` veya formatlı ağaç basar.
3. **Giriş:** `__main__` komut dağıtıcısı; `demo_arrange`, `demo_morph`, `demo_lineage`.

---

## LLM Geometri Probları (transformers/torch, tek-atış analiz)

### `tools/probe_llm_geometry.py`
1. **Amaç:** Açık LLM'in aktivasyon yörüngesinde gizli (sonlu-rank, üreten) yasa olup olmadığını oku.
2. **Ne yapar:** `_MODELS` listesinden yüklenebilen ilk modeli (Qwen2.5-0.5B / SmolLM2-135M /
   mamba-130m) `transformers` ile yükler, sabit `_PROMPT`'u tokenize edip `hidden_states` alır. 0.25/
   0.5/0.75 katman fraksiyonlarında: katman matrisini `_top_pc` ile baskın PC'ye projekte eder
   (konum-boyunca skaler dizi), `structural_decomposition` ile rank/structured/sv_gap raporlar;
   kontrol olarak diziyi karıştırıp rank yükselişini ölçer ("YAPI VAR" vs "yapı zayıf" yargısı).
3. **Giriş:** `main()`, `_load`, `_top_pc`, `_report`.

### `tools/probe_multimodel_spectrum.py`
1. **Amaç:** Dil temsil-geometrisinin power-law spektrum imzasının modeller arası evrensel mi olduğunu sına.
2. **Ne yapar:** `_MODELS` (gpt2, pythia-160m, mamba-130m, Qwen2.5-0.5B) için sabit `_PASSAGE`'ı
   tokenize edip `hidden_states` alır. Erken (0.25) ve son (1.0) katmanda `_spectrum` (SVD normalize
   eigenvalue) hesaplayıp `SpectralMeasure` ile etkin-rank/entropi + `_powerlaw` (log-log lstsq) ile
   α ve R² basar. Sonda rastgele Gauss matrisi kontrol satırı (`RASTGELE`) basar — imza tüm
   modellerde aynıysa evrensel yasa.
3. **Giriş:** `main()`, `_spectrum`, `_powerlaw`, `_row`.

---

## Web (`web/`)

### `web/api.py`
1. **Amaç:** Tantrium ASI için FastAPI HTTP/REST + statik UI sunucusu.
2. **Ne yapar:** Modül yüklenince `sys.path`'e `src` ekler, cwd'yi repo köküne çevirir (engine
   relatif yol kullanır). `get_ai()` lazy singleton `tantrium.AI()`. CORS açık, `/static` mount.
   Endpoint'ler: `GET /` (static/index.html servisi); `GET /api/status` (kavram/edge/paradigma);
   `POST /api/discover` (`ai.discover` → aday molekül listesi + 3D/SDF bayrakları); `GET
   /api/download/{filename}` (yalnız .sdf, path-traversal koruması, results/molecules|agi'den
   FileResponse); `POST /api/certify` (encode → `network.run` → paradigma sonuçları + spektrum +
   çapa + en-yakın kavram → İngilizce verdict/finding); `POST /api/transport` (`ai.transport` →
   certified/dyadic/sturm/zeta + verdict); `POST /api/compare` (`ai.compare`); `POST /api/anchor`
   (`ai.anchor_of`); `GET /api/topology` (`ai.topology(grid_n=10)` → dense/frontier/void sayımı).
   Pydantic istek modelleri: CertifyRequest, TransportRequest, CompareRequest, DiscoverRequest.
3. **Giriş:** `app` (FastAPI), `get_ai()`, endpoint coroutine'leri.

### `web/run.py`
1. **Amaç:** Web API başlatıcısı (uvicorn launcher).
2. **Ne yapar:** `sys.path`'e `src` ekler; argv'den port (varsayılan 8000) alır, banner basıp
   `uvicorn.run("api:app", host="0.0.0.0", port=port, app_dir=<web dizini>)` ile sunucuyu başlatır.
3. **Giriş:** `__main__` bloğu; `python web/run.py [port]`.

---

wrote docs/_understanding/14_tools_web.md
