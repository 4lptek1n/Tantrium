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

## Organlar (hedef durum)

| # | Organ | Bugünkü durum | Hedef |
|---|-------|----------------|-------|
| 1 | **Yasa avcısı** | Prony (yalnız C-finite) | Hiyerarşi: C-finite → holonomik/P-recursive → rasyonel ÜF → dürüst "yasasız" damgası |
| 2 | **Kanonik kimlik** | (yasa, seed, σ) | + faz izi (özvektör izi) — izospektral çakışmaları ayırır |
| 3 | **coord_91 paneli** | Statik kat dolu; dinamik kat DOLDU (bu commit) | Popülasyon kalibrasyonlu (doygunluk yok) |
| 4 | **Büyük beyin** | 40k–100k nesne, pickle | Kanonik genotip indeksli, domain-aşan sorgu |
| 5 | **Köprü** | `neural_brain.py` yazılı, eğitilmemiş | coord→düşünce-token, LoRA ile eğitilmiş |
| 6 | **Kapı** | `nn.Linear` ölü kod; fiili kapı regex | Hidden-state'ten eğitilmiş; regex silinir |
| 7 | **Ağız (LLM)** | Prompt-injection ile besleniyor | Yalnız köprü üzerinden beslenir |

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

### Faz 0 — Dinamik kat + dürüstlük (BU COMMIT)
- [x] NEWTON, Q, AKIŞ, RESH gerçek matematikle doldu
- [x] 19 yanlışlanabilir test yeşil (`python3 test_dinamik.py`)
- [x] README fiili durumu anlatıyor (regex kapı, C-finite kapsam)
- Kabul: test_dinamik.py çıkış kodu 0. ✅

### Faz 1 — Kalibrasyon
- Her dim'in popülasyon dağılımına göre quantile/whitening normalizasyonu
  (tanh doygunluğu: 53, 80, 82 raporlanmıştı; RESH bu commit'te çözüldü)
- `cross_space.py`'deki d=0.00000 sonucunun kalibre panelde yeniden ölçümü
- Kabul: 40k popülasyonda hiçbir dim std<0.05'te yapışık değil;
  domain-aşan mesafeler doygunluk artefaktı değilse rapor, artefaktsa geri çekilir.

### Faz 2 — Yasa hiyerarşisi
- Prony üstüne P-recursive/holonomik uydurucu (katsayılar n'e bağlı:
  faktöriyel, Catalan, çoğu OEIS buraya düşer), üstüne rasyonel üreteç fonksiyonu
- Kabul: Catalan ve n! holonomik katta σ<1e-8; asallar tüm katlarda
  "yasasız" damgası yer — ve bu benchmark'ta **başarı** olarak raporlanır.

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
