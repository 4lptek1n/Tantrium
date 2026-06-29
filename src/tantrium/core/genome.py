"""GenomeRecord — nesnenin DNA'sı: özdeğer + var-eden-yasa (cansız snapshot değil).

KATMAN 5 — HAFIZA ilkesi: evren fotoğraf saklamaz, üreteç saklar. Sakladığımız
şey donmuş bir koordinat (coord_91) değil; nesneyi VAR EDEN yasadır.

  genotip  = (eigenvalues tohumu + üreten yasa + σ)
  fenotip  = moment / RH / 91-dim / GOE-GUE   ← istenince TÜRETİLİR

Yasa, mevcut saf-matematik makinesinden okunur (yeni matematik YOK):
  · lineer  → Prony/AR rekürans  (structure.fit_recurrence): x[n] = Σ cᵢ·x[n-(i+1)]
  · nonlineer → Koopman/EDMD polinom-NARX (structure.nonlinear_fit)
  · trivial → çok kısa dizi (n<4) ya da yasaya oturmayan → tohumu birebir sakla

σ (residual) birinci-sınıf ölçüdür: "bu nesne ne kadar yasaya tabi?" — düşük σ
deterministik bir yasanın ürünü (kristal/periyodik), yüksek σ yapısız/karmaşık
(çoğu molekül). σ büyük olsa bile eigenvalues tohumuyla nesne KAYIPSIZ saklanır;
yalnız "minik yasaya inme" (ekstra sıkıştırma) olmaz.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from tantrium.core.structure import _poly_features, fit_recurrence, nonlinear_fit


@dataclass
class GenomeRecord:
    """Bir nesnenin genotipi: özdeğer tohumu + onu üreten yasa + σ."""
    eigenvalues: list[float]            # tam spektrum (ground-truth tohum)
    law: list[float] = field(default_factory=list)  # cᵢ (lineer) | wᵢ (nonlineer)
    order: int = 0                      # p (lineer rekürans mertebesi) | embed (nonlineer)
    degree: int = 0                     # 0 = lineer/trivial | ≥1 = nonlineer NARX derecesi
    sigma: float = 0.0                  # residual std = yasalılık ölçüsü (düşük = yasalı)
    seed: list[float] = field(default_factory=list)  # yasayı çalıştırmak için ilk `order` değer
    law_type: str = "trivial"           # "linear" | "nonlinear" | "trivial"

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "GenomeRecord":
        return cls(**{k: d[k] for k in d if k in cls.__dataclass_fields__})


def fit_genome(eigenvalues, sigma_rel_tol: float = 1e-6) -> GenomeRecord:
    """Özdeğer spektrumu → onu üreten yasa (genotip).

    Önce lineer (Prony) dene; residual yeterince küçükse (σ ≤ tol·max|λ|) lineer
    sakla. Değilse Koopman/EDMD (nonlineer). n<4 ya da yasa bulunamazsa trivial
    (tohumu birebir sakla → yine kayıpsız).

    sigma_rel_tol: relative eşik (özdeğerler genelde [0,1]'e normalize → mutlak≈relative).
    """
    eigs = [float(e) for e in eigenvalues]
    n = len(eigs)
    scale = max((abs(e) for e in eigs), default=1.0) or 1.0

    if n < 4:
        return GenomeRecord(eigenvalues=eigs, law=[], order=n, degree=0,
                            sigma=0.0, seed=list(eigs), law_type="trivial")

    c, p, sigma_lin = fit_recurrence(eigs)
    if c and sigma_lin <= sigma_rel_tol * scale:
        return GenomeRecord(eigenvalues=eigs, law=c, order=p, degree=0,
                            sigma=float(sigma_lin), seed=eigs[:p], law_type="linear")

    w, e, d, sigma_nl = nonlinear_fit(eigs, degree=2, embed=2)
    if w:
        return GenomeRecord(eigenvalues=eigs, law=w, order=e, degree=d,
                            sigma=float(sigma_nl), seed=eigs[:e], law_type="nonlinear")

    # Yasa çıkmadı → trivial (tohum = tüm spektrum, kayıpsız)
    return GenomeRecord(eigenvalues=eigs, law=[], order=n, degree=0,
                        sigma=0.0, seed=list(eigs), law_type="trivial")


def regenerate(genome: GenomeRecord, depth: int) -> list[float]:
    """Yasayı tohumdan ileri çalıştır → spektrumu `depth` uzunluğa yeniden üret.

    σ≈0 olduğunda çıktı saklanan eigenvalues ile birebir (np.allclose). Bu, "DNA"
    özelliği: genotipten fenotip (tam spektrum) yeniden doğar.
    """
    seed = [float(s) for s in genome.seed]

    if genome.law_type == "trivial" or not genome.law:
        out = seed[:depth]
        if len(out) < depth:
            out = out + [0.0] * (depth - len(out))
        return out

    seq = list(seed)
    if genome.law_type == "linear":
        c = genome.law
        while len(seq) < depth:
            seq.append(sum(ci * seq[-(i + 1)] for i, ci in enumerate(c)))
    elif genome.law_type == "nonlinear":
        w, e, d = genome.law, genome.order, genome.degree
        while len(seq) < depth:
            seq.append(sum(wi * fi for wi, fi in zip(w, _poly_features(seq[-e:], d))))
    return seq[:depth]
