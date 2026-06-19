"""Fitsiz DERİNLİK — contextual_embed: statik gömme + L-katmanlı fitsiz attention → bağlamsal
temsil. Statik gömme kelime başına TEK vektör (polisemi çözemez); attention katmanı token'ı
bağlama göre kaydırır (transformer'ın contextual yaptığı, eğitimsiz). Sentetik gömmeyle
deterministik kilitlenir: aynı hedef, iki bağlamda FARKLI kümeye kayar.
"""
import numpy as np
import tantrium


def _inject(ai, vocab, vecs):
    E = np.asarray(vecs, dtype=float)
    ai._embeddings = (E, list(vocab), {w: i for i, w in enumerate(vocab)})


def test_context_shifts_target_to_correct_cluster():
    ai = tantrium.AI()
    # x = belirsiz hedef (iki küme ortası); a* küme A, b* küme B
    vocab = ["x", "a1", "a2", "a3", "b1", "b2", "b3"]
    vecs = [[0.5, 0.5], [1, 0], [1, 0.05], [0.95, 0.0], [0, 1], [0.05, 1], [0.0, 0.95]]
    _inject(ai, vocab, vecs)
    ra = ai.contextual_embed("x a1 a2 a3", "x", k=3, layers=2)
    rb = ai.contextual_embed("x b1 b2 b3", "x", k=3, layers=2)
    near_a = {w for w, _ in ra["nearest"]}
    near_b = {w for w, _ in rb["nearest"]}
    # A bağlamında x A-kümesine, B bağlamında B-kümesine yakın → bağlam kaydırdı
    assert near_a & {"a1", "a2", "a3"}
    assert near_b & {"b1", "b2", "b3"}
    assert near_a != near_b                       # AYNI kelime, FARKLI bağlamsal temsil


def test_no_embeddings_is_honest():
    ai = tantrium.AI()
    ai._embeddings = (np.zeros((0, 0)), [], {})
    r = ai.contextual_embed("the cell membrane", "cell")
    assert r["nearest"] == []
    assert "reason" in r
