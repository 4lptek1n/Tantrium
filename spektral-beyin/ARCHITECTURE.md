# SPEKTRAL BEYİN — Hedef Mimari ve Yol Haritası

> Sahiplik ilkesi: **Her iddia ya kodda test edilir ya README'den çıkar.**
> Metafor isim koyabilir; kanıt sayılmaz. Başarısızlık da rapordur:
> σ'sı patlayan nesneye "yasasız" demek sistemin zaafı değil, çıktısıdır.

## Vizyon (dürüst dille)

Bir nesnenin kimliği verisi değil, onu **üreten yasa + tohumdur** (hesaplanabilir
MDL). Her domain bir operatöre iner (dizi→Hankel, molekül→bağ matrisi),
operatör spektruma, spektrum 91 ölçüm operatörlü bir **teorem paneline**
(coord_91) yansır. LLM düşünen şey değil, dilsiz çekirdeğin **hoparlörüdür**.
Ouroboros: sıkıştır (nesne→yasa+seed) ve aç (yasa+seed→nesne ve ötesi);
NEWTON dim'i bu döngünün tutarlılık sertifikasıdır.

## Omurga (OTURDU — `cekirdek/beyin.py`)

Dört fiil tek `Kimlik` tipinde, tek çağrı yüzeyinde birleşti. Uçtan uca
kanıt: `test_beyin.py` (24/24). Dağıtık organlar artık tek döngü:

```
kodla(veri, domain)   her domain -> operator -> özdeğer(+özvektör) -> yasa+seed -> coord_91
kopru / ayni_yasa     ortak grounding uzayında domainler arası eş-kimlik
coz(cep)              istenen kimlik/cep -> geçerli yeni nesne (de novo)
ouroboros(kimlik)     nesne -> kimlik -> nesne, kimliği koruyarak kapat (kayıpsız)
```

Ölçülen gerçekler (test çıktısı): Fibonacci σ=3e-16; DNA→RNA transkripsiyon
d=0.0 (kimlik tam korunur); periyot-3 dna~rna~protein~math **aynı kanonik
yasaya** iner; de novo cep→geçerli molekül; ouroboros dizi recon_err=4e-13,
molekül RMSD=2e-15; **yasasız gürültü sahte başarı vermez** (döngü kapanmaz).

### coord_91 kablolaması (dim-dim, `cekirdek/kablolama.py`)

91 dim'in her biri **pozisyonuna göre değil, gerçekte ne hesapladığına göre** tek
bir role kablolandı — tam bölüşüm (91 dim / 9 rol), `dogrula()` ile kanıtlı:

| Rol | # | Ne ölçer |
|-----|---|----------|
| sekil | 20 | momentler μ₀₋₁₅ + klasik kümülantlar κ₁₋₄ (dağılım şekli) |
| yapi | 18 | Hankel/moment-problemi geometrisi (pivot d, τ, cross-ratio) |
| kritiklik | 12 | Λ, Li, HET-Li, Q, GIMEL (RH / kritik çizgi) |
| baskinlik | 12 | DALET p, HE, Schur, Sylvester, Perron (dominant mod) |
| karmasiklik | 8 | rank, Euler, BET, RESH, YOD-MDL, VAV (entropi/etkin boyut) |
| varolabilirlik | 8 | Hamburger/Stieltjes moment-problemi sertifikaları |
| serbestlik | 5 | Voiculescu serbest kümülantları (yarımdaire testi) |
| kaos | 4 | Wigner–Dyson ⟨r⟩, β (GOE/GUE/Poisson sınıfı) |
| dinamik | 4 | Newton artığı + spektral akış (zaman/tutarlılık) |

**Kaba blok yanlıştı:** aynı rol farklı bloklara dağılmıştı (kritiklik 27+59+72+84;
entropi 53+80-82). Kablolama bunları doğru yere topladı. `FACET` artık `range`
değil, bu kayıt defterinden (`ROL`) geliyor.

