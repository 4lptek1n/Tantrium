# Tantrium — Mimari

*Durumsuz, saf-matematik yapısal sertifikasyon makinesi.*

---

## Temel Felsefe (değişmez)

Evren zaten matematikseldir. Encoder "çevirmez" — okur.

```
girdi (sayı, dizi, matris, dict/graf, molekül/SMILES)
  → A matrisi (yapının doğal gösterimi)
  → G = AᵀA  (Gram — daima PSD)
  → μ_k = Tr(G^k)/n  (spektral momentler)
  → 8 rasyonel moment  (kompakt destekli ölçünün tam temsili)
```

**Hamburger Teoremi**: kompakt destekli ölçü moment dizisiyle TEK biçimde belirlenir.
G = AᵀA daima PSD → moment dizisi geçerli → Hankel PSD → ALEPH daima geçer. Bu, RH
ispatının (Xi-fonksiyon momentleri) evrensel uygulamasıdır.

Tüm aritmetik exact `Fraction`: yuvarlama yok, kanıt-taşıyan, bit-bit tekrarlanabilir.

---

## Tasarım İlkesi: Durumsuzluk

Bu makine **durumsuzdur**. Öğrenilen kavram grafı (TAU), manifold, hafıza, ajans,
büyüme döngüsü **yoktur**. Her çağrı girdiyi saf matematik olarak işler; oturumlar
arası bir şey biriktirmez. Güç "zekâ"da değil — **deterministik, denetlenebilir
sertifikada**.

> Tarihsel: Bu çekirdek, dil/öğrenme/kod/graf katmanları olan tam bir ASI prototipinden
> (`claude/seninle-agi-yapacagiz-XwJRz`) o katmanlar silinerek türetildi. Silinenler:
> `language/`, `reasoning/`, `research/`, `meta/`, `perception/`, `core/{semantic,
> meaning_*,nl_code,topology_encode,code_*,enrichment}`, `graph/{knowledge_graph,
> memory,relations}`, manifold/TAU verisi.

---

## Katmanlı Mimari (6 katman)

```
┌──────────────────────────────────────────────────────────────────┐
│  Katman 5: SDK + SENTEZ                                          │
│  ai/ — durumsuz giriş (mixin paketi, ~60 matematik metodu)       │
│  ask / certify_all / transport / discover_law / reconstruct /    │
│  produce_math / design / quantum_distance / sturm / positivity / │
│  spectral_reading / spectral_geometry / interact / relate /      │
│  spectral_flow / compute_zeros / zeta_operator / hilbert_polya   │
│  universe.py (YEDİ YÜZ sentez) · cosmos.py (T₀→T₁₀ evrim)        │
│  serve.py — opsiyonel FastAPI REST                               │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│  Katman 4: Sertifikalı Transport                                  │
│  transport.py: DYADIC (solve_greedy, exact) + STURM (PSD-yol)    │
│               + ZETA (ζ-sıfır ailesine L1). CERTIFIED=dyadic∧sturm│
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│  Katman 3: Domainler (matematiğe indirgenen)                      │
│  domains/ (spectral, molecular via inverse/molecular_space/       │
│  molecular_genesis/molecular_3d), production + production_judge    │
│  (6-eksen üretim yargısı), structure.py (discover_law/forecast/    │
│  reverse_engineer — Prony, Koopman/EDMD)                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│  Katman 2: Sertifikasyon Motoru (22+1 paradigma)                  │
│  engine.py (CertificationEngine, DURUMSUZ orkestratör)           │
│  network.py (CertificationPipeline, topolojik sıra)              │
│  codex.py (23 paradigma sınıfı — verify() okur, hesaplamaz)      │
│  pipeline.py (run_pipeline, L0-L7) · unified.py (CoreMachine)    │
│  truth/grounding → N/A (manifold yok) · confidence · collision   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│  Katman 1: Kodlama                                                │
│  encoder.py — girdi→moment (domain-kör). Sayı/dizi→power moments, │
│  matris/dict→Gram, SMILES→bigram Laplacian, diğer string→         │
│  deterministik imza-hash (math; yakınlık/anlam/dil YOK)          │
│  quantum_moments.py — Voiculescu serbest kümülant κ              │
│  reconstruct.py — momentlerden ölçü (Gauss kuadratür)            │
└───────────────────────────┬──────────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────────┐
│  Katman 0: Cebir                                                  │
│  algebra/ (Sturm zinciri, positivity, Sheffer)                  │
│  proof/ (dyadic_flow.solve_greedy [Fraction], certificate.Cell)  │
│  graph/anchors.py (10 kanonik dağılım: ZETA_ZEROS, GUE, ...)     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Üç Eksen (v0.4.0 — tek operatörün üç yüzü)

Her şey aynı `G=A†A` operatörünün bir yüzü; üçü de tek `eigh`'ten okunur:

```
1. TEK OPERATÖR  bir girdiyi oku
   spectral_reading.py  → 4 katman: MAKRO (momentler) · MİKRO (⟨r⟩) · SİMETRİ (Dyson β) ·
                          ÖZVEKTÖR (IPR/localization + fraktal boyut D₂)
   spectral_geometry.py → Connes/NCG: Seeley-de Witt ısı-çekirdeği (boyut d_s · eğrilik a₂ · etki)

