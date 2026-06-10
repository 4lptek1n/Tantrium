"""Tantrium Algı Katmanı — duyusal grounding.

Dil katmanı kavramları yapısal olarak okur ama fiziksel gerçekliğe bağlı
değildir ("elma" kelimesinin tadını bilmez). Bu modül o boşluğu kapatır:
ham duyusal sinyali — ses dalgası, görüntü piksel ızgarası, herhangi bir
ölçüm zaman serisi — AYNI moment uzayına çeker.

Matematiksel temel (encoder.py ile birebir aynı dil):

  SES / zaman serisi:
    Bir durağan sinyalin otokorelasyon dizisi R[k], güç spektral
    yoğunluğunun (PSD ≥ 0) moment dizisidir (Wiener–Khinchin + Bochner).
    R'den kurulan Toeplitz matrisi her zaman PSD'dir → geçerli moment
    dizisi → Aleph geçer. Yani ses ZATEN moment uzayına aittir; bu
    Hamburger teoreminin sinyal versiyonudur.

  GÖRÜNTÜ:
    Piksel ızgarası P doğrudan bir matristir. G = PᵀP daima PSD'dir,
    spektral momentleri görüntünün tekil-değer dağılımıdır — dokunun,
    tekrarın, yapının domain-blind imzası.

Her iki modalite de tek bir evrensel adıma indirgenir:
    ham sinyal → negatif-olmayan matris A → G=AᵀA → μ_k → CodexObject
Encoder yeni bir katman eklemez — mevcut katmanı duyusal veriye uygular.

Kullanım:
    from tantrium.perception import encode_signal, encode_image
    obj = encode_signal(samples, name="440hz_tone")
    run = engine.process(obj)            # 23 paradigma
"""
from __future__ import annotations

from tantrium.perception.encode import (
    encode_image,
    encode_matrix,
    encode_signal,
    encode_signal_temporal,
    signal_autocorrelation,
)
from tantrium.perception.generate import (
    chord,
    checkerboard_image,
    concentric_image,
    gradient_image,
    noise_image,
    solid_image,
    stripes_image,
    tone,
    white_noise,
)
from tantrium.perception.crypto import (
    analyze,
    achilles,
    bytes_to_signal,
    count_repeated_blocks,
    CryptoReading,
    AchillesReading,
)

__all__ = [
    "encode_signal",
    "encode_signal_temporal",
    "encode_image",
    "encode_matrix",
    "signal_autocorrelation",
    "tone",
    "chord",
    "white_noise",
    "solid_image",
    "gradient_image",
    "stripes_image",
    "concentric_image",
    "checkerboard_image",
    "noise_image",
    # Kriptografik yapı okuyucu (savunma / zafiyet tespiti)
    "analyze",
    "achilles",
    "bytes_to_signal",
    "count_repeated_blocks",
    "CryptoReading",
    "AchillesReading",
]
