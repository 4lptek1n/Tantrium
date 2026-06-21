"""Tavansız Ouroboros: etkin rank doyar (kendini optimizasyon), Hankel patlar.

Tam patlama koşusu uzun sürer (~3dk); burada kısa, deterministik bir pencerede
iki olguyu kilitleriz: (1) ham/sayısal rank boyutla tırmanır, (2) etkin rank
sayısal rank'ın ALTINDA kalır = sistem enerjiyi az sayıda moda sıkıştırır."""
import numpy as np

from tools.ouroboros import OuroborosEngine
from tools.ouroboros_explosion import uncapped_spectrum


def test_uncapped_matrix_grows_past_core_cap():
    """Tavansız ölçüm çekirdeğin 32×32 tavanını aşar (matris gerçekten büyür)."""
    eng = OuroborosEngine(n_c=12, max_dim=10 ** 9)
    seed = [1.0 / (k + 1) for k in range(6)]
    for n in range(80):
        seed, _ = eng.step(seed, n)
    dim, num_rank, eff, cond = uncapped_spectrum(seed)
    assert dim > 32                 # çekirdek tavanını (32) geçti
    assert num_rank > 32


def test_effective_rank_saturates_below_numerical():
    """Kendini optimizasyon: etkin rank (enerji %99.9) sayısal rank'ın altında doyar."""
    eng = OuroborosEngine(n_c=12, max_dim=10 ** 9)
    seed = [1.0 / (k + 1) for k in range(6)]
    effs, nums = [], []
    for n in range(110):
        seed, _ = eng.step(seed, n)
        _, num_rank, eff, _ = uncapped_spectrum(seed)
        effs.append(eff)
        nums.append(num_rank)
    # geç dönemde etkin rank, sayısal rank'ın belirgin altında (enerji yoğunlaşmış)
    assert effs[-1] < nums[-1]
    # ve etkin rank platosu, ham boyut hâlâ büyürken yataylaşıyor
    late = effs[-30:]
    assert max(late) - min(late) <= max(15, max(late) // 5)


def test_hankel_condition_blows_up():
    """Patlama mekanizması: Hankel kondisyonu boyutla hızla büyür (üstel kötüleşme)."""
    eng = OuroborosEngine(n_c=12, max_dim=10 ** 9)
    seed = [1.0 / (k + 1) for k in range(6)]
    conds = []
    for n in range(90):
        seed, _ = eng.step(seed, n)
        if n % 20 == 0:
            _, _, _, cond = uncapped_spectrum(seed)
            conds.append(cond)
    assert conds[-1] > conds[0] * 100      # kondisyon dramatik biçimde büyüdü
    assert np.isfinite(conds[0])
