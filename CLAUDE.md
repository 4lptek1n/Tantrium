# Tantrium — Sistem Hafızası

> **NE OLDUĞU (tek cümle):** Durumsuz, saf-matematik yapısal sertifikasyon makinesi.
> Girdiyi (sayı/dizi/matris/dict/SMILES) spektral momentlere okur, Riemann Hipotezi
> ispat yapısından türetilmiş 23 pozitiflik paradigmasıyla sertifikalar. **Dil yok,
> öğrenme yok, manifold/graf yok, ajans yok, istatistik yok.**

## Aktif Branch
`claude/asi-pure-math` — saf-matematik makinesi. (Geçmiş: `claude/seninle-agi-yapacagiz-XwJRz`
tam ASI sistemiydi; dil/kod/graf/büyüme katmanları o branch'ten silinerek bu makine türetildi.)

## Temel Kural
`from tantrium import ...` — her şey düz. `from tantrium.agi import ...` → YOK.

---

## Felsefe

```
girdi → A matris → G=AᵀA (daima PSD) → μ_k=Tr(G^k)/n → 8 rasyonel moment
```
**Hamburger Teoremi**: kompakt destekli ölçü moment dizisiyle tek biçimde belirlenir.
Encoder "çevirmez" — okur. Sayı, matris, molekül — hepsi aynı formül. Tüm aritmetik
exact `Fraction` (yuvarlama yok, bit-bit tekrarlanabilir = denetlenebilir sertifika).

---

## Proje Yapısı (47 .py)

```
src/tantrium/
  ai.py                ← tantrium.AI() — durumsuz SDK girişi (~48 matematik metodu)
  serve.py             ← opsiyonel FastAPI REST
  core/                ← 28 dosya
    encoder.py         ← girdi→moment (domain-kör). String: geçerli SMILES→bigram,
                          diğer string→deterministik imza-hash (math, YAKINLIK/ANLAM YOK)
    codex.py           ← 23 paradigma (verify() okur, hesaplamaz)
    pipeline.py        ← run_pipeline() L0-L7 sıralı hesap
    network.py         ← CertificationPipeline (topolojik DAG)
    engine.py          ← CertificationEngine (DURUMSUZ) + engine.core (CoreMachine lazy)
    unified.py         ← CoreMachine — tek geçiş sertifika
    concept.py         ← Concept + moment_distance (saf moment L1)
    rh_criteria.py     ← RH-kriter katmanı: momentlerden τ/pivot/cross-ratio/Stieltjes/
                          kümülant/Λ (tce-collapse RH zinciri, exact). 16-derinlik; encoder
                          her çıktıya structure["rh_criteria"] ekler. rank = AYIRT EDİCİ
                          (benzene rank≈1, aspirin rank≈6). criteria_distance = rh_distance.
    metric.py          ← canonical_distance (spectral W2), l1_distance
    reconstruct.py     ← reconstruct_measure() — Gauss kuadratür geri-çıkarım
    collision.py       ← CollisionHunter — adversarial teklik testi (8 moment)
    truth.py           ← TruthCertifier (komşu yok → N/A; durumsuz)
    confidence.py      ← calibrate() — geometrik ortalama
    grounding.py       ← GroundingCertifier (manifold yok → N/A; durumsuz)
    transport.py       ← CertifiedTransport (dyadic + Sturm + Zeta)
    structure.py       ← reverse_engineer / discover_law / forecast (Prony, Koopman/EDMD)
    quantum_moments.py ← FreeCumulants (Voiculescu κ) + QuantumSignature
    moment_ops.py      ← convex_combine konveks moment çekirdeği
    inverse.py         ← InverseTransport — hedef→W2-minimal moleküller→3D SDF
    molecular_space.py ← MolecularSpace (arrange/morph/lineage)
    molecular_genesis.py ← saf matematiksel molekül türevi
    molecular_3d.py    ← embed_3d_sdf() (RDKit ETKDGv3)
    production.py / production_judge.py ← produce/produce_math + 6-eksen yargı
    positivity_ladder.py · diversity.py · certificate.py · primitive_invention.py
  algebra/             ← sturm.py, positivity.py, sheffer.py
  proof/               ← dyadic_flow.py (solve_greedy, Fraction), certificate.py (Cell)
  domains/             ← bridge, certifier, generator, math_kernel*, spectral
  graph/
    anchors.py         ← 10 kanonik dağılım (ZETA_ZEROS, GUE, Gauss, ...) — saf matematik

* math_kernel.inject_math_kernel: manifold gerektirdiği için durumsuz makinede no-op.
```

---

## 23 Paradigma (L0-L7 Pipeline)

| Aşama | Paradigma | Hesaplama |
|-------|-----------|-----------|
| L2.5 | DALET | eigvalsh(Gram) → gerçek eigenvalue'lar |
| L0.5 | BET | ‖A‖²_F = Tr(G) |
| L1.5 | HE | V(k) = μ_k / λ_max^k |
| L2   | ZAYIN | path_sum = Tr(G) |
| L3   | HET | Li: λ_n > 0 |
| L4   | TAV | de Bruijn-Newman: Λ = −var₀ ≤ 0 |
| L5   | GIMEL | Achilles: zayıf paradigma yok |
| L6   | EMET | çelişki yok |
| Yrd. | ALEPH,KAF,AYIN,MEM,LAMED,TET,YOD,RESH,TSADI,SHIN,PE,VAV,NUN,SU3,KUF | |

Gerçek ayrımcılık CertifiedTransport'ta: benzene DYADIC_FAILED, aspirin CERTIFIED.

---

## CertifiedTransport

```
Kaynak/Hedef eigenvalues → Cell (Fraction kütleler)
1. DYADIC: solve_greedy → "verified_exact" veya FAIL
2. STURM:  H(t)=(1-t)H_src+t·H_tgt tüm t∈[0,1] için PSD
3. ZETA:   L1(hedef, ⊕ANCHOR:ZETA_ZEROS)
CERTIFIED = dyadic ✓ AND sturm ✓
```
**ÖNEMLİ:** SMILES için `structure["eigenvalues"]` = n×n moleküler Laplacian; metin için 4×4 Gram-Hankel.

---

## API (saf matematik)

```python
import tantrium
ai = tantrium.AI()

ai.status()                       # durumsuz makine özeti
ai.ask("EGFR")                    # AskResult: paradigma sertifikası
ai.certify_all("EGFR")            # UnifiedCertificate (tek geçiş)
ai.paradigms("c1ccccc1")          # 23 paradigma dökümü
ai.transport("CCO", "CC(=O)O")    # TransportCertificate
ai.sturm("x^3 - 3*x + 1")         # Sturm zinciri
ai.positivity("x^2 + 1")          # Hankel PSD
ai.rh_criteria("EGFR")            # RH-kriter: τ/pivot/cross-ratio/Stieltjes/κ/Λ/rank
ai.rh_distance("EGFR", "c1ccccc1")# RH-kriter ayırt edici mesafe (rank+pivot+κ)
ai.reconstruct([1,1,2,3,5,8])     # momentlerden ölçü
ai.reverse_engineer(gözlem)       # gizli üreten yapı
ai.discover_law(seri)             # yönetici yasa + tahmin (Koopman/EDMD)
ai.forecast(seri)                 # holdout-sertifikalı tahmin
ai.detect_anomalies(seri)         # yapısal anomali
ai.quantum_distance(a, b)         # (1-γ)·W2 + γ·κ
ai.entangle(a, b)                 # klasik-uzak / κ-yakın gizli bağ
ai.design("EGFR")                 # ters transport → moleküller (RDKit varsa 3D SDF)
ai.arrange("EGFR") / ai.morph(a,b) / ai.lineage_mol(s)
ai.produce_math([...])            # ölçülen κ → gerçeklenebilir spektrum
ai.design_peptide("ACDEFGHIK")    # Sturm-sertifikalı biyopolimer
ai.produce/cure/simulate/judge_binding  # üretim dökümhanesi (6-eksen yargı)
```

**N/A eksenleri:** `grounding` ve `truth` öğrenilen manifolda/komşulara muhtaçtı →
durumsuz makinede `"N/A"`. Geriye sertifikasyon + transport + confidence kalır.

---

## Hilbert-Pólya / RH Bağlantısı (mimari temel)

Her girdi → G=AᵀA (Hermitian, daima PSD) → eigenvalue dağılımı = spektral ölçü. Bu, Hilbert-
Pólya'nın aradığı operatör türünden. RH bağlantıları kodda CANLI:
- `graph/anchors.py`: ZETA_ZEROS (50 sıfır) + GUE (Montgomery-Odlyzko)
- `pipeline.py` TAV: `Λ = −var₀ ≤ 0` = de Bruijn-Newman (RH eşdeğeri)
- `quantum_moments.py`: Voiculescu serbest kümülant κ-additivite
- `transport.py` Sturm pivotları = normalize Hankel determinantları = subdiscriminantlar
- Tam RH ispat zinciri ayrı branch'te: `tce-collapse-engine` (Lean 4, `external_formalization: PENDING`).

---

## Kritik Pitfall'lar

1. `from tantrium.agi import ...` → YOK. Her şey düz.
2. **Durumsuz makine:** manifold/graf/öğrenme YOK. `truth`/`grounding` → N/A. Bunları
   "bozuk" sanıp manifold geri-eklemeye çalışma — kasıtlı tasarım.
3. **Encoder string yolu = saf math:** geçerli SMILES bigram'a, diğer string deterministik
   imza-momentine (pozisyon+codepoint hash) gider. Bu DİL DEĞİL — yakınlık/anlam/nearest
   katmanı silindi; yalnız "string→sayı" deterministik dönüşüm.
4. **23 paradigma tek başına ayırt edici DEĞİL** (G=AᵀA daima PSD → her şey "geçer"). Eski
   sistemde grounding ekseni elerdi; o silindi. Gerçek ayrım transport'ta (Sturm/dyadic)
   VE **RH-kriter rank/pivot/cross-ratio vektöründe** (`rh_criteria.py`): pozitiflik
   verdictleri çoğu girdide geçer ama VEKTÖR (rank, pivot değerleri, κ) ayırt eder.
5. **8 moment ile temsil** (Hamburger tekliği sonsuz limitte tam). `collision.py` teklik/çakışma testi yapar.
6. `transport.py` → `tantrium.proof.dyadic_flow` import eder.
7. `math_kernel.inject_math_kernel` durumsuz makinede no-op (manifold yok).
8. SMILES için exact Fraction determinant uzun dizide patlar → encoder momentleri float'ta
   hesaplayıp küçük Hankel kurar (hızlı yol).

---

## Silinen Katmanlar (artık YOK — kafa karıştırmasın)

`claude/seninle-agi-yapacagiz-XwJRz`'de vardı, bu branch'te SİLİNDİ:
`language/` (dil/konuşma/akıcılık), `reasoning/` (reason/causal/think), `research/`
(growth/cognition/proof_loop/autonomous), `meta/` (self_model/vision/synthesis),
`perception/` (ses/görüntü/DNA-sinyal), `core/{semantic,meaning_*,nl_code,topology_encode,
code_*,enrichment}`, `graph/{knowledge_graph,memory,relations}`, manifold/TAU verisi.
Bunlara referans gören kod kalıntısı = hata; temizlenmeli.

---

## Mevcut Durum
- 47 .py modül, ~108+ test geçiyor. Durumsuz, saf matematik.
- Theorem candidate dokümanları: `docs/`, `theorems/`. Tam RH ispatı: `tce-collapse-engine` branch.
