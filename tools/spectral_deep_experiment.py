"""DERİN-KATMAN SPEKTRAL INIT DENEYİ — tezin frontier'ı.

Önceki deney: yalnız GÖMME spektral (PMI-SVD) → random'ın inemediği tabana iniyor ama erken yavaş.
Hipotez: derin katmanları (attention V/out-proj + MLP) da SPEKTRAL başlatırsak — rasgele Gauss
yerine gömmenin asal eigenbazı V_e'de, veri-operatörünün spektral magnitüd profili Σ_e ile —
çaprazlama erkene kayar / taban daha düşer. (Kullanıcı: 'rasgele yerine spektral bağlantılar.')

ÜÇ KOŞUL, birebir aynı veri + seed + RANDOM DERİN TABAN (kopya), her değiştirilen matris random
init'in Frobenius normuna eşitlenir → fark MAGNİTÜD değil SPEKTRAL YAPI:
  (R) random        : her şey N(0,0.02)  [LLM standardı]
  (E) spectral-embed: yalnız token-gömme = PMI-SVD
  (D) spectral-deep : gömme = PMI-SVD  +  attn V/out-proj + MLP = spektral-hizalı (V_e, Σ_e)

Kapalı-form YOK derin optimum için (Blum-Rivest) — bu bir INIT deneyi, iddia değil.
"""
from __future__ import annotations

import os
import re
import sys
import time
import json
import copy
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tantrium.core.transformer import GPT  # noqa: E402

STATE = ROOT / ".tantrium"
DIM = 160
CTX = 64
BATCH = 16
STEPS = int(os.environ.get("EXP_STEPS", "400"))
LR = 3e-4
TOKEN_BUFFER = int(os.environ.get("EXP_TOKENS", "600000"))
SEED = int(os.environ.get("EXP_SEED", "1234"))


def load_spectral():
    E = np.load(STATE / "embeddings.npy").astype(np.float32)
    vocab = json.loads((STATE / "embed_vocab.json").read_text())
    return E, vocab, {w: i for i, w in enumerate(vocab)}


def stream_tokens(tok2id, n_tokens):
    from datasets import load_dataset
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    word = re.compile(r"[a-z]+")
    unk = len(tok2id)
    ids = []
    for row in ds:
        for w in word.findall((row.get("text") or "").lower()):
            ids.append(tok2id.get(w, unk))
        if len(ids) >= n_tokens:
            break
    return np.array(ids[:n_tokens], dtype=np.int64)


def make_batches(ids, n_steps, rng):
    out, maxstart = [], len(ids) - CTX - 1
    for _ in range(n_steps):
        s = rng.integers(0, maxstart, size=BATCH)
        x = np.stack([ids[i:i + CTX] for i in s])
        y = np.stack([ids[i + 1:i + 1 + CTX] for i in s])
        out.append((torch.from_numpy(x), torch.from_numpy(y)))
    return out


def principal_basis(E):
    """Gömmenin asal eigenbazı V_e (dim×dim) + spektral magnitüd profili Σ_e (dim,)."""
    Ec = E - E.mean(0, keepdims=True)
    # E = U Σ V^T ; V (dim×dim) = embedding-uzayı asal yönleri, Σ = spektrum
    _, S, Vt = np.linalg.svd(Ec, full_matrices=False)
    return Vt.T.astype(np.float32), (S / S[0]).astype(np.float32)   # V_e, normalize spektrum


def spectral_matrix(out_dim, in_dim, Ve, spec, rng, target_norm):
    """Singular spektrumu veri-operatörünün profili (spec), tekil-vektörleri gömmenin asal
    bazından (V_e) gelen bir matris → 'spektral bağlantı' init. Random ortogonal sağ-baz ile
    simetri kırılır. Sonra target_norm'a (random init normu) ölçeklenir → magnitüd eşit."""
    k = min(out_dim, in_dim, Ve.shape[0])
    # sol baz: V_e'nin ilk yönleri (out_dim'e göre); sağ baz: random ortogonal
    U = np.zeros((out_dim, k), dtype=np.float32)
    U[:min(out_dim, Ve.shape[0]), :k] = Ve[:min(out_dim, Ve.shape[0]), :k]
    Rg = rng.standard_normal((in_dim, k)).astype(np.float32)
    Q, _ = np.linalg.qr(Rg)                                          # random ortonormal sağ-baz
    g = spec[:k].copy()
    if g.shape[0] < k:                                              # pad (nadiren)
        g = np.pad(g, (0, k - g.shape[0]), constant_values=g[-1])
    W = (U * g[None, :]) @ Q.T                                       # (out_dim, in_dim)
    n = np.linalg.norm(W)
    if n > 0:
        W = W * (target_norm / n)
    return torch.from_numpy(W)


