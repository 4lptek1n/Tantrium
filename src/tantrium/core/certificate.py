"""TEK geçerlilik ölçütü — "doğru yolda mı / genelleşiyor mu".

Sistemde aynı fikrin dağınık 5 kopyası vardı: pozitiflik merdiveni (positivity_ladder),
Sturm-pivot (production), leave-one-out (code_meta._generalizes), holdout (discover_law/
forecast), Sturm-zincir (ai._sturm_chain_ok). Hepsi tek soruyu sorar: bir aday (geçiş/
kural/strateji/program) KRİTİK HAT üzerinde mi (pozitiflik korunuyor) ve EZBER değil
GENELLEŞİYOR mu (görülmemişi sağlıyor). Bu modül o soruya tek arayüz verir.

Meta-sentezin (core/meta.py) kabul ölçütü budur: "çıktısı certify'ı geçen prosedürleri
icat et." Tek ve değişmez ölçüt → halüsinasyon her katmanda (kural/strateji dahil) imkânsız.

İki eksen:
  certify_transition(src, tgt) — moment geçişi pozitiflik merdiveninde kaç basamak (0–3);
                                 on_path = tam kritik hatta (Hankel→Newton→Sturm/Jensen).
  certify_generalization(builder, instances, verify) — leave-one-out: her örneği sırayla
                                 dışarıda bırak, kalanlara kur, dışarıdakini sağlıyor mu;
                                 HEPSİ geçerse genelleşir (ezber değil). Holdout sertifikası.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence


@dataclass
class CertResult:
    """Bir adayın geçerlilik yargısı — tek para birimi."""
    on_path: bool                 # kritik hatta mı (pozitiflik geçti)
    depth: int = 0                # pozitiflik merdiveni derinliği (0–3)
    generalizes: bool | None = None   # leave-one-out genelleşme (uygulanmadıysa None)
    detail: dict = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.on_path)


# Pozitiflik için tam kritik-hat eşiği (merdivenin en üst basamağı = Sturm/Jensen)
_FULL_DEPTH = 3


def certify_transition(src: Sequence[float], tgt: Sequence[float], *,
                       min_depth: int = _FULL_DEPTH) -> CertResult:
    """Moment geçişinin pozitiflik geçerliliği — positivity_ladder'a delege (tek-gerçek math).

    on_path = depth ≥ min_depth (varsayılan 3 = tam kritik hatta: Hankel + Newton + Sturm/Jensen).
    """
    from tantrium.core.positivity_ladder import positivity_depth
    depth, rungs = positivity_depth(list(src), list(tgt))
    return CertResult(on_path=(depth >= min_depth), depth=depth,
                      generalizes=None, detail=dict(rungs))


def certify_generalization(builder: Callable[[list], object],
                           instances: Sequence,
                           verify: Callable[[object, list], bool],
                           *, min_instances: int = 3) -> bool:
    """Leave-one-out genelleşme geçidi (ezber-karşıtı; holdout sertifikası).

    builder(train) → aday (veya None); verify(aday, [held]) → held'i sağlıyor mu.
    Her örnek SIRAYLA dışarıda bırakılır; aday kalanlara kurulup dışarıdaki sağlanır.
    HEPSİ geçerse genelleşir. < min_instances → güvenilir test edilemez → False (İDDİA ETME).
    """
    items = list(instances)
    n = len(items)
    if n < min_instances:
        return False
    for i in range(n):
        train = items[:i] + items[i + 1:]
        cand = builder(train)
        if cand is None or not verify(cand, [items[i]]):
            return False
    return True
