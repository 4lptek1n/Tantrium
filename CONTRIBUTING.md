# Katkı Rehberi

Tantrium — durumsuz, saf-matematik yapısal sertifikasyon makinesi.

## Kurulum

```bash
pip install -e ".[dev,server]"     # + chem için: pip install rdkit
```

## Geliştirme döngüsü

```bash
pytest -q                          # tüm testler (~290)
ruff check src tests               # lint (0 hata olmalı)
ruff check src tests --fix         # otomatik düzelt
python -c "import tantrium; print(tantrium.AI().certify_all('EGFR'))"   # smoke
```

## Değişmez ilkeler

1. **Durumsuz, saf matematik.** Dil / öğrenme / manifold / graf / ajans YOK. `truth`/`grounding`
   eksenleri öğrenilen komşuya muhtaçtı → N/A. Bunları "bozuk" sanıp geri ekleme.
2. **Exact `Fraction` aritmetiği.** Sertifikalar bit-bit tekrarlanabilir olmalı — float'a düşme.
3. **`from tantrium import ...` düz.** `from tantrium.agi import ...` → YOK.
4. **Public API'yi koru.** Modülleri pakete bölerken `__init__.py` tüm public sembolleri
   `__all__` ile re-export etmeli; `from tantrium.core.X import Y` kırılmamalı.
5. **8 moment + RH-kriter omurgası.** Yeni yetenekler `rh_certificate` bundle'ına ve
   sertifikasyon akışına bağlanır — yan/izole metot değil.
6. **Dosya başına ≤ 500 satır.** Büyüyen modül aynı-isimli pakete bölünür.

## Mimari

```
encoder → moment + structure["rh"]  →  CoreMachine (23 paradigma + RH bundle + mühür)
                                    →  CertifiedTransport (dyadic + Sturm + Zeta)
```

Detay: `ARCHITECTURE.md`, `MATHEMATICS.md`, `CLAUDE.md`.

## Test ve lint zorunlu

PR'lar CI'dan geçmeli: `ruff check` temiz + `pytest` yeşil (Python 3.10–3.12).
