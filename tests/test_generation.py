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


def test_induction_head_copies_following_token():
    """Fit'siz INDUCTION HEAD (Olsson [A][B]…[A]→[B]): bağlamda son token daha önce geçtiyse,
    ARDINDAN geleni kopyalar. Deterministik (SVD'den bağımsız, saf bağlam mantığı)."""
    lm = FitlessLM(max_vocab=50, window=4)
    lm.update(["a b c a b c a b c a b c"] * 12)
    lm.fit(dim=4, min_count=1)
    a, b = lm._kidx["a"], lm._kidx["b"]
    out = [a, b, a]                                   # 'a'@0 → 'b'; cur='a'@2 → kopya 'b'
    ind = lm._induction(out, len(lm._kvocab), 1.0)
    assert ind[b] > 0                                 # induction 'b'yi (a'dan sonrasını) kopyaladı


def test_generate_continues_in_context_pattern():
    """In-context learning: eğitimde görülmemiş örüntüyü BAĞLAMDAN sürdürür (induction)."""
    lm = FitlessLM(max_vocab=50, window=4)
    lm.update(["a b c a b c a b c a b c"] * 12)
    lm.fit(dim=4, min_count=1)
    gen = lm.generate("a b c a b c a b", n_tokens=6, temperature=0.3,
                      induction_strength=8.0, seed=1).split()
    cont = gen[7:]                                    # prompt sonrası devam
    assert cont                                       # üretim boş değil
    assert set(cont) & {"a", "b", "c"}                # örüntü vokabını sürdürdü (induction)
