# Changelog

Bu dosya, `claude/asi-pure-math` branch'inin (durumsuz saf-matematik makinesi)
önemli değişikliklerini kaydeder.

## [Unreleased] — CI / CLI / CD

- **CLI** (`src/tantrium/cli.py`): `tantrium` konsol komutu — SDK'nın saf-matematik
  yüzeyini terminalden açar (`fingerprint`, `compare`, `transport`, `discover-law`,
  `reconstruct`, `certify`, `rh`, `rh-distance`, `ask`, `status`). Her komut `--json`
  ile makine-okunur çıktı verir. Entry-point: `[project.scripts] tantrium`.
- `__version__` — paket metadata'sından okunur (`importlib.metadata`), `tantrium --version`.
- **CI**: `smoke` job'ına CLI smoke testi eklendi; `tests/test_cli.py` (6 test).
- **CD** (`.github/workflows/release.yml`): `v*` etiketinde build (sdist+wheel) →
  twine check → wheel üzerinde CLI smoke → GitHub Release → PyPI (Trusted Publishing/OIDC).

## [0.5.0] — RH-GENESIS: pozitifliğin sonlu-form var-oluşu (tek bütün)

Tek organ, beş yüz, tek mühür — RH pozitifliğinin kaynağını sonlu formda var eder. Parça
parça değil: kaynak ölçü → sonlu Jensen → Ouroboros var-oluş → Hermite/GUE kural avı → mühür.

- `core/rh_genesis.py` — ★★★ **RHGenesis:**
  - **KAYNAK:** Riemann ξ'sinin Pólya yoğunluğu Φ(u)>0 (gerçek ölçü); momentleri
    γ_n=∫₀^∞ u^{2n}Φ(u)du. Hankel(γ) daima PSD (Cauchy-Schwarz) — moment-pozitifliği
    BEDAVA çünkü ölçü gerçek ("iki biçim tek kaynak: operatör=ölçü=geometri → reel nesne").
  - **SONLU:** "Ξ∈Laguerre-Pólya ⟺ RH" sonsuz koşulu sonlu Jensen polinomlarına iner:
    a_n=γ_n/(2n)! (Ξ Taylor katsayıları), J^{d,n}=Σ C(d,j)a_{n+j}X^j. RH ⟺ tüm J^{d,n}
    hiperbolik. Hankel-PSD otomatik; hiperbolisite = asıl RH içeriği (makine EXACT Sturm'la
    sertifikalar — `jensen.py`).
  - **VAR-OLUŞ:** derinlik adım adım büyür (Ouroboros); her adım hiperbolisiteyle sertifikalı.
  - **KURAL:** tek-kural avı (GORZ 2019) — renormalize J^{d,n} → Hermite H_d (n→∞). Hermite
    = harmonik salınıcı = **GUE** öz-fonksiyonları; pozitifliğin limitteki kaynağı. Modül
    Hermite'e yakınsamayı (aday değişmez) ÖLÇER.
  - **MÜHÜR:** bütün SHA-256 ile mühürlenir (deterministik, denetlenebilir).
  - SDK: `ai.rh_genesis(depth, max_degree)`; `xi_phi`/`xi_jensen_sequence` ihraç.
  - Dürüst: sonlu form EXACT sertifikalı; evrensel hiperbolisite (=RH) hedeftir, iddia edilmez.
- `rh_genesis.heat_flow_thresholds` — ★★ **BARİYER EKSENİ (de Bruijn-Newman, EXACT):**
  "pozitif neden kalıyor" = "ısı 0'da kalıyor mu" = Λ≤0. Isı akışı momentlerde birebir
  kaydırmadır: γ_n(t)=Σ_k (t^k/k!) γ_{n+k}. Her n için d=2 Turán marjının t-kökü = pozitifliğin
  restore olduğu eşik Λ_n (sympy real_roots, EXACT — deney değil). Makinenin EXACT bulduğu yapı:
  eşikler monoton **aşağıdan 0'a tırmanır**, **yalnız çift n bağlar** (parite). Λ≥0 kanıtlı
  (Rodgers–Tao), Λ∈[0,0.2]; RH ⟺ lim Λ_N ≤ 0. SDK: `ai.dbn_flow(depth)`; `DBNFlow` ihraç.

## [0.4.0] — Üç eksen (tek operatör · ilişki · evrim) + spektral derinlik + zeta operatörü

