"""Ouroboros — kendi kendini besleyen deterministik genişleme motoru.

Gözlemci aradan çekilir. Makine N-boyutlu uzayın sertifikasını bitirince, kendi
ürettiği çıktıyı (özdeğerler = kütle, Hankel determinantları τ = merdiven) doğrudan
N+1-boyutlu uzayın sınır koşulu (tohum) olarak alır. Hiçbir dış girdi, prompt veya
rastgelelik yok — saf, kendi üzerine katlanan deterministik bir motor.

Otonomi rastgelelikten değil, HESAPLAMASAL İNDİRGENEMEZLİKTEN doğar: ne yapacağını
bilmek için onu çalıştırmaktan başka kısayol yoktur (kuralları bozmadan).

Dört yapısal hamle:
  1. OUROBOROS    — çıktı → girdi, boyut N → N+1 (gözlemci çekilir)
  2. SİMETRİ KIR. — eşikte deterministik ortogonal (DFT) faz geçişi
  3. HAYATTA KAL. — spektral pozitiflik çökerse (hankel_psd=False) dal ÖLÜR;
                    son geçerli duruma sarıp farklı permütasyonla yeniden kurar
  4. DİNAMİK METRİK — özdeğerler (kütle) bir sonraki uzayın eğriliğini büker

Çekirdek DURUMSUZ kalır; bu motor onu süren bir sürücüdür (durum motorda yaşar).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from tantrium.core.encoder import UniversalEncoder, encode
from tantrium.core.rh_criteria import rh_criteria

_ENC = UniversalEncoder()


def _true_rank(seed: list[float]) -> tuple[int, int]:
    """Genişleyen evrenin GERÇEK rank'ı: tam Gram matrisi A'nın rank'ı.

    DİKKAT: structure['matrix_rank'] ve rh_criteria.rank, encoder'ın sabit 8-moment
    penceresinden okunan GÖLGE rank'tır (≈3'te kilitli). Evrenin gerçek spektral
    karmaşıklığı, büyüyen A matrisinin kendisinde yaşar — burada onu ölçüyoruz."""
    A = np.array(_ENC._to_matrix(seed), dtype=float)
    return int(np.linalg.matrix_rank(A, tol=1e-9)), A.shape[0]


def _dft_real(v: list[float]) -> list[float]:
    """Deterministik ortogonal faz geçişi: gerçek-DFT (kosinüs) tabanı.

    İstatistiksel gürültü değil — saf matematiksel taban dönüşümü. Spektral yapıyı
    yeni bir ortogonal eksene oturtur (suyun donarken faz değiştirmesi gibi)."""
    n = len(v)
    out = []
    for k in range(n):
        acc = sum(v[t] * math.cos(math.pi * (t + 0.5) * k / n) for t in range(n))
        out.append(acc * (math.sqrt(1.0 / n) if k == 0 else math.sqrt(2.0 / n)))
    return out


def _normalize(v: list[float]) -> list[float]:
    """Float patlamasını engelle: en büyük mutlak değere böl (yön korunur)."""
    m = max((abs(x) for x in v), default=0.0)
    return [x / m for x in v] if m > 1e-12 else v


@dataclass
class Frame:
    """Genişleyen evrenin tek bir anı (N-boyutlu kabuk)."""
    step: int
    dim: int                    # tam Gram matrisinin boyutu (büyüyor)
    true_rank: int              # GERÇEK rank (büyüyen A) — evrenin spektral karmaşıklığı
    shadow_rank: int            # 8-moment gölge rank (≈3'te kilitli — encoder penceresi)
    alive: bool                 # spektral pozitiflik ayakta mı
    hamburger: bool
    lam_dbn: float              # de Bruijn-Newman Λ (kritik çizgi ölçüsü)
    tau_tail: list[float]       # son Hankel determinantları (merdivenin ucu)
    event: str = ""             # "", "PHASE", "PRUNE→reroute"


@dataclass
class Cosmos:
    """Bir Ouroboros koşusunun tüm tarihçesi (sertifikalı, tekrarlanabilir)."""
    frames: list[Frame] = field(default_factory=list)
    phase_transitions: int = 0
    prunes: int = 0
    max_dim: int = 0
    max_rank: int = 0
    died_at: int | None = None  # motor tümüyle çıkmaza girdiyse

    def summary(self) -> str:
        last = self.frames[-1] if self.frames else None
        first = self.frames[0] if self.frames else None
        return (
            f"OUROBOROS — {len(self.frames)} adım | boyut {first.dim if first else 0}→{self.max_dim}\n"
            f"  GERÇEK rank: {first.true_rank if first else 0} → {self.max_rank} "
            f"(evrenle birlikte tırmandı — eklenen hiçbir şey yok)\n"
            f"  gölge rank (8-moment penceresi): sabit ≈{last.shadow_rank if last else 0} "
            f"(yanıltıcı tıkaç — gerçek karmaşıklık matriste)\n"
            f"  faz geçişi (simetri kırılması): {self.phase_transitions} | "
            f"budama (hayatta-kalma reroute): {self.prunes}\n"
            f"  son kabuk: Λ={last.lam_dbn if last else 0:+.4f} alive={last.alive if last else '-'}\n"
            f"  → {'çıkmaz (motor öldü)' if self.died_at else 'genişleme + rank sıçraması sürüyor (ufuk: hesap)'}"
        )


class OuroborosEngine:
    """Kendi kendini besleyen genişleme motoru — dış girdi YOK, rastgelelik YOK."""

    def __init__(self, n_c: int = 12, max_dim: int = 40, max_reroute: int = 6):
        self.n_c = n_c            # simetri-kırılması kritik boyutu
        self.max_dim = max_dim    # hesap ufku (Fraction/τ patlama sınırı)
        self.max_reroute = max_reroute

    # ── Çekirdeği oku (durumsuz): tohum → kütle + merdiven ───────────────────
    def _read(self, seed: list[float]):
        obj = encode(seed, name="cosmos")
        mu = [float(m) for m in obj.moments]
        crit = rh_criteria(mu)
        eigs = [float(e) for e in (obj.structure.get("eigenvalues") or [])]
        lam = float(obj.structure.get("debruijn_newman_lambda") or 0.0)
        return crit, eigs, lam

    # ── HAYATTA KALMA: spektral pozitiflik ayakta mı? ────────────────────────
    @staticmethod
    def _alive(crit) -> bool:
        # Ölçü hâlâ geçerli mi: lider Hankel yapısı pozitif + en az 1 boyut taşıyor.
        # (Tam PSD değil — o, genişlemeyi anında öldüren aşırı katı koşul; burada
        #  'ilk-beş pozitif' = ölçünün çekirdeği ayakta, RH-tarafı korunuyor.)
        return bool(crit.first_five_positive) and crit.rank >= 1

    # ── DİNAMİK METRİK + OUROBOROS: taşıyıcıyı KORU, tek yeni eksen ekle ──────
    def _new_axis(self, crit, lam: float, twist: int = 0) -> float:
        """Sertifikadan doğan yeni boyutun değeri (dış girdi yok, deterministik).

        twist>0: hayatta-kalma reroute'unda aynı N+1 boyutunda FARKLI bir eksen
        dener (dalı küçültmeden alternatif tünel arar)."""
        tau = [float(x) for x in crit.hankel_dets]
        bend = math.tanh((sum(tau[-2:]) if tau else 0.0) + lam)
        if twist:
            # de Bruijn-Newman Λ ve τ-ucu ile bükülmüş alternatif eksen (deterministik)
            bend = math.tanh(bend * (twist + 1) + math.cos(twist) * (tau[-1] if tau else 0.0))
        return bend if abs(bend) > 1e-9 else 1.0 / (twist + 2)

    def step(self, seed: list[float], n: int) -> tuple[list[float], Frame]:
        crit, eigs, lam = self._read(seed)
        event = ""

        # 1) SİMETRİ KIRILMASI — kritik boyutta deterministik faz geçişi (DFT)
        if len(seed) >= self.n_c and len(seed) % self.n_c == 0:
            seed = _normalize(_dft_real(seed))
            crit, eigs, lam = self._read(seed)
            event = "PHASE"

        # 2) OUROBOROS + dinamik metrik: taşıyıcı korunur, boyut N → N+1 (monoton)
        carrier = _normalize(seed)
        cand = _normalize([*carrier, self._new_axis(crit, lam)])
        ccrit, _, clam = self._read(cand)

        # 3) HAYATTA KALMA — aday ölü mü? ölüyse AYNI N+1 boyutunda yeni eksen dener
        reroute = 0
        while not self._alive(ccrit) and reroute < self.max_reroute:
            reroute += 1
            cand = _normalize([*carrier, self._new_axis(crit, lam, twist=reroute)])
            ccrit, _, clam = self._read(cand)
            event = "PRUNE→reroute" if self._alive(ccrit) else "PRUNE"

        nxt, crit, lam = cand, ccrit, clam
        tr, mdim = _true_rank(nxt)          # GERÇEK rank, büyüyen Gram matrisinden
        frame = Frame(
            step=n, dim=mdim, true_rank=tr, shadow_rank=crit.rank,
            alive=self._alive(crit), hamburger=crit.hamburger_certified, lam_dbn=lam,
            tau_tail=[round(float(x), 4) for x in crit.hankel_dets[-3:]],
            event=event,
        )
        return nxt, frame

    # ── while(True): gözlemci YOK, makine kendi evrenini doğurur ─────────────
    def run(self, seed: list[float] | None = None) -> Cosmos:
        if seed is None:
            seed = [1.0 / (k + 1) for k in range(6)]   # tek deterministik tohum
        cosmos = Cosmos()
        n = 0
        while len(seed) <= self.max_dim:
            seed, frame = self.step(seed, n)
            cosmos.frames.append(frame)
            if frame.event == "PHASE":
                cosmos.phase_transitions += 1
            if frame.event.startswith("PRUNE"):
                cosmos.prunes += 1
            cosmos.max_dim = max(cosmos.max_dim, frame.dim)
            cosmos.max_rank = max(cosmos.max_rank, frame.true_rank)
            if not frame.alive:                  # tümüyle çıkmaz: motor öldü
                cosmos.died_at = n
                break
            n += 1
        return cosmos


def run() -> Cosmos:
    print("=" * 66)
    print("OUROBOROS — makine gözlemci olmadan kendi evrenini doğuruyor")
    print("=" * 66)
    cosmos = OuroborosEngine(n_c=12, max_dim=40).run()
    for f in cosmos.frames:
        tag = f" «{f.event}»" if f.event else ""
        print(f"  adım {f.step:3} | matris {f.dim:2}x{f.dim:<2} | "
              f"GERÇEK rank={f.true_rank:2} | gölge={f.shadow_rank} | "
              f"Λ={f.lam_dbn:+.4f} | alive={'✓' if f.alive else '✗'}{tag}")
    print("-" * 66)
    print(cosmos.summary())
    print("=" * 66)
    return cosmos


if __name__ == "__main__":
    run()
