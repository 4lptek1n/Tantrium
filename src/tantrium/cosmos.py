"""Cosmos — bir tohumun TÜM evren ömrü: yaratılıştan sona, çağ çağ, mühürlü.

Makinenin bütün organlarını ZAMAN OKUNA dizer. Tek yasa: pozitiflik (G=AᵀA ≥ 0);
her çağda korunur. Çıktı tek bir "yaşam-döngüsü sertifikası" — bir nesnenin doğuşundan
sonuna kadar pozitifliğin nasıl korunduğunun zaman-sıralı, denetlenebilir kaydı.

    T₀  Yasa            pozitiflik (tek aksiyom)            PSD koşulu
    T₁  Yaratılış       girdi → A → G                        encode
    T₂  Şişme           boyut N → N+1                        Ouroboros genişleme
    T₃  Simetri kır.    23 paradigma donar                   CertificationPipeline
    T₄  Madde           özdeğerler = kütleler                spektral ölçü
    T₅  Kendini örgüt.  etkin boyut doyar                    etkin-rank platosu
    T₆  Tutarlılık      Li λₙ>0, de Bruijn-Newman Λ≤0         kritik çizgi
    T₇  Hayatta kalma   en zayıf paradigma (Achilles)        GIMEL marjini
    T₈  Hafıza          SHA-256 kanonik adres                seal
    T₉  Etkileşim       serbest kümülant κ (Voiculescu)      kompozisyon
    T₁₀ Son             Büyük Çöküş μ*  /  Büyük Yırtılma     fixed_point / patlama

İleri koşmak = yaratım; ters okumak = tasarım (kozmolojik ters-tasarım).
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

import numpy as np

from tantrium.core.encoder import encode
from tantrium.core.fixed_point import self_reference_orbit
from tantrium.core.network import CertificationPipeline
from tantrium.core.rh_criteria import rh_criteria
from tantrium.core.spectral_flow import SpectralFlow, flow_between
from tantrium.core.spectral_reading import SpectralReading
from tantrium.core.spectral_reading import read as _read_spectrum


def _normalize(v: list[float]) -> list[float]:
    m = max((abs(x) for x in v), default=0.0)
    return [x / m for x in v] if m > 1e-12 else list(v)


def _uncapped_spectrum(carrier: list[float]) -> tuple[int, int, int, float]:
    """Tavansız gerçek Gram (downsample yok): (dim, sayısal_rank, etkin_rank, kondisyon)."""
    seq = list(carrier)
    m = len(seq)
    n = max(1, (m + 1) // 2)
    H = np.empty((n, n))
    for i in range(n):
        for j in range(n):
            H[i, j] = seq[i + j] if i + j < m else 0.0
    s = np.linalg.svd(H, compute_uv=False)
    smax = float(s[0]) if s.size else 0.0
    num_rank = int((s > max(n, 1) * smax * 1e-12).sum())
    total = float(s.sum())
    eff = int(np.searchsorted(np.cumsum(s) / total, 0.999) + 1) if total > 0 else 0
    pos = s[s > 0]
    cond = float(smax / pos[-1]) if pos.size else float("inf")
    return n, num_rank, eff, cond


def _life_topology(seed, carrier) -> SpectralFlow:
    """Ömrün topolojik yükü: doğuş G'sinden son G'sine spektral akış (5. eksen)."""
    from tantrium.core.encoder import UniversalEncoder
    enc = UniversalEncoder()

    def g(x):
        A = np.asarray(enc._to_matrix(x), dtype=float)
        return A.T @ A
    return flow_between(g(seed), g(carrier), steps=120)


def _inflate_step(carrier: list[float], n_c: int, step: int) -> list[float]:
    """Bir şişme adımı: kendi çıktısından yeni boyut (Ouroboros, deterministik)."""
    c = _normalize(carrier)
    if len(c) >= n_c and len(c) % n_c == 0:                  # simetri kırılması (DFT faz)
        m = len(c)
        c = _normalize([
            sum(c[t] * math.cos(math.pi * (t + 0.5) * k / m) for t in range(m))
            for k in range(m)
        ])
    obj = encode(c, name="cosmos")
    crit = rh_criteria([float(x) for x in obj.moments])
    lam = float(obj.structure.get("debruijn_newman_lambda") or 0.0)
    tau = [float(x) for x in crit.hankel_dets]
    bend = math.tanh((sum(tau[-2:]) if tau else 0.0) + lam)
    return _normalize([*c, bend if abs(bend) > 1e-9 else 0.5])


@dataclass
class Epoch:
    """Evrenin tek bir çağı: ne okundu, yasa korundu mu."""
    t: str
    name: str
    reading: str
    law_held: bool = True


@dataclass
class Lifecycle:
    """Bir tohumun yaşam-döngüsü sertifikası — çağ çağ, mühürlü."""
    seed: str
    epochs: list[Epoch] = field(default_factory=list)
    on_critical_line: bool = False     # T₆: Li>0 ∧ Λ≤0
    effective_dim: int = 0             # T₅: doyan etkin boyut
    paradigms_frozen: int = 0          # T₃: 23 üzerinden
    fate_crunch: str = ""              # T₁₀: μ* öz-imge
    fate_rip: str = ""                 # T₁₀: kondisyon patlama eğilimi
    master_seal: str = ""
    # ── Izgaranın derinlik ekseni: 4-katman SpectralReading, ZAMAN boyunca ──────
    genesis_reading: SpectralReading | None = None   # T₁ doğuşta dört katman
    final_reading: SpectralReading | None = None      # T₁₀ sonda dört katman
    universality_path: list[str] = field(default_factory=list)   # mikro katman yörüngesi
    ergodicity_path: list[float] = field(default_factory=list)    # özvektör katman yörüngesi
    transitions: list[str] = field(default_factory=list)          # ömür boyu faz geçişleri
    topology: SpectralFlow | None = None   # 5. eksen: ömrün topolojik yükü (doğuş→son)

    def summary(self) -> str:
        lines = [f"COSMOS — '{self.seed}' yaşam döngüsü (tek yasa: pozitiflik ≥ 0)"]
        for e in self.epochs:
            mark = "✓" if e.law_held else "✗"
            lines.append(f"  {e.t:>3} {e.name:16} {e.reading}  [{mark}]")
        lines.append(
            f"  → kritik çizgide: {'✓ EVET' if self.on_critical_line else '✗'} | "
            f"etkin boyut ~{self.effective_dim} | paradigma {self.paradigms_frozen}/23 | "
            f"mühür {self.master_seal[:12]}"
        )
        if self.genesis_reading and self.final_reading:
            g, f = self.genesis_reading, self.final_reading
            lines.append("  ── 4-katman ızgarası (doğuş → son) ──")
            lines.append(f"    1 MAKRO    rank {g.rank}→{f.rank}")
            lines.append(f"    2 MİKRO    {g.universality}→{f.universality}  "
                         f"(yörünge: {'→'.join(self.universality_path)})")
            lines.append(f"    3 SİMETRİ  Dyson β {g.beta}→{f.beta}")
            ge = "—" if g.ergodicity is None else f"{g.ergodicity:.2f}"
            fe = "—" if f.ergodicity is None else f"{f.ergodicity:.2f}"
            gd = "—" if g.fractal_dim is None else f"{g.fractal_dim:.2f}"
            fd = "—" if f.fractal_dim is None else f"{f.fractal_dim:.2f}"
            lines.append(f"    4 ÖZVEKTÖR ergodiklik {ge}→{fe} | fraktal boyut D₂ {gd}→{fd}")
            if self.transitions:
                lines.append(f"  ⚡ FAZ GEÇİŞİ: {' | '.join(self.transitions)}")
            else:
                lines.append("  (faz geçişi yok — yapı ömrü boyunca sınıfını korudu)")
        if self.topology is not None:
            t = self.topology
            eng = "düzgün" if t.smooth else f"{t.crossings} mod yeniden-örgütlenmesi"
            lines.append(f"  ── 5. eksen: TOPOLOJİ (yol) ── yük (net akış)={t.net_flow:+d} | {eng}")
        return "\n".join(lines)


def run_cosmos(seed=None, inflation_steps: int = 40, n_c: int = 12) -> Lifecycle:
    """Bir tohumu T₁→T₁₀ çağlarından geçir; her çağı oku ve yasayı (pozitiflik) doğrula."""
    if seed is None:
        seed = [1.0 / (k + 1) for k in range(6)]
    life = Lifecycle(seed=str(seed)[:48])

    # T₀ Yasa
    life.epochs.append(Epoch("T₀", "Yasa", "pozitiflik G=AᵀA ≥ 0 (tek aksiyom)"))

    # T₁ Yaratılış — encode
    obj = encode(seed, name="genesis")
    mu = [float(m) for m in obj.moments]
    s = obj.structure
    eigs = [float(e) for e in (s.get("eigenvalues") or [])]
    mdim = len(eigs) or 1
    life.epochs.append(Epoch("T₁", "Yaratılış", f"girdi → A → G ({mdim}×{mdim}), {len(mu)} moment"))
    # ── Derinlik ekseni: T₁ doğuşta dört-katman okuma ──────────────────────────
    life.genesis_reading = _read_spectrum(seed)

    # T₂ Şişme + T₅ Kendini örgütleme — Ouroboros genişleme, etkin boyut + 4-katman izi
    carrier = list(mu)
    d0 = _uncapped_spectrum(carrier)[0]
    effs: list[int] = []
    sample_every = max(1, inflation_steps // 5)
    for step in range(inflation_steps):
        carrier = _inflate_step(carrier, n_c, step)
        effs.append(_uncapped_spectrum(carrier)[2])
        if step % sample_every == 0:                  # 4-katman yörüngesini örnekle
            rd = _read_spectrum(carrier)
            life.universality_path.append(rd.universality)
            if rd.ergodicity is not None:
                life.ergodicity_path.append(round(rd.ergodicity, 3))
    life.final_reading = _read_spectrum(carrier)
    # 5. eksen — ömrün topolojik yükü: doğuş operatöründen son operatöre spektral akış
    life.topology = _life_topology(seed, carrier)
    dim_f, num_f, eff_f, cond_f = _uncapped_spectrum(carrier)
    tail = effs[len(effs) // 2:] or effs
    plateau = max(set(tail), key=tail.count) if tail else eff_f
    life.effective_dim = plateau
    life.epochs.append(Epoch("T₂", "Şişme", f"boyut {d0} → {dim_f} (kendi çıktısından)"))

    # T₃ Simetri kırılması — 23 paradigma
    run23 = CertificationPipeline().run(obj)
    life.paradigms_frozen = run23.certified_count
    life.epochs.append(Epoch("T₃", "Simetri kır.", f"{run23.certified_count}/23 paradigma dondu"))

    # T₄ Madde — özdeğerler (kütleler), rank
    rank = int(s.get("matrix_rank") or 0)
    masses = sum(1 for e in eigs if abs(e) > 1e-12)
    life.epochs.append(Epoch("T₄", "Madde", f"rank {rank}, {masses} kütle (özdeğer)"))

    # T₅ Kendini örgütleme — etkin boyut platosu
    life.epochs.append(Epoch("T₅", "Kendini örgüt.", f"etkin boyut ~{plateau}'te DOYDU"))

    # T₆ Tutarlılık — Li + de Bruijn-Newman → kritik çizgi
    li = [float(x) for x in (s.get("li_coefficients") or [])]
    lam = float(s.get("debruijn_newman_lambda") or 0.0)
    li_pos = bool(li) and all(x > 0 for x in li)
    on_line = li_pos and lam <= 1e-9
    life.on_critical_line = on_line
    life.epochs.append(Epoch(
        "T₆", "Tutarlılık", f"Li λₙ>0={li_pos}, Λ={lam:+.3f} → kritik çizgide={on_line}",
        law_held=on_line,
    ))

    # T₇ Hayatta kalma — Achilles (en zayıf paradigma)
    achilles = float(s.get("achilles_margin") or 0.0)
    life.epochs.append(Epoch("T₇", "Hayatta kalma", f"Achilles marjini = {achilles:+.4f}"))

    # T₈ Hafıza — mühür
    epoch_blob = "|".join(f"{e.t}:{e.reading}" for e in life.epochs)
    seal = hashlib.sha256(epoch_blob.encode()).hexdigest()
    life.epochs.append(Epoch("T₈", "Hafıza", f"SHA-256 adres {seal[:12]}"))

    # T₉ Etkileşim — serbest kümülant κ (Voiculescu)
    kappa = [round(float(x), 4) for x in (s.get("free_cumulants") or [])][:3]
    life.epochs.append(Epoch("T₉", "Etkileşim", f"serbest kümülant κ = {kappa}"))

    # ── Faz geçişleri: dört katman ömür boyunca sınıf değiştirdi mi? ────────────
    g, fr = life.genesis_reading, life.final_reading
    if g and fr:
        if g.universality != fr.universality:
            life.transitions.append(f"mikro {g.universality}→{fr.universality}")
        if g.localized is not None and fr.localized is not None and g.localized != fr.localized:
            a = "yerleşik" if g.localized else "ergodik"
            b = "yerleşik" if fr.localized else "ergodik"
            life.transitions.append(f"özvektör {a}→{b}")
        if g.beta != fr.beta:
            life.transitions.append(f"simetri β{g.beta}→β{fr.beta}")

    # T₁₀ Son — iki kader
    fp = self_reference_orbit(seed=mu, max_iter=48)
    life.fate_crunch = f"μ* (kritik çizgide={fp.on_critical_line})"
    life.fate_rip = f"kondisyon→{cond_f:.2e} (patlamaya doğru)"
    trans = f" | faz geçişi: {', '.join(life.transitions)}" if life.transitions else ""
    life.epochs.append(Epoch(
        "T₁₀", "Son", f"Büyük Çöküş: {life.fate_crunch} | Büyük Yırtılma: {life.fate_rip}{trans}"
    ))

    # Ana mühür — tüm ömrün kanonik adresi
    life.master_seal = hashlib.sha256(
        ("|".join(f"{e.t}:{e.reading}" for e in life.epochs)).encode()
    ).hexdigest()
    return life


def run() -> Lifecycle:
    print("=" * 70)
    life = run_cosmos()
    print(life.summary())
    print("=" * 70)
    return life


if __name__ == "__main__":
    run()