2. İLİŞKİ         iki girdiyi bağla   → relation.py (çatı)
   interaction.py   → KUVVET (köşegen-dışı kuplaj) + HAYAT (von Neumann dolanıklık), ortak H=M†M
   spectral_flow.py → TOPOLOJİ: G_A→G_B yolunun net özdeğer geçişi (Atiyah-Singer aile indeksi)

3. EVRİM          bir girdiyi zamanda akıt
   cosmos.py        → T₀ Yasa → T₁₀ μ*/patlama; her T'de SpectralReading akar (4-katman yörünge)
```

`universe.py` üçünü bir girdiden **YEDİ YÜZ** + tek mühürde sentezler
(1 MADDE · 2 FİZİK · 3 GEOMETRİ · 6 ZAMAN · 7 TOPOLOJİ; `.couple`→ 4 KUVVET + 5 HAYAT).

---

## Veri Akışı (tek sertifikasyon)

```
ai.certify_all("EGFR")
  → encoder.encode("EGFR")                  # → 8 moment (imza-hash)
  → CoreMachine.certify                     # tek geçiş
      → pipeline.run_pipeline (23 paradigma, L0-L7)
      → confidence.calibrate
      → (truth/grounding → N/A, durumsuz)
  → UnifiedCertificate(paradigms_passed, coherent, ...)
```

```
ai.transport("CCO", "CC(=O)O")
  → encode her iki SMILES → moleküler Laplacian eigenvalue'ları
  → _obj_to_cells (Fraction kütleler)
  → DYADIC solve_greedy → STURM PSD-yol → ZETA L1
  → TransportCertificate(certified = dyadic ∧ sturm)
```

---

## Hilbert-Pólya / RH Bağlantısı

Her girdi → G=AᵀA (Hermitian, daima PSD) → eigenvalue dağılımı = spektral ölçü = Hilbert-
Pólya'nın aradığı operatör türünden. Kodda canlı bağlantılar:

- `graph/anchors.py`: ZETA_ZEROS (50 Riemann sıfırı) + GUE (Montgomery-Odlyzko)
- `pipeline.py` TAV: `Λ = −var₀ ≤ 0` = de Bruijn-Newman (RH eşdeğeri, 2020'de Λ≥0 kanıtlandı)
- `transport.py` Sturm pivotları = normalize Hankel determinantları = subdiscriminantlar
- `quantum_moments.py`: Voiculescu serbest kümülant κ-additivite
- `zeta_operator.py`: ★ Hilbert-Pólya operatörünü DOĞAL malzemeden kurar (fit yok) — Berry-Keating
  yarı-klasik iskelet (asal içermez, fonksiyonel denklem) + Weil explicit-formula asal düzeltmesi
  (Euler çarpımı). Sıfırlar yalnız skor; taban RMS≈0.02 (koşullu yakınsama), kapatan sonlu
  operatör = Hilbert-Pólya hedefi. `compute_zeros` Riemann-Siegel Z'den sıfırları DOĞRUDAN hesaplar.

Tam RH ispat zinciri (D-pozitiflik → Sturm pivot → Jensen hiperbolisitesi → RH, Lean 4)
ayrı branch'te: `tce-collapse-engine`.