**Onarım (`cekirdek/onarim.py`) — 32 boşa dim gerçek işe bağlandı:** 200+
spektrumla kanıtlanan israf: **18 dim yapısal tekrar** (varyans 4 dim'de:
d₁=τ₁/τ₀=κ₂=Hankel-oran=serbest-κ₂; ortalama 2 dim'de; klasik=serbest kümülant
1-2-3. mertebede özdeş), **14 dim ölü** — içinde gerçek bir bug: **Li katsayıları
(37-40, 65-68) hiç ateşlenmiyordu** çünkü kod `x>1` arıyor ama λ̂≤1 (max'a
normalize). Sylvester (52) de ölü: Gram hep PSD → n₊/r=1.

Çözüm: her boşa dim değişken+benzersiz bir niceliğe bağlandı (çarpıklık, basıklık,
spektral boşluklar, IPR, etkin rank, düzeltilmiş Li, Stieltjes pivotları, serbestlik
defekti κ₄-κf₄, Gini, çeyrekler...). Kanıt: 500 spektrumda **sıfır ölü, sıfır
tekrar** (`test_beyin.py`). Dürüstlük notu: ~10 özdeğerlik nesnenin ~10 bağımsız
serbestliği var — 91 dim zorunlu **fazla-tam**; amaç dim'leri bağımsız yapmak değil
(imkânsız), her birinin **ayrı formülü** olması. Efektif statik rank 72/91: farklı
mercekler aynı ışığa bakar, ama iki mercek artık aynı değil.

**Büyük beyin (*.pkl) yeniden üretilmeli** (`hazirla.py`) — C91 sütunları değişti.

### Köprü = çok-açılı panel (yasa yalnızca bir açı)

Köprü tek öklit mesafesi değil; coord_91 semantik bloklara (facet) ayrılır ve
"hangi açıdan aynı?" sorulur. Ölçülen: periyot-3 dna~protein **6 açının 5'inde
özdeş** (varolabilirlik=0.000, kaos=0.006, Li=0.000, içerik=0.007, kritiklik=0.09);
tüm 0.95 ayrılık **tek blokta** (paradigma=0.947) toplanıyor. Ham 91-öklit bu yüzden
yanıltır — 46-boyutlu yarı-doygun paradigma bloğu toplamı ezer. Çözüm: `mesafe`
**facet-ortalaması** (kalibre=0.21 vs ham=0.95); hiçbir blok boyut sayısıyla domine
edemez. `ayni_yasa` artık açılardan sadece biri (İSKELET). `kopru(hedef, adaylar,
facet='kaos')` bir açıdan sorar; farklı açı farklı komşu döndürebilir.
API: `facet_mesafe`, `benzerlik` (tam profil), `ham_mesafe` (kıyas), `FACET`.

### MANİPÜLE organı (`cekirdek/manipule.py`) — evren kurmak VE bükmek

Mimarinin asıl amacı netleşti: arka beyin **evren kurar** (yasa+seed) ve o evreni
**amaca göre manipüle eder**. 91 dim evrenin kendisi değil — **kokpit**: köprü
dim'leri durumu dile çevirir (Gemma'ya gösterge), manipülasyon dim'leri uzayı
bükmek için tutamak/ölçümdür. Gemma'ya karışılmaz; o sadece konuşur.

Evren mod uzayında tutulur: s[k] = Re(Σ aⱼ·zⱼᵏ) — bizim evrenimizin izin
verdiği işlemler doğal operatör olur (test_manipule.py, 18/18):

| İşlem | Operatör | Kanıt |
|---|---|---|
| **Zaman (iki yön)** | zⱼᵏ her tamsayı k | Fibonacci'nin GEÇMİŞİ: −1,1,0,1 (rekürans geriye sağlar) |
| **Süperpozisyon** | mod birleşimi = yasa çarpımı | fib⊕2ⁿ: dizi toplamı, order 3, kökler {φ,−1/φ,2} |
| **Mod cerrahisi** | aⱼ söndür / |zⱼ| bük | 3-modu söndür → evren fib'e döner |
| **Kritikleştir** | kökleri çembere taşı | Q: 0.51 → 10⁹, crit → 0 (kayıpsız rejim) |
| **Hedefe bük** | amaç = hedef panel değeri | dim59(Q)=1.0 iste → kökler çembere *yürür* (crit 0.51→0.002) |

