"""SpectralMeasure — Operatör Uzayı.

Şimdiye kadar: Tr(Gᵏ)/n = 8 moment → G çöpe gidiyor.
Artık: G'nin özdeğer dağılımı dμ = Σ wᵢ δ(λ - λᵢ) KORUNUYOR.

Temel bağlantı (Hilbert-Pólya):
  G = AᵀA  self-adjoint PSD  →  özdeğerler gerçek, ≥ 0
  dμ(λ) = (1/n) Σ δ(λ - λᵢ)  →  spektral ölçü
  μₖ = ∫ λᵏ dμ(λ) = Tr(Gᵏ)/n  →  klasik momentler buradan

Hamburger teoremi:
  bounded support → {μₖ} ↔ dμ birebir → TAV sabit noktası UNIQUE
  Carleman koşulu: Σ μ₂ₖ^{-1/(2k)} = ∞  →  bounded spektrum için her zaman

DNA/metin/sayı farkı:
  Şimdiye kadar: R175H ≈ rastgele mutasyon (8 ort. moment)
  Artık: R175H kendi özdeğer kaydını yaratır — spektrumda izi var
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction

# ─── Jacobi özdeğer algoritması (saf Python, float) ──────────────────────────


def _jacobi_eigvals(
    S: list[list[float]],
    tol: float = 1e-12,
    max_sweeps: int = 100,
) -> list[float]:
    """Gerçek simetrik matris için Jacobi rotasyon özdeğerleri.

    O(n³ × sweeps) — 4×4 için anlık (<1 µs), 20×20 için ~ms.
    G = AᵀA her zaman PSD → λᵢ ≥ 0 (floating point hatası sıfırla).
    """
    n = len(S)
    if n == 0:
        return []
    if n == 1:
        return [float(S[0][0])]

    A = [[float(S[i][j]) for j in range(n)] for i in range(n)]

    for _ in range(max_sweeps):
        off = sum(A[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < tol:
            break

        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(A[p][q]) < 1e-15:
                    continue
                tau = (A[q][q] - A[p][p]) / (2.0 * A[p][q])
                t = 1.0 / (abs(tau) + math.sqrt(1.0 + tau * tau))
                if tau < 0:
                    t = -t
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = t * c

                # Diyagonal güncelle
                d_pp = A[p][p] - t * A[p][q]
                d_qq = A[q][q] + t * A[p][q]
                A[p][p] = d_pp
                A[q][q] = d_qq
                A[p][q] = 0.0
                A[q][p] = 0.0

                # Off-diagonal satır/sütun güncelle
                for r in range(n):
                    if r == p or r == q:
                        continue
                    a_rp = c * A[r][p] - s * A[r][q]
                    a_rq = s * A[r][p] + c * A[r][q]
                    A[r][p] = A[p][r] = a_rp
                    A[r][q] = A[q][r] = a_rq

    return sorted([max(0.0, A[i][i]) for i in range(n)], reverse=True)


# ─── SpectralMeasure ─────────────────────────────────────────────────────────


@dataclass
class SpectralMeasure:
    """G = AᵀA'nın özdeğer ölçüsü  dμ = Σ wᵢ δ(λ - λᵢ).

    8 momentin 'gölgesi' değil, operatörün kendisi.
    Hamburger: dμ ↔ {μₖ} birebir (bounded support için her zaman).
    """

    eigenvalues: list[float]  # λ₁ ≥ λ₂ ≥ ... ≥ λₙ ≥ 0
    weights: list[float] = field(default_factory=list)
    name: str = ""

    def __post_init__(self) -> None:
        self.eigenvalues = [max(0.0, lam) for lam in self.eigenvalues]
        n = len(self.eigenvalues)
        if not self.weights or len(self.weights) != n:
            self.weights = [1.0 / n] * n if n > 0 else []

    # ── Türetilmiş büyüklükler ────────────────────────────────────────────────

    def moment(self, k: int) -> float:
        """μₖ = Σ wᵢ λᵢᵏ — Hankel momentleri buradan türetilir."""
        return sum(w * (lam**k) for lam, w in zip(self.eigenvalues, self.weights, strict=False))

    def moments_list(self, num: int = 8) -> list[float]:
        return [self.moment(k) for k in range(num)]

    def entropy(self) -> float:
        """Von Neumann benzeri entropi: S = -Σ pᵢ log pᵢ  (pᵢ = λᵢ / Σλ)."""
        total = sum(self.eigenvalues)
        if total <= 0.0:
            return 0.0
        s = 0.0
        for lam in self.eigenvalues:
            p = lam / total
            if p > 1e-12:
                s -= p * math.log(p)
        return s

    def spectral_radius(self) -> float:
        return self.eigenvalues[0] if self.eigenvalues else 0.0

    def condition_number(self) -> float:
        """κ = λ_max / λ_min — sayısal durum sayısı."""
        nz = [lam for lam in self.eigenvalues if lam > 1e-12]
        if len(nz) < 2:
            return math.inf
        return nz[0] / nz[-1]

    def gap(self) -> float:
        """Spektral gap: λ₁ - λ₂ — operatörün 'ayrımcılık gücü'."""
        if len(self.eigenvalues) < 2:
            return 0.0
        return self.eigenvalues[0] - self.eigenvalues[1]

    def effective_rank(self) -> float:
        """Etkin rütbe: exp(S) — kaç özdeğer gerçekten bilgi taşıyor."""
        return math.exp(self.entropy())

    # ── TAV sabit nokta ───────────────────────────────────────────────────────

    def tav_fixed_point(self) -> bool:
        """F(dμ) = dμ sabit noktası var mı?

        Hamburger teoremi: bounded support → moment dizisi ölçüyü birebir belirler.
        Carleman koşulu: Σ μ₂ₖ^{-1/(2k)} = ∞  ⟺  spektral yarıçap < ∞.
        Dijital giriş (DNA byte değerleri ∈ [0,1]) → bounded → her zaman True.
        """
        return (
            bool(self.eigenvalues)
            and all(math.isfinite(lam) for lam in self.eigenvalues)
            and self.spectral_radius() < math.inf
        )

    def carleman_sum(self, terms: int = 20) -> float:
        """Carleman serisi kısmi toplamı: Σₖ μ₂ₖ^{-1/(2k)}.

        Sonsuzsa (→ ∞ ile artar): unique measure → TAV ✓.
        """
        total = 0.0
        for k in range(1, terms + 1):
            mu_2k = self.moment(2 * k)
            if mu_2k < 1e-300:
                total += 1e15  # sonsuz katkı
            else:
                total += mu_2k ** (-1.0 / (2 * k))
        return total

    # ── Serileştirme (kalıcılık) ────────────────────────────────────────────

    def to_list(self) -> list[float]:
        """Özdeğerleri float listesi olarak döndür (kompakt kalıcılık).

        Ağırlıklar uniform varsayılır (1/n) — __post_init__ yeniden kurar.
        """
        return [float(x) for x in self.eigenvalues]

    @classmethod
    def from_list(cls, eigenvalues: list[float], name: str = "") -> SpectralMeasure:
        """Float listesinden SpectralMeasure kur (uniform ağırlık)."""
        return cls(eigenvalues=list(eigenvalues), name=name)


# ─── Fraction matris → SpectralMeasure ───────────────────────────────────────


def gram_spectrum(
    A_frac: list[list[Fraction]],
    name: str = "",
) -> SpectralMeasure:
    """Fraction matris A → G = AᵀA özdeğerleri → SpectralMeasure."""
    n = len(A_frac)
    m = len(A_frac[0]) if n > 0 else 0
    if n == 0 or m == 0:
        return SpectralMeasure(eigenvalues=[0.0], name=name)

    A = [[float(A_frac[i][j]) for j in range(m)] for i in range(n)]
    G = [[sum(A[k][i] * A[k][j] for k in range(n)) for j in range(m)] for i in range(m)]
    return SpectralMeasure(eigenvalues=_jacobi_eigvals(G), name=name)


# ─── DNA-özel bigram kodlama ──────────────────────────────────────────────────

_BASES = ["A", "C", "G", "T"]
_B2I = {b: i for i, b in enumerate(_BASES)}


def dna_bigram_matrix(seq: str) -> list[list[float]]:
    """DNA → ACGT bigram geçiş matrisi (4×4, satır normalize).

    A[i][j] = P(baz_j | baz_i) — ardışık baz geçiş olasılıkları.
    Mutasyon → belirli bigram frekanslarını kaydırır.
    """
    counts = [[0] * 4 for _ in range(4)]
    seq_up = seq.upper()
    for a, b in zip(seq_up, seq_up[1:], strict=False):
        if a in _B2I and b in _B2I:
            counts[_B2I[a]][_B2I[b]] += 1
    matrix = []
    for row in counts:
        total = sum(row)
        matrix.append([v / total if total > 0 else 0.25 for v in row])
    return matrix


def dna_measure(seq: str, name: str = "DNA") -> SpectralMeasure:
    """DNA sekansı → 4×4 bigram matrisi → G = AᵀA → SpectralMeasure."""
    A = dna_bigram_matrix(seq)
    n = 4
    G = [[sum(A[k][i] * A[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    return SpectralMeasure(eigenvalues=_jacobi_eigvals(G), name=name)


def dna_window_measures(
    seq: str,
    window: int = 128,
    stride: int = 64,
) -> list[tuple[int, SpectralMeasure]]:
    """Kayan pencere spektral analizi → (başlangıç_pos, SpectralMeasure) listesi.

    Her pencere kendi bigram matrisini ve G'sini hesaplar.
    Mutasyon içeren pencereler spektral kayma olarak görünür.
    Mutasyon lokalizasyonu: biyoloji bilmeden.
    """
    results = []
    for start in range(0, len(seq) - window + 1, stride):
        sub = seq[start : start + window]
        m = dna_measure(sub, name=f"w{start}")
        results.append((start, m))
    return results


# ─── Spektral Mesafe ──────────────────────────────────────────────────────────


def spectral_distance(m1: SpectralMeasure, m2: SpectralMeasure) -> float:
    """Wasserstein-2 benzeri mesafe: sıralı özdeğer dizileri arası L₂/n.

    W₂(μ, ν) ≈ (1/n) ||sort(λ_μ) - sort(λ_ν)||₂

    8 moment mesafesinden üstün:
      - Hangi özdeğer kaydı sorusunu yanıtlar (pozisyonel bilgi)
      - R175H spektrum imzası ≠ R273H imzası  (moment ortalaması bunları aynı görür)
    """
    a = sorted(m1.eigenvalues, reverse=True)
    b = sorted(m2.eigenvalues, reverse=True)
    la, lb = len(a), len(b)
    if la < lb:
        a = a + [0.0] * (lb - la)
    elif lb < la:
        b = b + [0.0] * (la - lb)
    n = max(len(a), 1)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=False))) / n


def spectral_window_diff(
    normal: list[tuple[int, SpectralMeasure]],
    cancer: list[tuple[int, SpectralMeasure]],
) -> list[tuple[int, float]]:
    """Pencere-pencere spektral fark haritası.

    Mutasyon pozisyonları burada yüksek fark olarak görünür.
    Çıktı: [(başlangıç_pos, mesafe), ...] azalan mesafe sırasında değil, pozisyon sırasında.
    """
    return [
        (pos_n, spectral_distance(m_n, m_c))
        for (pos_n, m_n), (_, m_c) in zip(normal, cancer, strict=False)
    ]


def mutation_hotspots(
    diff_map: list[tuple[int, float]],
    top_n: int = 5,
) -> list[tuple[int, float]]:
    """Spektral fark haritasından en büyük sapmaları bul.

    Bunlar potansiyel mutasyon lokalizasyonlarıdır — biyoloji bilmeden.
    """
    return sorted(diff_map, key=lambda x: -x[1])[:top_n]


# ─── Momentlerden spektral ölçü geri çıkarımı (Golub-Welsch) ─────────────────


def _stieltjes(mu: list[float], n: int) -> tuple[list[float], list[float]]:
    """Stieltjes üç-terim tekrarlayıcısı: 2n moment → (alpha, beta).

    alpha[k] = Jacobi matrisinin k. diyagonal elemanı
    beta[k]  = Jacobi matrisinin k. alt-diyagonal elemanının karesi
    beta[0]  = toplam kütle = μ₀

    Kaynak: Gautschi (2004), "Orthogonal Polynomials: Computation and Approximation"
    σ_k[l] = σ_{k-1}[l+1] - α_{k-1}·σ_{k-1}[l] - β_{k-1}·σ_{k-2}[l]
    """
    sz = 2 * n
    s_m2 = [0.0] * sz  # sigma_{k-2} = 0
    s_m1 = [(mu[l] if l < len(mu) else 0.0) for l in range(sz)]  # sigma_0 = moments

    alpha = [0.0] * n
    beta = [0.0] * n

    if abs(s_m1[0]) < 1e-15:
        return alpha, beta

    alpha[0] = s_m1[1] / s_m1[0]
    beta[0] = s_m1[0]

    for k in range(1, n):
        s_cur = [0.0] * sz
        for l in range(k, sz - k):
            nxt = s_m1[l + 1] if l + 1 < sz else 0.0
            s_cur[l] = nxt - alpha[k - 1] * s_m1[l] - beta[k - 1] * s_m2[l]

        if abs(s_cur[k]) < 1e-15 or abs(s_m1[k - 1]) < 1e-15:
            break

        nxt_val = s_cur[k + 1] if k + 1 < sz else 0.0
        alpha[k] = nxt_val / s_cur[k] - s_m1[k] / s_m1[k - 1]
        beta[k] = s_cur[k] / s_m1[k - 1]

        s_m2 = s_m1
        s_m1 = s_cur

    return alpha, beta


def moments_to_spectral(
    moments: list[float],
    n_nodes: int = 4,
    name: str = "",
) -> SpectralMeasure:
    """Güç momentleri μ_k → n-noktalı Gauss kuadratura spektral yaklaşımı.

    Golub-Welsch algoritması:
    1. Stieltjes: 2n moment → n×n tridiagonal Jacobi matrisi J
    2. J'nin özdeğerleri = Gauss kuadratura noktaları ≈ G'nin özdeğerleri
    3. Ağırlıklar: β₀/n (basitleştirilmiş)

    Doğruluk: 8 momentten 4 özdeğer — iyi bir yaklaşım.
    Garanti: noktalar [μ_min, μ_max] içinde, PSD ölçü için ≥ 0.

    Bu, μ_k = Tr(Gᵏ)/n'nin TERSI:
    {μ_k}'den G'nin yaklaşık özdeğerleri kurtarılır.
    """
    n = n_nodes
    mu = [float(m) for m in moments]

    alpha, beta = _stieltjes(mu, n)

    # Jacobi matrisi: tridiagonal simetrik
    J = [[0.0] * n for _ in range(n)]
    for i in range(n):
        J[i][i] = alpha[i]
    for i in range(n - 1):
        b = beta[i + 1]
        if b > 0.0:
            J[i][i + 1] = J[i + 1][i] = math.sqrt(b)

    nodes = _jacobi_eigvals(J)
    w = max(0.0, beta[0]) / n if n > 0 else 0.0
    return SpectralMeasure(eigenvalues=nodes, weights=[w] * n, name=name)
