"""Core pipeline interface for Tantrium.

This file is a recovery interface. It does not fake the old tau computation.
The real Bareiss tau engine should replace build_tau_atlas.
"""


class TauEngineNotRestored(RuntimeError):
    pass


def build_tau_atlas(K=8, J=8, N=8):
    raise TauEngineNotRestored(
        f"tau engine not restored for K={K}, J={J}, N={N}; "
        "restore the Bareiss truncated-series implementation"
    )
