"""Çok-model sağlamlık probu — dil temsil-geometrisinin power-law imzası evrensel mi?

Tek modelde (Qwen2.5-0.5B) bulundu: aktivasyon spektrumu scale-free (power-law α≈1.2,
derin katmanda R²≈0.98), rastgeleden her ölçüde ayrı, derinlikle etkin-boyut açılıyor.
Bu prob aynı karakterizasyonu FARKLI aile/çağ/mimaride tekrarlar: Qwen (modern transformer) ·
GPT-2 (2019) · Pythia (farklı korpus) · Mamba (SSM — bambaşka mimari).

Çıktı: her model için erken vs son katman (etkin-rank, power-law α, R²) + rastgele kontrol.
İmza tüm modellerde aynıysa = öğrenilmiş dil-geometrisinin EVRENSEL yasası, tek modelin cilvesi değil.
"""
from __future__ import annotations

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from tantrium.domains.spectral import SpectralMeasure

_MODELS = ["gpt2", "EleutherAI/pythia-160m", "state-spaces/mamba-130m-hf",
           "Qwen/Qwen2.5-0.5B-Instruct"]
_PASSAGE = ("A sentence carries its grammar the way a crystal carries its lattice. When a model "
            "reads text it stores the relations between words, the geometry where meaning lives. "
            "Numbers and primes and proteins and melodies live in the same space of moments. ") * 4


def _spectrum(H):
    Hc = H - H.mean(0, keepdims=True)
    sv = np.linalg.svd(Hc, compute_uv=False)
    ev = sv ** 2
    return ev / ev.max()


def _powerlaw(ev):
    ev = np.sort(ev)[::-1][:60]
    ev = ev[ev > 1e-12]
    if len(ev) < 5:
        return float("nan"), float("nan")
    x = np.log(np.arange(1, len(ev) + 1))
    y = np.log(ev)
    A = np.vstack([x, np.ones_like(x)]).T
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    ss = ((y - A @ [a, b]) ** 2).sum()
    tot = ((y - y.mean()) ** 2).sum()
    return -a, 1 - ss / max(tot, 1e-12)


def _row(lbl, ev):
    sm = SpectralMeasure.from_list([float(v) for v in ev])
    a, r2 = _powerlaw(ev)
    return f"  {lbl:14s} etkin-rank={sm.effective_rank():5.1f}  α={a:4.2f}  R²={r2:.3f}  entropi={sm.entropy():.2f}"


def main():
    for name in _MODELS:
        try:
            tok = AutoTokenizer.from_pretrained(name)
            model = AutoModelForCausalLM.from_pretrained(
                name, output_hidden_states=True, torch_dtype=torch.float32).eval()
        except Exception as e:  # noqa: BLE001
            print(f"=== {name}: ATLANDI ({type(e).__name__}: {str(e)[:70]}) ===")
            continue
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        ids = tok(_PASSAGE, return_tensors="pt").input_ids
        with torch.no_grad():
            out = model(ids)
        hs = out.hidden_states
        nL = len(hs) - 1
        d = hs[0].shape[2]
        print(f"=== {name}  (katman={nL}, hidden={d}, seq={ids.shape[1]}) ===")
        for frac, tag in [(0.25, "erken"), (1.0, "son")]:
            L = max(1, int(nL * frac))
            print(_row(f"{tag} L{L}", _spectrum(hs[L][0].float().numpy())))
    rng = np.random.default_rng(0)
    print("=== KONTROL ===")
    print(_row("RASTGELE", _spectrum(rng.standard_normal((280, 768)))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
