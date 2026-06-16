"""LLM dil-geometrisi probu — açık modelin AKTİVASYON yörüngesinde gizli yasa var mı?

Tez (kullanıcı): dilin arkasındaki geometrinin kapalı bir formülü varsa, modelin iç
aktivasyon yörüngesi SONLU rank'lı (üreten lineer operatör) olmalı; yoksa gürültü gibi
tam rank. `structure.py` (Kronecker/Prony) bunu okur — Fibonacci→φ, gürültü→tam rank
diye doğrulandı. Burada gözlem = LLM'in residual-stream'i (metin DEĞİL, iç hesap).

Yöntem: prompt → hidden_states → seçili katmanda konum-boyunca vektör yörüngesi →
baskın PC'ye projeksiyon (skaler dizi) → structural_decomposition. KONTROL: aynı diziyi
karıştır (zamansal yapıyı yok et) → rank yükseliyorsa gerçek sıralı yapı vardı.

DÜRÜST SINIR: skaler projeksiyon tam vektör-dinamiğinin GÖLGESİdir; sonlu rank güçlü
ipucu, kesin kanıt için blok-Hankel (matris-Prony) gerekir (sıradaki adım).
"""
from __future__ import annotations

import sys

import numpy as np

from tantrium.core.structure import structural_decomposition

_MODELS = [
    "Qwen/Qwen2.5-0.5B-Instruct",
    "HuggingFaceTB/SmolLM2-135M-Instruct",
    "state-spaces/mamba-130m-hf",
]

_PROMPT = ("The mathematical structure behind language is not a metaphor; "
           "every sentence is already a geometric object that the model reads.")


def _load(name):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(name, output_hidden_states=True,
                                                 torch_dtype="float32")
    model.eval()
    return tok, model


def _top_pc(H):
    """H: [seq_len, hidden] → baskın temel bileşene projeksiyon (konum-boyunca skaler dizi)."""
    Hc = H - H.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(Hc, full_matrices=False)
    return Hc @ vt[0]


def _report(label, seq):
    sd = structural_decomposition([float(v) for v in seq])
    print(f"  {label:18s} n={sd.n:3d}  rank={sd.rank:3d}  structured={sd.structured}  "
          f"sv_gap={sd.sv_gap:.4f}")
    return sd.rank, sd.n


def main():
    import torch

    name = None
    tok = model = None
    for cand in _MODELS:
        try:
            print(f"[yükleniyor] {cand} ...", flush=True)
            tok, model = _load(cand)
            name = cand
            break
        except Exception as e:  # noqa: BLE001
            print(f"  atlandı ({type(e).__name__}: {str(e)[:80]})")
    if model is None:
        print("Hiçbir model yüklenemedi.")
        return 1

    print(f"\n=== MODEL: {name} ===")
    ids = tok(_PROMPT, return_tensors="pt").input_ids
    with torch.no_grad():
        out = model(ids)
    hs = out.hidden_states                      # (kat+1) × [1, seq_len, hidden]
    n_layers = len(hs) - 1
    seq_len = hs[0].shape[1]
    hidden = hs[0].shape[2]
    print(f"katman={n_layers}  seq_len={seq_len}  hidden={hidden}\n")

    rng = np.random.default_rng(0)
    for frac in (0.25, 0.5, 0.75):
        L = max(1, int(n_layers * frac))
        H = hs[L][0].float().numpy()            # [seq_len, hidden]
        traj = _top_pc(H)                        # konum-boyunca baskın mod
        print(f"katman {L}/{n_layers}:")
        r_real, n = _report("gerçek yörünge", traj)
        shuf = traj.copy(); rng.shuffle(shuf)
        r_shuf, _ = _report("karıştırılmış", shuf)
        verdict = ("YAPI VAR (gerçek << karıştırılmış)" if r_real < r_shuf - 1
                   else "yapı zayıf/yok (gerçek ≈ karıştırılmış)")
        print(f"  → {verdict}  [rank gerçek={r_real} vs karıştırılmış={r_shuf}, maks={n//2}]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
