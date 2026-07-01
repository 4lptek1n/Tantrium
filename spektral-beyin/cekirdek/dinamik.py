"""
DINAMIK KAT — coord_91'in bos devrelerini dolduran dort olcum operatoru.

Statik spektrum bu sorulari tek basina cevaplayamaz; her test daha fazlasini ister:
  NEWTON (dim 50)     yasayi ister   — yasa<->spektrum tutarliligi (ouroboros testi)
  Q      (dim 59)     kokleri ister  — kalite faktoru; birim cember = kritik cizgi
  AKIS   (dim 69-71)  zamani ister   — spektral akis: kimligin hareketi
  RESH   (dim 80-82)  bolmeyi ister  — bipartisyon entropileri + karsilikli bilgi

Hepsi saf numpy; LLM/torch gerektirmez. Testler: ../test_dinamik.py
"""
import numpy as np

# ---------------------------------------------------------------- yardimcilar

def _log_compress(seq):
    """olcek_pipeline.A_from_sequence ile ayni normalizasyon."""
    s = np.asarray(seq, float)
    return np.sign(s) * np.log1p(np.abs(s))

def _hankel_gram_spectrum(seq, win=10, center=False):
    """Dizi -> log-sikistirma -> Hankel -> G = H Hᵀ -> ozdegerler (azalan, >=0).
    center=True: DC bileseni cikar — sekil karsilastirmasi icin (NEWTON);
    aksi halde ortalama, spektrumu domine edip sekil farkini maskeler."""
    s = _log_compress(seq)
    if center:
        s = s - s.mean()
    if len(s) < win + 1:
        win = max(2, len(s) // 2)
    H = np.lib.stride_tricks.sliding_window_view(s, win).T   # win x cols
    G = H @ H.T
    return np.clip(np.linalg.eigvalsh(G), 0.0, None)[::-1]

def _shape_moments(w, mk=8):
    """Normalize spektrumun (λ̂ = λ/λ_max) guc toplamlari μ_1..μ_mk."""
    w = np.asarray(w, float)
    if len(w) == 0 or w[0] <= 0:
        return np.zeros(mk)
    lh = w / w[0]
    return np.array([np.mean(lh ** k) for k in range(1, mk + 1)])

def _entropy(w):
    """p = λ/Σλ dagiliminin Shannon entropisi, ln(dim) ile normalize -> [0,1]."""
    w = np.clip(np.asarray(w, float), 0.0, None)
    tot = w.sum()
    if tot <= 0 or len(w) < 2:
        return 0.0
    p = w / tot
    S = -np.sum(p * np.log(p + 1e-15))
    return float(S / np.log(len(w)))

# ------------------------------------------------------- 1) NEWTON (dim 50)

def newton_residual(seq, law, win=10, mk=8):
    """Ouroboros tutarlilik testi.

    Yasa + tohumdan nesneyi geri kur; geri kurulanin spektral guc toplamlari
    (momentler = Tr(G^k) izleri) orijinalinkiyle ortusuyor mu?
    Newton ozdesliklerinin ruhu: yasa ve spektrum ayni guc toplamlarini
    anlatmak zorunda. Tam yasali (C-finite) nesnede ~0; yasasiz nesnede buyuk.
    """
    s = np.asarray(seq, float)
    o = len(law)
    if o == 0 or len(s) < 2 * o:
        return 1.0
    r = list(s[:o])
    for _ in range(len(s) - o):
        nxt = float(np.dot(law, r[-o:][::-1]))
        # patlayan yasalara karsi kirpma; karsilastirma zaten log uzayinda
        r.append(float(np.clip(nxt, -1e12, 1e12)))
    r = np.array(r[: len(s)])
    w_obs = _hankel_gram_spectrum(s, win, center=True)
    w_rec = _hankel_gram_spectrum(r, win, center=True)
    mu_o, mu_r = _shape_moments(w_obs, mk), _shape_moments(w_rec, mk)
    shape = np.linalg.norm(mu_o - mu_r) / (np.linalg.norm(mu_o) + 1e-12)
    energy = abs(np.log((w_obs.sum() + 1e-12) / (w_rec.sum() + 1e-12))) / 10.0
    return float(shape + energy)

# ------------------------------------------------------------ 2) Q (dim 59)

def q_factor(roots):
    """Yasa koku z = r·e^{iθ} bir moddur: θ salinim, |ln r| sonum.

    Q = θ / (2|ln r|) — fizikteki kalite faktoru.
    Birim cember (r=1) bu sistemin KRITIK CIZGISI: Q -> sonsuz, kayipsiz mod.
    Reel pozitif kok (θ=0): salinim yok, Q=0.

    Doner: (Q_max, kritiklige_uzaklik = min|ln r|).
    """
    Q_max, crit = 0.0, np.inf
    for z in np.atleast_1d(np.asarray(roots, complex)):
        rr = abs(z)
        if rr < 1e-12:
            continue
        d = abs(np.log(rr))
        crit = min(crit, d)
        theta = abs(np.angle(z))
        if theta > 1e-9:
            Q_max = max(Q_max, theta / (2 * d) if d > 1e-15 else 1e9)
    if not np.isfinite(crit):
        crit = 0.0
    return float(Q_max), float(crit)

# ------------------------------------------------- 3) AKIS (dim 69, 70, 71)

def spectral_flow(seq, win=8, frame=None, hop=None):
    """Kayan cercevede spektrum: kimligin zaman icindeki hareketi.

      akis[0]  baskin-mod suruklenmesi  mean |Δ(λ₁/Σλ)|
      akis[1]  toplam enerji akisi      mean |Δ ln Σλ|
      akis[2]  faz kaymasi              mean (1 − |⟨v₁(t), v₁(t+1)⟩|)
               (ozvektor donmesi — spectral flow'un yon bileseni)

    Duragan yasa -> ~0. Rejim degisimi -> buyuk. Faz-3'un tohumu: kimlige
    ozvektor izini geri veren ilk dim budur.
    """
    s = _log_compress(seq)
    if frame is None:
        frame = max(2 * win, 12)
    if len(s) < frame + 4:
        return 0.0, 0.0, 0.0
    if hop is None:
        hop = max(1, frame // 4)
    doms, energies, tops = [], [], []
    w_ = max(2, min(win, frame // 2))
    for st in range(0, len(s) - frame + 1, hop):
        seg = s[st: st + frame]
        H = np.lib.stride_tricks.sliding_window_view(seg, w_).T
        G = H @ H.T
        ew, ev = np.linalg.eigh(G)
        ew = np.clip(ew, 0.0, None)
        doms.append(ew[-1] / (ew.sum() + 1e-12))
        energies.append(np.log(ew.sum() + 1e-12))
        tops.append(ev[:, -1])
    if len(doms) < 2:
        return 0.0, 0.0, 0.0
    drift = float(np.mean(np.abs(np.diff(doms))))
    eflow = float(np.mean(np.abs(np.diff(energies))))
    rot = float(np.mean([1.0 - abs(float(np.dot(tops[i], tops[i + 1])))
                         for i in range(len(tops) - 1)]))
    return drift, eflow, rot

# ---------------------------------------------------- 4) RESH (dim 80-82)

def resh_entropies(seq, win=10):
    """Hankel Gram operatorunu ikiye bol: ilk yarim modlar / ikinci yarim.

    S_tot (butun), S_alt (altsistem), S_cev (cevre) — von Neumann analogu.
    Karsilikli bilgi I = S_alt + S_cev − S_tot: parcalarin dolanikligi.
    Voiculescu dim'lerinin sordugu 'parcalar serbest mi?' sorusunun entropik ikizi.
    """
    s = _log_compress(seq)
    if len(s) < win + 1:
        win = max(4, len(s) // 2)
    H = np.lib.stride_tricks.sliding_window_view(s, win).T
    G = H @ H.T
    h = max(1, win // 2)
    S_tot = _entropy(np.linalg.eigvalsh(G))
    S_alt = _entropy(np.linalg.eigvalsh(G[:h, :h]))
    S_cev = _entropy(np.linalg.eigvalsh(G[h:, h:]))
    return float(S_tot), float(S_alt), float(S_cev)

def mutual_information(S_tot, S_alt, S_cev):
    """I = S_alt + S_cev − S_tot (normalize entropilerden, analog buyukluk)."""
    return float(S_alt + S_cev - S_tot)