En önemli test sonuncusu: **amaç kokpitten verildi** ("Q göstergesini tavana taşı"),
arama kök uzayında koştu, fizik doğrulandı (kökler gerçekten çembere yürüdü).
Kokpit → evren yönü çalışıyor: göstergeler tutamak olarak da iş görüyor.
Sınıf kapalı: manipüle edilen evren yine yasa+seed olarak saklanır (σ≈1e-16).
DÜRÜSTLÜK: organ C-finite evren sınıfında; doğrusal-olmayan evrenler Faz 2.

## Organlar (durum)

| # | Organ | Durum | Not |
|---|-------|-------|-----|
| 1 | **Yasa avcısı** | Prony (C-finite) ✅ | Hiyerarşi (holonomik/rasyonel) → Faz 2 |
| 2 | **Kanonik kimlik** | (yasa, seed, σ) + özvektör ✅ | Faz izi `de_novo.py`+omurgada çözülü (izospektral ayrışıyor) |
| 3 | **coord_91 paneli** | Statik + dinamik kat DOLU ✅ | Popülasyon kalibrasyonu → Faz 1 |
| 4 | **Omurga (kodla/köprü/çöz/ouroboros)** | OTURDU ✅ | `beyin.py`, 24/24 test |
| 5 | **Büyük beyin** | 40k–100k nesne, pickle | Kanonik genotip indeksli sorgu → Faz 1 |
| 6 | **Köprü (nöral)** | `neural_brain.py` yazılı, eğitilmemiş | coord→düşünce-token, LoRA → Faz 4 |
| 7 | **Kapı** | `nn.Linear` ölü kod; fiili kapı regex | Hidden-state'ten eğitilmiş → Faz 4 |
| 8 | **Ağız (LLM)** | Prompt-injection ile besleniyor | Yalnız köprü üzerinden → Faz 4 |

## Dinamik kat (bu commit ile dolan boş devreler)

| Dim | Ad | Ölçtüğü şey | İstediği girdi |
|-----|----|--------------|----------------|
| 50 | NEWTON | Yasa↔spektrum tutarlılığı (ouroboros artığı) | yasa |
| 59 | Q | Kalite faktörü — birim çember = kritik çizgi | kökler |
| 69–71 | AKIŞ | Sürüklenme, enerji akışı, faz kayması (spectral flow) | zaman |
| 80–82 | RESH | S_tot, S_alt, S_çev bipartisyon entropileri (+ karşılıklı bilgi) | bölme |

Ortak desen: dördü de statik spektrumun **cevaplayamayacağı** soruları sorar —
bu yüzden boştular. `coord_91(lam)` imzası dar; `coord_91_full(lam, seq, law, roots)`
doğru imzadır. Kod: `cekirdek/dinamik.py`, testler: `test_dinamik.py` (19 test).

## Fazlar ve kabul kriterleri

### Faz 0 — Dinamik kat + dürüstlük ✅
- [x] NEWTON, Q, AKIŞ, RESH gerçek matematikle doldu
- [x] 19 yanlışlanabilir test yeşil (`python3 test_dinamik.py`)
- [x] README fiili durumu anlatıyor (regex kapı, C-finite kapsam)

### Faz 0.5 — Omurga oturtma ✅
- [x] `cekirdek/beyin.py`: kodla/köprü/çöz/ouroboros tek `Kimlik` tipinde
- [x] Dört fiil uçtan uca kapalı döngü — `test_beyin.py` 24/24
- [x] Cross-space yasa düzeyinde kanıtlı; d=0.00000'ın anatomisi çıktı:
      transkripsiyonda gerçek 0, domain-aşan köprüde yasa özdeş / coord ölçek-bağımlı
