"""Fit'siz ÜRETİM — FitlessLM: yönlü ortak-geçiş → SVD log-bilineer → autoregressive P(next|ctx).
Gradient YOK. Deterministik (sentetik corpus) kilit: sintagmatik DEVAM doğru, seed-deterministik,
top-k decode çalışır, save/load roundtrip."""
import pytest

pytest.importorskip("torch")
from tantrium.core.generation import FitlessLM


def _corpus():
    # güçlü yönlü desen: 'sun' → 'rises'/'bright'; 'water' → 'flows'/'cold'
    return [
        "the sun rises in the morning and the sun is bright and warm",
        "the bright sun rises early and shines warm light on the field",
        "the water flows down the river and the water is cold and clear",
        "the cold water flows fast down the river toward the wide sea",
    ] * 30


def _lm():
    lm = FitlessLM(max_vocab=200, window=4)
    lm.update(_corpus())
    lm.fit(dim=12, min_count=2)
    return lm


def test_next_words_syntagmatic():
    """Sintagmatik DEVAM (benzerlik değil): 'sun' bağlamı 'rises/bright' getirir."""
    lm = _lm()
    nxt = {w for w, _ in lm.next_words("the sun", k=8)}
    assert nxt & {"rises", "bright", "warm", "shines"}


def test_generation_deterministic_and_nonempty():
    """seed → birebir aynı; üretim boş değil + prompt'la başlar."""
    lm = _lm()
    a = lm.generate("the sun", n_tokens=10, seed=7)
    b = lm.generate("the sun", n_tokens=10, seed=7)
    assert a == b and len(a.split()) >= 5
    assert a.startswith("the sun")


def test_generation_stays_in_vocab():
    """Üretilen her token modelin vocab'ında (uydurma token yok)."""
    lm = _lm()
    out = lm.generate("the water", n_tokens=12, seed=3).split()
    assert all(w in lm._kidx for w in out)


def test_save_load_roundtrip(tmp_path):
    lm = _lm()
    p = str(tmp_path / "lm")
    lm.save(p)
    lm2 = FitlessLM.load(p)
    assert lm2._kvocab == lm._kvocab                 # vocab korunur
    a = lm2.generate("the sun", n_tokens=8, seed=1)  # yüklenen model kendi içinde deterministik
    b = lm2.generate("the sun", n_tokens=8, seed=1)
    assert a == b and len(a.split()) >= 5
    assert all(w in lm2._kidx for w in a.split())