def apply_spectral_deep(model, Ve, spec, seed):
    """attn in_proj V-bloğu + out_proj + MLP fc1/fc2 → spektral-hizalı (norm-eşitli)."""
    rng = np.random.default_rng(seed + 9991)
    with torch.no_grad():
        for blk in model.blocks:
            ipw = blk.attn.in_proj_weight                           # (3*dim, dim): Q|K|V
            d = ipw.shape[1]
            vblock = ipw[2 * d:3 * d, :]                            # yalnız V-bloğu (değer yolu)
            vblock.copy_(spectral_matrix(d, d, Ve, spec, rng, vblock.norm().item()))
            ow = blk.attn.out_proj.weight                           # (dim, dim)
            ow.copy_(spectral_matrix(*ow.shape, Ve, spec, rng, ow.norm().item()))
            fc1 = blk.mlp[0].weight                                 # (4dim, dim)
            fc1.copy_(spectral_matrix(*fc1.shape, Ve, spec, rng, fc1.norm().item()))
            fc2 = blk.mlp[2].weight                                 # (dim, 4dim)
            fc2.copy_(spectral_matrix(*fc2.shape, Ve, spec, rng, fc2.norm().item()))


def set_spectral_embedding(model, E):
    with torch.no_grad():
        rn = model.tok.weight.norm().item()
        w = model.tok.weight.clone()
        w[:E.shape[0]] = torch.from_numpy(E)
        w.mul_(rn / w.norm().item())
        model.tok.weight.copy_(w)


def fresh_model(Vp1, base_state):
    torch.manual_seed(SEED)
    m = GPT(vocab=Vp1, dim=DIM, heads=4, layers=2, ctx=CTX, dropout=0.0)
    m.load_state_dict(copy.deepcopy(base_state))                    # AYNI random derin taban
    return m


def train(model, batches, thresholds):
    opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.95), weight_decay=0.01)
    model.train()
    curve, hit, ema = {}, {t: None for t in thresholds}, None
    for step, (x, y) in enumerate(batches):
        _, loss = model(x, y)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        lv = float(loss.item())
        ema = lv if ema is None else 0.9 * ema + 0.1 * lv
        for t in thresholds:
            if hit[t] is None and ema <= t:
                hit[t] = step
        if step in (0, 25, 50, 100, 150, 200, 300, len(batches) - 1):
            curve[step] = round(ema, 4)
    return curve, hit


def main():
    print(f"[{time.strftime('%H:%M:%S')}] DERİN-spektral deneyi seed={SEED} — {STEPS} adım", flush=True)
    E, vocab, tok2id = load_spectral()
    Ve, spec = principal_basis(E)
    print(f"  V_e={Ve.shape} spektrum[0:5]={np.round(spec[:5],3)} kuyruk={spec[-1]:.3f}", flush=True)
    t0 = time.time()
    ids = stream_tokens(tok2id, TOKEN_BUFFER)
    print(f"  buffer {len(ids):,} tok, UNK {float((ids==len(tok2id)).mean()):.1%} ({time.time()-t0:.0f}s)", flush=True)
    batches = make_batches(ids, STEPS, np.random.default_rng(SEED))
    thr = [7.0, 6.5, 6.0, 5.5, 5.2]
    Vp1 = len(vocab) + 1

    torch.manual_seed(SEED)
    base = GPT(vocab=Vp1, dim=DIM, heads=4, layers=2, ctx=CTX, dropout=0.0)
    base_state = copy.deepcopy(base.state_dict())                   # ortak random taban

    results = {}
    for tag, label in [("R", "random"), ("E", "spectral-embed"), ("D", "spectral-deep")]:
        m = fresh_model(Vp1, base_state)
        if tag in ("E", "D"):
            set_spectral_embedding(m, E)
        if tag == "D":
            apply_spectral_deep(m, Ve, spec, SEED)
        ts = time.time()
        c, h = train(m, batches, thr)
        results[tag] = {"label": label, "curve": c, "hit": h}
        print(f"  [{label:>14}] ({time.time()-ts:.0f}s) son={c[STEPS-1]} curve={c}", flush=True)

    print("\n" + "=" * 70)
    print("YAKINSAMA EĞRİSİ (EMA loss)")
    print(f"  {'adım':>5} {'RANDOM':>9} {'SP-EMBED':>9} {'SP-DEEP':>9}")
    alls = sorted(set().union(*[r["curve"] for r in results.values()]))
    for s in alls:
        row = [results[t]["curve"].get(s) for t in ("R", "E", "D")]
        if all(v is not None for v in row):
            print(f"  {s:>5} {row[0]:>9.4f} {row[1]:>9.4f} {row[2]:>9.4f}")
    print("\nEŞİĞE İLK İNİŞ (adım; düşük=hızlı, — = hiç ulaşmadı)")
    print(f"  {'eşik':>5} {'RANDOM':>9} {'SP-EMBED':>9} {'SP-DEEP':>9}")
    for t in thr:
        vals = [results[k]["hit"][t] for k in ("R", "E", "D")]
        print(f"  {t:>5} " + " ".join(f"{(str(v) if v is not None else '—'):>9}" for v in vals))
    print("=" * 70)
    (STATE / f"spectral_deep_{SEED}.json").write_text(json.dumps(results, indent=2))
    print(f"→ .tantrium/spectral_deep_{SEED}.json", flush=True)


if __name__ == "__main__":
    main()
