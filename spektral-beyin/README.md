# İki Katmanlı Beyin — Spektral Arka Beyin + LLM Ön Beyin

Tek makine: dil ve kesin matematik aynı gövdede. LLM (ön beyin) konuşur;
saf matematik bölgesi (arka beyin) LLM'in forward-pass'inin **içinde** çalışır.
Hiçbir dış araç/sandbox yok — matematik native, kapı anlamadan açılır.

## Mimari

```
KELIME (input)
   │
   ▼
ON BEYIN (LLM — degistirilebilir: Gemma 4 / Qwen / Llama...)
   │   forward-pass icinde:
   ├─► KAPI: hesap gerekiyor mu? (anlamadan, hidden-state'ten — router YOK)
   │
   ▼ (kapi acilirsa)
ARKA BEYIN (saf matematik, LLM'in ICINDE bir bolge)
   │   operator (A) ──► G=AᵀA ──► OZDEGER ──► coord_91 (91 dim)
   │   ham dizi ──► YASA (Prony) + SEED (kokler) + σ  = kanonik kimlik
   │
   ├─ SIKISTIR: dizi -> yasa+seed (calistirilabilir tohum, kayipsiz)
   ├─ AC/GENISLET: yasa+seed -> diziyi geri kur + otesini uret (simulasyon)
   │
   ├─ 91 dim ROLLERI:
   │     • 4 KOPRU dim    -> dil ile arka beyni baglar (on beyne acik)
   │     • BAG VEREN dim  -> arka beyinde dallanir (kelimeye kapali, ic bag)
   │     • UYUYAN dim     -> tool/skill gibi, cagri uzerine acilir (uzay/design)
   │
   ▼
ON BEYIN kesin gercekleri DILE doker -> CEVAP
```

Kimlik = **operator + ozdeger + seed + yasa** (coord_91 kimlik DEGIL, bag/cache).

## Model Degistirme (hepsi LLM, hepsine takilir)

`tek_makine.py` icinde tek satir:
```python
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"   # simdiki (kucuk, 3GB RAM)
# Gemma 4 (daha iyi konusur, ~5GB+ RAM gerekir):
# MODEL_ID = "google/gemma-4-e2b-it"      # en kucuk
# MODEL_ID = "google/gemma-4-12B-it"      # 16GB RAM
# MODEL_ID = "google/gemma-4-31B-it"      # GPU
```
Arka beyin / native bolge / koprular model-bagimsiz. Sadece MODEL_ID degisir.

## Kurulum (kod hafif, veri kodla uretilir)
```bash
pip install -r requirements.txt
python hazirla.py      # OEIS corpus indirir + 40k beyni kurar (ilk sefer, internet gerekir)
python tek_makine.py   # tek makineyi calistir
```
Not: agir veri (corpus 32MB, beyin 33MB) pakete KONMADI. hazirla.py onlari kodla uretir.


## Dosyalar
```
tek_makine.py            ANA — tek makine (LLM + native matematik bolgesi + buyuk beyin)
cekirdek/
  coord91.py             91-dim yasa-dedektoru (TANTRIUM matematigi) -> coord_91(lam)=(v,q)
  engine.py              gram_spectrum (G=AᵀA), prony_law
  domains.py             domain adaptorleri (math/dna/molecule/finance/material) + genotype()
  olcek_pipeline.py      OLCEK: batch_eigenvalues (GPU: device='cuda'), canonical_genotype, reconstruct
  neural_brain.py        CoreProjector + LoRA (opsiyonel derin entegrasyon)
  organism.py            surpriz-tetikli canli ogrenme
beyin/
  buyuk_beyin.pkl        40k gercek nesne (OEIS + PubChem): C91, Lam, beta, rank, names, doms
  scale100k.npz          100k gercek nesnenin ozdeger + seed'i
  canon20k.npz           20k gercek nesnenin tam kanonik genotipi
  uctan_uca.pkl          21-nesnelik egitilmis kopru (referans)
veri/
  stripped.gz            OEIS tum corpus (353k+ dizi) — tek dosya, offline
```

## Kanitlananlar
- Cekirdek 7/7 gercek sabiti buldu (φ=1.618, gumus=2.414, plastik=1.325...) σ≈1e-16
- Ozdeger hizi: 430.000 nesne/sn (batch tensor)
- 100.000 gercek nesne islendi (50k OEIS + 50k PubChem bulk akis)
- Kayipsiz sikistir/ac: yasa+seed -> dizi geri kur (1e-13) + otesini uret
- Domain-asan bag: matematik dizisi ~ molekul AYNI Λ enerjisinde (d=0.00000)
- Tek makine: sohbette matematik uyur (g≈0.0), hesapta acilir (g≈0.2)

## Olcek (kendi makinende sinirsiz)
`cekirdek/olcek_pipeline.py`:
```python
from olcek_pipeline import batch_eigenvalues, canonical_genotype, reconstruct
lam = batch_eigenvalues(seqs, device='cuda')   # GPU'da 1M+ nesne dakikalar
```
Veri: OEIS (veri/stripped.gz), PubChem CID-SMILES.gz (bulk akis), Materials Project.

## Sinirlar (durust)
- coord_91'in bazi paradigma dim'leri doygunlukta (53,80,82) — normalize gerekir
- Qwen-0.5B zayif konusur; Gemma 4 ile akici olur (RAM/GPU ister)
- Bir MATRIS icin kayipsiz geri kurma ozdeger DEGIL, tam operator (ozvektor) ister
  (dizi 1-boyut oldugu icin seed yetiyor; matris 2-boyut, yon sart)
