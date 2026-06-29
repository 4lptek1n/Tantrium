"""Relation — iki operatör arası TAM ilişki (mimarinin İLİŞKİ ekseni, tek nesne).

Makinenin üç ekseni var: TEK OPERATÖR (bir girdiyi oku → SpectralReading), İLİŞKİ (iki
girdiyi bağla → bu), EVRİM (bir girdiyi zamanda akıt → Cosmos). İlişki ekseni eskiden iki
ayrı modülde dağınıktı:

  • interaction.py  → KUVVET + HAYAT  (ortak uzayda H=M†M; köşegen-dışı kuplaj + dolanıklık)
  • spectral_flow.py → TOPOLOJİ        (G_A→G_B yolunun net özdeğer geçişi; topolojik yük)

İki operatör arası ilişkinin TAM yüzü ikisinin birlikteliğidir: ne kadar bağlılar (kuvvet),
ayrılamaz mı korele (hayat), ve dönüşüm yolu topolojik olarak engelli mi (topoloji). Relation
bunları tek nesnede toplar — yeni matematik değil, ilişki ekseninin çatısı. Universe.couple
bunu döndürür (evrenin 4 KUVVET + 5 HAYAT + 7 TOPOLOJİ yüzü, tek ilişkide).
"""
from __future__ import annotations

from dataclasses import dataclass

from tantrium.core.interaction import Interaction, interact
from tantrium.core.spectral_flow import SpectralFlow, spectral_flow


@dataclass
class Relation:
    """İki operatör arası tam ilişki: kuvvet + hayat (interaction) + topoloji (flow)."""
    interaction: Interaction       # 4 KUVVET + 5 HAYAT (kuplaj + dolanıklık + hibridleşme)
    flow: SpectralFlow             # 7 TOPOLOJİ (dönüşüm yolunun net özdeğer geçişi)

    # ── ilişki ekseninin doğrudan okumaları (interaction'a yönlendirme) ──
    @property
    def coupling(self) -> float:
        return self.interaction.coupling

    @property
    def entanglement(self) -> float:
        return self.interaction.entanglement

    @property
    def entangled(self) -> bool:
        return self.interaction.entangled

    @property
    def topological(self) -> bool:
        """Dönüşüm yolu topolojik olarak engelli mi (modlar yeniden örgütleniyor mu)."""
        return not self.flow.smooth

    def summary(self) -> str:
        it, fl = self.interaction, self.flow
        topo = ("düzgün (topolojik engel YOK)" if fl.smooth
                else f"{fl.crossings} mod yeniden-örgütlenmesi (yük {fl.net_flow:+d})")
        return (
            f"Relation — iki operatör arası tam ilişki:\n"
            f"  KUVVET     kuplaj={it.coupling:.3f} | hibridleşme={it.hybridization:.4f}\n"
            f"  HAYAT      dolanıklık S={it.entanglement:.4f} "
            f"({'DOLANIK' if it.entangled else 'ayrık'})\n"
            f"  TOPOLOJİ   {topo}"
        )


def relate(a, b, steps: int = 400) -> Relation:
    """İki girdi arası tam ilişkiyi kur: kuvvet + hayat + topoloji (tek nesne).

    interact(a,b) ile kuvvet/dolanıklık, spectral_flow(a,b) ile dönüşüm yolunun
    topolojik yükü — ilişki ekseninin iki yarısı tek Relation'da birleşir."""
    return Relation(interaction=interact(a, b), flow=spectral_flow(a, b, steps=steps))
