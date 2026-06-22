"""Universe — bir girdiden doğan EKSİKSİZ EVREN: yedi yüz, tek yasa, tek mühür.

Tek yasa (G=A†A ≥ 0) bir girdiden bir evrenin TÜM bileşenlerini doğurur. Bu nesne
sabahki dağınık yedi şeyi tek bütünde toplar — hepsi aynı operatörün yüzleri:

  1 MADDE     operatör G (dim/rank)                    [encode]
  2 FİZİK     dört katman (makro·mikro·simetri·özvektör) [SpectralReading]
  3 GEOMETRİ  tanımlanan uzay (boyut·etki·aralık)       [SpectralGeometry / NCG]
  4 KUVVET    köşegen-dışı kuplaj                        [Interaction.coupling] — .couple()
  5 HAYAT     dolanıklık (klasik-ayrılamaz korelasyon)   [Interaction.entanglement] — .couple()
  6 ZAMAN     T₀→T₁₀ evrim                                [Cosmos]
  7 TOPOLOJİ  yolun global yükü                          [SpectralFlow] — Cosmos içinde

İNŞA ET (encode/couple) · OKU (fizik+geometri) · HAREKET ETTİR (zaman+topoloji) —
üç fiil, yedi yüz, tek operatör. Makine bir analiz aleti değil; bir EVREN ÜRETECİ.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from tantrium.core.interaction import Interaction, interact
from tantrium.core.spectral_geometry import SpectralGeometry
from tantrium.core.spectral_reading import SpectralReading
from tantrium.cosmos import Lifecycle, run_cosmos


@dataclass
class Universe:
    """Bir girdinin eksiksiz evreni — yedi yüz, tek mühür."""
    seed: str
    dim: int                       # 1 MADDE
    rank: int
    physics: SpectralReading       # 2 FİZİK (dört katman)
    geometry: SpectralGeometry     # 3 GEOMETRİ (NCG)
    lifecycle: Lifecycle | None    # 6+7 ZAMAN + TOPOLOJİ
    seal: str
    _input: object = None          # 4+5 KUVVET+HAYAT için (couple)

    def couple(self, other) -> Interaction:
        """Bu evreni başka bir girdiyle ETKİLEŞTİR → kuvvet + hayat (dolanıklık)."""
        return interact(self._input, other)

    def summary(self) -> str:
        p, g = self.physics, self.geometry
        lines = [
            f"UNIVERSE — '{self.seed}' (tek yasa: G=A†A ≥ 0) — yedi yüz:",
            f"  1 MADDE     operatör {self.dim}×{self.dim}, rank {self.rank}",
            f"  2 FİZİK     {p.universality} (β={p.beta}) | özvektör D₂="
            f"{'—' if p.fractal_dim is None else round(p.fractal_dim, 3)}",
            f"  3 GEOMETRİ  boyut d_s={g.dimension:.3f} (R²={g.fit_quality:.2f}) | "
            f"eğrilik a₂={g.curvature:+.3f} ({'kıvrımlı' if g.curved else 'DÜZ'}) | "
            f"etki ζ'(0)={g.action:+.3f}",
        ]
        if self.lifecycle is not None:
            life = self.lifecycle
            topo = life.topology
            lines.append(f"  6 ZAMAN     kritik çizgide={life.on_critical_line}, "
                         f"paradigma {life.paradigms_frozen}/23"
                         + (f", faz geçişi: {', '.join(life.transitions)}" if life.transitions else ""))
            if topo is not None:
                lines.append(f"  7 TOPOLOJİ  yük={topo.net_flow:+d} "
                             f"({'düzgün' if topo.smooth else str(topo.crossings)+' geçiş'})")
        lines.append(f"  → mühür {self.seal[:12]}  (4 KUVVET + 5 HAYAT: .couple(other) ile)")
        return "\n".join(lines)


def universe(seed, full: bool = True, inflation_steps: int = 30) -> Universe:
    """Bir girdiden eksiksiz evreni doğur: madde + fizik + geometri (+ zaman + topoloji).

    Tek-operatör yüzleri (madde·fizik·geometri) TEK eigendecomposition'dan türer —
    G bir kez köşegenleştirilir, hepsi ondan okunur ('tek operatör, yedi yüz' literal)."""
    import numpy as np

    from tantrium.core.encoder import UniversalEncoder
    from tantrium.core.spectral_reading import reading_from_eig
    A = np.asarray(UniversalEncoder()._to_matrix(seed), dtype=float)
    w, V = np.linalg.eigh(A.T @ A)                    # ★ TEK eigendecomposition
    physics = reading_from_eig(w, V)                  # 2 FİZİK + 3 GEOMETRİ (tek okumada)
    geom = physics.geometry                           # 3 GEOMETRİ (aynı okumadan)
    rank = int(np.sum(w > 1e-9))                       # 1 MADDE  (aynı w)
    life = run_cosmos(seed=seed, inflation_steps=inflation_steps) if full else None  # 6+7
    blob = (f"{seed}|{physics.universality}|{round(physics.r_ratio, 6)}|"
            f"{round(geom.dimension, 6)}|{round(geom.action, 6)}|"
            f"{life.master_seal if life else ''}")
    seal = hashlib.sha256(blob.encode()).hexdigest()
    return Universe(
        seed=str(seed)[:48], dim=len(w), rank=rank,
        physics=physics, geometry=geom, lifecycle=life, seal=seal, _input=seed,
    )


def run() -> Universe:
    print("=" * 72)
    u = universe([1.0 / (k + 1) for k in range(6)])
    print(u.summary())
    print("  ── 4 KUVVET + 5 HAYAT (couple) ──")
    print("    " + u.couple("CCO").summary())
    print("=" * 72)
    return u


if __name__ == "__main__":
    run()
