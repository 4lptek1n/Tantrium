"""İki-modlu kesinleştirme: matematik → TÜRET (ağsız), dünya-bilgisi → ARAŞTIR.

Kullanıcı: 'matematik girdide internete gerek yok — bilmediğini biliyor, genişliyor,
hesaplıyor.' _ensure_certain artık girdi tipine göre yöntem seçer: gerçek-math nesnesi
(molekül/sayı/ispat) İNTERNETE GİTMEZ, türetir; dünya-bilgisi araştırır.
"""
import tantrium


def test_math_object_never_researches(monkeypatch):
    """Saf sayı dizisi (math-core) → _research_deep ÇAĞRILMAZ (internet yok)."""
    ai = tantrium.AI()
    called = {"research": 0, "derive": 0}
    monkeypatch.setattr(ai, "_research_deep",
                        lambda *a, **k: called.__setitem__("research", called["research"] + 1))
    orig_derive = ai._derive_certain
    monkeypatch.setattr(ai, "_derive_certain",
                        lambda t: (called.__setitem__("derive", called["derive"] + 1) or False))

    topic, facts, learned = ai._ensure_certain("2 3 5 7 11")   # saf sayılar = math-core
    assert called["research"] == 0          # internete GİTMEDİ
    assert called["derive"] == 1            # türetme yolunu seçti


def test_smiles_routes_to_derivation(monkeypatch):
    """Geçerli SMILES (math-core) → türetme yolu, araştırma DEĞİL. (RDKit yoksa atla.)"""
    import pytest
    from tantrium.core.meaning_pipeline import _is_math_core_object
    ai = tantrium.AI()
    if not _is_math_core_object(ai._engine, "CCO"):
        pytest.skip("SMILES tespiti yok (RDKit kurulu değil) — math-core ayrımı sayı/teoremle test edilir")
    hit = {"research": 0, "derive": 0}
    monkeypatch.setattr(ai, "_research_deep",
                        lambda *a, **k: hit.__setitem__("research", hit["research"] + 1))
    monkeypatch.setattr(ai, "_derive_certain",
                        lambda t: (hit.__setitem__("derive", hit["derive"] + 1) or False))
    ai._ensure_certain("CCO")               # etanol SMILES
    assert hit["research"] == 0 and hit["derive"] == 1


def test_world_topic_still_researches(monkeypatch):
    """Dünya-bilgisi konusu (kelime) → araştırma yolu (mevcut davranış korunur)."""
    ai = tantrium.AI()
    hit = {"research": 0, "derive": 0}
    monkeypatch.setattr(ai, "_tau_facts", lambda t: {})        # bilmiyor → araştırmalı
    monkeypatch.setattr(ai, "_research_deep",
                        lambda *a, **k: hit.__setitem__("research", hit["research"] + 1) or 0)
    monkeypatch.setattr(ai, "_derive_certain",
                        lambda t: hit.__setitem__("derive", hit["derive"] + 1) or False)
    ai._ensure_certain("photosynthesis")
    assert hit["research"] == 1 and hit["derive"] == 0


def test_derive_certain_never_adds_world_relation_edges():
    """F24 sınırı: _derive_certain matematik nesnesine dünya-ilişkisi (kausal) kenarı EKLEMEZ.

    Eski hata: derive_transitive_hypotheses (dünya-relasyon motoru) çağrılıyordu → math'e
    INHIBITS/ACTIVATES kenarı eklenebilirdi (kontaminasyon). Düzeltildi: sayı/SMILES no-op.
    """
    ai = tantrium.AI()
    e = ai._engine
    # saf sayısal kavram (math-core, theorem domain DEĞİL) — hiçbir kausal kenar eklenmemeli
    topic = "2 3 5 7 11 13"
    before = {k: len(v) for k, v in e.tau.edges.items()}
    res = ai._derive_certain(topic)
    after = {k: len(v) for k, v in e.tau.edges.items()}
    assert res is False                      # sayı dizisi: kontamine etmez, no-op
    # hiçbir düğüme yeni (dünya-ilişkisi) kenar eklenmedi
    assert all(after.get(k, 0) == before.get(k, 0) for k in after)


def test_derive_certain_does_not_call_transitive_engine(monkeypatch):
    """Kanıt: dünya-relasyon motoru (derive_transitive_hypotheses) ÇAĞRILMAZ."""
    import tantrium.reasoning.causal_rules as cr
    ai = tantrium.AI()
    called = {"n": 0}
    monkeypatch.setattr(cr, "derive_transitive_hypotheses",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1) or [])
    ai._derive_certain("2 3 5 7 11")
    assert called["n"] == 0                  # math çözümünde dünya-motoru hiç çağrılmadı