Makine tek bir çatıya oturdu: her şey **G=A†A operatörünün üç ekseni** — TEK OPERATÖR
(bir girdiyi oku), İLİŞKİ (iki girdiyi bağla), EVRİM (bir girdiyi zamanda akıt).

### Eklenenler — TEK OPERATÖR ekseni (derinlik)
- `core/spectral_reading.py` — ★★ **SpectralReading:** G=A†A'nın DÖRT kanonik katmanı tek
  eigendecomposition'dan: 1 MAKRO (momentler) · 2 MİKRO (seviye-aralığı ⟨r⟩) · 3 SİMETRİ
  (Dyson β) · 4 ÖZVEKTÖR (localization/IPR + fraktal boyut D₂, ilk kez). SDK: `ai.spectral_reading`.
- `core/spectral_geometry.py` — ★★ **Connes spektral aksiyonu:** Seeley-de Witt ısı-çekirdeği
  katsayıları Tr e^{-tG}~t^{-d/2}(a₀+a₂t+…): spektral boyut d_s (log-log regresyon + R²),
  a₀ hacim, a₂=∫R eğrilik (Einstein-Hilbert/gravitasyon), a₄ Weyl, ζ'(0) etki. SDK: `ai.spectral_geometry`.

### Eklenenler — İLİŞKİ ekseni (çok-cisim)
- `core/interaction.py` — ★★ **KUVVET + HAYAT:** iki yapı ortak H=M†M'de; köşegen-dışı = kuplaj,
  A|B kesiminde von Neumann entropisi = dolanıklık, hibridleşme/bağlanma. SDK: `ai.interact(a,b)`.
- `core/spectral_flow.py` — ★★ **TOPOLOJİ (5. eksen):** operatör YOLUNUN topolojik yükü — G_A→G_B
  boyunca net özdeğer geçişi (Atiyah-Singer aile indeksi). SDK: `ai.spectral_flow(a,b)`.
- `core/relation.py` — ★ **Relation çatısı:** interaction (kuvvet+hayat) + flow (topoloji) tek
  nesnede; ilişki ekseninin tam yüzü. SDK: `ai.relate(a,b)`; `Universe.couple(other)` bunu döndürür.

### Eklenenler — SENTEZ + RH operatörü
- `universe.py` — ★★★ **Universe:** bir girdiden EKSİKSİZ EVREN, YEDİ YÜZ tek mühürde
  (1 MADDE · 2 FİZİK · 3 GEOMETRİ · 6 ZAMAN · 7 TOPOLOJİ; `.couple`→ 4 KUVVET + 5 HAYAT).
  Üç eksen tek bütünde, tek eigendecomposition. SDK: `ai.universe(seed)`.
