"""Kriptografik yapı okuyucu — şifrelemeyi moment uzayında "gör".

Felsefe: iyi şifreleme çıktısı gürültü gibi olmalıdır (yüksek spektral
entropi, düz spektrum, yapı sızıntısı yok). Zayıf şifreleme yapı sızdırır
ve sistem bunu SÖYLENMEDEN okur — encoder'ın spektral entropi okumasıyla
birebir aynı mekanizma, bayt verisine uygulanmış.

NE YAPAR (savunma / denetim):
  - Şifreli verinin spektral entropisini ölçer (gürültü mü, yapılı mı?)
  - ECB-tipi blok tekrarını tespit eder (ünlü "ECB penguen" zafiyeti)
  - Düz metin / zayıf şifre / güçlü şifre ayrımı yapar

NE YAPMAZ:
  - Anahtar kurtarmaz, düz metni geri getirmez, güçlü şifre kırmaz.
  Yapıyı OKUMAK ≠ belirli bir anahtarı/yolu ÜRETMEK. Bu araç zayıflık
  tespiti içindir — güçlü şifreleme bu okuyucuya gürültü olarak görünür.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tantrium.perception.encode import encode_signal

# Spektral entropi (μ₁) eşikleri — bayt sinyallerinde ampirik:
#   düz metin/yapılı:  μ₁ ≲ 0.20
#   zayıf/sızdıran:    0.20 ≲ μ₁ ≲ 0.55
#   güçlü/gürültü:     μ₁ ≳ 0.55
_STRUCTURED_MAX = 0.20
_STRONG_MIN = 0.55


# GIMEL marjin eksenleri (paradigm_margins anahtarları)
_MARGIN_KEYS = ("ALEPH", "DALET", "HE", "ZAYIN", "TAU")

# Aşil sapma eşiği — bu altında "gerçek zafiyet ekseni yok" (güçlü).
# ALEPH ekseni gürültüde doğal ~0.13 varyans gösterir; zayıf şifrelerin
# ZAYIN sızıntısı 0.6+'dır. Eşik ikisinin arasında: gürültü varyansını
# zafiyet sanmaz, gerçek sızıntıyı kaçırmaz.
_ACHILLES_MIN_DEVIATION = 0.25


@dataclass(frozen=True)
class AchillesReading:
    """GIMEL ile bulunan Aşil topuğu: yapının en zayıf/sızan ekseni."""

    name: str
    achilles_paradigm: str  # gürültüden en çok sapan paradigma
    deviation: float  # ideal gürültüden sapma miktarı
    all_deviations: dict  # her eksenin sapması
    exploitable: bool  # gerçek bir Aşil topuğu var mı?

    def summary(self) -> str:
        if not self.exploitable:
            return (
                f"«{self.name}»  AŞİL TOPUĞU YOK — gürültüden ayırt edilemiyor "
                f"(maks sapma {self.deviation:.4f} < {_ACHILLES_MIN_DEVIATION}).\n"
                f"  Güçlü: bu okuyucuya saf gürültü; sızan yapısal eksen yok."
            )
        dev = ", ".join(
            f"{k}={v:.3f}" for k, v in sorted(self.all_deviations.items(), key=lambda kv: -kv[1])
        )
        return (
            f"«{self.name}»  AŞİL TOPUĞU → {self.achilles_paradigm} "
            f"(gürültüden sapma {self.deviation:.4f})\n"
            f"  Yapı bu eksenden sızıyor. Tüm eksenler: {dev}"
        )


@dataclass(frozen=True)
class CryptoReading:
    """Bir bayt dizisinin yapısal okuması."""

    name: str
    spectral_entropy: float  # μ₁ — düşük=yapılı, yüksek=gürültü
    verdict: str  # "STRUCTURED" | "WEAK_LEAK" | "STRONG"
    repeated_blocks: int  # özdeş blok sayısı (ECB imzası)
    block_size: int
    n_bytes: int

    def summary(self) -> str:
        flag = {
            "STRUCTURED": "yapılı (şifresiz/açık yapı — okunabilir)",
            "WEAK_LEAK": "ZAYIF — şifreli ama yapı sızdırıyor",
            "STRONG": "güçlü (gürültü gibi, yapı yok)",
        }[self.verdict]
        ecb = f"  ECB blok tekrarı: {self.repeated_blocks} " + (
            "(ZAFİYET: özdeş bloklar sızıyor)" if self.repeated_blocks > 0 else "(temiz)"
        )
        return (
            f"«{self.name}»  {self.n_bytes} bayt\n"
            f"  Spektral entropi μ₁ = {self.spectral_entropy:.4f} → {flag}\n"
            f"{ecb}"
        )


def bytes_to_signal(data: bytes) -> np.ndarray:
    """Bayt dizisini sayısal sinyale çevir (her bayt bir örnek)."""
    return np.frombuffer(bytes(data), dtype=np.uint8).astype(float)


def count_repeated_blocks(data: bytes, block_size: int = 16) -> int:
    """Özdeş blok tekrarlarını say — ECB modunun doğrudan imzası.

    ECB: aynı düz-metin bloğu → aynı şifreli blok. Bu yüzden düz metindeki
    blok tekrarları şifreli çıktıda da kalır. Güçlü modlar (CTR/CBC) bunu
    sıfıra indirir. Döner: (tekrar eden blok adedi) = Σ(count−1).
    """
    b = bytes(data)
    n = len(b) // block_size
    seen: dict[bytes, int] = {}
    for i in range(n):
        blk = b[i * block_size : (i + 1) * block_size]
        seen[blk] = seen.get(blk, 0) + 1
    return sum(c - 1 for c in seen.values() if c > 1)


def analyze(data: bytes, name: str = "data", block_size: int = 16) -> CryptoReading:
    """Bayt dizisini yapısal olarak oku → CryptoReading.

    İki bağımsız sinyal birleştirilir:
      1. spektral entropi (μ₁): düz spektrum mu, yapılı mı?
      2. blok tekrarı: ECB-tipi özdeş blok sızıntısı var mı?

    Blok tekrarı varsa verdict her zaman en az WEAK_LEAK olur (ECB imzası
    entropiyi geçersiz kılar — özdeş bloklar kesin zafiyettir).
    """
    sig = bytes_to_signal(data)
    obj = encode_signal(sig, name=name)
    mu1 = float(obj.moments[1])
    rep = count_repeated_blocks(data, block_size=block_size)

    # Karar mantığı:
    #   düşük entropi  → STRUCTURED (açık yapı; düz metin ya da yapıyı tümüyle
    #                    koruyan ECB — şifreli sayılmaz, yapısı okunabilir)
    #   yüksek entropi + blok yok → STRONG (gürültü, güçlü)
    #   aradaki / blok sızan       → WEAK_LEAK (şifrelenmiş ama yapı kaçırıyor)
    # Blok tekrarı her durumda ayrı bir ZAFİYET bayrağı (repeated_blocks).
    if mu1 <= _STRUCTURED_MAX:
        verdict = "STRUCTURED"
    elif rep > 0:
        verdict = "WEAK_LEAK"
    elif mu1 >= _STRONG_MIN:
        verdict = "STRONG"
    else:
        verdict = "WEAK_LEAK"

    return CryptoReading(
        name=name,
        spectral_entropy=mu1,
        verdict=verdict,
        repeated_blocks=rep,
        block_size=block_size,
        n_bytes=len(data),
    )


def _paradigm_margins(data: bytes) -> dict:
    """GIMEL marjinlerini oku (encode_signal yapısından)."""
    obj = encode_signal(bytes_to_signal(data), name="_margins")
    return obj.structure.get("paradigm_margins", {})


def _noise_reference(n: int, trials: int = 5) -> dict:
    """İdeal gürültünün ortalama GIMEL marjinleri (referans çapa)."""
    acc: dict[str, list[float]] = {k: [] for k in _MARGIN_KEYS}
    for s in range(trials):
        rng = np.random.default_rng(10_000 + s)
        rnd = bytes(rng.integers(0, 256, size=n, dtype=np.uint8).tolist())
        m = _paradigm_margins(rnd)
        for k in _MARGIN_KEYS:
            acc[k].append(float(m.get(k, 0.0)))
    return {k: float(np.mean(v)) if v else 0.0 for k, v in acc.items()}


def achilles(data: bytes, name: str = "data") -> AchillesReading:
    """GIMEL ile Aşil topuğunu bul: yapının gürültüden en çok saptığı eksen.

    GIMEL (L5) zaten her paradigmanın "marjinini" hesaplar — ne kadar sağlam
    geçtiğini. İdeal şifreleme = gürültü; gürültünün marjin profili referanstır.
    Aşil topuğu = bu profilden EN ÇOK sapan paradigma; yapı oradan sızar.

    Güçlü şifreleme tüm eksenlerde gürültüye yakın kalır → kayda değer Aşil
    topuğu yok (exploitable=False). Zayıf şifreleme bir eksende belirgin sapar
    (tipik olarak ZAYIN — Turán/Schur pozitiflik — yapısal tutarlılık sızıntısı).

    DİKKAT: bu, zafiyetin HANGİ eksende olduğunu söyler — anahtar vermez.
    """
    ref = _noise_reference(len(data))
    m = _paradigm_margins(data)
    dev = {k: abs(float(m.get(k, 0.0)) - ref[k]) for k in _MARGIN_KEYS}
    ach = max(dev, key=lambda k: dev[k])
    return AchillesReading(
        name=name,
        achilles_paradigm=ach,
        deviation=dev[ach],
        all_deviations=dev,
        exploitable=dev[ach] >= _ACHILLES_MIN_DEVIATION,
    )
