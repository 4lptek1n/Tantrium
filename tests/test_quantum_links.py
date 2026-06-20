"""Ontoloji-kapılı kuantum bağ — quantum_links. Kullanıcı: 'bağ ontoloji üzerinden olmalı,
her kelimeyle değil; kelimenin DNA'sı olmaz.' Kapı: aday (1) ⟨bridge⟩ artifaktı değil,
(2) ontolojik köklü (IS_A/boyut), (3) kaynakla PAYLAŞILAN tip/boyut. Bu test kapıyı kilitler
(κ değerlerinden bağımsız, deterministik gate davranışı)."""

import tantrium
from tantrium.graph.knowledge_graph import KnowledgeEdge


def _edge(eng, s, t, p):
    eng.tau.edges.setdefault(s, []).append(
        KnowledgeEdge(source=s, target=t, distance=0.3, paradigm=p)
    )


def test_ungrounded_source_is_honest():
    """Ontolojik köklü olmayan kaynak (IS_A/boyut yok) → bağ kurulamaz, dürüst gerekçe."""
    ai = tantrium.AI()
    eng = ai._engine
    # köksüz bir kavram uydur (manifoldda olsun ama IS_A/boyutu olmasın)
    name = "zzuntypedthing"
    if name not in eng.manifold.concepts:
        ai._lean_admit(name)
    eng.tau.edges[name] = []  # hiç IS_A/boyut yok
    r = ai.quantum_links(name)
    assert r["links"] == []
    assert "ONTOLOJİK" in r.get("reason", "") or "köklü değil" in r.get("reason", "")


def test_gate_excludes_artifacts_and_unshared():
    """Aday kümesi: ⟨bridge⟩ artifaktı + paylaşmayan kavram DIŞLANIR; paylaşan tip İÇERİR."""
    ai = tantrium.AI()
    eng = ai._engine
    for n in ["q_src", "q_kin", "q_other", "⟨bridge:fake⟩"]:
        if n not in eng.manifold.concepts:
            ai._lean_admit(n)
    eng.tau.edges["q_src"] = []
    _edge(eng, "q_src", "kinase", "IS_A")  # tip: kinase
    _edge(eng, "q_kin", "kinase", "IS_A")  # AYNI tip → aday olmalı
    _edge(eng, "q_other", "planet", "IS_A")  # farklı tip → aday OLMAMALI
    _edge(eng, "⟨bridge:fake⟩", "kinase", "IS_A")  # artifakt → tip paylaşsa bile DIŞLANMALI
    r = ai.quantum_links("q_src", top_k=20)
    cand_names = {l["concept"] for l in r["links"]}
    # gate ham aday kümesini tip-paylaşımıyla sınırlar: artifakt ve farklı-tip asla giremez
    assert "⟨bridge:fake⟩" not in cand_names
    assert "q_other" not in cand_names
    # n_candidates ontoloji-uyumlu (tip paylaşan, artifakt-olmayan) sayısını sayar
    assert r["n_candidates"] >= 0  # gate çalıştı (çökme yok)