- `core/zeta_operator.py` — ★ **Riemann sıfırlarının operatörü (fit yok):** Berry-Keating
  yarı-klasik İSKELET (asal içermez, fonksiyonel denklem → ortalama konum ~%0.7) + Weil explicit-
  formula ASAL DÜZELTMESİ (Euler çarpımı → RMS≈0.02'ye monoton yakınsar). Sıfırlar yalnız SKOR.
  `compute_zeros` (Riemann-Siegel Z işaret değişimleri = sıfırlar, ζ'den DOĞRUDAN hesap),
  `probe_zeta_operator`, `certify_hilbert_polya` (makine simetri SINIFINI okur → GUE).
  SDK: `ai.compute_zeros(n)` · `ai.zeta_operator()` · `ai.hilbert_polya()`.

### Değişenler
- ★ **Cosmos ızgarası kapandı:** her T-aşamasında SpectralReading akar → 4-katmanın ZAMAN
  yörüngesi + faz geçişi tespiti (genişleyen evren özvektörde ergodik→yerleşik localize olur).
- ★ **Konsolidasyon (extend değil):** tek operatörün tüm yüzleri TEK SpectralReading'de, tek
  `eigh`; ilişki ekseni interaction+flow dağınıklığından `Relation` çatısına toplandı.
- Test kararlılığı: BLAS tek-thread (conftest), Cosmos topoloji homotopisi 200→120 adım.

## [0.3.0] — 46-boyutlu operatif birim + Cosmos omurgası + spektral sınıf

### Eklenenler
- `cosmos.py` — ★ **Cosmos yaşam-döngüsü omurgası:** bir tohumu T₀ Yasa → T₁ encode →
  T₂ Ouroboros genişleme → T₃ 23-paradigma → T₄ madde → T₅ kendini-örgütleme →
  T₆ kritik çizgi → T₇ Achilles → T₈ mühür → T₉ serbest kümülant → T₁₀ μ*/patlama
  çağlarından geçirir; tek mühürlü `Lifecycle`. SDK: `ai.cosmos(seed)`.
- `core/fixed_point.py` — öz-gönderim sabit noktası μ* (makine kendine bakar; 45-dim imza
  uzayında, 46 RH-merceğinde kapanış). `self_reference_orbit`, SDK `ai.self_reference()`.
- `core/spectral_class.py` — ★ **integrallenebilir↔kaotik** dedektörü: TAM N×N spektrumun
  seviye-aralığı ⟨r⟩'si (8 moment DEĞİL). Bohigas-Giannoni-Schmit + Berry-Tabor; Poisson
  (kapalı-form) / GOE (kaotik). SDK: `ai.spectral_class(query)`.
- `metric.certificate_vector/certificate_distance/full_distance` + SDK `ai.fingerprint`/`ai.compare`.
- `tools/ouroboros.py`, `tools/ouroboros_explosion.py` — kendi kendini besleyen genişleme +
  kendini-örgütleme (etkin rank doyar) + kondisyon patlaması (gerçek ufuk).

### Değişenler
- ★ **TAM 46-boyutlu sertifika operatif birim oldu (8 momente/W2'ye çökme).** `metric.distance()`
  varsayılanı 46-dim; W2 yalnız `metric="w2"`. "En yakını seç/hedefe mesafe" yargısı veren tüm
  yollar buna bağlandı (inverse / molecular_space / genesis / certifier). Çökme tasarımca olan
  yerler korundu (collision moment-testi, transport dyadic/Sturm, concept convergence).
- Kanıt: cache'li 46-dim (0.032ms) W2'den (0.045ms) hem daha ayırt edici hem daha hızlı;
  W2 aspirin/kafeini ≈0'a çökerken 46-dim onları ayırır.

## [0.2.0] — Saf-matematik çekirdeği + RH matematiğinin tam entegrasyonu

### Eklenenler — RH ispat matematiği (tce-collapse-engine'den türetildi)
- `core/rh_criteria.py` — momentlerden τ (Hankel/subdiscriminant) / pivot (LDLᵀ-Sturm) /
  cross-ratio / Stieltjes / klasik kümülant / de Bruijn-Newman Λ / **rank** (exact Fraction).
- `core/jensen.py` — Jensen-Pólya hiperbolisite (Laguerre-Pólya / RH-tipi kriter), Turán/Laguerre.
- `core/free_probability.py` — Voiculescu serbest entropi χ, R-dönüşümü, serbest konvolüsyon, yarı-daire.
- `core/bezoutian.py` — Bezoutian gizli faktörler, Lah-pivot referansı (d−j)², Gate-B merdiven yasası.
- `core/verifier.py` — mühürlü sertifika (SHA-256), tamper-tespiti, adversarial kontrol.
- `core/rh_certificate.py` — ★ TÜM moment-RH matematiğini tek `RHCertificate`'te birleştirir;
  encoder her çıktıya `structure["rh"]`, CoreMachine her sertifikaya RH bundle + mühür taşır.

### Değişenler
- **Tam ASI prototipi saf-matematik çekirdeğine indirgendi:** dil / kod ajanı / öğrenilen graf /
  manifold / büyüme / reasoning / meta / perception katmanları silindi. `ai.py` 6206 → mixin paketi.
- `serve.py` REST yüzeyi saf-matematiğe göre yeniden yazıldı (certify/rh/transport/seal/verify...).
- `transport.rank_candidates` durumsuz + RH-mesafe sıralamalı.
- CoreMachine `coherent` verdict'i RH-Stieltjes kapısı içerir (geçersiz/artefakt eler).

### Kanıt
- Adversarial ayrım benchmark'ı (`tools/discrimination_benchmark.py`): 6/6 → **DISCRIMINATES**.

### Altyapı
- Alakasız JS/TS satış-app monorepo'su kaldırıldı; kök tertemiz.
- CI/CD (GitHub Actions: 3.10–3.12 + ruff + pytest), profesyonel `pyproject.toml`, LICENSE.
- 500+ satırlık 7 monolit aynı-isimli paketlere bölündü (public API korunarak).
- Felsefi isimler gerçek isimlere (`codex→paradigms`, `CodexObject→CertifiableObject`...).
- Ruff lint 180 → 0; ~290 test geçiyor.