- Kabul: test_beyin.py + test_dinamik.py çıkış kodu 0 (43 test). ✅

### Faz 1 — Kalibrasyon
- Her dim'in popülasyon dağılımına göre quantile/whitening normalizasyonu
  (tanh doygunluğu: 53, 80, 82 raporlanmıştı; RESH bu commit'te çözüldü)
- `cross_space.py`'deki d=0.00000 sonucunun kalibre panelde yeniden ölçümü
- Kabul: 40k popülasyonda hiçbir dim std<0.05'te yapışık değil;
  domain-aşan mesafeler doygunluk artefaktı değilse rapor, artefaktsa geri çekilir.

### Faz 2 — Yasa hiyerarşisi ✅ (`cekirdek/hiyerarsi.py`)
Körlüğün sebebi: Prony yalnız **sabit** katsayılı rekürans (C-finite) görüyordu.
Evrendeki kuralların çoğu **pozisyona bağlı** katsayılı (holonomik): n!→ s[n]=n·s[n-1],
Catalan→ (n+1)s[n]=(4n-2)s[n-1]. Merdiven: C-finite → holonomik (r,d taraması,
katsayılar lineer → SVD ile kesin) → dürüst "yasasız".
- [x] n!, Catalan holonomik order-1; Motzkin order-2; hepsi σ<1e-16
- [x] **Dürüstlük mekanizması:** son terimler saklanır (holdout); yasa onları
      GÖRMEDEN tahmin etmeli. n! → 18!'i görmeden doğru tahmin etti.
- [x] Occam: Fibonacci/2ⁿ hâlâ C-finite (basit kat kazanır)
- [x] Asallar, bölüntü sayıları, gürültü → "yasasız" (holdout reddi) — sahte yasa yok
- [x] Omurga: `kodla` seviye/holo taşıyor, `ouroboros` holonomik evreni kapatıyor
- Kapsama (9 dizi): eski avcı 3/9 → hiyerarşi 7/9. `test_hiyerarsi.py` 17/17.
- Kalan: cebirsel üreteç fonksiyonu katı + holonomik evrenlerde manipülasyon.

### Faz 3 — Faz izi (kimliğe özvektörü geri ver)
- Genotip = (yasa, seed, σ) + ilk k özvektörün kompakt izi
- Kabul: izospektral-ama-farklı test çifti panelde ayrışır.
  (AKIŞ[2] faz kayması bu fazın tohumu — özvektör zaten dinamik katta.)

### Faz 4 — Köprü ve kapı eğitimi
- Eğitim verisi bedava: çekirdek deterministik doğru cevap üretir →
  (coord, soru, kesin cevap) üçlüleri sonsuz üretilebilir
- `neural_brain.learn_step` ile köprü; gate hidden-state'ten eğitilir
- Kabul: kapı AUC>0.95 (sohbet/hesap karışımında); prompt-injection yolu
  ve regex silinir; benchmark köprü üzerinden aynı doğruluğu verir.

### Faz 5 — Dürüst benchmark
- C-finite dışı setler: asallar, Catalan, bölüntüler, kaotik seriler
- Rapor iki sütun: sistem neyi bilir + neyi bilmediğini bilir mi
- Kabul: her iddianın yanında test dosyası ve sayı.

## Bilinen borçlar (açık liste)

1. `tek_makine.py` gate = ölü kod; fiili kapı `re.findall` → Faz 4
2. Cevap yolu prompt-injection (in-process tool-call) → Faz 4
3. Benchmark yalnız C-finite sınıfını test ediyor → Faz 5
4. tanh doygunluğu (kalan dim'ler) → Faz 1
5. `README` "SHA-256" demiyor ama ana repo README'si diyor; oradaki hash djb2 → ayrı iş
6. Matris nesnelerde kayıpsız geri kurma özdeğerle imkânsız (özvektör şart) —
   README'de zaten dürüstçe yazılı; Faz 3 bunun cevabı.
