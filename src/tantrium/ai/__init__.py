"""Tantrium AI — Native SDK.

Kullanım:
    import tantrium
    ai = tantrium.AI()

    # Herhangi bir şeyi certify et
    r = ai.ask("EGFR nedir?")
    print(r.answer, r.certified)

    # Molekül certify
    r = ai.certify("Erlotinib", smiles="COCCOC1=CC2=...")
    print(r.certified, r.dyadic_score, r.sdf)

    # De novo molekül üret
    r = ai.discover("EGFR")
    print(r.smiles, r.sdf, r.score)

    # Ham veriden yasa keşfi (domain-kör)
    law = ai.discover_law([1, 1, 2, 3, 5, 8, 13, 21])
    print(law.summary())

    # Sertifikalı transport
    t = ai.transport("CCO", "CC(=O)O")
    print(t.certified)

    # Durum
    print(ai.status())

Yalın saf-matematik yüzeyi: dil/öğrenme/graf katmanları yoktur; yalnız
spektral moment → 23-paradigma sertifika → transport / rekonstrüksiyon /
yasa keşfi / moleküler üretim.

Bu paket mixin'lere bölünmüştür; tek dış-yüzey `AI` sınıfı ve result
dataclass'ları geriye dönük uyumlu olarak buradan dışa verilir.
"""
from __future__ import annotations

from ._base import _AIBase
from ._certify import CertifyMixin
from ._dynamics import DynamicsMixin
from ._molecular import MolecularMixin
from ._results import (
    AskResult,
    CompositeSignature,
    DesignResult,
    DiscoverResult,
    GenResult,
    GroundingSignature,
    LawDiscovery,
    MolResult,
    ReasonResult,
    UniverseReconstruction,
)
from ._rh import RHMixin

# ─── Ana AI sınıfı ───────────────────────────────────────────────────────────

class AI(CertifyMixin, RHMixin, DynamicsMixin, MolecularMixin, _AIBase):
    """Tantrium — Native SDK (durumsuz saf matematik).

    Her metot Aleph sertifikalı çıktı döndürür.
    Hiçbir şey tahmin değil, türetim.

    Örnek:
        ai = tantrum.AI()
        print(ai.ask("EGFR inhibitor"))
        print(ai.discover("EGFR"))

    Yüzey mixin'lere bölünmüştür (CertifyMixin / RHMixin / DynamicsMixin /
    MolecularMixin); kurulum + paylaşılan yardımcılar `_AIBase`'tedir. MRO bu
    sırayı korur — `_AIBase` en sonda taban olarak gelir.
    """


__all__ = [
    "AI",
    "AskResult",
    "MolResult",
    "GenResult",
    "ReasonResult",
    "DiscoverResult",
    "DesignResult",
    "CompositeSignature",
    "GroundingSignature",
    "UniverseReconstruction",
    "LawDiscovery",
]
